# Seeds one SectionStyle row per editable section.
#
# The countdown and pricing sections ship with the purple brand background
# they always had, so the dashboard shows the real current colours and the
# rendered site is unchanged until an editor picks something else.

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
        # 0 = every active pricing plan is rendered (the old hard-coded
        # limit of three hid plans that existed in the dashboard).
        "item_limit": 0,
    },
    # These two kept their previous cap so the homepage layout does not
    # change; editors can raise or clear the limit from the dashboard.
    "services": {"show_pattern": False, "item_limit": 8},
    "team": {"show_pattern": False, "item_limit": 4},
    "features": {"show_pattern": False, "item_limit": 0},
    "testimonials": {"show_pattern": False, "item_limit": 0},
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
