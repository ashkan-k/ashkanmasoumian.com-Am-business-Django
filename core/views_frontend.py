from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (
    SiteSettings, SocialLink, Navigation, HeroSection, Service,
    AboutSection, StatCounter, Feature, PricingPlan, Testimonial,
    TeamMember, ContactMessage, NewsletterSubscriber, EventCountdown,
    HomeSection, Page, SUPPORTED_LANGUAGES, get_sections
)


def get_lang(request):
    lang = request.COOKIES.get("django_language", "en").split("-")[0]
    return lang if lang in SUPPORTED_LANGUAGES else "en"


def say(request, en, fa, ar=""):
    """Translate a visitor-facing flash message for the active language."""
    lang = get_lang(request)
    if lang == "fa":
        return fa or en
    if lang == "ar":
        return ar or en
    return en


def grid_columns(count, max_columns=4):
    """Bootstrap column width (out of 12) so `count` cards fill the row.

    Three cards → 4 (three per row), four cards → 3, and so on; more cards
    than ``max_columns`` keep that width and simply wrap onto a new row.
    """
    if not count:
        return 12 // max_columns
    return 12 // max(1, min(count, max_columns))


def apply_limit(items, styles, section_key, fallback=None):
    """Trim a section's items to the limit set in the dashboard.

    ``item_limit`` of 0 means "show every active item"; ``fallback`` is used
    when the section has no row yet (first run before migrations).
    """
    style = (styles or {}).get(section_key)
    limit = style.item_limit if style else (fallback or 0)
    if limit and limit > 0:
        return items[:limit]
    return items


def frontend_context(request):
    """Common context for all frontend pages"""
    lang = get_lang(request)
    try:
        site = SiteSettings.objects.first()
    except Exception:
        site = None
    nav_items = Navigation.objects.filter(is_active=True, parent=None)
    social_links = SocialLink.objects.filter(is_active=True)
    return {
        "lang": lang,
        "site_settings": site,
        "nav_items": nav_items,
        "social_links": social_links,
        # Backgrounds/headings edited in the "Sections & Backgrounds" page.
        # Sections switched off there are simply missing from this mapping,
        # so the templates fall back to the theme defaults.
        "sections": get_sections(active_only=True),
    }


def _meta_title(lang, ctx, en, fa, ar):
    """Build a "<page> - <site name>" document title for the active language."""
    page_name = {"en": en, "fa": fa, "ar": ar}.get(lang, en)
    site = ctx.get("site_settings")
    site_name = site.get_site_name(lang) if site else "AM Business"
    return f"{page_name} - {site_name}"


def frontend_home(request):
    ctx = frontend_context(request)
    lang = ctx["lang"]
    styles = ctx["sections"]

    services = list(apply_limit(Service.objects.filter(is_active=True), styles, "services", 8))
    plans = list(apply_limit(PricingPlan.objects.filter(is_active=True), styles, "pricing"))
    features = list(apply_limit(Feature.objects.filter(is_active=True), styles, "features", 3))
    team = list(apply_limit(TeamMember.objects.filter(is_active=True), styles, "team", 4))
    testimonials = list(apply_limit(Testimonial.objects.filter(is_active=True), styles, "testimonials"))

    ctx.update({
        "hero": HeroSection.objects.filter(page="home", is_active=True).first(),
        "services": services,
        "service_columns": grid_columns(len(services)),
        "about": AboutSection.objects.filter(is_active=True).first(),
        "home_about": HomeSection.objects.filter(section_type="home_about", is_active=True).first(),
        "home_why": HomeSection.objects.filter(section_type="home_why", is_active=True).first(),
        "pricing_plans": plans,
        # One column per plan, so four plans in the dashboard show as four cards.
        "plan_columns": 12 // max(1, min(len(plans), 4)) if plans else 4,
        "features": features,
        "feature_columns": grid_columns(len(features), 4),
        "testimonials": testimonials,
        "team_members": team,
        "team_columns": 12 // max(1, min(len(team), 2)) if team else 6,
        "countdown": EventCountdown.objects.filter(is_active=True).first(),
        "meta_title": _meta_title(lang, ctx, "Home", "خانه", "الرئيسية"),
    })
    return render(request, "frontend/index.html", ctx)


def frontend_about(request):
    ctx = frontend_context(request)
    lang = ctx["lang"]
    services = list(apply_limit(Service.objects.filter(is_active=True), ctx["sections"], "services", 8))
    ctx.update({
        "hero": HeroSection.objects.filter(page="about", is_active=True).first(),
        "about": AboutSection.objects.filter(is_active=True).first(),
        "counters": StatCounter.objects.filter(is_active=True),
        "team_members": TeamMember.objects.filter(is_active=True),
        "services": services,
        "service_columns": grid_columns(len(services)),
        "countdown": EventCountdown.objects.filter(is_active=True).first(),
        "meta_title": _meta_title(lang, ctx, "About", "درباره ما", "من نحن"),
    })
    return render(request, "frontend/about.html", ctx)


def frontend_services(request):
    ctx = frontend_context(request)
    lang = ctx["lang"]
    services = list(Service.objects.filter(is_active=True))
    ctx.update({
        "hero": HeroSection.objects.filter(page="services", is_active=True).first(),
        "services": services,
        "service_columns": grid_columns(len(services)),
        "about": AboutSection.objects.filter(is_active=True).first(),
        "meta_title": _meta_title(lang, ctx, "Services", "خدمات", "الخدمات"),
    })
    return render(request, "frontend/services.html", ctx)


def frontend_page(request, slug):
    """Render a CMS page created in the dashboard (for example /page/portfolio/)."""
    ctx = frontend_context(request)
    lang = ctx["lang"]
    page = Page.objects.filter(slug=slug, is_active=True).first()
    if page is None:
        # A CMS page may exist but be inactive — still show it to staff so a
        # draft can be previewed, otherwise fall back to a 404.
        page = Page.objects.filter(slug=slug).first()
        if page is None or not request.user.is_staff:
            from django.http import Http404
            raise Http404("Page not found")

    hero = HeroSection.objects.filter(page=slug).first()
    if hero is None:
        hero = HeroSection.objects.filter(page="custom", is_active=True).first()

    meta_title = page.get_meta_title(lang) or page.get_title(lang)
    meta_description = page.get_meta_description(lang)

    ctx.update({
        "page": page,
        "hero": hero,
        "services": Service.objects.filter(is_active=True)[:4],
        "about": AboutSection.objects.filter(is_active=True).first(),
        "meta_title": f"{meta_title} - {ctx['site_settings'].get_site_name(lang)}" if ctx.get("site_settings") else meta_title,
        "meta_description": meta_description,
    })
    return render(request, "frontend/page.html", ctx)


def frontend_contact(request):
    ctx = frontend_context(request)
    lang = ctx["lang"]

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()
        if name and email and message:
            ContactMessage.objects.create(
                name=name, email=email, subject=subject, message=message
            )
            # Language-aware success toast
            messages.success(request, say(
                request,
                "Your message has been sent successfully!",
                "پیام شما با موفقیت ارسال شد!",
                "تم إرسال رسالتك بنجاح!",
            ))
            # Post/Redirect/Get pattern: redirect to avoid resubmission on refresh
            return redirect(f"{request.path}?sent=1")
        else:
            # Missing required fields — language-aware error toast
            messages.error(request, say(
                request,
                "Please fill in all required fields.",
                "لطفاً تمام فیلدهای ضروری را پر کنید.",
                "يرجى تعبئة جميع الحقول المطلوبة.",
            ))

    ctx.update({
        "hero": HeroSection.objects.filter(page="contact", is_active=True).first(),
        "testimonials": Testimonial.objects.filter(is_active=True),
        "contact_success": request.GET.get("sent") == "1",
        "meta_title": _meta_title(lang, ctx, "Contact", "تماس با ما", "اتصل بنا"),
    })
    return render(request, "frontend/contact.html", ctx)


def frontend_newsletter_subscribe(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        if email:
            obj, created = NewsletterSubscriber.objects.get_or_create(
                email=email, defaults={"name": name or "Subscriber"}
            )
            if created:
                messages.success(request, say(
                    request,
                    "You have successfully subscribed to our newsletter!",
                    "شما با موفقیت در خبرنامه ما عضو شدید!",
                    "لقد اشتركت بنجاح في نشرتنا الإخبارية!",
                ))
            else:
                messages.info(request, say(
                    request,
                    "You are already subscribed with this email address.",
                    "شما قبلاً با این ایمیل عضو خبرنامه شده‌اید.",
                    "أنت مشترك بالفعل بهذا البريد الإلكتروني.",
                ))
        else:
            messages.error(request, say(
                request,
                "Please provide a valid email address.",
                "لطفاً یک آدرس ایمیل معتبر وارد کنید.",
                "يرجى إدخال بريد إلكتروني صحيح.",
            ))
    # Redirect back
    referer = request.META.get("HTTP_REFERER", "/")
    return redirect(referer)
