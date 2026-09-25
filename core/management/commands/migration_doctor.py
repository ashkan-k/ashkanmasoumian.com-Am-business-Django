"""Read-only migration diagnostics for a checkout that has drifted.

Written for the incident where a server had a local-only merge migration that
collided with the migrations committed in the repository::

    CommandError: Conflicting migrations detected; multiple leaf nodes in the
    migration graph: (0004_merge_20260922_1842, 0007_feature_icons in core).

The command never writes to the database and never deletes files. It reports
what is applied, what exists only on this machine, whether the columns the
pending migrations expect are already present, and then prints the exact
commands to run.

    python manage.py migration_doctor
"""
import glob
import os
import subprocess

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder

APP = "core"

# Columns the recent core migrations introduce. A migration that "adds" a
# column which already exists fails with "duplicate column name".
EXPECTED_COLUMNS = {
    "core_service": ["title_ar", "description_ar"],
    "core_navigation": ["title_ar"],
    "core_page": ["title_ar", "content_ar", "meta_title_ar", "meta_description_ar"],
    "core_sitesettings": ["site_name_ar", "address_ar", "meta_description_ar", "copyright_text_ar"],
    "core_sectionstyle": ["item_limit"],
    "core_feature": ["custom_icon", "custom_svg"],
    "core_eventcountdown": ["image", "image_alt_en", "image_alt_fa", "image_alt_ar", "image_position"],
}

ARABIC_MIGRATION = "0003_add_arabic_translations"


class Command(BaseCommand):
    help = "Report migration drift (applied state, local-only files, missing columns) without changing anything"

    def add_arguments(self, parser):
        parser.add_argument(
            "--app", default=APP,
            help=f"App label to inspect (default: {APP})",
        )
        parser.add_argument(
            "--fix-history", action="store_true",
            help=(
                "Record a migration as applied when its columns are verifiably already "
                "in the database and only its history row is missing. Without this flag "
                "the command never writes anything."
            ),
        )
        parser.add_argument(
            "--clean-local", action="store_true",
            help=(
                "Delete the migration files that exist only on this machine (they are not "
                "in git) and are what create the extra branch behind 'Conflicting "
                "migrations detected'. Prints every file it removes."
            ),
        )

    def handle(self, *args, **options):
        app = options["app"]

        self._print_applied(app)
        local_only = self._print_local_only(app)

        if options["clean_local"] and local_only:
            self._remove_local_only(app, local_only)
            local_only = []

        leaves = self._print_leaves()
        columns = self._print_columns()
        inconsistent = self._print_history_check(app)
        self._print_recommendation(app, local_only, leaves, columns, inconsistent,
                                   fix=options["fix_history"])

    def _remove_local_only(self, app, names):
        """Delete untracked migration files (and their bytecode caches)."""
        migrations_dir = os.path.join(app, "migrations")
        pycache = os.path.join(migrations_dir, "__pycache__")
        removed = []
        for name in names:
            path = os.path.join(migrations_dir, name)
            try:
                os.remove(path)
                removed.append(path)
            except OSError as exc:  # noqa: BLE001
                self.stdout.write(self.style.ERROR(f"   could not remove {path}: {exc}"))
                continue
            # A stale __pycache__ entry must not keep the module importable.
            stem = os.path.splitext(name)[0]
            for cached in glob.glob(os.path.join(pycache, f"{stem}.*.pyc")):
                try:
                    os.remove(cached)
                    removed.append(cached)
                except OSError:
                    pass

        self.stdout.write(self.style.SUCCESS(
            f"\n   --clean-local: removed {len(removed)} file(s)"))
        for path in removed:
            self.stdout.write(f"      {path}")

    # ── sections ──
    def _print_applied(self, app):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n1. Migrations recorded as applied ({app})"))
        applied = [
            (name, applied_at)
            for app_label, name, applied_at in MigrationRecorder(connection)
            .migration_qs.filter(app=app)
            .order_by("id")
            .values_list("app", "name", "applied")
        ]
        if not applied:
            self.stdout.write("   (none)")
        for name, applied_at in applied:
            self.stdout.write(f"   [X] {name}  ({applied_at:%Y-%m-%d %H:%M} UTC)")

    def _print_local_only(self, app):
        migrations_dir = os.path.join(app, "migrations")
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n2. Migration files in {migrations_dir}/ that are NOT in git"
        ))
        local_only = []
        try:
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard", "--", migrations_dir],
                capture_output=True, text=True, timeout=20,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or f"git exited {result.returncode}")
            local_only = [
                os.path.basename(line.strip())
                for line in result.stdout.splitlines()
                if line.strip().endswith(".py")
            ]
        except Exception as exc:  # noqa: BLE001 - git may be unavailable
            self.stdout.write(self.style.WARNING(f"   could not run git: {exc}"))
            return []

        if not local_only:
            self.stdout.write("   (none - nothing to clean up)")
        for name in sorted(local_only):
            self.stdout.write(self.style.WARNING(f"   ?? {name}   <- exists only on this machine"))
        return sorted(local_only)

    def _print_leaves(self):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n3. Migration graph leaves ({APP})"))
        loader = MigrationLoader(connection, ignore_no_migrations=True)
        leaves = sorted(name for app, name in loader.graph.leaf_nodes() if app == APP)
        for name in leaves:
            marker = "" if len(leaves) == 1 else "   <- CONFLICT"
            self.stdout.write(f"   {name}{marker}")
        if len(leaves) > 1:
            self.stdout.write(self.style.ERROR(
                "   Multiple leaves: this is what raises 'Conflicting migrations detected'."))
        return leaves

    def _print_columns(self):
        self.stdout.write(self.style.MIGRATE_HEADING("\n4. Columns the pending migrations expect"))
        existing_tables = set(connection.introspection.table_names())
        present = {}
        with connection.cursor() as cursor:
            for table, wanted in EXPECTED_COLUMNS.items():
                if table not in existing_tables:
                    self.stdout.write(f"   {table}: table does not exist yet")
                    present[table] = set()
                    continue
                actual = {c.name for c in connection.introspection.get_table_description(cursor, table)}
                present[table] = actual
                for column in wanted:
                    found = column in actual
                    style = self.style.SUCCESS if found else self.style.WARNING
                    self.stdout.write(style(
                        f"   {'OK ' if found else 'MISSING'} {table}.{column}"))
        return present

    def _print_history_check(self, app):
        """Report applied migrations whose dependencies are not applied.

        Django refuses to run anything in that state with
        InconsistentMigrationHistory, so `migrate --fake` cannot be used to
        repair it — the history row has to be written directly.
        """
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n5. Applied history consistency ({app})"))
        recorder = MigrationRecorder(connection)
        applied = set(recorder.applied_migrations())
        loader = MigrationLoader(connection, ignore_no_migrations=True)
        inconsistent = []
        for key in sorted(applied):
            if key[0] != app or key not in loader.graph.nodes:
                continue
            for parent in loader.graph.node_map[key].parents:
                if parent[0] == app and parent not in applied:
                    inconsistent.append((key[1], parent[1]))
        if not inconsistent:
            self.stdout.write("   OK  every applied migration has its dependencies applied")
        for child, parent in inconsistent:
            self.stdout.write(self.style.ERROR(
                f"   {child} is applied but its dependency {parent} is not "
                "- this raises InconsistentMigrationHistory"))
        return inconsistent

    def _print_recommendation(self, app, local_only, leaves, columns, inconsistent, fix=False):
        self.stdout.write(self.style.MIGRATE_HEADING("\n6. What to do"))
        steps = []

        if local_only:
            steps.append(
                "These files exist only on this machine and are what created the extra branch. "
                "Back up the database, then remove them:\n"
                + "".join(f"      rm {app}/migrations/{name}\n" for name in local_only)
                + "   (or just re-run this command with --clean-local to delete them)"
            )
        if len(leaves) > 1:
            steps.append(
                "More than one leaf remains after removing local-only files. Either commit a merge "
                "migration (python manage.py makemigrations --merge) or delete the stale branch."
            )
        if not steps:
            steps.append("The migration graph is clean.")

        arabic_present = any(
            "title_ar" in columns.get(table, set())
            for table in ("core_service", "core_page", "core_navigation")
        )
        recorder = MigrationRecorder(connection)
        arabic_applied = recorder.migration_qs.filter(app=app, name=ARABIC_MIGRATION).exists()

        if arabic_present and not arabic_applied:
            # `migrate --fake` only works when nothing already depends on it.
            blocked_by_dependents = any(parent == ARABIC_MIGRATION for _child, parent in inconsistent)
            if blocked_by_dependents:
                command = (
                    "python manage.py shell -c \""
                    "from django.db.migrations.recorder import MigrationRecorder;"
                    f"MigrationRecorder.Migration.objects.get_or_create(app='{app}', name='{ARABIC_MIGRATION}')\""
                )
                target = inconsistent[0][0] if inconsistent else ARABIC_MIGRATION
                steps.append(
                    f"The Arabic columns are already in the database but {ARABIC_MIGRATION} is not "
                    f"recorded as applied, while {target} already depends on it. `migrate --fake` "
                    "cannot be used here because Django rejects the inconsistent history first, so "
                    "add the missing history row directly:\n"
                    f"      {command}\n"
                    "   (re-run this command with --fix-history to do exactly that)"
                )
                if fix:
                    from django.db.migrations.recorder import MigrationRecorder as Recorder

                    _, created = Recorder.Migration.objects.get_or_create(
                        app=app, name=ARABIC_MIGRATION)
                    self.stdout.write(self.style.SUCCESS(
                        f"   --fix-history: recorded {ARABIC_MIGRATION} as applied "
                        f"({'inserted' if created else 'already present'})"))
            else:
                steps.append(
                    f"The Arabic columns are already in the database but {ARABIC_MIGRATION} is not "
                    "recorded as applied (an older, differently named migration added them). Tell "
                    "Django not to run it again:\n"
                    f"      python manage.py migrate {app} {ARABIC_MIGRATION} --fake"
                )
        elif arabic_present and arabic_applied:
            steps.append("The Arabic migration is applied and its columns exist. Nothing to fake.")
        elif not arabic_present:
            steps.append("The Arabic columns are missing; the normal migrate will add them.")

        if columns.get("core_sectionstyle") is not None and "item_limit" not in columns.get("core_sectionstyle", set()):
            steps.append(
                "sectionstyle.item_limit is missing, so 0006 has not run yet. Make sure you are on a "
                "commit that contains the fixed 0005_seed_section_styles.py (it must NOT seed "
                "item_limit - that column is created by 0006)."
            )

        for index, step in enumerate(steps, 1):
            self.stdout.write(f"   {index}. {step}")

        self.stdout.write(self.style.MIGRATE_HEADING("\nThen:"))
        self.stdout.write(f"      python manage.py migrate {app}")
        self.stdout.write(self.style.WARNING(
            "\nAlways back up the database before removing migration files:\n"
            "      cp db.sqlite3 db.sqlite3.bak-$(date +%F-%H%M)\n"
        ))
