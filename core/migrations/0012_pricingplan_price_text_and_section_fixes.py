# Pricing plans: free-text price line + clear seeded eyebrows/titles that
# fought the new homepage defaults, and dial down overlays that hid uploads.

from decimal import Decimal

from django.db import migrations, models


SEEDED_CLEAR = {
    "countdown": {
        "subheading_en": ("Don't wait", "DON'T WAIT"),
        "subheading_fa": ("منتظر نمانید",),
        "subheading_ar": ("لا تنتظر",),
    },
    "why": {
        "subheading_en": ("Why AM Business", "WHY AM BUSINESS"),
        "subheading_fa": ("چرا ما", "چرا ای ام بیزینس"),
        "subheading_ar": ("لماذا إي إم بيزنس",),
    },
    "services": {
        "subheading_en": ("Services", "SERVICES"),
        "subheading_fa": ("خدمات",),
        "subheading_ar": ("الخدمات",),
    },
    "pricing": {
        "subheading_en": ("Prices for everyone", "PRICES FOR EVERYONE"),
        "subheading_fa": ("قیمت برای همه",),
        "subheading_ar": ("أسعار للجميع",),
        "title_en": ("Pricing",),
        "title_fa": ("قیمت‌گذاری",),
        "title_ar": ("الأسعار",),
    },
    "team": {
        "subheading_en": ("Team", "TEAM"),
        "subheading_fa": ("تیم",),
        "subheading_ar": ("الفريق",),
    },
}


def forwards(apps, schema_editor):
    PricingPlan = apps.get_model("core", "PricingPlan")
    SectionStyle = apps.get_model("core", "SectionStyle")

    for plan in PricingPlan.objects.all():
        if (plan.price_text_en or "").strip():
            continue
        if plan.price is None:
            continue
        currency = plan.currency or ""
        cents = plan.cents or ""
        # Keep a readable legacy line so existing cards do not go blank.
        amount = plan.price
        if isinstance(amount, Decimal):
            amount_str = f"{amount:f}".rstrip("0").rstrip(".")
        else:
            amount_str = str(amount)
        plan.price_text_en = f"{currency}{amount_str}{cents}".strip()
        plan.save(update_fields=["price_text_en"])

    for section, fields in SEEDED_CLEAR.items():
        style = SectionStyle.objects.filter(section=section).first()
        if style is None:
            continue
        changed = []
        for field, seeded_values in fields.items():
            current = (getattr(style, field, "") or "").strip()
            if current in seeded_values:
                setattr(style, field, "")
                changed.append(field)
        if changed:
            style.save(update_fields=changed)

    # Background uploads were invisible under the seeded 92% purple overlay.
    for style in SectionStyle.objects.exclude(background_image="").exclude(background_image=None):
        if (style.overlay_opacity or 0) >= 70:
            style.overlay_opacity = 35
            style.save(update_fields=["overlay_opacity"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_clear_removed_eyebrows"),
    ]

    operations = [
        migrations.AddField(
            model_name="pricingplan",
            name="price_text_ar",
            field=models.CharField(blank=True, default="", max_length=300, verbose_name="Price / Options (AR)"),
        ),
        migrations.AddField(
            model_name="pricingplan",
            name="price_text_en",
            field=models.CharField(
                blank=True,
                default="",
                help_text='Free text shown on the card — e.g. "$975", "From $500", or an options line.',
                max_length=300,
                verbose_name="Price / Options (EN)",
            ),
        ),
        migrations.AddField(
            model_name="pricingplan",
            name="price_text_fa",
            field=models.CharField(blank=True, default="", max_length=300, verbose_name="Price / Options (FA)"),
        ),
        migrations.AlterField(
            model_name="pricingplan",
            name="cents",
            field=models.CharField(blank=True, default="", max_length=5, verbose_name="Cents (legacy)"),
        ),
        migrations.AlterField(
            model_name="pricingplan",
            name="currency",
            field=models.CharField(blank=True, default="", max_length=10, verbose_name="Currency (legacy)"),
        ),
        migrations.AlterField(
            model_name="pricingplan",
            name="price",
            field=models.DecimalField(
                blank=True, decimal_places=2, default=None, max_digits=10, null=True, verbose_name="Price (legacy)"
            ),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
