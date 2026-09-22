from .models import SiteSettings, RTL_LANGUAGES, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

#: Selectable languages: code, native label, flag emoji, right-to-left flag.
LANGUAGE_CHOICES = [
    {"code": "en", "label": "English", "native": "English", "flag": "🇬🇧", "short": "EN", "rtl": False},
    {"code": "fa", "label": "Persian", "native": "فارسی", "flag": "🇮🇷", "short": "FA", "rtl": True},
    {"code": "ar", "label": "Arabic", "native": "العربية", "flag": "🇸🇦", "short": "AR", "rtl": True},
]


def normalize_lang(value):
    """Return a supported language code, defaulting to English."""
    lang = (value or DEFAULT_LANGUAGE).split("-")[0].lower()
    return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def site_settings(request):
    """Add site settings, theme and language state to all templates."""
    try:
        settings = SiteSettings.objects.first()
    except Exception:
        settings = None

    theme = request.COOKIES.get("theme", "light")
    language = normalize_lang(request.COOKIES.get("django_language", DEFAULT_LANGUAGE))
    rtl = language in RTL_LANGUAGES

    return {
        "site_settings": settings,
        "theme": theme,
        "lang": language,
        # Text direction for <html dir="…"> and RTL stylesheets
        "is_rtl": rtl,
        "text_direction": "rtl" if rtl else "ltr",
        "languages": LANGUAGE_CHOICES,
        "current_theme": theme,
        "current_language": language,
    }
