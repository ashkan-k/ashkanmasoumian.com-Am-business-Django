"""Ad-hoc smoke test for the trilingual (en/fa/ar) admin panel and frontend.

Renders every admin and frontend page in all three languages, verifies that the
bulk-action dropdown matches the actions the backend accepts, exercises each
bulk action, and checks that Arabic content round-trips through the admin forms.

Run from the project root:

    $env:PYTHONIOENCODING="utf-8"; .\\.venv\\Scripts\\python.exe tests\\smoke_check.py

It creates a throwaway staff user and removes it again, and cleans up every
row it creates.
"""
import os
import sys
from pathlib import Path

# Allow "python tests/smoke_check.py" from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "am_business.settings")
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from core.models import (
    SiteSettings, Navigation, HeroSection, Service, Feature, StatCounter,
    PricingPlan, Testimonial, TeamMember, ContactMessage, NewsletterSubscriber,
    Page, SocialLink, HomeSection, AboutSection, EventCountdown, SectionStyle,
)

ADMIN_PAGES = [
    "admin_dashboard", "admin_site_settings", "admin_social_links",
    "admin_navigation", "admin_hero_sections", "admin_services", "admin_about",
    "admin_stat_counters", "admin_features", "admin_pricing",
    "admin_testimonials", "admin_team", "admin_event_countdown",
    "admin_home_sections", "admin_sections", "admin_messages",
    "admin_newsletter", "admin_pages",
]
FRONTEND_PAGES = ["frontend_home", "frontend_about", "frontend_services", "frontend_contact"]

# Admin pages that are not list pages, so they carry no bulk toolbar.
NO_BULK_PAGES = {
    "admin_dashboard", "admin_site_settings", "admin_about",
    "admin_event_countdown",
}

# Arabic inputs each admin page must expose (checked while lang == 'ar')
ARABIC_FIELDS = {
    "admin_site_settings": ["site_name_ar", "address_ar", "meta_description_ar", "copyright_text_ar"],
    "admin_navigation": ["title_ar"],
    "admin_hero_sections": ["heading_ar", "subheading_ar", "cta_text_ar"],
    "admin_services": ["title_ar", "description_ar"],
    "admin_about": ["title_ar", "content_ar", "who_we_are_ar", "we_are_expert_ar",
                    "why_choose_us_title_ar", "why_choose_us_content_ar", "cta_text_ar"],
    "admin_stat_counters": ["label_ar"],
    "admin_features": ["title_ar", "description_ar"],
    "admin_pricing": ["name_ar", "description_ar", "button_text_ar"],
    "admin_testimonials": ["quote_ar", "author_role_ar"],
    "admin_team": ["position_ar", "bio_ar"],
    "admin_event_countdown": ["title_ar", "subheading_ar", "ended_message_ar", "cta_text_ar"],
    "admin_home_sections": ["title_ar", "subheading_ar", "content_ar", "cta_text_ar"],
    "admin_sections": ["title_ar", "subheading_ar", "subtitle_ar"],
    "admin_pages": ["title_ar", "content_ar", "meta_title_ar", "meta_description_ar"],
}

from django.urls import reverse

failures = []


def check(label, response, expect=200):
    ok = response.status_code == expect
    if not ok:
        failures.append(f"{label}: HTTP {response.status_code} (expected {expect})")
    print(f"{'OK ' if ok else 'FAIL'} {label} -> {response.status_code}")
    return response


def main():
    """Run every check. Creates a throwaway staff user and removes it again."""
    user, _existing = User.objects.get_or_create(username="smoke_admin")
    user.is_staff = True
    user.is_superuser = True
    user.set_unusable_password()
    user.save()

    client = Client()
    client.force_login(user)
    try:
        run_checks(client)
    finally:
        User.objects.filter(username="smoke_admin").delete()


def run_checks(client):
    print("\n=== Backend sanity ===")
    from core.models import pick_lang, is_rtl
    s = SiteSettings.objects.first()
    if s:
        for lang in ("en", "fa", "ar"):
            print(f"  site_name[{lang}] = {s.get_site_name(lang)!r}")
    print(f"  is_rtl('ar')={is_rtl('ar')} is_rtl('fa')={is_rtl('fa')} is_rtl('en')={is_rtl('en')}")

    print("\n=== Admin pages × 3 languages ===")
    for lang in ("en", "fa", "ar"):
        client.cookies["django_language"] = lang
        for name in ADMIN_PAGES:
            res = check(f"[{lang}] {name}", client.get(reverse(name)))
            if res.status_code == 200:
                html = res.content.decode("utf-8")
                if lang == "ar":
                    if 'dir="rtl"' not in html:
                        failures.append(f"[ar] {name}: missing dir=rtl")
                    # each list page must expose its Arabic inputs
                    for field in ARABIC_FIELDS.get(name, []):
                        if f'name="{field}"' not in html:
                            failures.append(f"[ar] {name}: missing Arabic input {field}")
                if name not in NO_BULK_PAGES:
                    if "bulk-form" not in html:
                        failures.append(f"[{lang}] {name}: no bulk form rendered")
                    if "select-all" not in html:
                        failures.append(f"[{lang}] {name}: no select-all checkbox")

    # message detail
    msg = ContactMessage.objects.create(name="Smoke", email="s@x.com", subject="Hi", message="Body")
    client.cookies["django_language"] = "ar"
    check("admin_message_detail", client.get(reverse("admin_message_detail", args=[msg.pk])))

    print("\n=== Frontend pages × 3 languages ===")
    for lang in ("en", "fa", "ar"):
        client.cookies["django_language"] = lang
        for name in FRONTEND_PAGES:
            res = check(f"[{lang}] {name}", client.get(reverse(name)))
            html = res.content.decode("utf-8")
            if lang in ("fa", "ar") and 'dir="rtl"' not in html:
                failures.append(f"[{lang}] {name}: frontend missing dir=rtl")
            if f'lang="{lang}"' not in html:
                failures.append(f"[{lang}] {name}: <html lang> is wrong")
            if lang == "ar" and "العربية" not in html:
                failures.append(f"[ar] {name}: language switcher has no Arabic option")

    # CMS page rendered through frontend_page (added with the SectionStyle work)
    print("\n=== CMS page frontend route ===")
    cms = Page.objects.create(
        title_en="__smoke_cms", title_fa="__ص", title_ar="__صع",
        slug="__smoke-cms", content_en="body", content_fa="متن", content_ar="نص",
        is_active=True, show_in_menu=False,
    )
    for lang in ("en", "fa", "ar"):
        client.cookies["django_language"] = lang
        res = check(f"[{lang}] frontend_page", client.get(reverse("frontend_page", args=[cms.slug])))
        if res.status_code == 200:
            html = res.content.decode("utf-8")
            if lang in ("fa", "ar") and 'dir="rtl"' not in html:
                failures.append(f"[{lang}] frontend_page: missing dir=rtl")
    cms.delete()

    # Transliterated database content must actually reach the page per language.
    print("\n=== Stored translations reach the frontend ===")
    from django.utils.html import escape

    for lang in ("en", "fa", "ar"):
        client.cookies["django_language"] = lang
        html = client.get(reverse("frontend_services")).content.decode("utf-8")
        service = Service.objects.filter(is_active=True).first()
        if service is None:
            continue
        expected = getattr(service, f"title_{lang}")
        # templates escape their output, so compare against the escaped form
        found = bool(expected) and escape(expected) in html
        print(f"{'OK  ' if found else 'FAIL'} service title_{lang} = {expected!r} on /services/")
        if not found:
            failures.append(f"frontend /services/ [{lang}]: title_{lang} not rendered")

    print("\n=== Language switch cookie ===")
    for lang in ("en", "fa", "ar"):
        res = client.get(reverse("set_language", args=[lang]))
        got = res.cookies.get("django_language")
        print(f"  set_language('{lang}') -> {res.status_code}, cookie={got.value if got else None}")
        if not got or got.value != lang:
            failures.append(f"set_language({lang}) did not set the cookie")

    print("\n=== Bulk actions ===")
    client.cookies["django_language"] = "en"

    # --- activate / deactivate on real-looking throwaway rows ---
    a = Feature.objects.create(title_en="__smoke_a", title_fa="آ", description_en="d", description_fa="د", is_active=False)
    b = Feature.objects.create(title_en="__smoke_b", title_fa="ب", description_en="d", description_fa="د", is_active=False)
    res = client.post(reverse("admin_features"), {
        "action": "bulk", "bulk_action": "activate", "pks": [a.pk, b.pk],
    })
    check("bulk activate (features)", res, expect=302)
    a.refresh_from_db(); b.refresh_from_db()
    print(f"  is_active -> {a.is_active}, {b.is_active}")
    if not (a.is_active and b.is_active):
        failures.append("bulk activate did not update rows")

    res = client.post(reverse("admin_features"), {
        "action": "bulk", "bulk_action": "deactivate", "pks": [a.pk],
    })
    check("bulk deactivate (features)", res, expect=302)
    a.refresh_from_db()
    if a.is_active:
        failures.append("bulk deactivate did not update the row")

    # --- duplicate ---
    res = client.post(reverse("admin_features"), {
        "action": "bulk", "bulk_action": "duplicate", "pks": [b.pk],
    })
    check("bulk duplicate (features)", res, expect=302)
    dupes = Feature.objects.filter(title_en="__smoke_b")
    print(f"  rows named __smoke_b: {dupes.count()}")
    if dupes.count() != 2:
        failures.append("bulk duplicate did not create a copy")

    # --- bulk delete (cleans up the throwaways) ---
    ids = list(Feature.objects.filter(title_en__startswith="__smoke_").values_list("pk", flat=True))
    res = client.post(reverse("admin_features"), {
        "action": "bulk", "bulk_action": "delete", "pks": ids,
    })
    check("bulk delete (features)", res, expect=302)
    left = Feature.objects.filter(title_en__startswith="__smoke_").count()
    print(f"  remaining throwaway rows: {left}")
    if left:
        failures.append("bulk delete did not remove the rows")

    # --- every list page: the rendered dropdown and the backend must agree ---
    from core.views import BULK_PAGES

    page_map = {
        "social_links": (SocialLink, "activate", "is_active", True),
        "navigation": (Navigation, "activate", "is_active", True),
        "hero_sections": (HeroSection, "deactivate", "is_active", False),
        "services": (Service, "activate", "is_active", True),
        "stat_counters": (StatCounter, "activate", "is_active", True),
        "features": (Feature, "activate", "is_active", True),
        "pricing": (PricingPlan, "mark_popular", "is_popular", True),
        "testimonials": (Testimonial, "activate", "is_active", True),
        "team": (TeamMember, "activate", "is_active", True),
        "home_sections": (HomeSection, "activate", "is_active", True),
        "messages": (ContactMessage, "mark_read", "is_read", True),
        "newsletter": (NewsletterSubscriber, "deactivate", "is_active", False),
        "pages": (Page, "show_in_menu", "show_in_menu", True),
        "sections": (SectionStyle, "deactivate", "is_active", False),
    }

    client.cookies["django_language"] = "en"

    # throwaway rows for the two pages the seed data does not populate
    temp_page = Page.objects.create(
        title_en="__smoke_page", title_fa="ص", title_ar="ص", slug="__smoke-page",
        content_en="c", content_fa="م", content_ar="م", is_active=False,
    )
    temp_sub = NewsletterSubscriber.objects.create(
        name="__smoke_sub", email="__smoke_sub@example.com", is_active=True,
    )
    temp_names = ["__smoke_page"]
    temp_emails = ["__smoke_sub@example.com"]

    for key, (model, action, field, expected) in page_map.items():
        redirect_name = BULK_PAGES[key]["redirect"]

        html = client.get(reverse(redirect_name)).content.decode("utf-8")
        for allowed in BULK_PAGES[key]["actions"]:
            if f'value="{allowed}"' not in html:
                failures.append(f"{key}: action {allowed!r} missing from the rendered dropdown")

        obj = model.objects.first()
        if obj is None:
            print(f"SKIP bulk {key}: no rows in the database to test with")
            continue
        before = getattr(obj, field)
        res = client.post(reverse(redirect_name), {
            "action": "bulk", "bulk_action": action, "pks": [obj.pk],
        })
        obj.refresh_from_db()
        after = getattr(obj, field)
        good = res.status_code == 302 and after == expected
        print(f"{'OK  ' if good else 'FAIL'} bulk {action} ({key}) -> {res.status_code}, {field}: {before} -> {after}")
        if not good:
            failures.append(f"bulk {action} on {key} failed (status {res.status_code}, {field}={after})")

        # Put the original value back so the dev database keeps its appearance
        # (the section rows in particular must stay active on the live site).
        setattr(obj, field, before)
        obj.save(update_fields=[field])

    Page.objects.filter(title_en__in=temp_names).delete()
    NewsletterSubscriber.objects.filter(email__in=temp_emails).delete()

    # --- sections page: the three reset levels must clear the right fields ---
    print("\n=== Sections bulk resets ===")
    probe = SectionStyle.objects.create(
        section="__smoke_section",
        title_en="T", title_fa="ت", title_ar="تع",
        subheading_en="S", subheading_fa="س", subheading_ar="سع",
        subtitle_en="D", subtitle_fa="د", subtitle_ar="دع",
        background_color="#530e69", overlay_color="#530e69", overlay_opacity=92,
        text_color="#ffffff", heading_color="#e2a83e",
        card_background="#111111", card_text_color="#eeeeee",
        show_pattern=True, is_active=True,
    )
    sections_url = reverse("admin_sections")

    def post_bulk(action):
        return client.post(sections_url, {
            "action": "bulk", "bulk_action": action, "pks": [probe.pk],
        })

    def set_all_fields():
        SectionStyle.objects.filter(pk=probe.pk).update(
            title_en="T", subheading_en="S", subtitle_en="D",
            background_color="#530e69", overlay_color="#530e69", overlay_opacity=92,
            text_color="#ffffff", heading_color="#e2a83e",
            card_background="#111111", card_text_color="#eeeeee",
        )

    # reset_appearance -> colours gone, headings kept
    res = post_bulk("reset_appearance")
    probe.refresh_from_db()
    ok = (res.status_code == 302 and probe.background_color == "" and probe.overlay_color == ""
          and probe.overlay_opacity == 0 and probe.title_en == "T" and probe.subtitle_ar == "دع")
    print(f"{'OK  ' if ok else 'FAIL'} reset_appearance keeps headings, clears colours")
    if not ok:
        failures.append("sections reset_appearance did not behave as expected")

    # reset_headings -> headings gone, colours kept
    set_all_fields()
    res = post_bulk("reset_headings")
    probe.refresh_from_db()
    ok = (res.status_code == 302 and probe.title_en == "" and probe.subheading_fa == ""
          and probe.subtitle_ar == "" and probe.background_color == "#530e69")
    print(f"{'OK  ' if ok else 'FAIL'} reset_headings clears headings, keeps colours")
    if not ok:
        failures.append("sections reset_headings did not behave as expected")

    # reset_all -> everything back to the theme default
    set_all_fields()
    res = post_bulk("reset_all")
    probe.refresh_from_db()
    ok = (res.status_code == 302 and probe.title_en == "" and probe.subtitle_en == ""
          and probe.background_color == "" and probe.card_text_color == ""
          and probe.overlay_opacity == 0 and not probe.background_image)
    print(f"{'OK  ' if ok else 'FAIL'} reset_all clears headings and appearance")
    if not ok:
        failures.append("sections reset_all did not behave as expected")

    # show_pattern / hide_pattern
    set_all_fields()
    post_bulk("hide_pattern")
    probe.refresh_from_db()
    hidden = probe.show_pattern is False
    post_bulk("show_pattern")
    probe.refresh_from_db()
    shown = probe.show_pattern is True
    print(f"{'OK  ' if hidden and shown else 'FAIL'} show/hide pattern toggles")
    if not (hidden and shown):
        failures.append("sections show_pattern/hide_pattern did not behave as expected")

    probe.delete()
    print(f"  remaining active section rows: {SectionStyle.objects.filter(is_active=True).count()}")

    # --- guards ---
    res = client.post(reverse("admin_features"), {"action": "bulk", "bulk_action": "activate", "pks": []}, follow=True)
    check("bulk with no selection (warning)", res)
    if "No rows were selected" not in res.content.decode("utf-8"):
        failures.append("bulk with no selection did not warn")

    res = client.post(reverse("admin_features"), {
        "action": "bulk", "bulk_action": "explode", "pks": [1],
    }, follow=True)
    check("bulk with unknown action (error)", res)
    if "Unknown bulk action" not in res.content.decode("utf-8"):
        failures.append("bulk with unknown action did not error")

    # --- messages page actions ---
    res = client.post(reverse("admin_messages"), {
        "action": "bulk", "bulk_action": "mark_read", "pks": [msg.pk],
    })
    check("bulk mark_read (messages)", res, expect=302)
    msg.refresh_from_db()
    if not msg.is_read:
        failures.append("bulk mark_read did not update the message")

    res = client.post(reverse("admin_messages"), {
        "action": "bulk", "bulk_action": "export_csv", "pks": [msg.pk],
    })
    check("bulk export_csv (messages)", res)
    if res.status_code == 200 and "text/csv" not in res["Content-Type"]:
        failures.append("export_csv did not return a CSV")

    res = client.post(reverse("admin_messages"), {
        "action": "bulk", "bulk_action": "delete", "pks": [msg.pk],
    })
    check("bulk delete (messages)", res, expect=302)

    # --- single-row actions still work ---
    res = client.post(reverse("admin_features"), {
        "action": "add", "title_en": "__smoke_add", "title_fa": "ا", "title_ar": "أ",
        "description_en": "d", "description_fa": "د", "description_ar": "ذ",
        "order": "0", "is_active": "on",
    })
    check("single add (features)", res, expect=302)
    obj = Feature.objects.filter(title_en="__smoke_add").first()
    if not obj or obj.title_ar != "أ":
        failures.append("single add did not persist the Arabic title")
    if obj:
        res = client.post(reverse("admin_features"), {
            "action": "edit", "pk": obj.pk, "title_en": "__smoke_add", "title_fa": "ا",
            "title_ar": "أ2", "description_en": "d", "description_fa": "د",
            "description_ar": "ذ2", "order": "5", "is_active": "on",
        })
        check("single edit (features)", res, expect=302)
        obj.refresh_from_db()
        if obj.title_ar != "أ2" or obj.order != 5:
            failures.append("single edit did not persist Arabic title/order")
        client.post(reverse("admin_features"), {"action": "delete", "pk": obj.pk})

    print("\n=== Arabic content round-trips through the admin forms ===")
    from core.models import AboutSection, SiteSettings as SettingsModel

    # (label, url_name, model, add-payload, lookup (field, value), expected Arabic values)
    add_cases = [
        ("services", "admin_services", Service,
         {"title_en": "__smoke_svc", "title_fa": "خ", "title_ar": "خ-ع",
          "description_en": "d", "description_fa": "د", "description_ar": "ذ-ع",
          "icon": "gear", "order": "0", "is_active": "on"},
         ("title_en", "__smoke_svc"),
         {"title_ar": "خ-ع", "description_ar": "ذ-ع"}),
        ("stat_counters", "admin_stat_counters", StatCounter,
         {"label_en": "__smoke_cnt", "label_fa": "ش", "label_ar": "ش-ع", "value": "7",
          "order": "0", "is_active": "on"},
         ("label_en", "__smoke_cnt"),
         {"label_ar": "ش-ع"}),
        ("features", "admin_features", Feature,
         {"title_en": "__smoke_feat", "title_fa": "و", "title_ar": "و-ع",
          "description_en": "d", "description_fa": "د", "description_ar": "ذ-ع",
          "order": "0", "is_active": "on"},
         ("title_en", "__smoke_feat"),
         {"title_ar": "و-ع", "description_ar": "ذ-ع"}),
        ("pricing", "admin_pricing", PricingPlan,
         {"name_en": "__smoke_plan", "name_fa": "ط", "name_ar": "ط-ع",
          "description_en": "d", "description_fa": "د", "description_ar": "ذ-ع",
          "price": "10", "currency": "$", "cents": ".00",
          "button_text_en": "Buy", "button_text_fa": "خرید", "button_text_ar": "ب-ع",
          "button_url": "#", "order": "0", "is_active": "on"},
         ("name_en", "__smoke_plan"),
         {"name_ar": "ط-ع", "description_ar": "ذ-ع", "button_text_ar": "ب-ع"}),
        ("testimonials", "admin_testimonials", Testimonial,
         {"quote_en": "q", "quote_fa": "ن", "quote_ar": "ن-ع",
          "author_name": "__smoke_author",
          "author_role_en": "r", "author_role_fa": "س", "author_role_ar": "س-ع",
          "order": "0", "is_active": "on"},
         ("author_name", "__smoke_author"),
         {"quote_ar": "ن-ع", "author_role_ar": "س-ع"}),
        ("team", "admin_team", TeamMember,
         {"name": "__smoke_member", "position_en": "p", "position_fa": "س", "position_ar": "س-ع",
          "bio_en": "b", "bio_fa": "ب", "bio_ar": "ب-ع",
          "order": "0", "is_active": "on"},
         ("name", "__smoke_member"),
         {"position_ar": "س-ع", "bio_ar": "ب-ع"}),
        ("pages", "admin_pages", Page,
         {"title_en": "__smoke_pg", "title_fa": "ص", "title_ar": "ص-ع",
          "content_en": "c", "content_fa": "م", "content_ar": "م-ع",
          "meta_title_en": "mt", "meta_title_fa": "مت", "meta_title_ar": "مت-ع",
          "meta_description_en": "md", "meta_description_fa": "مد", "meta_description_ar": "مد-ع",
          "is_active": "on"},
         ("title_en", "__smoke_pg"),
         {"title_ar": "ص-ع", "content_ar": "م-ع",
          "meta_title_ar": "مت-ع", "meta_description_ar": "مد-ع"}),
        ("navigation", "admin_navigation", Navigation,
         {"title_en": "__smoke_nav", "title_fa": "م", "title_ar": "م-ع",
          "url": "/x/", "order": "9", "is_active": "on"},
         ("title_en", "__smoke_nav"),
         {"title_ar": "م-ع"}),
    ]

    for label, url_name, model, payload, (lookup, lookup_value), ar_expected in add_cases:
        res = client.post(reverse(url_name), {"action": "add", **payload})
        obj = model.objects.filter(**{lookup: lookup_value}).first()
        if res.status_code != 302 or obj is None:
            failures.append(f"{label}: add did not create the row (HTTP {res.status_code})")
            print(f"FAIL add {label} -> {res.status_code}")
            continue
        wrong = {
            field: (expected, getattr(obj, field, None))
            for field, expected in ar_expected.items()
            if getattr(obj, field, None) != expected
        }
        print(f"{'OK  ' if not wrong else 'FAIL'} add {label}: {list(ar_expected)}")
        if wrong:
            failures.append(f"{label}: Arabic fields not persisted correctly: {wrong}")
        model.objects.filter(pk=obj.pk).delete()

    # Singleton / unique-keyed forms are edited in place. The views keep any
    # field that is missing from POST (`request.POST.get(name, obj.name)`), so a
    # payload only needs the Arabic fields — but it must always carry
    # `is_active`, because a missing checkbox means "off".
    def edit_in_place(label, url_name, obj, ar_fields, extra=None):
        extra = extra or {}
        original = {field: getattr(obj, field) for field in ar_fields}
        base = {"action": "edit", "pk": obj.pk, **extra}
        if getattr(obj, "is_active", False):
            base["is_active"] = "on"

        sentinels = {field: f"__probe_{field}" for field in ar_fields}
        res = client.post(reverse(url_name), {**base, **sentinels})
        obj.refresh_from_db()
        not_saved = {
            field: (expected, getattr(obj, field, None))
            for field, expected in sentinels.items()
            if getattr(obj, field, None) != expected
        }

        # Put the original values back so the dev database is left untouched.
        client.post(reverse(url_name), {**base, **original})
        obj.refresh_from_db()
        not_restored = {
            field: (expected, getattr(obj, field, None))
            for field, expected in original.items()
            if getattr(obj, field, None) != expected
        }

        ok = res.status_code == 302 and not not_saved and not not_restored
        print(f"{'OK  ' if ok else 'FAIL'} edit {label} ({len(ar_fields)} Arabic fields)")
        if not_saved:
            failures.append(f"{label}: Arabic fields not persisted: {not_saved}")
        if not_restored:
            failures.append(f"{label}: could not restore the original values: {not_restored}")
        return ok

    hero = HeroSection.objects.first()
    if hero:
        edit_in_place("hero_sections", "admin_hero_sections", hero,
                      ["heading_ar", "subheading_ar", "cta_text_ar"])

    section = HomeSection.objects.first()
    if section:
        edit_in_place("home_sections", "admin_home_sections", section,
                      ["title_ar", "subheading_ar", "content_ar", "cta_text_ar"])

    about = AboutSection.objects.first()
    if about:
        edit_in_place("about", "admin_about", about,
                      ["title_ar", "content_ar", "who_we_are_ar", "we_are_expert_ar",
                       "why_choose_us_title_ar", "why_choose_us_content_ar", "cta_text_ar"])

    settings_obj = SettingsModel.objects.first()
    if settings_obj:
        edit_in_place("site_settings", "admin_site_settings", settings_obj,
                      ["site_name_ar", "address_ar", "meta_description_ar", "copyright_text_ar"])

    countdown = EventCountdown.objects.first()
    if countdown:
        edit_in_place("event_countdown", "admin_event_countdown", countdown,
                      ["title_ar", "subheading_ar", "ended_message_ar", "cta_text_ar"],
                      extra={"event_date": countdown.event_date.strftime("%Y-%m-%dT%H:%M")})

    print("\n=== Result ===")
    if failures:
        print(f"{len(failures)} FAILURES:")
        for f in failures:
            print("  -", f)
    else:
        print("All checks passed.")


if __name__ == "__main__":
    main()
