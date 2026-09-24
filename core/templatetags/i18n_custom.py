"""Language helpers for the AM Business templates.

The site ships three languages — English (``en``), Persian (``fa``) and
Arabic (``ar``).  Persian and Arabic are both right-to-left.

The main entry point is the ``{% tr %}`` tag::

    {% tr "Services" "خدمات" "الخدمات" %}

It renders the string that matches the active language and falls back to
English when a translation is missing.  Model values are resolved through
``pick_lang`` so an empty Arabic/Persian field also falls back to English.
"""
from django import template

from core.models import (
    DEFAULT_LANGUAGE,
    RTL_LANGUAGES,
    SUPPORTED_LANGUAGES,
    pick_lang,
)

register = template.Library()


# ──────────────────────── Language registry ────────────────────────
LANGUAGE_META = {
    "en": {"name": "English", "native": "English", "flag": "🇬🇧", "short": "EN", "rtl": False},
    "fa": {"name": "Persian", "native": "فارسی", "flag": "🇮🇷", "short": "FA", "rtl": True},
    "ar": {"name": "Arabic", "native": "العربية", "flag": "🇸🇦", "short": "AR", "rtl": True},
}

LANGUAGE_ORDER = ("en", "fa", "ar")


def normalize_lang(lang):
    """Normalise an arbitrary language code (``en-us`` → ``en``)."""
    lang = (lang or DEFAULT_LANGUAGE).split("-")[0].lower()
    return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


@register.simple_tag(takes_context=True)
def tr(context, en="", fa="", ar=""):
    """Return the string for the active language.

    ``{% tr "English" "فارسی" "العربية" %}`` — any argument may be omitted,
    in which case English is used as the fallback.
    """
    lang = normalize_lang(context.get("lang"))
    if lang == "fa" and fa:
        return fa
    if lang == "ar" and ar:
        return ar
    return en


@register.simple_tag(takes_context=True)
def current_lang(context):
    """The active language code."""
    return normalize_lang(context.get("lang"))


@register.simple_tag(takes_context=True)
def is_rtl(context):
    """True when the active language is right-to-left (Persian or Arabic)."""
    return normalize_lang(context.get("lang")) in RTL_LANGUAGES


@register.simple_tag(takes_context=True)
def text_dir(context):
    """``rtl`` or ``ltr`` for the active language."""
    return "rtl" if normalize_lang(context.get("lang")) in RTL_LANGUAGES else "ltr"


@register.simple_tag(takes_context=True)
def lang_name(context):
    """Native name of the active language (used by the switcher button)."""
    return LANGUAGE_META[normalize_lang(context.get("lang"))]["native"]


@register.simple_tag
def languages():
    """The ordered list of selectable languages, for language switchers."""
    return [
        {"code": code, **LANGUAGE_META[code]}
        for code in LANGUAGE_ORDER
    ]


@register.filter
def lang_field(obj, field_and_lang):
    """Usage: ``{{ object|lang_field:"title:fa" }}``

    Resolves ``obj.get_title(lang)`` when available, otherwise falls back to
    the ``<field>_<lang>`` attribute and finally to the English field.
    """
    if obj is None:
        return ""
    parts = str(field_and_lang).split(":")
    if len(parts) != 2:
        return ""
    field_name, lang = parts
    lang = normalize_lang(lang)

    getter = getattr(obj, f"get_{field_name}", None)
    if callable(getter):
        try:
            return getter(lang)
        except Exception:
            pass
    return pick_lang(obj, field_name, lang)


@register.simple_tag(takes_context=True)
def trans_field(context, obj, field_prefix):
    """Usage: ``{% trans_field countdown "title" %}``

    Picks ``<field_prefix>_<lang>`` from ``obj`` using the context language,
    falling back to English when the translation is empty.
    """
    return pick_lang(obj, field_prefix, context.get("lang"))


def _make_getter(field, name):
    """Build and register a ``simple_tag`` named ``name`` that reads
    ``<field>_<lang>`` from any object, preferring the model's getter."""

    @register.simple_tag(takes_context=True, name=name)
    def _tag(context, obj):
        lang = context.get("lang")
        method = getattr(obj, f"get_{field}", None)
        if callable(method):
            try:
                value = method(lang)
                if value:
                    return value
            except Exception:
                pass
        return pick_lang(obj, field, lang)

    return _tag


# Field getters used across the frontend templates. The tag name is always
# passed explicitly — a nested function would otherwise register as `_tag`
# for every one of them.
get_heading = _make_getter("heading", "get_heading")
get_subheading = _make_getter("subheading", "get_subheading")
get_title = _make_getter("title", "get_title")
get_description = _make_getter("description", "get_description")
get_content = _make_getter("content", "get_content")
get_name = _make_getter("name", "get_name")
get_button_text = _make_getter("button_text", "get_button_text")
get_position = _make_getter("position", "get_position")
get_bio = _make_getter("bio", "get_bio")
get_quote = _make_getter("quote", "get_quote")
get_role = _make_getter("author_role", "get_role")
get_label = _make_getter("label", "get_label")
get_ended_message = _make_getter("ended_message", "get_ended_message")
get_image_alt = _make_getter("image_alt", "get_image_alt")
get_why_title = _make_getter("why_choose_us_title", "get_why_title")
get_why_content = _make_getter("why_choose_us_content", "get_why_content")
get_who_we_are = _make_getter("who_we_are", "get_who_we_are")
get_we_are_expert = _make_getter("we_are_expert", "get_we_are_expert")
get_meta_title = _make_getter("meta_title", "get_meta_title")
get_meta_description = _make_getter("meta_description", "get_meta_description")


@register.simple_tag(takes_context=True)
def sec_text(context, style, prefix, en="", fa="", ar=""):
    """Heading text of an editable section.

    Usage::

        {% sec_text sections.pricing "title" "Pricing" "قیمت‌گذاری" "الأسعار" %}

    The value stored on the :class:`~core.models.SectionStyle` row wins; when
    that field is empty (or the section has no row yet) the built-in default
    for the active language is used instead.
    """
    if style:
        value = pick_lang(style, prefix, context.get("lang"))
        if value:
            return value

    lang = normalize_lang(context.get("lang"))
    if lang == "fa" and fa:
        return fa
    if lang == "ar" and ar:
        return ar
    return en


@register.simple_tag(takes_context=True)
def sec_bg_style(context, style):
    """Inline CSS custom properties for a section wrapper (may be empty)."""
    if not style:
        return ""
    return style.style_attribute()


@register.simple_tag(takes_context=True)
def sec_has(context, style):
    """True when the section has any heading configured (for fallback logic)."""
    if not style:
        return False
    for prefix in ("title", "subheading", "subtitle"):
        if pick_lang(style, prefix, context.get("lang")):
            return True
    return False


@register.simple_tag(takes_context=True)
def get_cta_text(context, obj):
    """CTA text for the active language (hero, countdown, about, …)."""
    lang = context.get("lang")
    method = getattr(obj, "get_cta_text", None)
    if callable(method):
        try:
            value = method(lang)
            if value:
                return value
        except Exception:
            pass
    return pick_lang(obj, "cta_text", lang)


@register.simple_tag(takes_context=True)
def get_nav_title(context, obj):
    """Navigation item title for the active language."""
    lang = context.get("lang")
    method = getattr(obj, "get_title", None)
    if callable(method):
        try:
            value = method(lang)
            if value:
                return value
        except Exception:
            pass
    return pick_lang(obj, "title", lang)


@register.simple_tag(takes_context=True)
def site_name(context):
    """Site name for the active language."""
    lang = context.get("lang")
    site = context.get("site_settings")
    if site:
        return pick_lang(site, "site_name", lang) or "AM Business"
    return "AM Business"


@register.simple_tag(takes_context=True)
def site_field(context, field):
    """Read a translated :class:`SiteSettings` field for the active language."""
    site = context.get("site_settings")
    return pick_lang(site, field, context.get("lang"))


# Localised headings for the admin pages. The views keep passing the English
# title (the sidebar uses it to highlight the active item), and templates turn
# it into a label with this tag.
ADMIN_PAGE_TITLES = {
    "Dashboard": ("Dashboard", "داشبورد", "لوحة المعلومات"),
    "Site Settings": ("Site Settings", "تنظیمات سایت", "إعدادات الموقع"),
    "Social Links": ("Social Links", "شبکه‌های اجتماعی", "روابط التواصل"),
    "Navigation": ("Navigation", "منوی ناوبری", "قائمة التنقل"),
    "Hero Sections": ("Hero Sections", "بنرهای صفحه", "بانرات الصفحات"),
    "Services": ("Services", "خدمات", "الخدمات"),
    "About Section": ("About Section", "بخش درباره ما", "قسم من نحن"),
    "Stat Counters": ("Stat Counters", "شمارنده‌ها", "العدادات"),
    "Features": ("Features", "ویژگی‌ها", "الميزات"),
    "Pricing Plans": ("Pricing Plans", "طرح‌های قیمت‌گذاری", "الخطط السعرية"),
    "Testimonials": ("Testimonials", "نظرات مشتریان", "شهادات العملاء"),
    "Team Members": ("Team Members", "اعضای تیم", "أعضاء الفريق"),
    "Event Countdown": ("Event Countdown", "شمارش معکوس رویداد", "العد التنازلي للحدث"),
    "Home Sections": ("Home Sections", "بخش‌های صفحه اصلی", "أقسام الصفحة الرئيسية"),
    "Sections & Backgrounds": ("Sections & Backgrounds", "بخش‌ها و پس‌زمینه‌ها", "الأقسام والخلفيات"),
    "Contact Messages": ("Contact Messages", "پیام‌های تماس", "رسائل التواصل"),
    "Message Detail": ("Message Detail", "جزئیات پیام", "تفاصيل الرسالة"),
    "Newsletter Subscribers": ("Newsletter Subscribers", "مشترکین خبرنامه", "مشتركو النشرة البريدية"),
    "CMS Pages": ("CMS Pages", "صفحات CMS", "صفحات الموقع"),
}


@register.simple_tag(takes_context=True)
def page_heading(context, title):
    """Localise an admin page title (falls back to the English string)."""
    labels = ADMIN_PAGE_TITLES.get(title)
    if not labels:
        return title
    return {
        "en": labels[0],
        "fa": labels[1],
        "ar": labels[2] or labels[0],
    }[normalize_lang(context.get("lang"))]
