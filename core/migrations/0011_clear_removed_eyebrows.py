# Removes two eyebrow lines the client asked to be gone.
#
# "Don't wait" above the countdown and "Why AM Business" above the Why block were
# seeded by this project (0005 + 0009 copied the countdown one from
# EventCountdown; seed_data filled the Why one), so they are cleared here rather
# than left for the editor to hunt down.  A value is only cleared when it still
# matches the seeded text, so anything typed by hand is kept.
#
# The Subheading field itself stays available on the Sections & Backgrounds page
# and the templates now render the eyebrow only when it has a value.

from django.db import migrations

# section -> {field: seeded value}
SEEDED_EYEBROWS = {
    "countdown": {
        "subheading_en": "Don't wait",
        "subheading_fa": "منتظر نمانید",
        "subheading_ar": "لا تنتظر",
    },
    "why": {
        "subheading_en": "Why AM Business",
        "subheading_fa": "چرا ما",
        "subheading_ar": "لماذا إي إم بيزنس",
    },
}


def clear_seeded_eyebrows(apps, schema_editor):
    SectionStyle = apps.get_model("core", "SectionStyle")
    for section, fields in SEEDED_EYEBROWS.items():
        style = SectionStyle.objects.filter(section=section).first()
        if style is None:
            continue
        changed = []
        for field, seeded_value in fields.items():
            if getattr(style, field, "") == seeded_value:
                setattr(style, field, "")
                changed.append(field)
        if changed:
            style.save(update_fields=changed)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_service_url"),
    ]

    operations = [
        migrations.RunPython(clear_seeded_eyebrows, migrations.RunPython.noop),
    ]
