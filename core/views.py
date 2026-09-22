import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import translation
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from .models import (
    SiteSettings, SocialLink, Navigation, HeroSection, Service,
    AboutSection, StatCounter, Feature, PricingPlan, Testimonial,
    TeamMember, ContactMessage, NewsletterSubscriber, EventCountdown,
    Page, HomeSection, SUPPORTED_LANGUAGES, RTL_LANGUAGES
)


def get_lang(request):
    lang = request.COOKIES.get("django_language", "en").split("-")[0]
    return lang if lang in SUPPORTED_LANGUAGES else "en"


def safe_int(value, default=0):
    """Safely convert a value to int, returning default on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """Safely convert a value to float, returning default on failure."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def say(request, en, fa, ar=""):
    """Translate an admin flash message for the active language."""
    lang = get_lang(request)
    if lang == "fa":
        return fa or en
    if lang == "ar":
        return ar or en
    return en


def set_language_view(request, lang):
    """Set language preference via cookie (English / Persian / Arabic)."""
    supported = [code for code, _label in settings.LANGUAGES]
    if lang not in supported:
        lang = settings.LANGUAGE_CODE

    response = redirect(_safe_referer(request, "admin_dashboard"))
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        lang,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH or "/",
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )
    translation.activate(lang)
    return response


def _safe_referer(request, fallback_name):
    """Redirect back to the referring page, but only on this host."""
    referer = request.META.get("HTTP_REFERER", "")
    if referer:
        from urllib.parse import urlparse
        host = request.get_host()
        if urlparse(referer).netloc in ("", host):
            return referer
    return reverse(fallback_name)


def set_theme_view(request, theme):
    """Set theme preference via cookie"""
    if theme not in ("light", "dark"):
        theme = "light"
    response = redirect(request.META.get("HTTP_REFERER", "/admin-panel/"))
    response.set_cookie("theme", theme, max_age=365 * 24 * 60 * 60)
    return response


# ══════════════════════════════════════════════════════════════════
#  BULK ACTIONS
#  Every admin list page posts `action=bulk` together with `bulk_action`
#  and one or more `pks`.  The catalogue below defines which actions each
#  page offers and how they behave, and it also feeds the template so the
#  dropdown in the UI can never drift from what the backend accepts.
# ══════════════════════════════════════════════════════════════════

# key → (English, Persian, Arabic) labels
BULK_LABELS = {
    "activate": ("Activate", "فعال‌سازی", "تفعيل"),
    "deactivate": ("Deactivate", "غیرفعال‌سازی", "إلغاء التفعيل"),
    "delete": ("Delete permanently", "حذف دائمی", "حذف نهائي"),
    "duplicate": ("Duplicate", "کپی/تکثیر", "نسخ/تكرار"),
    "mark_read": ("Mark as read", "علامت‌گذاری به عنوان خوانده‌شده", "وضع علامة مقروء"),
    "mark_unread": ("Mark as unread", "علامت‌گذاری به عنوان خوانده‌نشده", "وضع علامة غير مقروء"),
    "mark_replied": ("Mark as replied", "علامت‌گذاری به عنوان پاسخ داده‌شده", "وضع علامة تم الرد"),
    "mark_unreplied": ("Mark as not replied", "حذف علامت پاسخ داده‌شده", "إزالة علامة الرد"),
    "mark_popular": ("Mark as popular", "علامت‌گذاری به عنوان محبوب", "وضع علامة مميز"),
    "unmark_popular": ("Remove popular mark", "حذف علامت محبوب", "إزالة علامة التمييز"),
    "show_in_menu": ("Show in navigation", "نمایش در منوی سایت", "إظهار في القائمة"),
    "hide_from_menu": ("Hide from navigation", "پنهان کردن از منو", "إخفاء من القائمة"),
    "export_csv": ("Export to CSV", "خروجی CSV", "تصدير إلى CSV"),
}

# key → styling / behaviour metadata for the dropdown
BULK_META = {
    "activate": {"icon": "ph-check-circle", "group": "status", "confirm": False},
    "deactivate": {"icon": "ph-prohibit", "group": "status", "confirm": False},
    "mark_read": {"icon": "ph-envelope-open", "group": "status", "confirm": False},
    "mark_unread": {"icon": "ph-envelope", "group": "status", "confirm": False},
    "mark_replied": {"icon": "ph-check", "group": "status", "confirm": False},
    "mark_unreplied": {"icon": "ph-arrow-counter-clockwise", "group": "status", "confirm": False},
    "mark_popular": {"icon": "ph-star", "group": "status", "confirm": False},
    "unmark_popular": {"icon": "ph-star-half", "group": "status", "confirm": False},
    "show_in_menu": {"icon": "ph-list-plus", "group": "status", "confirm": False},
    "hide_from_menu": {"icon": "ph-list", "group": "status", "confirm": False},
    "duplicate": {"icon": "ph-copy", "group": "content", "confirm": False},
    "export_csv": {"icon": "ph-download-simple", "group": "content", "confirm": False},
    "delete": {"icon": "ph-trash", "group": "danger", "confirm": True},
}

BULK_GROUP_LABELS = {
    "status": ("Change status", "تغییر وضعیت", "تغيير الحالة"),
    "content": ("Content tools", "ابزارهای محتوا", "أدوات المحتوى"),
    "danger": ("Danger zone", "عملیات خطرناک", "منطقة الخطر"),
}


def _bulk_set(**fields):
    """Build a handler that applies ``queryset.update(**fields)``."""
    def handler(queryset):
        return queryset.update(**fields)
    return handler


def _bulk_duplicate(queryset):
    """Copy each selected row, leaving unique fields to regenerate."""
    created = 0
    for obj in list(queryset):
        obj.pk = None
        obj._state.adding = True
        if hasattr(obj, "slug"):
            obj.slug = ""
        if hasattr(obj, "order"):
            obj.order = (obj.order or 0) + 1
        obj.save()
        created += 1
    return created


def _bulk_export(model_fields, filename, header_en):
    """Build a CSV-export handler for the given model fields."""
    def handler(queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write("\ufeff")  # BOM so Excel reads UTF-8 correctly
        writer = csv.writer(response)
        writer.writerow(header_en)
        for obj in queryset:
            row = []
            for field in model_fields:
                value = getattr(obj, field, "")
                row.append("" if value is None else str(value))
            writer.writerow(row)
        return response
    return handler


# key → handler(queryset) → row count, or a Response for downloads
BULK_HANDLERS = {
    "activate": _bulk_set(is_active=True),
    "deactivate": _bulk_set(is_active=False),
    "mark_read": _bulk_set(is_read=True),
    "mark_unread": _bulk_set(is_read=False),
    "mark_replied": _bulk_set(is_replied=True),
    "mark_unreplied": _bulk_set(is_replied=False),
    "mark_popular": _bulk_set(is_popular=True),
    "unmark_popular": _bulk_set(is_popular=False),
    "show_in_menu": _bulk_set(show_in_menu=True),
    "hide_from_menu": _bulk_set(show_in_menu=False),
    "duplicate": _bulk_duplicate,
    "export_csv": _bulk_export(
        ["name", "email", "subject", "message", "is_read", "is_replied", "created_at"],
        "contact-messages.csv",
        ["Name", "Email", "Subject", "Message", "Is Read", "Is Replied", "Created At"],
    ),
}


def _bulk_delete(queryset):
    count = queryset.count()
    queryset.delete()
    return count


# Page registry: which actions each admin list page exposes.
BULK_PAGES = {
    "social_links": {
        "model": SocialLink, "redirect": "admin_social_links", "noun": ("link", "لینک", "رابط"),
        "actions": ["activate", "deactivate", "duplicate", "delete"],
    },
    "navigation": {
        "model": Navigation, "redirect": "admin_navigation", "noun": ("item", "آیتم", "عنصر"),
        "actions": ["activate", "deactivate", "duplicate", "delete"],
    },
    "hero_sections": {
        "model": HeroSection, "redirect": "admin_hero_sections", "noun": ("hero section", "بنر", "بانر"),
        "actions": ["activate", "deactivate", "delete"],
    },
    "services": {
        "model": Service, "redirect": "admin_services", "noun": ("service", "خدمت", "خدمة"),
        "actions": ["activate", "deactivate", "duplicate", "delete"],
    },
    "stat_counters": {
        "model": StatCounter, "redirect": "admin_stat_counters", "noun": ("counter", "شمارنده", "عداد"),
        "actions": ["activate", "deactivate", "duplicate", "delete"],
    },
    "features": {
        "model": Feature, "redirect": "admin_features", "noun": ("feature", "ویژگی", "ميزة"),
        "actions": ["activate", "deactivate", "duplicate", "delete"],
    },
    "pricing": {
        "model": PricingPlan, "redirect": "admin_pricing", "noun": ("pricing plan", "طرح قیمت‌گذاری", "خطة سعرية"),
        "actions": ["activate", "deactivate", "mark_popular", "unmark_popular", "duplicate", "delete"],
    },
    "testimonials": {
        "model": Testimonial, "redirect": "admin_testimonials", "noun": ("testimonial", "نظر", "شهادة"),
        "actions": ["activate", "deactivate", "duplicate", "delete"],
    },
    "team": {
        "model": TeamMember, "redirect": "admin_team", "noun": ("team member", "عضو تیم", "عضو فريق"),
        "actions": ["activate", "deactivate", "duplicate", "delete"],
    },
    "home_sections": {
        "model": HomeSection, "redirect": "admin_home_sections", "noun": ("home section", "بخش", "قسم"),
        "actions": ["activate", "deactivate", "delete"],
    },
    "messages": {
        "model": ContactMessage, "redirect": "admin_messages", "noun": ("message", "پیام", "رسالة"),
        "actions": ["mark_read", "mark_unread", "mark_replied", "mark_unreplied", "export_csv", "delete"],
    },
    "newsletter": {
        "model": NewsletterSubscriber, "redirect": "admin_newsletter", "noun": ("subscriber", "مشترک", "مشترك"),
        "actions": ["activate", "deactivate", "delete"],
        "replace": {"export_csv": _bulk_export(
            ["name", "email", "is_active", "created_at"],
            "newsletter-subscribers.csv",
            ["Name", "Email", "Is Active", "Subscribed At"],
        )},
    },
    "pages": {
        "model": Page, "redirect": "admin_pages", "noun": ("page", "صفحه", "صفحة"),
        "actions": ["activate", "deactivate", "show_in_menu", "hide_from_menu", "duplicate", "delete"],
    },
}


def bulk_menu(request, page_key):
    """Build the dropdown model for a list page (labels for the active language)."""
    page = BULK_PAGES[page_key]
    lang = get_lang(request)
    entries = []
    for key in page["actions"]:
        labels = BULK_LABELS[key]
        meta = BULK_META[key]
        entries.append({
            "key": key,
            "label": labels[0] if lang == "en" else (labels[1] if lang == "fa" else (labels[2] or labels[0])),
            "icon": meta["icon"],
            "group": meta["group"],
            "confirm": meta["confirm"],
        })
    groups = []
    for group_key in ("status", "content", "danger"):
        items = [e for e in entries if e["group"] == group_key]
        if not items:
            continue
        glabels = BULK_GROUP_LABELS[group_key]
        groups.append({
            "key": group_key,
            "label": glabels[0] if lang == "en" else (glabels[1] if lang == "fa" else (glabels[2] or glabels[0])),
            "actions": items,
        })
    return {"groups": groups, "actions": entries, "page_key": page_key}


def run_bulk_action(request, page_key):
    """Dispatch an ``action=bulk`` POST for the given list page."""
    page = BULK_PAGES[page_key]
    model = page["model"]
    redirect_to = redirect(page["redirect"])
    bulk_action = request.POST.get("bulk_action", "")
    noun = page["noun"]

    pks = [safe_int(raw) for raw in request.POST.getlist("pks")]
    pks = [pk for pk in pks if pk]

    if not pks:
        messages.warning(request, say(
            request,
            "No rows were selected. Tick at least one checkbox first.",
            "هیچ ردیفی انتخاب نشده است. ابتدا حداقل یک چک‌باکس را علامت بزنید.",
            "لم يتم تحديد أي صف. حدّد مربع اختيار واحدًا على الأقل أولًا.",
        ))
        return redirect_to

    if bulk_action not in page["actions"]:
        messages.error(request, say(
            request,
            "Unknown bulk action.",
            "عملیات گروهی نامعتبر است.",
            "إجراء جماعي غير معروف.",
        ))
        return redirect_to

    queryset = model.objects.filter(pk__in=pks)
    total = queryset.count()
    if not total:
        messages.warning(request, say(
            request,
            "The selected rows no longer exist.",
            "ردیف‌های انتخاب‌شده دیگر وجود ندارند.",
            "الصفوف المحددة لم تعد موجودة.",
        ))
        return redirect_to

    if bulk_action == "delete":
        handler = _bulk_delete
    else:
        handler = page.get("replace", {}).get(bulk_action) or BULK_HANDLERS[bulk_action]

    result = handler(queryset)
    if isinstance(result, HttpResponse):
        return result

    labels = BULK_LABELS[bulk_action]
    action_label = labels[0] if get_lang(request) == "en" else (labels[1] if get_lang(request) == "fa" else labels[2])
    messages.success(request, say(
        request,
        f"{action_label} applied to {total} {noun[0]}{'' if total == 1 else 's'}.",
        f"«{action_label}» برای {total} {noun[1]} انجام شد.",
        f"تم تطبيق «{action_label}» على {total} {noun[2]}.",
    ))
    return redirect_to


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
        messages.error(request, say(
            request,
            "Invalid username or password",
            "نام کاربری یا رمز عبور نادرست است",
            "اسم المستخدم أو كلمة المرور غير صحيحة",
        ))
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
        obj.site_name_ar = request.POST.get("site_name_ar", obj.site_name_ar)
        obj.phone = request.POST.get("phone", obj.phone)
        obj.email = request.POST.get("email", obj.email)
        obj.address_en = request.POST.get("address_en", obj.address_en)
        obj.address_fa = request.POST.get("address_fa", obj.address_fa)
        obj.address_ar = request.POST.get("address_ar", obj.address_ar)
        obj.meta_description_en = request.POST.get("meta_description_en", obj.meta_description_en)
        obj.meta_description_fa = request.POST.get("meta_description_fa", obj.meta_description_fa)
        obj.meta_description_ar = request.POST.get("meta_description_ar", obj.meta_description_ar)
        obj.copyright_text_en = request.POST.get("copyright_text_en", obj.copyright_text_en)
        obj.copyright_text_fa = request.POST.get("copyright_text_fa", obj.copyright_text_fa)
        obj.copyright_text_ar = request.POST.get("copyright_text_ar", obj.copyright_text_ar)
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
        messages.success(request, say(
            request, "Settings saved successfully!", "تنظیمات با موفقیت ذخیره شد!", "تم حفظ الإعدادات بنجاح!"))
        return redirect("admin_site_settings")
    return render(request, "admin_panel/site_settings.html", {"lang": lang, "settings": obj, "page_title": "Site Settings"})


# ──────────────────────── SOCIAL LINKS ────────────────────────
@login_required(login_url="/accounts/login/")
def social_links_view(request):
    lang = get_lang(request)
    items = SocialLink.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "bulk":
            return run_bulk_action(request, "social_links")
        if action == "add":
            sl = SocialLink(
                platform=request.POST.get("platform", "facebook"),
                url=request.POST.get("url", "#"),
                icon_class=request.POST.get("icon_class", ""),
                is_active="is_active" in request.POST,
                order=safe_int(request.POST.get("order", 0)),
            )
            if request.FILES.get("icon_image"):
                sl.icon_image = request.FILES["icon_image"]
            sl.save()
            messages.success(request, say(request, "Social link added!", "لینک شبکه اجتماعی اضافه شد!", "تمت إضافة الرابط!"))
        elif action == "delete":
            pk = request.POST.get("pk")
            SocialLink.objects.filter(pk=pk).delete()
            messages.success(request, say(request, "Social link deleted!", "لینک شبکه اجتماعی حذف شد!", "تم حذف الرابط!"))
        elif action == "edit":
            pk = request.POST.get("pk")
            obj = get_object_or_404(SocialLink, pk=pk)
            obj.platform = request.POST.get("platform", obj.platform)
            obj.url = request.POST.get("url", obj.url)
            obj.icon_class = request.POST.get("icon_class", obj.icon_class)
            obj.is_active = "is_active" in request.POST
            obj.order = safe_int(request.POST.get("order", 0))
            if request.FILES.get("icon_image"):
                obj.icon_image = request.FILES["icon_image"]
            obj.save()
            messages.success(request, say(request, "Social link updated!", "لینک شبکه اجتماعی به‌روزرسانی شد!", "تم تحديث الرابط!"))
        return redirect("admin_social_links")
    return render(request, "admin_panel/social_links.html", {
        "lang": lang, "items": items, "page_title": "Social Links",
        "bulk": bulk_menu(request, "social_links"),
    })


# ──────────────────────── NAVIGATION ────────────────────────
@login_required(login_url="/accounts/login/")
def navigation_view(request):
    lang = get_lang(request)
    items = Navigation.objects.filter(parent=None)
    all_items = Navigation.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "bulk":
            return run_bulk_action(request, "navigation")
        if action == "add":
            parent_id = request.POST.get("parent")
            parent = Navigation.objects.filter(pk=parent_id).first() if parent_id else None
            Navigation.objects.create(
                title_en=request.POST.get("title_en", ""),
                title_fa=request.POST.get("title_fa", ""),
                title_ar=request.POST.get("title_ar", ""),
                url=request.POST.get("url", "#"),
                is_active="is_active" in request.POST,
                order=safe_int(request.POST.get("order", 0)),
                parent=parent,
            )
            messages.success(request, say(request, "Navigation item added!", "آیتم منو اضافه شد!", "تمت إضافة عنصر القائمة!"))
        elif action == "delete":
            pk = request.POST.get("pk")
            Navigation.objects.filter(pk=pk).delete()
            messages.success(request, say(request, "Navigation item deleted!", "آیتم منو حذف شد!", "تم حذف عنصر القائمة!"))
        elif action == "edit":
            pk = request.POST.get("pk")
            obj = get_object_or_404(Navigation, pk=pk)
            obj.title_en = request.POST.get("title_en", obj.title_en)
            obj.title_fa = request.POST.get("title_fa", obj.title_fa)
            obj.title_ar = request.POST.get("title_ar", obj.title_ar)
            obj.url = request.POST.get("url", obj.url)
            obj.is_active = "is_active" in request.POST
            obj.order = safe_int(request.POST.get("order", 0))
            parent_id = request.POST.get("parent")
            obj.parent = Navigation.objects.filter(pk=parent_id).first() if parent_id else None
            obj.save()
            messages.success(request, say(request, "Navigation item updated!", "آیتم منو به‌روزرسانی شد!", "تم تحديث عنصر القائمة!"))
        return redirect("admin_navigation")
    return render(request, "admin_panel/navigation.html", {
        "lang": lang, "items": items, "all_items": all_items, "page_title": "Navigation",
        "bulk": bulk_menu(request, "navigation"),
    })


# ──────────────────────── HERO SECTIONS ────────────────────────
@login_required(login_url="/accounts/login/")
def hero_sections_view(request):
    lang = get_lang(request)
    items = HeroSection.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "bulk":
            return run_bulk_action(request, "hero_sections")
        if action == "edit":
            pk = request.POST.get("pk")
            obj = get_object_or_404(HeroSection, pk=pk)
            obj.heading_en = request.POST.get("heading_en", obj.heading_en)
            obj.heading_fa = request.POST.get("heading_fa", obj.heading_fa)
            obj.heading_ar = request.POST.get("heading_ar", obj.heading_ar)
            obj.subheading_en = request.POST.get("subheading_en", obj.subheading_en)
            obj.subheading_fa = request.POST.get("subheading_fa", obj.subheading_fa)
            obj.subheading_ar = request.POST.get("subheading_ar", obj.subheading_ar)
            obj.cta_text_en = request.POST.get("cta_text_en", obj.cta_text_en)
            obj.cta_text_fa = request.POST.get("cta_text_fa", obj.cta_text_fa)
            obj.cta_text_ar = request.POST.get("cta_text_ar", obj.cta_text_ar)
            obj.cta_url = request.POST.get("cta_url", obj.cta_url)
            obj.is_active = "is_active" in request.POST
            if request.FILES.get("background_image"):
                obj.background_image = request.FILES["background_image"]
            obj.save()
            messages.success(request, say(request, "Hero section updated!", "بنر به‌روزرسانی شد!", "تم تحديث البانر!"))
        elif action == "add":
            hero = HeroSection(
                page=request.POST.get("page", "home"),
                heading_en=request.POST.get("heading_en", ""),
                heading_fa=request.POST.get("heading_fa", ""),
                heading_ar=request.POST.get("heading_ar", ""),
                subheading_en=request.POST.get("subheading_en", ""),
                subheading_fa=request.POST.get("subheading_fa", ""),
                subheading_ar=request.POST.get("subheading_ar", ""),
                cta_text_en=request.POST.get("cta_text_en", ""),
                cta_text_fa=request.POST.get("cta_text_fa", ""),
                cta_text_ar=request.POST.get("cta_text_ar", ""),
                cta_url=request.POST.get("cta_url", "#"),
                is_active="is_active" in request.POST,
            )
            if request.FILES.get("background_image"):
                hero.background_image = request.FILES["background_image"]
            hero.save()
            messages.success(request, say(request, "Hero section added!", "بنر اضافه شد!", "تمت إضافة البانر!"))
        elif action == "delete":
            pk = request.POST.get("pk")
            HeroSection.objects.filter(pk=pk).delete()
            messages.success(request, say(request, "Hero section deleted!", "بنر حذف شد!", "تم حذف البانر!"))
        return redirect("admin_hero_sections")
    return render(request, "admin_panel/hero_sections.html", {
        "lang": lang, "items": items, "page_title": "Hero Sections",
        "bulk": bulk_menu(request, "hero_sections"),
    })


# ──────────────────────── SERVICES ────────────────────────
@login_required(login_url="/accounts/login/")
def services_view(request):
    lang = get_lang(request)
    items = Service.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "bulk":
            return run_bulk_action(request, "services")
        if action == "add":
            svc = Service(
                title_en=request.POST.get("title_en", ""),
                title_fa=request.POST.get("title_fa", ""),
                title_ar=request.POST.get("title_ar", ""),
                description_en=request.POST.get("description_en", ""),
                description_fa=request.POST.get("description_fa", ""),
                description_ar=request.POST.get("description_ar", ""),
                icon=request.POST.get("icon", "gear"),
                custom_svg=request.POST.get("custom_svg", ""),
                is_active="is_active" in request.POST,
                order=safe_int(request.POST.get("order", 0)),
            )
            if request.FILES.get("image"):
                svc.image = request.FILES["image"]
            if request.FILES.get("custom_icon"):
                svc.custom_icon = request.FILES["custom_icon"]
            svc.save()
            messages.success(request, say(request, "Service added!", "خدمت اضافه شد!", "تمت إضافة الخدمة!"))
        elif action == "delete":
            pk = request.POST.get("pk")
            Service.objects.filter(pk=pk).delete()
            messages.success(request, say(request, "Service deleted!", "خدمت حذف شد!", "تم حذف الخدمة!"))
        elif action == "edit":
            pk = request.POST.get("pk")
            obj = get_object_or_404(Service, pk=pk)
            obj.title_en = request.POST.get("title_en", obj.title_en)
            obj.title_fa = request.POST.get("title_fa", obj.title_fa)
            obj.title_ar = request.POST.get("title_ar", obj.title_ar)
            obj.description_en = request.POST.get("description_en", obj.description_en)
            obj.description_fa = request.POST.get("description_fa", obj.description_fa)
            obj.description_ar = request.POST.get("description_ar", obj.description_ar)
            obj.icon = request.POST.get("icon", obj.icon)
            obj.custom_svg = request.POST.get("custom_svg", obj.custom_svg)
            obj.is_active = "is_active" in request.POST
            obj.order = safe_int(request.POST.get("order", 0))
            if request.FILES.get("image"):
                obj.image = request.FILES["image"]
            if request.FILES.get("custom_icon"):
                obj.custom_icon = request.FILES["custom_icon"]
            obj.save()
            messages.success(request, say(request, "Service updated!", "خدمت به‌روزرسانی شد!", "تم تحديث الخدمة!"))
        return redirect("admin_services")
    return render(request, "admin_panel/services.html", {
        "lang": lang, "items": items, "page_title": "Services",
        "bulk": bulk_menu(request, "services"),
    })


# ──────────────────────── ABOUT ────────────────────────
@login_required(login_url="/accounts/login/")
def about_view(request):
    lang = get_lang(request)
    obj = AboutSection.objects.first()
    if not obj:
        obj = AboutSection.objects.create(
            title_en="About Us", title_fa="درباره ما", title_ar="من نحن",
            content_en="About content", content_fa="محتوای درباره ما", content_ar="محتوى من نحن"
        )
    if request.method == "POST":
        obj.title_en = request.POST.get("title_en", obj.title_en)
        obj.title_fa = request.POST.get("title_fa", obj.title_fa)
        obj.title_ar = request.POST.get("title_ar", obj.title_ar)
        obj.content_en = request.POST.get("content_en", obj.content_en)
        obj.content_fa = request.POST.get("content_fa", obj.content_fa)
        obj.content_ar = request.POST.get("content_ar", obj.content_ar)
        obj.who_we_are_en = request.POST.get("who_we_are_en", obj.who_we_are_en)
        obj.who_we_are_fa = request.POST.get("who_we_are_fa", obj.who_we_are_fa)
        obj.who_we_are_ar = request.POST.get("who_we_are_ar", obj.who_we_are_ar)
        obj.we_are_expert_en = request.POST.get("we_are_expert_en", obj.we_are_expert_en)
        obj.we_are_expert_fa = request.POST.get("we_are_expert_fa", obj.we_are_expert_fa)
        obj.we_are_expert_ar = request.POST.get("we_are_expert_ar", obj.we_are_expert_ar)
        obj.why_choose_us_title_en = request.POST.get("why_choose_us_title_en", obj.why_choose_us_title_en)
        obj.why_choose_us_title_fa = request.POST.get("why_choose_us_title_fa", obj.why_choose_us_title_fa)
        obj.why_choose_us_title_ar = request.POST.get("why_choose_us_title_ar", obj.why_choose_us_title_ar)
        obj.why_choose_us_content_en = request.POST.get("why_choose_us_content_en", obj.why_choose_us_content_en)
        obj.why_choose_us_content_fa = request.POST.get("why_choose_us_content_fa", obj.why_choose_us_content_fa)
        obj.why_choose_us_content_ar = request.POST.get("why_choose_us_content_ar", obj.why_choose_us_content_ar)
        obj.cta_text_en = request.POST.get("cta_text_en", obj.cta_text_en)
        obj.cta_text_fa = request.POST.get("cta_text_fa", obj.cta_text_fa)
        obj.cta_text_ar = request.POST.get("cta_text_ar", obj.cta_text_ar)
        obj.cta_url = request.POST.get("cta_url", obj.cta_url)
        obj.is_active = "is_active" in request.POST
        if request.FILES.get("image"):
            obj.image = request.FILES["image"]
        if request.FILES.get("why_choose_us_image"):
            obj.why_choose_us_image = request.FILES["why_choose_us_image"]
        obj.save()
        messages.success(request, say(request, "About section saved!", "بخش درباره ما ذخیره شد!", "تم حفظ قسم «من نحن»!"))
        return redirect("admin_about")
    return render(request, "admin_panel/about.html", {"lang": lang, "obj": obj, "page_title": "About Section"})


# ──────────────────────── STAT COUNTERS ────────────────────────
@login_required(login_url="/accounts/login/")
def stat_counters_view(request):
    lang = get_lang(request)
    items = StatCounter.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "bulk":
            return run_bulk_action(request, "stat_counters")
        if action == "add":
            StatCounter.objects.create(
                label_en=request.POST.get("label_en", ""),
                label_fa=request.POST.get("label_fa", ""),
                label_ar=request.POST.get("label_ar", ""),
                value=safe_int(request.POST.get("value", 0)),
                icon_class=request.POST.get("icon_class", ""),
                is_active="is_active" in request.POST,
                order=safe_int(request.POST.get("order", 0)),
            )
            messages.success(request, say(request, "Counter added!", "شمارنده اضافه شد!", "تمت إضافة العداد!"))
        elif action == "delete":
            StatCounter.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, say(request, "Counter deleted!", "شمارنده حذف شد!", "تم حذف العداد!"))
        elif action == "edit":
            obj = get_object_or_404(StatCounter, pk=request.POST.get("pk"))
            obj.label_en = request.POST.get("label_en", obj.label_en)
            obj.label_fa = request.POST.get("label_fa", obj.label_fa)
            obj.label_ar = request.POST.get("label_ar", obj.label_ar)
            obj.value = safe_int(request.POST.get("value", obj.value))
            obj.icon_class = request.POST.get("icon_class", obj.icon_class)
            obj.is_active = "is_active" in request.POST
            obj.order = safe_int(request.POST.get("order", 0))
            obj.save()
            messages.success(request, say(request, "Counter updated!", "شمارنده به‌روزرسانی شد!", "تم تحديث العداد!"))
        return redirect("admin_stat_counters")
    return render(request, "admin_panel/stat_counters.html", {
        "lang": lang, "items": items, "page_title": "Stat Counters",
        "bulk": bulk_menu(request, "stat_counters"),
    })


# ──────────────────────── FEATURES ────────────────────────
@login_required(login_url="/accounts/login/")
def features_view(request):
    lang = get_lang(request)
    items = Feature.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "bulk":
            return run_bulk_action(request, "features")
        if action == "add":
            Feature.objects.create(
                title_en=request.POST.get("title_en", ""),
                title_fa=request.POST.get("title_fa", ""),
                title_ar=request.POST.get("title_ar", ""),
                description_en=request.POST.get("description_en", ""),
                description_fa=request.POST.get("description_fa", ""),
                description_ar=request.POST.get("description_ar", ""),
                icon=request.POST.get("icon", ""),
                is_active="is_active" in request.POST,
                order=safe_int(request.POST.get("order", 0)),
            )
            messages.success(request, say(request, "Feature added!", "ویژگی اضافه شد!", "تمت إضافة الميزة!"))
        elif action == "delete":
            Feature.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, say(request, "Feature deleted!", "ویژگی حذف شد!", "تم حذف الميزة!"))
        elif action == "edit":
            obj = get_object_or_404(Feature, pk=request.POST.get("pk"))
            obj.title_en = request.POST.get("title_en", obj.title_en)
            obj.title_fa = request.POST.get("title_fa", obj.title_fa)
            obj.title_ar = request.POST.get("title_ar", obj.title_ar)
            obj.description_en = request.POST.get("description_en", obj.description_en)
            obj.description_fa = request.POST.get("description_fa", obj.description_fa)
            obj.description_ar = request.POST.get("description_ar", obj.description_ar)
            obj.icon = request.POST.get("icon", obj.icon)
            obj.is_active = "is_active" in request.POST
            obj.order = safe_int(request.POST.get("order", 0))
            obj.save()
            messages.success(request, say(request, "Feature updated!", "ویژگی به‌روزرسانی شد!", "تم تحديث الميزة!"))
        return redirect("admin_features")
    return render(request, "admin_panel/features.html", {
        "lang": lang, "items": items, "page_title": "Features",
        "bulk": bulk_menu(request, "features"),
    })


# ──────────────────────── PRICING ────────────────────────
@login_required(login_url="/accounts/login/")
def pricing_view(request):
    lang = get_lang(request)
    items = PricingPlan.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "bulk":
            return run_bulk_action(request, "pricing")
        if action == "add":
            PricingPlan.objects.create(
                name_en=request.POST.get("name_en", ""),
                name_fa=request.POST.get("name_fa", ""),
                name_ar=request.POST.get("name_ar", ""),
                description_en=request.POST.get("description_en", ""),
                description_fa=request.POST.get("description_fa", ""),
                description_ar=request.POST.get("description_ar", ""),
                price=safe_float(request.POST.get("price", 0)),
                currency=request.POST.get("currency", "$"),
                cents=request.POST.get("cents", ".99"),
                is_popular="is_popular" in request.POST,
                button_text_en=request.POST.get("button_text_en", "Buy"),
                button_text_fa=request.POST.get("button_text_fa", "خرید"),
                button_text_ar=request.POST.get("button_text_ar", "اشترِ"),
                button_url=request.POST.get("button_url", "#"),
                is_active="is_active" in request.POST,
                order=safe_int(request.POST.get("order", 0)),
            )
            messages.success(request, say(request, "Pricing plan added!", "طرح قیمت‌گذاری اضافه شد!", "تمت إضافة الخطة!"))
        elif action == "delete":
            PricingPlan.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, say(request, "Pricing plan deleted!", "طرح قیمت‌گذاری حذف شد!", "تم حذف الخطة!"))
        elif action == "edit":
            obj = get_object_or_404(PricingPlan, pk=request.POST.get("pk"))
            obj.name_en = request.POST.get("name_en", obj.name_en)
            obj.name_fa = request.POST.get("name_fa", obj.name_fa)
            obj.name_ar = request.POST.get("name_ar", obj.name_ar)
            obj.description_en = request.POST.get("description_en", obj.description_en)
            obj.description_fa = request.POST.get("description_fa", obj.description_fa)
            obj.description_ar = request.POST.get("description_ar", obj.description_ar)
            obj.price = safe_float(request.POST.get("price", obj.price))
            obj.currency = request.POST.get("currency", obj.currency)
            obj.cents = request.POST.get("cents", obj.cents)
            obj.is_popular = "is_popular" in request.POST
            obj.button_text_en = request.POST.get("button_text_en", obj.button_text_en)
            obj.button_text_fa = request.POST.get("button_text_fa", obj.button_text_fa)
            obj.button_text_ar = request.POST.get("button_text_ar", obj.button_text_ar)
            obj.button_url = request.POST.get("button_url", obj.button_url)
            obj.is_active = "is_active" in request.POST
            obj.order = safe_int(request.POST.get("order", 0))
            obj.save()
            messages.success(request, say(request, "Pricing plan updated!", "طرح قیمت‌گذاری به‌روزرسانی شد!", "تم تحديث الخطة!"))
        return redirect("admin_pricing")
    return render(request, "admin_panel/pricing.html", {
        "lang": lang, "items": items, "page_title": "Pricing Plans",
        "bulk": bulk_menu(request, "pricing"),
    })


# ──────────────────────── TESTIMONIALS ────────────────────────
@login_required(login_url="/accounts/login/")
def testimonials_view(request):
    lang = get_lang(request)
    items = Testimonial.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "bulk":
            return run_bulk_action(request, "testimonials")
        if action == "add":
            Testimonial.objects.create(
                quote_en=request.POST.get("quote_en", ""),
                quote_fa=request.POST.get("quote_fa", ""),
                quote_ar=request.POST.get("quote_ar", ""),
                author_name=request.POST.get("author_name", ""),
                author_role_en=request.POST.get("author_role_en", ""),
                author_role_fa=request.POST.get("author_role_fa", ""),
                author_role_ar=request.POST.get("author_role_ar", ""),
                is_active="is_active" in request.POST,
                order=safe_int(request.POST.get("order", 0)),
            )
            messages.success(request, say(request, "Testimonial added!", "نظر اضافه شد!", "تمت إضافة الشهادة!"))
        elif action == "delete":
            Testimonial.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, say(request, "Testimonial deleted!", "نظر حذف شد!", "تم حذف الشهادة!"))
        elif action == "edit":
            obj = get_object_or_404(Testimonial, pk=request.POST.get("pk"))
            obj.quote_en = request.POST.get("quote_en", obj.quote_en)
            obj.quote_fa = request.POST.get("quote_fa", obj.quote_fa)
            obj.quote_ar = request.POST.get("quote_ar", obj.quote_ar)
            obj.author_name = request.POST.get("author_name", obj.author_name)
            obj.author_role_en = request.POST.get("author_role_en", obj.author_role_en)
            obj.author_role_fa = request.POST.get("author_role_fa", obj.author_role_fa)
            obj.author_role_ar = request.POST.get("author_role_ar", obj.author_role_ar)
            obj.is_active = "is_active" in request.POST
            obj.order = safe_int(request.POST.get("order", 0))
            if request.FILES.get("author_image"):
                obj.author_image = request.FILES["author_image"]
            obj.save()
            messages.success(request, say(request, "Testimonial updated!", "نظر به‌روزرسانی شد!", "تم تحديث الشهادة!"))
        return redirect("admin_testimonials")
    return render(request, "admin_panel/testimonials.html", {
        "lang": lang, "items": items, "page_title": "Testimonials",
        "bulk": bulk_menu(request, "testimonials"),
    })


# ──────────────────────── TEAM ────────────────────────
@login_required(login_url="/accounts/login/")
def team_view(request):
    lang = get_lang(request)
    items = TeamMember.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "bulk":
            return run_bulk_action(request, "team")
        if action == "add":
            TeamMember.objects.create(
                name=request.POST.get("name", ""),
                position_en=request.POST.get("position_en", ""),
                position_fa=request.POST.get("position_fa", ""),
                position_ar=request.POST.get("position_ar", ""),
                bio_en=request.POST.get("bio_en", ""),
                bio_fa=request.POST.get("bio_fa", ""),
                bio_ar=request.POST.get("bio_ar", ""),
                is_active="is_active" in request.POST,
                order=safe_int(request.POST.get("order", 0)),
            )
            messages.success(request, say(request, "Team member added!", "عضو تیم اضافه شد!", "تمت إضافة عضو الفريق!"))
        elif action == "delete":
            TeamMember.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, say(request, "Team member deleted!", "عضو تیم حذف شد!", "تم حذف عضو الفريق!"))
        elif action == "edit":
            obj = get_object_or_404(TeamMember, pk=request.POST.get("pk"))
            obj.name = request.POST.get("name", obj.name)
            obj.position_en = request.POST.get("position_en", obj.position_en)
            obj.position_fa = request.POST.get("position_fa", obj.position_fa)
            obj.position_ar = request.POST.get("position_ar", obj.position_ar)
            obj.bio_en = request.POST.get("bio_en", obj.bio_en)
            obj.bio_fa = request.POST.get("bio_fa", obj.bio_fa)
            obj.bio_ar = request.POST.get("bio_ar", obj.bio_ar)
            obj.is_active = "is_active" in request.POST
            obj.order = safe_int(request.POST.get("order", 0))
            if request.FILES.get("image"):
                obj.image = request.FILES["image"]
            if request.FILES.get("photo_square"):
                obj.photo_square = request.FILES["photo_square"]
            obj.save()
            messages.success(request, say(request, "Team member updated!", "عضو تیم به‌روزرسانی شد!", "تم تحديث عضو الفريق!"))
        return redirect("admin_team")
    return render(request, "admin_panel/team.html", {
        "lang": lang, "items": items, "page_title": "Team Members",
        "bulk": bulk_menu(request, "team"),
    })


# ──────────────────────── EVENT COUNTDOWN ────────────────────────
@login_required(login_url="/accounts/login/")
def event_countdown_view(request):
    lang = get_lang(request)
    obj = EventCountdown.objects.first()
    if request.method == "POST":
        event_date_str = request.POST.get("event_date", "").strip()
        if not event_date_str:
            messages.error(request, say(request, "Event date is required.", "تاریخ رویداد الزامی است.", "تاريخ الحدث مطلوب."))
            return redirect("admin_event_countdown")
        from django.utils.dateparse import parse_datetime
        from django.utils.timezone import make_aware, is_aware
        parsed_date = parse_datetime(event_date_str)
        if parsed_date is None:
            messages.error(request, say(
                request,
                "Invalid event date format. Use YYYY-MM-DD HH:MM.",
                "قالب تاریخ رویداد نامعتبر است. از YYYY-MM-DD HH:MM استفاده کنید.",
                "صيغة تاريخ الحدث غير صحيحة. استخدم YYYY-MM-DD HH:MM.",
            ))
            return redirect("admin_event_countdown")
        if not is_aware(parsed_date):
            parsed_date = make_aware(parsed_date)
        if not obj:
            obj = EventCountdown.objects.create(
                event_date=parsed_date,
            )
        obj.title_en = request.POST.get("title_en", obj.title_en)
        obj.title_fa = request.POST.get("title_fa", obj.title_fa)
        obj.title_ar = request.POST.get("title_ar", obj.title_ar)
        obj.subheading_en = request.POST.get("subheading_en", obj.subheading_en)
        obj.subheading_fa = request.POST.get("subheading_fa", obj.subheading_fa)
        obj.subheading_ar = request.POST.get("subheading_ar", obj.subheading_ar)
        obj.event_date = parsed_date
        obj.ended_message_en = request.POST.get("ended_message_en", obj.ended_message_en)
        obj.ended_message_fa = request.POST.get("ended_message_fa", obj.ended_message_fa)
        obj.ended_message_ar = request.POST.get("ended_message_ar", obj.ended_message_ar)
        obj.cta_text_en = request.POST.get("cta_text_en", obj.cta_text_en)
        obj.cta_text_fa = request.POST.get("cta_text_fa", obj.cta_text_fa)
        obj.cta_text_ar = request.POST.get("cta_text_ar", obj.cta_text_ar)
        obj.cta_url = request.POST.get("cta_url", obj.cta_url)
        obj.is_active = "is_active" in request.POST
        obj.save()
        messages.success(request, say(request, "Event countdown saved!", "شمارش معکوس ذخیره شد!", "تم حفظ العد التنازلي!"))
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
        if action == "bulk":
            return run_bulk_action(request, "home_sections")
        if action == "edit":
            pk = request.POST.get("pk")
            obj = get_object_or_404(HomeSection, pk=pk)
            obj.title_en = request.POST.get("title_en", obj.title_en)
            obj.title_fa = request.POST.get("title_fa", obj.title_fa)
            obj.title_ar = request.POST.get("title_ar", obj.title_ar)
            obj.subheading_en = request.POST.get("subheading_en", obj.subheading_en)
            obj.subheading_fa = request.POST.get("subheading_fa", obj.subheading_fa)
            obj.subheading_ar = request.POST.get("subheading_ar", obj.subheading_ar)
            obj.content_en = request.POST.get("content_en", obj.content_en)
            obj.content_fa = request.POST.get("content_fa", obj.content_fa)
            obj.content_ar = request.POST.get("content_ar", obj.content_ar)
            obj.cta_text_en = request.POST.get("cta_text_en", obj.cta_text_en)
            obj.cta_text_fa = request.POST.get("cta_text_fa", obj.cta_text_fa)
            obj.cta_text_ar = request.POST.get("cta_text_ar", obj.cta_text_ar)
            obj.cta_url = request.POST.get("cta_url", obj.cta_url)
            obj.is_active = "is_active" in request.POST
            if request.FILES.get("image"):
                obj.image = request.FILES["image"]
            obj.save()
            messages.success(request, say(request, "Home section updated!", "بخش صفحه اصلی به‌روزرسانی شد!", "تم تحديث قسم الصفحة الرئيسية!"))
        return redirect("admin_home_sections")
    return render(request, "admin_panel/home_sections.html", {
        "lang": lang, "items": items, "page_title": "Home Sections",
        "bulk": bulk_menu(request, "home_sections"),
    })


# ──────────────────────── MESSAGES ────────────────────────
@login_required(login_url="/accounts/login/")
def messages_view(request):
    lang = get_lang(request)
    items = ContactMessage.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "bulk":
            return run_bulk_action(request, "messages")
        if action == "delete":
            ContactMessage.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, say(request, "Message deleted!", "پیام حذف شد!", "تم حذف الرسالة!"))
        elif action == "mark_read":
            obj = get_object_or_404(ContactMessage, pk=request.POST.get("pk"))
            obj.is_read = True
            obj.save()
            messages.success(request, say(request, "Message marked as read!", "پیام به عنوان خوانده‌شده علامت خورد!", "تم وضع علامة مقروء على الرسالة!"))
        elif action == "mark_replied":
            obj = get_object_or_404(ContactMessage, pk=request.POST.get("pk"))
            obj.is_replied = True
            obj.save()
            messages.success(request, say(request, "Message marked as replied!", "پیام به عنوان پاسخ داده‌شده علامت خورد!", "تم وضع علامة تم الرد على الرسالة!"))
        return redirect("admin_messages")
    return render(request, "admin_panel/messages.html", {
        "lang": lang, "items": items, "page_title": "Contact Messages",
        "bulk": bulk_menu(request, "messages"),
    })


# ──────────────────────── NEWSLETTER ────────────────────────
@login_required(login_url="/accounts/login/")
def newsletter_view(request):
    lang = get_lang(request)
    items = NewsletterSubscriber.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "bulk":
            return run_bulk_action(request, "newsletter")
        if action == "delete":
            NewsletterSubscriber.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, say(request, "Subscriber deleted!", "مشترک حذف شد!", "تم حذف المشترك!"))
        elif action == "toggle":
            obj = get_object_or_404(NewsletterSubscriber, pk=request.POST.get("pk"))
            obj.is_active = not obj.is_active
            obj.save()
            messages.success(request, say(request, "Subscriber status toggled!", "وضعیت مشترک تغییر کرد!", "تم تغيير حالة المشترك!"))
        return redirect("admin_newsletter")
    return render(request, "admin_panel/newsletter.html", {
        "lang": lang, "items": items, "page_title": "Newsletter Subscribers",
        "bulk": bulk_menu(request, "newsletter"),
    })


# ──────────────────────── PAGES (CMS) ────────────────────────
@login_required(login_url="/accounts/login/")
def pages_view(request):
    lang = get_lang(request)
    items = Page.objects.all()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "bulk":
            return run_bulk_action(request, "pages")
        if action == "add":
            from django.utils.text import slugify
            base_slug = slugify(request.POST.get("title_en", "page")) or "page"
            slug = base_slug
            counter = 1
            while Page.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            Page.objects.create(
                title_en=request.POST.get("title_en", ""),
                title_fa=request.POST.get("title_fa", ""),
                title_ar=request.POST.get("title_ar", ""),
                slug=slug,
                content_en=request.POST.get("content_en", ""),
                content_fa=request.POST.get("content_fa", ""),
                content_ar=request.POST.get("content_ar", ""),
                meta_title_en=request.POST.get("meta_title_en", ""),
                meta_title_fa=request.POST.get("meta_title_fa", ""),
                meta_title_ar=request.POST.get("meta_title_ar", ""),
                meta_description_en=request.POST.get("meta_description_en", ""),
                meta_description_fa=request.POST.get("meta_description_fa", ""),
                meta_description_ar=request.POST.get("meta_description_ar", ""),
                is_active="is_active" in request.POST,
                show_in_menu="show_in_menu" in request.POST,
            )
            messages.success(request, say(request, "Page added!", "صفحه اضافه شد!", "تمت إضافة الصفحة!"))
        elif action == "delete":
            Page.objects.filter(pk=request.POST.get("pk")).delete()
            messages.success(request, say(request, "Page deleted!", "صفحه حذف شد!", "تم حذف الصفحة!"))
        elif action == "edit":
            obj = get_object_or_404(Page, pk=request.POST.get("pk"))
            obj.title_en = request.POST.get("title_en", obj.title_en)
            obj.title_fa = request.POST.get("title_fa", obj.title_fa)
            obj.title_ar = request.POST.get("title_ar", obj.title_ar)
            obj.content_en = request.POST.get("content_en", obj.content_en)
            obj.content_fa = request.POST.get("content_fa", obj.content_fa)
            obj.content_ar = request.POST.get("content_ar", obj.content_ar)
            obj.meta_title_en = request.POST.get("meta_title_en", obj.meta_title_en)
            obj.meta_title_fa = request.POST.get("meta_title_fa", obj.meta_title_fa)
            obj.meta_title_ar = request.POST.get("meta_title_ar", obj.meta_title_ar)
            obj.meta_description_en = request.POST.get("meta_description_en", obj.meta_description_en)
            obj.meta_description_fa = request.POST.get("meta_description_fa", obj.meta_description_fa)
            obj.meta_description_ar = request.POST.get("meta_description_ar", obj.meta_description_ar)
            obj.is_active = "is_active" in request.POST
            obj.show_in_menu = "show_in_menu" in request.POST
            obj.save()
            messages.success(request, say(request, "Page updated!", "صفحه به‌روزرسانی شد!", "تم تحديث الصفحة!"))
        return redirect("admin_pages")
    return render(request, "admin_panel/pages.html", {
        "lang": lang, "items": items, "page_title": "CMS Pages",
        "bulk": bulk_menu(request, "pages"),
    })


@login_required(login_url="/accounts/login/")
def message_detail_view(request, pk):
    lang = get_lang(request)
    obj = get_object_or_404(ContactMessage, pk=pk)
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "mark_replied":
            obj.is_replied = True
            obj.is_read = True
            obj.save()
            messages.success(request, say(request, "Message marked as replied!", "پیام به عنوان پاسخ داده‌شده علامت خورد!", "تم وضع علامة تم الرد على الرسالة!"))
        elif action == "mark_read":
            obj.is_read = True
            obj.save()
            messages.success(request, say(request, "Message marked as read!", "پیام به عنوان خوانده‌شده علامت خورد!", "تم وضع علامة مقروء على الرسالة!"))
        elif action == "delete":
            obj.delete()
            messages.success(request, say(request, "Message deleted!", "پیام حذف شد!", "تم حذف الرسالة!"))
            return redirect("admin_messages")
        return redirect("admin_message_detail", pk=pk)
    return render(request, "admin_panel/message_detail.html", {
        "lang": lang, "obj": obj, "page_title": "Message Detail"
    })
