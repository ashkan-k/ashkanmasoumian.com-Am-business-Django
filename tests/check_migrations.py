"""Verify the migration chain on throwaway databases — never touches db.sqlite3.

Two things this guards against:

  1. the incident that started it all — `migrate` applying 0004_sectionstyle_…
     and then crashing inside 0005_seed_section_styles with
     ``FieldError: Invalid field name(s) for model SectionStyle: 'item_limit'``
     because 0005 seeded a column that 0006 only creates afterwards;
  2. the consolidation onto "Sections & Backgrounds" — 0009 moves the countdown
     and home-block headings into SectionStyle before dropping the duplicate
     columns, so an existing database must not lose the text on screen.

Run from the project root:

    $env:PYTHONIOENCODING="utf-8"; .\\.venv\\Scripts\\python.exe tests\\check_migrations.py

Checks performed:
  1. a brand-new database migrates from zero to the latest migration and gets
     the expected SectionStyle rows and item limits
  2. an old-schema database (migrated up to 0004 only) holding countdown and
     home-block text is upgraded, and that text lands in SectionStyle
  3. migrate is idempotent and no migration is missing for the current models

Note: the chain is deliberately *not* tested in reverse.  ``RemoveField`` on a
NOT NULL column cannot be undone on SQLite once rows exist, which is Django's
documented behaviour; rewinding would need a hand-written data restore.
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
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

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

OLD_SCHEMA = "0004_sectionstyle_eventcountdown_image_and_more"

# What the old schema is seeded with, and where 0009 must put it.
COUNTDOWN_TITLE = "Legacy Countdown Title"
COUNTDOWN_SUBHEADING = "Legacy Subheading"
HOME_ABOUT_BODY = "Legacy about body text"
ABOUT_WHY_TITLE = "Legacy why title"
ABOUT_WHY_BODY = "Legacy why body text"

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


def assert_copied(section, field, expected, label):
    from core.models import SectionStyle

    style = SectionStyle.objects.filter(section=section).first()
    got = getattr(style, field, None) if style else None
    ok = got == expected
    print(f"  {'OK ' if ok else 'BAD'} {label:34} {section}.{field} = {got!r}")
    if not ok:
        failures.append(f"{label}: {section}.{field} = {got!r}, expected {expected!r}")


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

# ────────── 2. old schema (0004) with text, upgraded to the latest ──────────
print(f"\n=== 2. old-schema database ({OLD_SCHEMA}) upgraded to the latest ===")
old_db = os.path.join(tmpdir, "old.sqlite3")
use_db(old_db)
try:
    call_command("migrate", "core", OLD_SCHEMA, verbosity=0, interactive=False)
    print(f"  built the old schema at {OLD_SCHEMA}")

    # Use the historical models, so the rows look exactly like they did then.
    executor = MigrationExecutor(connections["default"])
    apps = executor.loader.project_state([("core", OLD_SCHEMA)]).apps
    EventCountdown = apps.get_model("core", "EventCountdown")
    HomeSection = apps.get_model("core", "HomeSection")
    AboutSection = apps.get_model("core", "AboutSection")

    EventCountdown.objects.create(
        title_en=COUNTDOWN_TITLE, title_fa="عنوان قدیمی", title_ar="عنوان قديم",
        subheading_en=COUNTDOWN_SUBHEADING, subheading_fa="زیرعنوان قدیمی",
        subheading_ar="عنوان فرعي قديم",
        event_date=timezone.now(),
        ended_message_en="done", ended_message_fa="تمام", ended_message_ar="انتهى",
        cta_text_en="go", cta_text_fa="برو", cta_text_ar="اذهب",
        cta_url="#", is_active=True,
    )
    HomeSection.objects.create(
        section_type="home_about",
        title_en="Legacy home title", title_fa="t", title_ar="t",
        subheading_en="Legacy home sub", subheading_fa="s", subheading_ar="s",
        content_en=HOME_ABOUT_BODY, content_fa="متن", content_ar="نص",
        cta_text_en="Read", cta_text_fa="بخوان", cta_text_ar="اقرأ",
        cta_url="/about/", is_active=True,
    )
    AboutSection.objects.create(
        title_en="About", title_fa="د", title_ar="ع",
        content_en="body", content_fa="م", content_ar="ن",
        why_choose_us_title_en=ABOUT_WHY_TITLE,
        why_choose_us_content_en=ABOUT_WHY_BODY,
        is_active=True,
    )
    print("  seeded old-schema rows")

    migrate()
    print("OK  upgraded to the latest migration")
    assert_copied("countdown", "title_en", COUNTDOWN_TITLE, "countdown title moved")
    assert_copied("countdown", "subheading_en", COUNTDOWN_SUBHEADING, "countdown subheading moved")
    assert_copied("about_home", "subtitle_en", HOME_ABOUT_BODY, "home About body moved")
    assert_copied("why", "title_en", ABOUT_WHY_TITLE, "why title moved")
    assert_copied("why", "subtitle_en", ABOUT_WHY_BODY, "why body moved")
    report_limit_values("upgraded")

    # the duplicate columns must really be gone
    with connections["default"].cursor() as cursor:
        cursor.execute("PRAGMA table_info(core_eventcountdown)")
        countdown_cols = {row[1] for row in cursor.fetchall()}
        cursor.execute("PRAGMA table_info(core_homesection)")
        home_cols = {row[1] for row in cursor.fetchall()}
    stale = ({"title_en", "subheading_en"} & countdown_cols) | (
        {"title_en", "subheading_en", "content_en"} & home_cols)
    print(f"  {'OK ' if not stale else 'BAD'} duplicate columns dropped"
          f"{'' if not stale else f' (still present: {sorted(stale)})'}")
    if stale:
        failures.append(f"duplicate columns still present: {sorted(stale)}")
except Exception as exc:  # noqa: BLE001
    failures.append(f"old-schema upgrade failed: {type(exc).__name__}: {exc}")
    print("FAIL old-schema upgrade:", type(exc).__name__, exc)

# ─────────────────────── 3. idempotent & complete ───────────────────────
print("\n=== 3. re-running migrate is a no-op ===")
try:
    call_command("migrate", verbosity=0, interactive=False)
    print("OK  second migrate produced no changes")
except Exception as exc:  # noqa: BLE001
    failures.append(f"second migrate failed: {type(exc).__name__}: {exc}")
    print("FAIL second migrate:", type(exc).__name__, exc)

print("\n=== 4. no migration is missing for the current models ===")
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
