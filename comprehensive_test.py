"""
Comprehensive test script for AM Business Django project.
Tests all pages, forms, and scenarios for 500 errors and data saving issues.
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "am_business.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from core.models import (
    SiteSettings, SocialLink, Navigation, HeroSection, Service,
    AboutSection, StatCounter, Feature, PricingPlan, Testimonial,
    TeamMember, ContactMessage, NewsletterSubscriber, EventCountdown,
    Page, HomeSection
)

client = Client()
admin_client = Client()
admin_user = User.objects.get(username="admin")
admin_client.force_login(admin_user)

results = {"pass": [], "fail_500": [], "fail_other": [], "form_issues": []}

def test_page(name, url, use_admin=False):
    c = admin_client if use_admin else client
    try:
        resp = c.get(url)
        if resp.status_code == 200:
            results["pass"].append(f"{name}: {url} -> {resp.status_code}")
        elif resp.status_code == 500:
            results["fail_500"].append(f"{name}: {url} -> {resp.status_code}")
            # Try to get the error
            try:
                exc = resp.context.get("exception") if hasattr(resp, "context") else None
                if exc:
                    results["fail_500"][-1] += f" | Exception: {exc}"
            except:
                pass
        else:
            results["fail_other"].append(f"{name}: {url} -> {resp.status_code}")
    except Exception as e:
        results["fail_500"].append(f"{name}: {url} -> EXCEPTION: {e}")

def test_post(name, url, data, use_admin=False, follow=True):
    c = admin_client if use_admin else client
    try:
        resp = c.post(url, data, follow=follow)
        if resp.status_code in (200, 302):
            if resp.status_code == 302 and not follow:
                results["pass"].append(f"POST {name}: {url} -> {resp.status_code}")
            else:
                results["pass"].append(f"POST {name}: {url} -> {resp.status_code}")
        elif resp.status_code == 500:
            results["fail_500"].append(f"POST {name}: {url} -> 500")
        else:
            results["fail_other"].append(f"POST {name}: {url} -> {resp.status_code}")
    except Exception as e:
        results["fail_500"].append(f"POST {name}: {url} -> EXCEPTION: {type(e).__name__}: {e}")

print("=" * 70)
print("TESTING FRONTEND PAGES")
print("=" * 70)

frontend_pages = [
    ("Home", "/"),
    ("About", "/about/"),
    ("Services", "/services/"),
    ("Contact", "/contact/"),
]

for name, url in frontend_pages:
    test_page(name, url)
    print(f"  Tested: {name} ({url})")

print("\n" + "=" * 70)
print("TESTING ADMIN PANEL PAGES (GET)")
print("=" * 70)

admin_pages = [
    ("Dashboard", "/admin-panel/"),
    ("Site Settings", "/admin-panel/settings/"),
    ("Social Links", "/admin-panel/social-links/"),
    ("Navigation", "/admin-panel/navigation/"),
    ("Hero Sections", "/admin-panel/hero/"),
    ("Services", "/admin-panel/services/"),
    ("About", "/admin-panel/about/"),
    ("Stat Counters", "/admin-panel/counters/"),
    ("Features", "/admin-panel/features/"),
    ("Pricing", "/admin-panel/pricing/"),
    ("Testimonials", "/admin-panel/testimonials/"),
    ("Team", "/admin-panel/team/"),
    ("Event Countdown", "/admin-panel/event-countdown/"),
    ("Home Sections", "/admin-panel/home-sections/"),
    ("Messages", "/admin-panel/messages/"),
    ("Newsletter", "/admin-panel/newsletter/"),
    ("Pages", "/admin-panel/pages/"),
    ("Login Page", "/accounts/login/"),
]

for name, url in admin_pages:
    test_page(name, url, use_admin=True)
    print(f"  Tested: {name} ({url})")

# Test message detail if any messages exist
if ContactMessage.objects.exists():
    msg = ContactMessage.objects.first()
    test_page("Message Detail", f"/admin-panel/messages/{msg.pk}/", use_admin=True)
    print(f"  Tested: Message Detail (/admin-panel/messages/{msg.pk}/)")

print("\n" + "=" * 70)
print("TESTING FRONTEND FORM SUBMISSIONS")
print("=" * 70)

# Test contact form
initial_count = ContactMessage.objects.count()
test_post("Contact Form", "/contact/", {
    "name": "Test User",
    "email": "test@example.com",
    "subject": "Test Subject",
    "message": "This is a test message from comprehensive testing.",
})
new_count = ContactMessage.objects.count()
if new_count > initial_count:
    results["pass"].append("Contact Form: data saved successfully")
    print(f"  Contact Form: data saved (count: {initial_count} -> {new_count})")
else:
    results["form_issues"].append("Contact Form: data NOT saved after submission!")
    print(f"  Contact Form: data NOT saved! (count: {initial_count} -> {new_count})")

# Test newsletter subscribe
initial_sub = NewsletterSubscriber.objects.count()
test_post("Newsletter Subscribe", "/newsletter/subscribe/", {
    "name": "Newsletter Test",
    "email": "newsletter_test@example.com",
})
new_sub = NewsletterSubscriber.objects.count()
if new_sub > initial_sub:
    results["pass"].append("Newsletter: data saved successfully")
    print(f"  Newsletter: data saved (count: {initial_sub} -> {new_sub})")
else:
    results["form_issues"].append("Newsletter: data NOT saved after submission!")
    print(f"  Newsletter: data NOT saved! (count: {initial_sub} -> {new_sub})")

print("\n" + "=" * 70)
print("TESTING ADMIN PANEL FORM SUBMISSIONS (ADD)")
print("=" * 70)

# Test Social Link add
test_post("Social Link Add", "/admin-panel/social-links/", {
    "action": "add",
    "platform": "facebook",
    "url": "https://facebook.com/test",
    "icon_class": "icon-facebook",
    "is_active": "on",
    "order": "0",
}, use_admin=True)
sl = SocialLink.objects.filter(url="https://facebook.com/test").exists()
if sl:
    results["pass"].append("Social Link Add: data saved")
    print("  Social Link Add: data saved")
else:
    results["form_issues"].append("Social Link Add: data NOT saved!")
    print("  Social Link Add: data NOT saved!")

# Test Navigation add
test_post("Navigation Add", "/admin-panel/navigation/", {
    "action": "add",
    "title_en": "Test Nav",
    "title_fa": "تست",
    "url": "/test/",
    "is_active": "on",
    "order": "0",
    "parent": "",
}, use_admin=True)
nav = Navigation.objects.filter(title_en="Test Nav").exists()
if nav:
    results["pass"].append("Navigation Add: data saved")
    print("  Navigation Add: data saved")
else:
    results["form_issues"].append("Navigation Add: data NOT saved!")
    print("  Navigation Add: data NOT saved!")

# Test Service add
test_post("Service Add", "/admin-panel/services/", {
    "action": "add",
    "title_en": "Test Service",
    "title_fa": "تست سرویس",
    "description_en": "Test description",
    "description_fa": "توصیف تست",
    "icon": "gear",
    "custom_svg": "",
    "is_active": "on",
    "order": "0",
}, use_admin=True)
svc = Service.objects.filter(title_en="Test Service").exists()
if svc:
    results["pass"].append("Service Add: data saved")
    print("  Service Add: data saved")
else:
    results["form_issues"].append("Service Add: data NOT saved!")
    print("  Service Add: data NOT saved!")

# Test Stat Counter add
test_post("Stat Counter Add", "/admin-panel/counters/", {
    "action": "add",
    "label_en": "Test Counter",
    "label_fa": "تست",
    "value": "100",
    "icon_class": "icon-check",
    "is_active": "on",
    "order": "0",
}, use_admin=True)
sc = StatCounter.objects.filter(label_en="Test Counter").exists()
if sc:
    results["pass"].append("Stat Counter Add: data saved")
    print("  Stat Counter Add: data saved")
else:
    results["form_issues"].append("Stat Counter Add: data NOT saved!")
    print("  Stat Counter Add: data NOT saved!")

# Test Feature add
test_post("Feature Add", "/admin-panel/features/", {
    "action": "add",
    "title_en": "Test Feature",
    "title_fa": "تست",
    "description_en": "Test feature description",
    "description_fa": "توصیف",
    "icon": "star",
    "is_active": "on",
    "order": "0",
}, use_admin=True)
ft = Feature.objects.filter(title_en="Test Feature").exists()
if ft:
    results["pass"].append("Feature Add: data saved")
    print("  Feature Add: data saved")
else:
    results["form_issues"].append("Feature Add: data NOT saved!")
    print("  Feature Add: data NOT saved!")

# Test Pricing Plan add
test_post("Pricing Add", "/admin-panel/pricing/", {
    "action": "add",
    "name_en": "Test Plan",
    "name_fa": "تست",
    "description_en": "Test pricing",
    "description_fa": "تست",
    "price": "99.99",
    "currency": "$",
    "cents": ".99",
    "is_popular": "on",
    "button_text_en": "Buy",
    "button_text_fa": "خرید",
    "button_url": "#",
    "is_active": "on",
    "order": "0",
}, use_admin=True)
pp = PricingPlan.objects.filter(name_en="Test Plan").exists()
if pp:
    results["pass"].append("Pricing Add: data saved")
    print("  Pricing Add: data saved")
else:
    results["form_issues"].append("Pricing Add: data NOT saved!")
    print("  Pricing Add: data NOT saved!")

# Test Testimonial add
test_post("Testimonial Add", "/admin-panel/testimonials/", {
    "action": "add",
    "quote_en": "Great service!",
    "quote_fa": "عالی!",
    "author_name": "Test Person",
    "author_role_en": "CEO",
    "author_role_fa": "مدیر",
    "is_active": "on",
    "order": "0",
}, use_admin=True)
tm = Testimonial.objects.filter(author_name="Test Person").exists()
if tm:
    results["pass"].append("Testimonial Add: data saved")
    print("  Testimonial Add: data saved")
else:
    results["form_issues"].append("Testimonial Add: data NOT saved!")
    print("  Testimonial Add: data NOT saved!")

# Test Team Member add
test_post("Team Add", "/admin-panel/team/", {
    "action": "add",
    "name": "Test Member",
    "position_en": "Developer",
    "position_fa": "توسعه‌دهنده",
    "bio_en": "Test bio",
    "bio_fa": "تست",
    "is_active": "on",
    "order": "0",
}, use_admin=True)
tm_member = TeamMember.objects.filter(name="Test Member").exists()
if tm_member:
    results["pass"].append("Team Add: data saved")
    print("  Team Add: data saved")
else:
    results["form_issues"].append("Team Add: data NOT saved!")
    print("  Team Add: data NOT saved!")

# Test Page add
test_post("Page Add", "/admin-panel/pages/", {
    "action": "add",
    "title_en": "Test Page",
    "title_fa": "تست",
    "content_en": "Test content",
    "content_fa": "تست",
    "meta_title_en": "Test Page",
    "meta_title_fa": "تست",
    "meta_description_en": "Test desc",
    "meta_description_fa": "تست",
    "is_active": "on",
    "show_in_menu": "on",
}, use_admin=True)
pg = Page.objects.filter(title_en="Test Page").exists()
if pg:
    results["pass"].append("Page Add: data saved")
    print("  Page Add: data saved")
else:
    results["form_issues"].append("Page Add: data NOT saved!")
    print("  Page Add: data NOT saved!")

# Test Site Settings save
test_post("Site Settings Save", "/admin-panel/settings/", {
    "site_name_en": "AM Business Updated",
    "site_name_fa": "ای ام بیزینس",
    "phone": "+968 94 749 749",
    "email": "info@ambusinessintl.com",
    "address_en": "Muscat, Oman",
    "address_fa": "مسقط، عمان",
    "meta_description_en": "AM Business",
    "meta_description_fa": "ای ام بیزینس",
    "copyright_text_en": "By Am Business",
    "copyright_text_fa": "توسط ای ام بیزینس",
    "footer_phone": "+968 94 749 749",
    "footer_location": "Muscat",
    "footer_linkedin": "ambusinessintl",
    "footer_whatsapp": "+96894749749",
    "footer_instagram": "ambusinessintl",
    "footer_email": "info@ambusinessintl.com",
}, use_admin=True)
ss = SiteSettings.objects.first()
if ss and ss.site_name_en == "AM Business Updated":
    results["pass"].append("Site Settings Save: data saved")
    print("  Site Settings Save: data saved")
else:
    results["form_issues"].append("Site Settings Save: data NOT saved!")
    print("  Site Settings Save: data NOT saved!")

# Test About Section save
test_post("About Save", "/admin-panel/about/", {
    "title_en": "About Us Updated",
    "title_fa": "درباره ما",
    "content_en": "About content",
    "content_fa": "محتوا",
    "who_we_are_en": "We are AM",
    "who_we_are_fa": "ما ای ام هستیم",
    "we_are_expert_en": "Expert team",
    "we_are_expert_fa": "تیم متخصص",
    "why_choose_us_title_en": "Why Choose Us",
    "why_choose_us_title_fa": "چرا ما",
    "why_choose_us_content_en": "Because we are the best",
    "why_choose_us_content_fa": "چون بهترین هستیم",
    "cta_text_en": "Get Started",
    "cta_text_fa": "شروع",
    "cta_url": "#",
    "is_active": "on",
}, use_admin=True)
ab = AboutSection.objects.first()
if ab and ab.title_en == "About Us Updated":
    results["pass"].append("About Save: data saved")
    print("  About Save: data saved")
else:
    results["form_issues"].append("About Save: data NOT saved!")
    print("  About Save: data NOT saved!")

# Test Event Countdown save
test_post("Event Countdown Save", "/admin-panel/event-countdown/", {
    "title_en": "Big Event",
    "title_fa": "رویداد بزرگ",
    "subheading_en": "Don't miss it",
    "subheading_fa": "از دستش ندهید",
    "event_date": "2026-12-31T23:59",
    "ended_message_en": "Event ended!",
    "ended_message_fa": "رویداد تمام شد!",
    "cta_text_en": "Join Now",
    "cta_text_fa": "همین حالا عضو شوید",
    "cta_url": "#",
    "is_active": "on",
}, use_admin=True)
ec = EventCountdown.objects.first()
if ec and ec.title_en == "Big Event":
    results["pass"].append("Event Countdown Save: data saved")
    print("  Event Countdown Save: data saved")
else:
    results["form_issues"].append("Event Countdown Save: data NOT saved!")
    print("  Event Countdown Save: data NOT saved!")

# Test Home Section edit
if HomeSection.objects.exists():
    hs = HomeSection.objects.first()
    test_post("Home Section Edit", "/admin-panel/home-sections/", {
        "action": "edit",
        "pk": str(hs.pk),
        "title_en": "Updated Title",
        "title_fa": "عنوان به‌روزرسانی‌شده",
        "subheading_en": "Updated sub",
        "subheading_fa": "زیرعنوان",
        "content_en": "Updated content",
        "content_fa": "محتوا",
        "cta_text_en": "Updated CTA",
        "cta_text_fa": "دکمه",
        "cta_url": "#",
        "is_active": "on",
    }, use_admin=True)
    hs.refresh_from_db()
    if hs.title_en == "Updated Title":
        results["pass"].append("Home Section Edit: data saved")
        print("  Home Section Edit: data saved")
    else:
        results["form_issues"].append("Home Section Edit: data NOT saved!")
        print("  Home Section Edit: data NOT saved!")

# Test Hero Section edit
if HeroSection.objects.exists():
    hero = HeroSection.objects.first()
    test_post("Hero Section Edit", "/admin-panel/hero/", {
        "action": "edit",
        "pk": str(hero.pk),
        "heading_en": "Updated Hero",
        "heading_fa": "بنر به‌روزرسانی‌شده",
        "subheading_en": "Updated sub",
        "subheading_fa": "زیرعنوان",
        "cta_text_en": "Updated CTA",
        "cta_text_fa": "دکمه",
        "cta_url": "#",
        "is_active": "on",
    }, use_admin=True)
    hero.refresh_from_db()
    if hero.heading_en == "Updated Hero":
        results["pass"].append("Hero Section Edit: data saved")
        print("  Hero Section Edit: data saved")
    else:
        results["form_issues"].append("Hero Section Edit: data NOT saved!")
        print("  Hero Section Edit: data NOT saved!")

# Test Messages actions
if ContactMessage.objects.exists():
    msg = ContactMessage.objects.first()
    test_post("Message Mark Read", "/admin-panel/messages/", {
        "action": "mark_read",
        "pk": str(msg.pk),
    }, use_admin=True)
    msg.refresh_from_db()
    if msg.is_read:
        results["pass"].append("Message Mark Read: success")
        print("  Message Mark Read: success")
    else:
        results["form_issues"].append("Message Mark Read: FAILED!")
        print("  Message Mark Read: FAILED!")

    test_post("Message Mark Replied", "/admin-panel/messages/", {
        "action": "mark_replied",
        "pk": str(msg.pk),
    }, use_admin=True)
    msg.refresh_from_db()
    if msg.is_replied:
        results["pass"].append("Message Mark Replied: success")
        print("  Message Mark Replied: success")
    else:
        results["form_issues"].append("Message Mark Replied: FAILED!")
        print("  Message Mark Replied: FAILED!")

# Test Newsletter toggle
if NewsletterSubscriber.objects.exists():
    sub = NewsletterSubscriber.objects.first()
    initial_active = sub.is_active
    test_post("Newsletter Toggle", "/admin-panel/newsletter/", {
        "action": "toggle",
        "pk": str(sub.pk),
    }, use_admin=True)
    sub.refresh_from_db()
    if sub.is_active != initial_active:
        results["pass"].append("Newsletter Toggle: success")
        print("  Newsletter Toggle: success")
    else:
        results["form_issues"].append("Newsletter Toggle: FAILED!")
        print("  Newsletter Toggle: FAILED!")

print("\n" + "=" * 70)
print("TESTING EDGE CASES")
print("=" * 70)

# Test with invalid order value
test_post("Service Add (invalid order)", "/admin-panel/services/", {
    "action": "add",
    "title_en": "Bad Order Service",
    "title_fa": "تست",
    "description_en": "desc",
    "description_fa": "تست",
    "icon": "gear",
    "custom_svg": "",
    "is_active": "on",
    "order": "abc",  # Invalid integer
}, use_admin=True)
print("  Tested: Service Add with invalid order value")

# Test with invalid price
test_post("Pricing Add (invalid price)", "/admin-panel/pricing/", {
    "action": "add",
    "name_en": "Bad Price Plan",
    "name_fa": "تست",
    "description_en": "desc",
    "description_fa": "تست",
    "price": "not_a_number",  # Invalid float
    "currency": "$",
    "cents": ".99",
    "button_text_en": "Buy",
    "button_text_fa": "خرید",
    "button_url": "#",
    "is_active": "on",
    "order": "0",
}, use_admin=True)
print("  Tested: Pricing Add with invalid price value")

# Test Event Countdown with empty date
test_post("Event Countdown (empty date)", "/admin-panel/event-countdown/", {
    "title_en": "No Date",
    "title_fa": "بدون تاریخ",
    "subheading_en": "sub",
    "subheading_fa": "زیر",
    "event_date": "",  # Empty date
    "ended_message_en": "Ended",
    "ended_message_fa": "تمام",
    "cta_text_en": "CTA",
    "cta_text_fa": "دکمه",
    "cta_url": "#",
    "is_active": "on",
}, use_admin=True)
print("  Tested: Event Countdown with empty date")

# Test unauthenticated access to admin panel
try:
    resp = client.get("/admin-panel/")
    if resp.status_code == 302 and "/accounts/login/" in resp.url:
        results["pass"].append("Unauthenticated admin redirect: correct")
        print("  Unauthenticated admin redirect: correct")
    else:
        results["fail_other"].append(f"Unauthenticated admin: {resp.status_code} (expected 302)")
        print(f"  Unauthenticated admin: {resp.status_code} (expected 302)")
except Exception as e:
    results["fail_500"].append(f"Unauthenticated admin: EXCEPTION: {e}")
    print(f"  Unauthenticated admin: EXCEPTION: {e}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"PASS: {len(results['pass'])}")
print(f"FAIL (500): {len(results['fail_500'])}")
print(f"FAIL (Other): {len(results['fail_other'])}")
print(f"FORM ISSUES: {len(results['form_issues'])}")

if results["fail_500"]:
    print("\n--- 500 ERRORS ---")
    for f in results["fail_500"]:
        print(f"  {f}")

if results["fail_other"]:
    print("\n--- OTHER ERRORS ---")
    for f in results["fail_other"]:
        print(f"  {f}")

if results["form_issues"]:
    print("\n--- FORM ISSUES ---")
    for f in results["form_issues"]:
        print(f"  {f}")

if not results["fail_500"] and not results["fail_other"] and not results["form_issues"]:
    print("\n  ALL TESTS PASSED!")
