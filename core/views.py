from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import translation
from django.views.decorators.http import require_POST
from .models import (
    SiteSettings, SocialLink, Navigation, HeroSection, Service,
    AboutSection, StatCounter, Feature, PricingPlan, Testimonial,
    TeamMember, ContactMessage, NewsletterSubscriber, EventCountdown,
    Page, HomeSection
)


def get_lang(request):
    return request.COOKIES.get("django_language", "en")


def set_language_view(request, lang):
    """Set language preference via cookie"""
    if lang not in ("en", "fa"):
        lang = "en"
    response = redirect(request.META.get("HTTP_REFERER", "/admin-panel/"))
    response.set_cookie("django_language", lang, max_age=365 * 24 * 60 * 60)
    translation.activate(lang)
    return response


def set_theme_view(request, theme):
    """Set theme preference via cookie"""
    if theme not in ("light", "dark"):
        theme = "light"
    response = redirect(request.META.get("HTTP_REFERER", "/admin-panel/"))
    response.set_cookie("theme", theme, max_age=365 * 24 * 60 * 60)
    return response


# ──────────────────────── AUTH ────────────────────────
def admin_login(request):
    if request.user.is_authenticated:
        return redirect("admin_dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect("admin_dashboard")
        messages.error(request, "Invalid username or password")
    lang = get_lang(request)
    return render(request, "admin_panel/login.html", {"lang": lang, "theme": request.COOKIES.get("theme", "light")})


@login_required(login_url="/accounts/login/")
def admin_logout(request):
    logout(request)
    return redirect("admin_login")


# ──────────────────────── DASHBOARD ────────────────────────
@login_required(login_url="/accounts/login/")
def dashboard(request):
    lang = get_lang(request)
    ctx = {
        "lang": lang,
        "page_title": "Dashboard",
        "services_count": Service.objects.filter(is_active=True).count(),
        "team_count": TeamMember.objects.filter(is_active=True).count(),
        "testimonials_count": Testimonial.objects.filter(is_active=True).count(),
        "pricing_count": PricingPlan.objects.filter(is_active=True).count(),
        "messages_count": ContactMessage.objects.count(),
        "unread_messages": ContactMessage.objects.filter(is_read=False).count(),
        "subscribers_count": NewsletterSubscriber.objects.filter(is_active=True).count(),
        "pages_count": Page.objects.filter(is_active=True).count(),
        "recent_messages": ContactMessage.objects.all()[:5],
    }
    return render(request, "admin_panel/dashboard.html", ctx)


# ──────────────────────── SITE SETTINGS ────────────────────────
@login_required(login_url="/accounts/login/")
def site_settings_view(request):
    lang = get_lang(request)
    obj = SiteSettings.objects.first()
    if not obj:
        obj = SiteSettings.objects.create(site_name_en="AM Business")
    if request.method == "POST":
        obj.site_name_en = request.POST.get("site_name_en", obj.site_name_en)
        obj.site_name_fa = request.POST.get("site_name_fa", obj.site_name_fa)
        obj.phone = request.POST.get("phone", obj.phone)
        obj.email = request.POST.get("email", obj.email)
        obj.address_en = request.POST.get("address_en", obj.address_en)
        obj.address_fa = request.POST.get("address_fa", obj.address_fa)
        obj.meta_description_en = request.POST.get("meta_description_en", obj.meta_description_en)
        obj.meta_description_fa = request.POST.get("meta_description_fa", obj.meta_description_fa)
        obj.copyright_text_en = request.POST.get("copyright_text_en", obj.copyright_text_en)
        obj.copyright_text_fa = request.POST.get("copyright_text_fa", obj.copyright_text_fa)
        obj.footer_phone = request.POST.get("footer_phone", obj.footer_phone)
        obj.footer_location = request.POST.get("footer_location", obj.footer_location)
        obj.footer_linkedin = request.POST.get("footer_linkedin", obj.footer_linkedin)
        obj.footer_whatsapp = request.POST.get("footer_whatsapp", obj.footer_whatsapp)
        obj.footer_instagram = request.POST.get("footer_instagram", obj.footer_instagram)
        obj.footer_email = request.POST.get("footer_email", obj.footer_email)
        if request.FILES.get("logo"):
            obj.logo = request.FILES["logo"]
        if request.FILES.get("favicon"):
            obj.favicon = request.FILES["favicon"]
        obj.save()
        messages.success(request, "Settings saved successfully!")
        return redirect("admin_site_settings")
    return render(request, "admin_panel/site_settings.html", {"lang": lang, "settings": obj, "page_title": "Site Settings"})


# ──────────────────────── SOCIAL LINKS ────────────────────────
@login_required(login_url="/accounts/login/")
def social_links_view(request):
    lang = get_lang(request)
    items = SocialLink.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "add":
            sl = SocialLink(
                platform=request.POST.get("platform", "facebook"),
                url=request.POST.get("url", "#"),
                icon_class=request.POST.get("icon_class", ""),
                is_active="is_active" in request.POST,
                order=int(request.POST.get("order", 0)),
            )
            if request.FILES.get("icon_image"):
                sl.icon_image = request.FILES["icon_image"]
            sl.save()
            messages.success(request, "Social link added!")
        elif action == "delete":
            pk = request.POST.get("pk")
            SocialLink.objects.filter(pk=pk).delete()
            messages.success(request, "Social link deleted!")
        elif action == "edit":
            pk = request.POST.get("pk")
            obj = get_object_or_404(SocialLink, pk=pk)
            obj.platform = request.POST.get("platform", obj.platform)
            obj.url = request.POST.get("url", obj.url)
            obj.icon_class = request.POST.get("icon_class", obj.icon_class)
            obj.is_active = "is_active" in request.POST
            obj.order = int(request.POST.get("order", 0))
            if request.FILES.get("icon_image"):
                obj.icon_image = request.FILES["icon_image"]
            obj.save()
            messages.success(request, "Social link updated!")
        return redirect("admin_social_links")
    return render(request, "admin_panel/social_links.html", {"lang": lang, "items": items, "page_title": "Social Links"})


# ──────────────────────── NAVIGATION ────────────────────────
@login_required(login_url="/accounts/login/")
def navigation_view(request):
    lang = get_lang(request)
    items = Navigation.objects.filter(parent=None)
    all_items = Navigation.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "add":
            parent_id = request.POST.get("parent")
            parent = Navigation.objects.filter(pk=parent_id).first() if parent_id else None
            Navigation.objects.create(
                title_en=request.POST.get("title_en", ""),
                title_fa=request.POST.get("title_fa", ""),
                url=request.POST.get("url", "#"),
                is_active="is_active" in request.POST,
                order=int(request.POST.get("order", 0)),
                parent=parent,
            )
            messages.success(request, "Navigation item added!")
        elif action == "delete":
            pk = request.POST.get("pk")
            Navigation.objects.filter(pk=pk).delete()
            messages.success(request, "Navigation item deleted!")
        elif action == "edit":
            pk = request.POST.get("pk")
            obj = get_object_or_404(Navigation, pk=pk)
            obj.title_en = request.POST.get("title_en", obj.title_en)
            obj.title_fa = request.POST.get("title_fa", obj.title_fa)
            obj.url = request.POST.get("url", obj.url)
            obj.is_active = "is_active" in request.POST
            obj.order = int(request.POST.get("order", 0))
            parent_id = request.POST.get("parent")
            obj.parent = Navigation.objects.filter(pk=parent_id).first() if parent_id else None
            obj.save()
            messages.success(request, "Navigation item updated!")
        return redirect("admin_navigation")
    return render(request, "admin_panel/navigation.html", {
        "lang": lang, "items": items, "all_items": all_items, "page_title": "Navigation"
    })


# ──────────────────────── HERO SECTIONS ────────────────────────
@login_required(login_url="/accounts/login/")
def hero_sections_view(request):
    lang = get_lang(request)
    items = HeroSection.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "edit":
            pk = request.POST.get("pk")
            obj = get_object_or_404(HeroSection, pk=pk)
            obj.heading_en = request.POST.get("heading_en", obj.heading_en)
            obj.heading_fa = request.POST.get("heading_fa", obj.heading_fa)
            obj.subheading_en = request.POST.get("subheading_en", obj.subheading_en)
            obj.subheading_fa = request.POST.get("subheading_fa", obj.subheading_fa)
            obj.cta_text_en = request.POST.get("cta_text_en", obj.cta_text_en)
            obj.cta_text_fa = request.POST.get("cta_text_fa", obj.cta_text_fa)
            obj.cta_url = request.POST.get("cta_url", obj.cta_url)
            obj.is_active = "is_active" in request.POST
            if request.FILES.get("background_image"):
                obj.background_image = request.FILES["background_image"]
            obj.save()
            messages.success(request, "Hero section updated!")
        elif action == "add":
            HeroSection.objects.create(
                page=request.POST.get("page", "home"),
                heading_en=request.POST.get("heading_en", ""),
                heading_fa=request.POST.get("heading_fa", ""),
                subheading_en=request.POST.get("subheading_en", ""),
                subheading_fa=request.POST.get("subheading_fa", ""),
                cta_text_en=request.POST.get("cta_text_en", ""),
                cta_text_fa=request.POST.get("cta_text_fa", ""),
                cta_url=request.POST.get("cta_url", "#"),
                is_active="is_active" in request.POST,
            )
            messages.success(request, "Hero section added!")
        return redirect("admin_hero_sections")
    return render(request, "admin_panel/hero_sections.html", {
        "lang": lang, "items": items, "page_title": "Hero Sections"
    })


# ──────────────────────── SERVICES ────────────────────────
@login_required(login_url="/accounts/login/")
def services_view(request):
    lang = get_lang(request)
    items = Service.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "add":
            svc = Service(
                title_en=request.POST.get("title_en", ""),
                title_fa=request.POST.get("title_fa", ""),
                description_en=request.POST.get("description_en", ""),
                description_fa=request.POST.get("description_fa", ""),
                icon=request.POST.get("icon", "gear"),
                custom_svg=request.POST.get("custom_svg", ""),
                is_active="is_active" in request.POST,
                order=int(request.POST.get("order", 0)),
            )
            if request.FILES.get("image"):
                svc.image = request.FILES["image"]
            if request.FILES.get("custom_icon"):
                svc.custom_icon = request.FILES["custom_icon"]
            svc.save()
            messages.success(request, "Service added!")
        elif action == "delete":
            pk = request.POST.get("pk")
            Service.objects.filter(pk=pk).delete()
            messages.success(request, "Service deleted!")
        elif action == "edit":
            pk = request.POST.get("pk")
            obj = get_object_or_404(Service, pk=pk)
            obj.title_en = request.POST.get("title_en", obj.title_en)
            obj.title_fa = request.POST.get("title_fa", obj.title_fa)
            obj.description_en = request.POST.get("description_en", obj.description_en)
            obj.description_fa = request.POST.get("description_fa", obj.description_fa)
            obj.icon = request.POST.get("icon", obj.icon)
            obj.custom_svg = request.POST.get("custom_svg", obj.custom_svg)
            obj.is_active = "is_active" in request.POST
            obj.order = int(request.POST.get("order", 0))
            if request.FILES.get("image"):
                obj.image = request.FILES["image"]
            if request.FILES.get("custom_icon"):
                obj.custom_icon = request.FILES["custom_icon"]
            obj.save()
            messages.success(request, "Service updated!")
        return redirect("admin_services")
    return render(request, "admin_panel/services.html", {
        "lang": lang, "items": items, "page_title": "Services"
    })


# ──────────────────────── ABOUT ────────────────────────
@login_required(login_url="/accounts/login/")
def about_view(request):
    lang = get_lang(request)
    obj = AboutSection.objects.first()
    if not obj:
        obj = AboutSection.objects.create(
            title_en="About Us", title_fa="درباره ما",
            content_en="About content", content_fa="محتوای درباره ما"
        )
    if request.method == "POST":
        obj.title_en = request.POST.get("title_en", obj.title_en)
        obj.title_fa = request.POST.get("title_fa", obj.title_fa)
        obj.content_en = request.POST.get("content_en", obj.content_en)
        obj.content_fa = request.POST.get("content_fa", obj.content_fa)
        obj.who_we_are_en = request.POST.get("who_we_are_en", obj.who_we_are_en)
        obj.who_we_are_fa = request.POST.get("who_we_are_fa", obj.who_we_are_fa)
        obj.we_are_expert_en = request.POST.get("we_are_expert_en", obj.we_are_expert_en)
        obj.we_are_expert_fa = request.POST.get("we_are_expert_fa", obj.we_are_expert_fa)
        obj.why_choose_us_title_en = request.POST.get("why_choose_us_title_en", obj.why_choose_us_title_en)
        obj.why_choose_us_title_fa = request.POST.get("why_choose_us_title_fa", obj.why_choose_us_title_fa)
        obj.why_choose_us_content_en = request.POST.get("why_choose_us_content_en", obj.why_choose_us_content_en)
        obj.why_choose_us_content_fa = request.POST.get("why_choose_us_content_fa", obj.why_choose_us_content_fa)
        obj.cta_text_en = request.POST.get("cta_text_en", obj.cta_text_en)
        obj.cta_text_fa = request.POST.get("cta_text_fa", obj.cta_text_fa)
        obj.cta_url = request.POST.get("cta_url", obj.cta_url)
        obj.is_active = "is_active" in request.POST
        if request.FILES.get("image"):
            obj.image = request.FILES["image"]
        if request.FILES.get("why_choose_us_image"):
            obj.why_choose_us_image = request.FILES["why_choose_us_image"]
        obj.save()
        messages.success(request, "About section saved!")
        return redirect("admin_about")
    return render(request, "admin_panel/about.html", {"lang": lang, "obj": obj, "page_title": "About Section"})


# ──────────────────────── STAT COUNTERS ────────────────────────
@login_required(login_url="/accounts/login/")
def stat_counters_view(request):
    lang = get_lang(request)
    items = StatCounter.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "add":
            StatCounter.objects.create(
                label_en=request.POST.get("label_en", ""),
                label_fa=request.POST.get("label_fa", ""),
                value=int(request.POST.get("value", 0)),
                icon_class=request.POST.get("icon_class", ""),
                is_active="is_active" in request.POST,
                order=int(request.POST.get("order", 0)),
            )
            messages.success(request, "Counter added!")
        elif action == "delete":
            StatCounter.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, "Counter deleted!")
        elif action == "edit":
            obj = get_object_or_404(StatCounter, pk=request.POST.get("pk"))
            obj.label_en = request.POST.get("label_en", obj.label_en)
            obj.label_fa = request.POST.get("label_fa", obj.label_fa)
            obj.value = int(request.POST.get("value", obj.value))
            obj.icon_class = request.POST.get("icon_class", obj.icon_class)
            obj.is_active = "is_active" in request.POST
            obj.order = int(request.POST.get("order", 0))
            obj.save()
            messages.success(request, "Counter updated!")
        return redirect("admin_stat_counters")
    return render(request, "admin_panel/stat_counters.html", {
        "lang": lang, "items": items, "page_title": "Stat Counters"
    })


# ──────────────────────── FEATURES ────────────────────────
@login_required(login_url="/accounts/login/")
def features_view(request):
    lang = get_lang(request)
    items = Feature.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "add":
            Feature.objects.create(
                title_en=request.POST.get("title_en", ""),
                title_fa=request.POST.get("title_fa", ""),
                description_en=request.POST.get("description_en", ""),
                description_fa=request.POST.get("description_fa", ""),
                icon=request.POST.get("icon", ""),
                is_active="is_active" in request.POST,
                order=int(request.POST.get("order", 0)),
            )
            messages.success(request, "Feature added!")
        elif action == "delete":
            Feature.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, "Feature deleted!")
        elif action == "edit":
            obj = get_object_or_404(Feature, pk=request.POST.get("pk"))
            obj.title_en = request.POST.get("title_en", obj.title_en)
            obj.title_fa = request.POST.get("title_fa", obj.title_fa)
            obj.description_en = request.POST.get("description_en", obj.description_en)
            obj.description_fa = request.POST.get("description_fa", obj.description_fa)
            obj.icon = request.POST.get("icon", obj.icon)
            obj.is_active = "is_active" in request.POST
            obj.order = int(request.POST.get("order", 0))
            obj.save()
            messages.success(request, "Feature updated!")
        return redirect("admin_features")
    return render(request, "admin_panel/features.html", {
        "lang": lang, "items": items, "page_title": "Features"
    })


# ──────────────────────── PRICING ────────────────────────
@login_required(login_url="/accounts/login/")
def pricing_view(request):
    lang = get_lang(request)
    items = PricingPlan.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "add":
            PricingPlan.objects.create(
                name_en=request.POST.get("name_en", ""),
                name_fa=request.POST.get("name_fa", ""),
                description_en=request.POST.get("description_en", ""),
                description_fa=request.POST.get("description_fa", ""),
                price=float(request.POST.get("price", 0)),
                currency=request.POST.get("currency", "$"),
                cents=request.POST.get("cents", ".99"),
                is_popular="is_popular" in request.POST,
                button_text_en=request.POST.get("button_text_en", "Buy"),
                button_text_fa=request.POST.get("button_text_fa", "خرید"),
                button_url=request.POST.get("button_url", "#"),
                is_active="is_active" in request.POST,
                order=int(request.POST.get("order", 0)),
            )
            messages.success(request, "Pricing plan added!")
        elif action == "delete":
            PricingPlan.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, "Pricing plan deleted!")
        elif action == "edit":
            obj = get_object_or_404(PricingPlan, pk=request.POST.get("pk"))
            obj.name_en = request.POST.get("name_en", obj.name_en)
            obj.name_fa = request.POST.get("name_fa", obj.name_fa)
            obj.description_en = request.POST.get("description_en", obj.description_en)
            obj.description_fa = request.POST.get("description_fa", obj.description_fa)
            obj.price = float(request.POST.get("price", obj.price))
            obj.currency = request.POST.get("currency", obj.currency)
            obj.cents = request.POST.get("cents", obj.cents)
            obj.is_popular = "is_popular" in request.POST
            obj.button_text_en = request.POST.get("button_text_en", obj.button_text_en)
            obj.button_text_fa = request.POST.get("button_text_fa", obj.button_text_fa)
            obj.button_url = request.POST.get("button_url", obj.button_url)
            obj.is_active = "is_active" in request.POST
            obj.order = int(request.POST.get("order", 0))
            obj.save()
            messages.success(request, "Pricing plan updated!")
        return redirect("admin_pricing")
    return render(request, "admin_panel/pricing.html", {
        "lang": lang, "items": items, "page_title": "Pricing Plans"
    })


# ──────────────────────── TESTIMONIALS ────────────────────────
@login_required(login_url="/accounts/login/")
def testimonials_view(request):
    lang = get_lang(request)
    items = Testimonial.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "add":
            Testimonial.objects.create(
                quote_en=request.POST.get("quote_en", ""),
                quote_fa=request.POST.get("quote_fa", ""),
                author_name=request.POST.get("author_name", ""),
                author_role_en=request.POST.get("author_role_en", ""),
                author_role_fa=request.POST.get("author_role_fa", ""),
                is_active="is_active" in request.POST,
                order=int(request.POST.get("order", 0)),
            )
            messages.success(request, "Testimonial added!")
        elif action == "delete":
            Testimonial.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, "Testimonial deleted!")
        elif action == "edit":
            obj = get_object_or_404(Testimonial, pk=request.POST.get("pk"))
            obj.quote_en = request.POST.get("quote_en", obj.quote_en)
            obj.quote_fa = request.POST.get("quote_fa", obj.quote_fa)
            obj.author_name = request.POST.get("author_name", obj.author_name)
            obj.author_role_en = request.POST.get("author_role_en", obj.author_role_en)
            obj.author_role_fa = request.POST.get("author_role_fa", obj.author_role_fa)
            obj.is_active = "is_active" in request.POST
            obj.order = int(request.POST.get("order", 0))
            if request.FILES.get("author_image"):
                obj.author_image = request.FILES["author_image"]
            obj.save()
            messages.success(request, "Testimonial updated!")
        return redirect("admin_testimonials")
    return render(request, "admin_panel/testimonials.html", {
        "lang": lang, "items": items, "page_title": "Testimonials"
    })


# ──────────────────────── TEAM ────────────────────────
@login_required(login_url="/accounts/login/")
def team_view(request):
    lang = get_lang(request)
    items = TeamMember.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "add":
            TeamMember.objects.create(
                name=request.POST.get("name", ""),
                position_en=request.POST.get("position_en", ""),
                position_fa=request.POST.get("position_fa", ""),
                bio_en=request.POST.get("bio_en", ""),
                bio_fa=request.POST.get("bio_fa", ""),
                is_active="is_active" in request.POST,
                order=int(request.POST.get("order", 0)),
            )
            messages.success(request, "Team member added!")
        elif action == "delete":
            TeamMember.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, "Team member deleted!")
        elif action == "edit":
            obj = get_object_or_404(TeamMember, pk=request.POST.get("pk"))
            obj.name = request.POST.get("name", obj.name)
            obj.position_en = request.POST.get("position_en", obj.position_en)
            obj.position_fa = request.POST.get("position_fa", obj.position_fa)
            obj.bio_en = request.POST.get("bio_en", obj.bio_en)
            obj.bio_fa = request.POST.get("bio_fa", obj.bio_fa)
            obj.is_active = "is_active" in request.POST
            obj.order = int(request.POST.get("order", 0))
            if request.FILES.get("image"):
                obj.image = request.FILES["image"]
            if request.FILES.get("photo_square"):
                obj.photo_square = request.FILES["photo_square"]
            obj.save()
            messages.success(request, "Team member updated!")
        return redirect("admin_team")
    return render(request, "admin_panel/team.html", {
        "lang": lang, "items": items, "page_title": "Team Members"
    })


# ──────────────────────── EVENT COUNTDOWN ────────────────────────
@login_required(login_url="/accounts/login/")
def event_countdown_view(request):
    lang = get_lang(request)
    obj = EventCountdown.objects.first()
    if request.method == "POST":
        if not obj:
            obj = EventCountdown.objects.create(
                event_date=request.POST.get("event_date", ""),
            )
        obj.title_en = request.POST.get("title_en", obj.title_en)
        obj.title_fa = request.POST.get("title_fa", obj.title_fa)
        obj.subheading_en = request.POST.get("subheading_en", obj.subheading_en)
        obj.subheading_fa = request.POST.get("subheading_fa", obj.subheading_fa)
        obj.event_date = request.POST.get("event_date", obj.event_date)
        obj.ended_message_en = request.POST.get("ended_message_en", obj.ended_message_en)
        obj.ended_message_fa = request.POST.get("ended_message_fa", obj.ended_message_fa)
        obj.cta_text_en = request.POST.get("cta_text_en", obj.cta_text_en)
        obj.cta_text_fa = request.POST.get("cta_text_fa", obj.cta_text_fa)
        obj.cta_url = request.POST.get("cta_url", obj.cta_url)
        obj.is_active = "is_active" in request.POST
        obj.save()
        messages.success(request, "Event countdown saved!")
        return redirect("admin_event_countdown")
    return render(request, "admin_panel/event_countdown.html", {
        "lang": lang, "obj": obj, "page_title": "Event Countdown"
    })


# ──────────────────────── HOME SECTIONS ────────────────────────
@login_required(login_url="/accounts/login/")
def home_sections_view(request):
    lang = get_lang(request)
    items = HomeSection.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "edit":
            pk = request.POST.get("pk")
            obj = get_object_or_404(HomeSection, pk=pk)
            obj.title_en = request.POST.get("title_en", obj.title_en)
            obj.title_fa = request.POST.get("title_fa", obj.title_fa)
            obj.subheading_en = request.POST.get("subheading_en", obj.subheading_en)
            obj.subheading_fa = request.POST.get("subheading_fa", obj.subheading_fa)
            obj.content_en = request.POST.get("content_en", obj.content_en)
            obj.content_fa = request.POST.get("content_fa", obj.content_fa)
            obj.cta_text_en = request.POST.get("cta_text_en", obj.cta_text_en)
            obj.cta_text_fa = request.POST.get("cta_text_fa", obj.cta_text_fa)
            obj.cta_url = request.POST.get("cta_url", obj.cta_url)
            obj.is_active = "is_active" in request.POST
            if request.FILES.get("image"):
                obj.image = request.FILES["image"]
            obj.save()
            messages.success(request, "Home section updated!")
        return redirect("admin_home_sections")
    return render(request, "admin_panel/home_sections.html", {
        "lang": lang, "items": items, "page_title": "Home Sections"
    })


# ──────────────────────── MESSAGES ────────────────────────
@login_required(login_url="/accounts/login/")
def messages_view(request):
    lang = get_lang(request)
    items = ContactMessage.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "delete":
            ContactMessage.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, "Message deleted!")
        elif action == "mark_read":
            obj = get_object_or_404(ContactMessage, pk=request.POST.get("pk"))
            obj.is_read = True
            obj.save()
            messages.success(request, "Message marked as read!")
        elif action == "mark_replied":
            obj = get_object_or_404(ContactMessage, pk=request.POST.get("pk"))
            obj.is_replied = True
            obj.save()
            messages.success(request, "Message marked as replied!")
        return redirect("admin_messages")
    return render(request, "admin_panel/messages.html", {
        "lang": lang, "items": items, "page_title": "Contact Messages"
    })


# ──────────────────────── NEWSLETTER ────────────────────────
@login_required(login_url="/accounts/login/")
def newsletter_view(request):
    lang = get_lang(request)
    items = NewsletterSubscriber.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "delete":
            NewsletterSubscriber.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, "Subscriber deleted!")
        elif action == "toggle":
            obj = get_object_or_404(NewsletterSubscriber, pk=request.POST.get("pk"))
            obj.is_active = not obj.is_active
            obj.save()
            messages.success(request, "Subscriber status toggled!")
        return redirect("admin_newsletter")
    return render(request, "admin_panel/newsletter.html", {
        "lang": lang, "items": items, "page_title": "Newsletter Subscribers"
    })


# ──────────────────────── PAGES (CMS) ────────────────────────
@login_required(login_url="/accounts/login/")
def pages_view(request):
    lang = get_lang(request)
    items = Page.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "add":
            from django.utils.text import slugify
            Page.objects.create(
                title_en=request.POST.get("title_en", ""),
                title_fa=request.POST.get("title_fa", ""),
                slug=slugify(request.POST.get("title_en", "page")),
                content_en=request.POST.get("content_en", ""),
                content_fa=request.POST.get("content_fa", ""),
                meta_title_en=request.POST.get("meta_title_en", ""),
                meta_title_fa=request.POST.get("meta_title_fa", ""),
                meta_description_en=request.POST.get("meta_description_en", ""),
                meta_description_fa=request.POST.get("meta_description_fa", ""),
                is_active="is_active" in request.POST,
                show_in_menu="show_in_menu" in request.POST,
            )
            messages.success(request, "Page added!")
        elif action == "delete":
            Page.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, "Page deleted!")
        elif action == "edit":
            obj = get_object_or_404(Page, pk=request.POST.get("pk"))
            obj.title_en = request.POST.get("title_en", obj.title_en)
            obj.title_fa = request.POST.get("title_fa", obj.title_fa)
            obj.content_en = request.POST.get("content_en", obj.content_en)
            obj.content_fa = request.POST.get("content_fa", obj.content_fa)
            obj.meta_title_en = request.POST.get("meta_title_en", obj.meta_title_en)
            obj.meta_title_fa = request.POST.get("meta_title_fa", obj.meta_title_fa)
            obj.meta_description_en = request.POST.get("meta_description_en", obj.meta_description_en)
            obj.meta_description_fa = request.POST.get("meta_description_fa", obj.meta_description_fa)
            obj.is_active = "is_active" in request.POST
            obj.show_in_menu = "show_in_menu" in request.POST
            obj.save()
            messages.success(request, "Page updated!")
        return redirect("admin_pages")
    return render(request, "admin_panel/pages.html", {
        "lang": lang, "items": items, "page_title": "CMS Pages"
    })


def message_detail_view(request, pk):
    lang = get_lang(request)
    obj = get_object_or_404(ContactMessage, pk=pk)
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "mark_replied":
            obj.is_replied = True
            obj.is_read = True
            obj.save()
            messages.success(request, "Message marked as replied!")
        elif action == "mark_read":
            obj.is_read = True
            obj.save()
            messages.success(request, "Message marked as read!")
        elif action == "delete":
            obj.delete()
            messages.success(request, "Message deleted!")
            return redirect("admin_messages")
        return redirect("admin_message_detail", pk=pk)
    return render(request, "admin_panel/message_detail.html", {
        "lang": lang, "obj": obj, "page_title": "Message Detail"
    })
