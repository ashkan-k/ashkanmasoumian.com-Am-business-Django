from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (
    SiteSettings, SocialLink, Navigation, HeroSection, Service,
    AboutSection, StatCounter, Feature, PricingPlan, Testimonial,
    TeamMember, ContactMessage, NewsletterSubscriber, EventCountdown,
    HomeSection, SUPPORTED_LANGUAGES
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
    ctx.update({
        "hero": HeroSection.objects.filter(page="home", is_active=True).first(),
        "services": Service.objects.filter(is_active=True)[:8],
        "about": AboutSection.objects.filter(is_active=True).first(),
        "home_about": HomeSection.objects.filter(section_type="home_about", is_active=True).first(),
        "pricing_plans": PricingPlan.objects.filter(is_active=True)[:3],
        "features": Feature.objects.filter(is_active=True)[:3],
        "testimonials": Testimonial.objects.filter(is_active=True),
        "team_members": TeamMember.objects.filter(is_active=True)[:4],
        "countdown": EventCountdown.objects.filter(is_active=True).first(),
        "meta_title": _meta_title(lang, ctx, "Home", "خانه", "الرئيسية"),
    })
    return render(request, "frontend/index.html", ctx)


def frontend_about(request):
    ctx = frontend_context(request)
    lang = ctx["lang"]
    ctx.update({
        "hero": HeroSection.objects.filter(page="about", is_active=True).first(),
        "about": AboutSection.objects.filter(is_active=True).first(),
        "counters": StatCounter.objects.filter(is_active=True),
        "team_members": TeamMember.objects.filter(is_active=True),
        "services": Service.objects.filter(is_active=True)[:8],
        "countdown": EventCountdown.objects.filter(is_active=True).first(),
        "meta_title": _meta_title(lang, ctx, "About", "درباره ما", "من نحن"),
    })
    return render(request, "frontend/about.html", ctx)


def frontend_services(request):
    ctx = frontend_context(request)
    lang = ctx["lang"]
    ctx.update({
        "hero": HeroSection.objects.filter(page="services", is_active=True).first(),
        "services": Service.objects.filter(is_active=True),
        "about": AboutSection.objects.filter(is_active=True).first(),
        "meta_title": _meta_title(lang, ctx, "Services", "خدمات", "الخدمات"),
    })
    return render(request, "frontend/services.html", ctx)


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
