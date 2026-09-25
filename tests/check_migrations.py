"""Verify the migration chain on throwaway databases — never touches db.sqlite3.

Reproduces the exact incident this was written for: `migrate` applying
0004_sectionstyle_… and then crashing inside 0005_seed_section_styles with

    FieldError: Invalid field name(s) for model SectionStyle: 'item_limit'

because 0005 seeded a column that 0006 only creates afterwards.

Run from the project root:

    $env:PYTHONIOENCODING="utf-8"; .\\.venv\\Scripts\\python.exe tests\\check_migrations.py

Checks performed:
  1. a brand-new database migrates from zero to the latest migration
  2. a copy of the project database rewound to 0004 then migrated forwards
     (the failing state from the incident)
  3. migrate is idempotent, 0005 is reversible, and no migrations are missing
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "am_business.settings")

import django

django.setup()

from django.conf import settings
from django.core.management import call_command
from django.db import connections

PROJECT_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db.sqlite3"
)

# section -> item_limit the seed plus 0006's backfill must end up with
EXPECTED_LIMITS = {
    "countdown": 0,
    "pricing": 0,
    "features": 0,
    "testimonials": 0,
    "why": 0,
    "team": 4,
    "services": 8,
    "about_home": 0,
    "newsletter": 0,
}

failures = []


def use_db(path):
    """Point Django at `path` and drop any open connection."""
    connections.close_all()
    settings.DATABASES["default"]["NAME"] = str(path)


def migrate(*args, **kwargs):
    return call_command("migrate", *args, verbosity=1, interactive=False, **kwargs)


def report_limit_values(label):
    from core.models import SectionStyle

    limits = dict(SectionStyle.objects.values_list("section", "item_limit"))
    print(f"  {label}: {len(limits)} SectionStyle rows")
    for section in sorted(EXPECTED_LIMITS):
        got = limits.get(section)
        want = EXPECTED_LIMITS[section]
        flag = "OK " if got == want else "BAD"
        print(f"    {flag} {section:12} item_limit={got} (expected {want})")
        if got != want:
            failures.append(f"{label}: {section} item_limit={got}, expected {want}")
    unexpected = set(limits) - set(EXPECTED_LIMITS)
    if unexpected:
        failures.append(f"{label}: unexpected seeded sections {sorted(unexpected)}")
    return limits


tmpdir = tempfile.mkdtemp(prefix="migcheck_")
print("throwaway databases in:", tmpdir)

# ─────────────────────────── 1. brand-new database ───────────────────────────
print("\n=== 1. fresh database, migrate from zero ===")
use_db(os.path.join(tmpdir, "fresh.sqlite3"))
try:
    migrate()
except Exception as exc:  # noqa: BLE001 - report any failure, keep going
    failures.append(f"fresh migrate failed: {type(exc).__name__}: {exc}")
    print("FAIL fresh migrate:", type(exc).__name__, exc)
else:
    print("OK  fresh migrate reached the latest migration")
    report_limit_values("fresh")

# ─────────────── 2. copy of the project DB, rewound to 0004 ───────────────
print("\n=== 2. project DB copy, rewound to 0004 then migrated forwards ===")
copy_path = os.path.join(tmpdir, "existing.sqlite3")
if not os.path.exists(PROJECT_DB):
    print("SKIP no db.sqlite3 next to manage.py")
else:
    shutil.copy2(PROJECT_DB, copy_path)
    use_db(copy_path)
    try:
        # Rewind to the state the incident was reported from.
        call_command("migrate", "core", "0004", verbosity=0, interactive=False)
        from django.db.migrations.recorder import MigrationRecorder

        applied = sorted(
            name
            for app, name in MigrationRecorder(connections["default"]).applied_migrations()
            if app == "core"
        )
        print("  core migrations applied after rewind:", applied)
        migrate()
        print("OK  0005 -> 0006 -> 0007 applied cleanly")
        report_limit_values("rewound")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"rewound migrate failed: {type(exc).__name__}: {exc}")
        print("FAIL rewound migrate:", type(exc).__name__, exc)

# ─────────────────────── 3. idempotent & reversible ───────────────────────
print("\n=== 3. re-running migrate is a no-op ===")
try:
    call_command("migrate", verbosity=0, interactive=False)
    print("OK  second migrate produced no changes")
except Exception as exc:  # noqa: BLE001
    failures.append(f"second migrate failed: {type(exc).__name__}: {exc}")
    print("FAIL second migrate:", type(exc).__name__, exc)

print("\n=== 4. 0005 reverses and re-applies ===")
try:
    call_command("migrate", "core", "0004", verbosity=0, interactive=False)
    from core.models import SectionStyle

    after_reverse = SectionStyle.objects.count()
    print(f"  after reversing to 0004: {after_reverse} SectionStyle rows")
    migrate()
    after_reapply = SectionStyle.objects.count()
    print(f"  after re-applying:       {after_reapply} SectionStyle rows")
    if after_reapply != len(EXPECTED_LIMITS):
        failures.append(f"re-apply left {after_reapply} rows, expected {len(EXPECTED_LIMITS)}")
    report_limit_values("re-applied")
except Exception as exc:  # noqa: BLE001
    failures.append(f"reverse/re-apply failed: {type(exc).__name__}: {exc}")
    print("FAIL reverse/re-apply:", type(exc).__name__, exc)

print("\n=== 5. no migration is missing for the current models ===")
try:
    call_command("makemigrations", "--check", "--dry-run", verbosity=0)
    print("OK  models and migrations agree")
except SystemExit as exc:
    failures.append(f"makemigrations --check found pending changes (exit {exc.code})")
    print("FAIL makemigrations --check ->", exc.code)

connections.close_all()
shutil.rmtree(tmpdir, ignore_errors=True)

print("\n=== Result ===")
if failures:
    print(f"{len(failures)} FAILURES:")
    for failure in failures:
        print("  -", failure)
    sys.exit(1)
print("All migration checks passed.")
