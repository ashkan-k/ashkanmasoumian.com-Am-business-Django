# Widen colour fields for rgba() values, drop legacy pricing numbers so an
# emptied price line stays empty, and clear auto-migrated "000" leftovers.

import re

from django.db import migrations, models


_ZEROISH = re.compile(r"^0+(\.0+)?$")


def forwards(apps, schema_editor):
    PricingPlan = apps.get_model("core", "PricingPlan")
    for plan in PricingPlan.objects.all():
        changed = []
        for field in ("price_text_en", "price_text_fa", "price_text_ar"):
            value = (getattr(plan, field, "") or "").strip()
            # Legacy migration of price=0 + cents="00" produced "000".
            if value and _ZEROISH.match(value):
                setattr(plan, field, "")
                changed.append(field)
        if plan.price is not None or plan.currency or plan.cents:
            plan.price = None
            plan.currency = ""
            plan.cents = ""
            changed.extend(["price", "currency", "cents"])
        if changed:
            plan.save(update_fields=list(dict.fromkeys(changed)))


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_pricingplan_price_text_and_section_fixes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sectionstyle",
            name="background_color",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Pick from the palette or type a value such as #530e69",
                max_length=50,
                verbose_name="Background Colour",
            ),
        ),
        migrations.AlterField(
            model_name="sectionstyle",
            name="card_background",
            field=models.CharField(blank=True, default="", max_length=50, verbose_name="Card Background"),
        ),
        migrations.AlterField(
            model_name="sectionstyle",
            name="card_text_color",
            field=models.CharField(blank=True, default="", max_length=50, verbose_name="Card Text Colour"),
        ),
        migrations.AlterField(
            model_name="sectionstyle",
            name="heading_color",
            field=models.CharField(blank=True, default="", max_length=50, verbose_name="Heading Colour"),
        ),
        migrations.AlterField(
            model_name="sectionstyle",
            name="overlay_color",
            field=models.CharField(blank=True, default="", max_length=50, verbose_name="Overlay Colour"),
        ),
        migrations.AlterField(
            model_name="sectionstyle",
            name="text_color",
            field=models.CharField(blank=True, default="", max_length=50, verbose_name="Body Text Colour"),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
