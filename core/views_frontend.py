from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (
    SiteSettings, SocialLink, Navigation, HeroSection, Service,
    AboutSection, StatCounter, Feature, PricingPlan, Testimonial,
    TeamMember, ContactMessage, NewsletterSubscriber, EventCountdown,
    HomeSection
)


def get_lang(request):
    return request.COOKIES.get("django_language", "en")


def get_frontend_context(request):
    """Common context for all frontend pages"""
    lang = get_lang(request)
    try:
        site = SiteSettings.objects.first()
    except:
        site = None
    nav_items = Navigation.objects.filter(is_active=True, parent=None)
    social_links = SocialLink.objects.filter(is_active=True)
    return {
        "lang": lang,
        "site_settings": site,
        "nav_items": nav_items,
        "social_links": social_links,
    }


def frontend_home(request):
    lang = get_lang(request)
    ctx = get_frontend_context(request)
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
        "meta_title": f"{'Home' if lang == 'en' else 'خانه'} - {ctx['site_settings'].site_name_en if ctx['site_settings'] else 'AM Business'}",
    })
    return render(request, "frontend/index.html", ctx)


def frontend_about(request):
    lang = get_lang(request)
    ctx = get_frontend_context(request)
    ctx.update({
        "hero": HeroSection.objects.filter(page="about", is_active=True).first(),
        "about": AboutSection.objects.filter(is_active=True).first(),
        "counters": StatCounter.objects.filter(is_active=True),
        "team_members": TeamMember.objects.filter(is_active=True),
        "services": Service.objects.filter(is_active=True)[:8],
        "meta_title": f"{'About' if lang == 'en' else 'درباره ما'} - {ctx['site_settings'].site_name_en if ctx['site_settings'] else 'AM Business'}",
    })
    return render(request, "frontend/about.html", ctx)


def frontend_services(request):
    lang = get_lang(request)
    ctx = get_frontend_context(request)
    ctx.update({
        "hero": HeroSection.objects.filter(page="services", is_active=True).first(),
        "services": Service.objects.filter(is_active=True),
        "about": AboutSection.objects.filter(is_active=True).first(),
        "meta_title": f"{'Services' if lang == 'en' else 'خدمات'} - {ctx['site_settings'].site_name_en if ctx['site_settings'] else 'AM Business'}",
    })
    return render(request, "frontend/services.html", ctx)


def frontend_contact(request):
    lang = get_lang(request)
    ctx = get_frontend_context(request)
    contact_success = False

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()
        if name and email and message:
            ContactMessage.objects.create(
                name=name, email=email, subject=subject, message=message
            )
            contact_success = True

    ctx.update({
        "hero": HeroSection.objects.filter(page="contact", is_active=True).first(),
        "testimonials": Testimonial.objects.filter(is_active=True),
        "contact_success": contact_success,
        "meta_title": f"{'Contact' if lang == 'en' else 'تماس با ما'} - {ctx['site_settings'].site_name_en if ctx['site_settings'] else 'AM Business'}",
    })
    return render(request, "frontend/contact.html", ctx)


def frontend_newsletter_subscribe(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        if email:
            NewsletterSubscriber.objects.get_or_create(
                email=email, defaults={"name": name or "Subscriber"}
            )
    # Redirect back
    referer = request.META.get("HTTP_REFERER", "/")
    return redirect(referer)
