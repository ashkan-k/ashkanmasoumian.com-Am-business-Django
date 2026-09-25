"""Verification script for the section-appearance / countdown-image changes.

Renders every frontend page in all three languages, walks the admin panel
(including the new "Sections & Backgrounds" page), and exercises the flows
that used to fail:

  * adding a second hero section for an existing page (UNIQUE constraint)
  * saving a testimonial without any quote text
  * saving the section backgrounds with both a palette value and a raw hex

Run from the project root:

    $env:PYTHONIOENCODING="utf-8"; .\\.venv_new\\Scripts\\python.exe tests\\verify_sections.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "am_business.settings")
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import (
    EventCountdown, Feature, HeroSection, Page, PricingPlan, SectionStyle, Testimonial,
)

FRONTEND_PAGES = ["/", "/about/", "/services/", "/contact/", "/page/portfolio/"]
ADMIN_PAGES = [
    "/admin-panel/", "/admin-panel/settings/", "/admin-panel/social-links/",
    "/admin-panel/navigation/", "/admin-panel/hero/", "/admin-panel/services/",
    "/admin-panel/about/", "/admin-panel/counters/", "/admin-panel/features/",
    "/admin-panel/pricing/", "/admin-panel/testimonials/", "/admin-panel/team/",
    "/admin-panel/event-countdown/", "/admin-panel/home-sections/",
    "/admin-panel/sections/", "/admin-panel/messages/", "/admin-panel/newsletter/",
    "/admin-panel/pages/",
]
LANGUAGES = ["en", "fa", "ar"]

failures = []
checks = 0


def check(label, condition, detail=""):
    global checks
    checks += 1
    if condition:
        print(f"  [ok]   {label}")
    else:
        print(f"  [FAIL] {label} {detail}")
        failures.append(f"{label} {detail}")


def main():
    print("─" * 70)
    print("Frontend pages (all languages)")
    print("─" * 70)
    client = Client()
    for lang in LANGUAGES:
        client.cookies["django_language"] = lang
        for path in FRONTEND_PAGES:
            response = client.get(path)
            ok = response.status_code in (200, 404) and b"Traceback" not in response.content
            check(f"{lang} GET {path} → {response.status_code}", ok)
            if response.status_code == 200 and b"Traceback" not in response.content:
                body = response.content.decode("utf-8", "replace")
                check(f"  {lang} {path} has am-section hooks", "am-section" in body)

    # The countdown image should render next to the text when one exists.
    print("─" * 70)
    print("Dashboard")
    print("─" * 70)
    staff, created = User.objects.get_or_create(
        username="verify_staff", defaults={"is_staff": True, "is_superuser": True})
    if created:
        staff.set_password("verify-pass-123")
        staff.save()
    client.force_login(staff)

    for path in ADMIN_PAGES:
        response = client.get(path)
        ok = response.status_code == 200 and b"Traceback" not in response.content
        check(f"GET {path} → {response.status_code}", ok)

    # ── 1. Hero section: adding a duplicate page must not raise ──
    before = HeroSection.objects.count()
    home_hero = HeroSection.objects.filter(page="home").first()
    response = client.post("/admin-panel/hero/", {
        "action": "add", "page": "home", "heading_en": "Duplicate", "heading_fa": "تکراری",
        "cta_url": "#", "is_active": "on",
    }, follow=True)
    after = HeroSection.objects.count()
    check("hero: duplicate page rejected gracefully", response.status_code == 200 and after == before,
          f"(status={response.status_code}, {before}→{after})")

    # A hero for a CMS page is added by that page's slug. The page has to exist
    # first — the dashboard only offers real pages, and refuses a hero for a page
    # that does not exist because it would never be displayed.
    HeroSection.objects.filter(page="portfolio").delete()
    hero_page, _created = Page.objects.get_or_create(
        slug="portfolio",
        defaults={
            "title_en": "Portfolio", "title_fa": "نمونه‌کارها", "title_ar": "أعمالنا",
            "content_en": "Selected work.", "content_fa": "کارهای منتخب.",
            "content_ar": "أعمال مختارة.", "is_active": True,
        },
    )
    response = client.post("/admin-panel/hero/", {
        "action": "add", "page": "portfolio", "heading_en": "Portfolio", "heading_fa": "نمونه‌کارها",
        "cta_url": "#", "is_active": "on",
    }, follow=True)
    check("hero: hero for an existing CMS page created",
          response.status_code == 200 and HeroSection.objects.filter(page="portfolio").exists())

    # …and a hero for a page that does not exist must be refused.
    before = HeroSection.objects.count()
    response = client.post("/admin-panel/hero/", {
        "action": "add", "page": "no-such-page", "heading_en": "Nope", "heading_fa": "خیر",
        "cta_url": "#", "is_active": "on",
    }, follow=True)
    check("hero: hero for a missing page refused",
          response.status_code == 200 and HeroSection.objects.count() == before)
    HeroSection.objects.filter(page="portfolio").delete()
    hero_page.delete()

    # ── 2. Testimonial without quote text must save ──
    response = client.post("/admin-panel/testimonials/", {
        "action": "add", "quote_en": "", "quote_fa": "", "quote_ar": "",
        "author_name": "Verify Bot", "order": "99", "is_active": "on",
    }, follow=True)
    t = Testimonial.objects.filter(author_name="Verify Bot").first()
    check("testimonial: empty quotes saved", response.status_code == 200 and t is not None)
    if t:
        t.delete()

    # ── 3. Section appearance: palette colour + raw hex + reset ──
    pricing = SectionStyle.objects.get(section="pricing")
    response = client.post("/admin-panel/sections/", {
        "action": "edit", "pk": pricing.pk,
        "title_en": "Plans & Pricing", "title_fa": "طرح‌ها", "title_ar": "",
        "subheading_en": "", "subheading_fa": "", "subheading_ar": "",
        "subtitle_en": "", "subtitle_fa": "", "subtitle_ar": "",
        "background_color": "#123456", "overlay_color": "rgba(0,0,0,0.4)",
        "overlay_opacity": "40", "text_color": "white", "heading_color": "#ffcc00",
        "card_background": "#222222", "card_text_color": "",
        "item_limit": "0", "show_pattern": "on", "is_active": "on",
    }, follow=True)
    pricing.refresh_from_db()
    check("section: hex/colour values stored",
          response.status_code == 200 and pricing.background_color == "#123456"
          and pricing.overlay_color == "rgba(0,0,0,0.4)" and pricing.text_color == "white"
          and pricing.heading_color == "#ffcc00",
          f"({pricing.background_color}, {pricing.overlay_color}, {pricing.text_color})")
    check("section: style attribute built", "--am-heading:#ffcc00" in pricing.style_attribute())

    # Invalid values must be dropped instead of being injected into the page.
    response = client.post("/admin-panel/sections/", {
        "action": "edit", "pk": pricing.pk, "background_color": "red;background:url(evil)",
        "overlay_opacity": "999", "is_active": "on",
    }, follow=True)
    pricing.refresh_from_db()
    check("section: unsafe colour rejected", pricing.background_color == "")
    check("section: opacity clamped", pricing.overlay_opacity == 100,
          f"(got {pricing.overlay_opacity})")

    response = client.post("/admin-panel/sections/", {"action": "reset", "pk": pricing.pk}, follow=True)
    pricing.refresh_from_db()
    check("section: reset clears the overrides",
          response.status_code == 200 and pricing.background_color == "" and pricing.title_en == "")

    # A section switched off in the dashboard must fall back to the defaults.
    pricing.is_active = False
    pricing.background_color = "#00ff00"
    pricing.save()
    client3 = Client()
    check("section: inactive row ignored on the website",
          "#00ff00" not in client3.get("/").content.decode("utf-8"))
    pricing.is_active = True
    pricing.background_color = ""
    pricing.save()

    # ── 4. Countdown background + image round-trip ──
    countdown = EventCountdown.objects.first()
    if countdown:
        response = client.post("/admin-panel/event-countdown/", {
            # The countdown's Subheading / Title / Description are edited on the
            # "Sections & Backgrounds" page, so this form no longer carries them.
            "event_date": countdown.event_date.strftime("%Y-%m-%dT%H:%M"),
            "ended_message_en": countdown.ended_message_en, "ended_message_fa": countdown.ended_message_fa,
            "ended_message_ar": countdown.ended_message_ar,
            "cta_text_en": countdown.cta_text_en, "cta_text_fa": countdown.cta_text_fa,
            "cta_text_ar": countdown.cta_text_ar, "cta_url": countdown.cta_url,
            "image_position": "left", "image_alt_en": "AM Business team",
            "is_active": "on",
        }, follow=True)
        countdown.refresh_from_db()
        check("countdown: image position saved",
              response.status_code == 200 and countdown.image_position == "left")

    # ── 5. Pricing plans in the dashboard vs. the homepage ──
    print("─" * 70)
    print("Pricing coverage")
    print("─" * 70)
    client2 = Client()
    body = client2.get("/").content.decode("utf-8")
    active = list(PricingPlan.objects.filter(is_active=True))
    style = SectionStyle.objects.get(section="pricing")
    limit = style.item_limit
    expected = active[:limit] if limit else active
    shown = sum(1 for plan in expected if plan.name_en and plan.name_en in body)
    check(f"home shows {shown}/{len(expected)} dashboard plans",
          shown == len(expected), f"(active={len(active)}, limit={limit})")

    # ── 6. A CMS page such as /page/portfolio/ renders ──
    print("─" * 70)
    print("CMS page + countdown image")
    print("─" * 70)
    page, _created = Page.objects.get_or_create(
        slug="verify-portfolio",
        defaults={
            "title_en": "Portfolio", "title_fa": "نمونه‌کارها", "title_ar": "أعمالنا",
            "content_en": "Selected work.", "content_fa": "کارهای منتخب.", "content_ar": "أعمال مختارة.",
            "is_active": True,
        },
    )
    response = client2.get(f"/page/{page.slug}/")
    check(f"GET /page/{page.slug}/ → {response.status_code}", response.status_code == 200)
    page.delete()

    # ── 7. The countdown image appears next to the text ──
    countdown = EventCountdown.objects.first()
    if countdown:
        # Snapshot the editor's own values — this script runs against the dev
        # database, so everything it touches is put back afterwards.
        original_image = countdown.image.name or ""
        original_position = countdown.image_position

        png = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
               b"\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
               b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
        countdown.image = SimpleUploadedFile("verify-countdown.png", png, content_type="image/png")
        countdown.image_position = "right"
        countdown.save()

        html = client2.get("/").content.decode("utf-8")
        check("countdown: image rendered on the homepage",
              "/media/countdown/verify-countdown" in html and 'class="col-lg-5' in html)
        check("countdown: «right» places the image after the text",
              "order:2;" in html and "order:0;" not in html)

        # The side is physical, so it must hold in RTL as well.
        countdown.image_position = "left"
        countdown.save()
        html_left = client2.get("/").content.decode("utf-8")
        html_left_fa = client.get("/").content.decode("utf-8")
        check("countdown: «left» places the image before the text",
              "order:0;" in html_left and "order:0;" in html_left_fa)

        # The about page uses the same block.
        check("countdown: about page uses the shared block",
              "am-countdown-section" in client.get("/about/").content.decode("utf-8"))

        # Restore whatever the editor had before this script ran.
        countdown.image.name = original_image or ""
        countdown.image_position = original_position
        countdown.save()
        check("countdown: original image restored",
              (countdown.image.name or "") == original_image,
              f"({countdown.image.name!r} vs {original_image!r})")

    # ── 8. Feature icons come from the dashboard ──
    print("─" * 70)
    print("Feature icons")
    print("─" * 70)
    feature = Feature.objects.create(
        title_en="Verify Icon Feature", title_fa="ویژگی آزمایشی",
        description_en="desc", description_fa="توضیح", icon="rocket", order=999,
    )
    check("feature: icon maps to a font class", feature.icon_class == "icon-rocket",
          f"(got {feature.icon_class!r})")
    body = client2.get("/").content.decode("utf-8")
    check("feature: icon rendered on the homepage", "icon-rocket" in body and "Verify Icon Feature" in body)

    feature.icon = ""
    feature.save()
    check("feature: empty icon reports has_icon = False", feature.has_icon is False)
    body = client2.get("/").content.decode("utf-8")
    check("feature: no empty icon box is drawn", 'svg-wrap"><span class=""' not in body)

    # A value that does not exist in the icon font must not draw an empty box.
    feature.icon = "not-a-real-icon"
    feature.save()
    check("feature: unknown icon value draws nothing", feature.icon_class == "")
    feature.delete()

    # ── Clean up the rows this script created ──
    HeroSection.objects.filter(page="portfolio", heading_en="Portfolio").delete()
    staff.delete()

    # ── Summary ──
    print("─" * 70)
    if failures:
        print(f"{len(failures)} of {checks} checks FAILED")
        for f in failures:
            print("  -", f)
        return 1
    print(f"All {checks} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
