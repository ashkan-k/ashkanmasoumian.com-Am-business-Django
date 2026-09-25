# Seeds one SectionStyle row per editable section.
#
# The countdown and pricing sections ship with the purple brand background
# they always had, so the dashboard shows the real current colours and the
# rendered site is unchanged until an editor picks something else.
#
# NOTE: `item_limit` must NOT be set here.  That column is created by
# 0006_section_item_limit, which runs after this migration, and referring to a
# field that does not exist yet in the historical model state raises
# FieldError: Invalid field name(s) for model SectionStyle: 'item_limit'.
# The homepage caps (services 8, team 4) are applied by 0006 instead.

from django.db import migrations

# section key -> field defaults
SEEDS = {
    "countdown": {
        "background_color": "#530e69",
        "overlay_color": "#530e69",
        "overlay_opacity": 92,
        "show_pattern": True,
    },
    "pricing": {
        "background_color": "#530e69",
        "overlay_color": "#530e69",
        "overlay_opacity": 92,
        "show_pattern": True,
        # item_limit stays 0 (the 0006 default) = every active pricing plan is
        # rendered.  The old hard-coded limit of three hid plans that existed
        # in the dashboard.
    },
    # These two keep their previous caps, applied by 0006_section_item_limit so
    # the homepage layout does not change; editors can raise or clear the limit
    # from the dashboard.
    "services": {"show_pattern": False},
    "team": {"show_pattern": False},
    "features": {"show_pattern": False},
    "testimonials": {"show_pattern": False},
    "why": {"show_pattern": False},
    "about_home": {"show_pattern": False},
    "newsletter": {"show_pattern": False},
}


def seed(apps, schema_editor):
    SectionStyle = apps.get_model("core", "SectionStyle")
    for section, defaults in SEEDS.items():
        SectionStyle.objects.get_or_create(section=section, defaults=defaults)


def unseed(apps, schema_editor):
    SectionStyle = apps.get_model("core", "SectionStyle")
    SectionStyle.objects.filter(section__in=list(SEEDS)).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_sectionstyle_eventcountdown_image_and_more"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
