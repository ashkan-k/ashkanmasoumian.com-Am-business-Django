from .models import SiteSettings


def site_settings(request):
    """Add site settings to all templates"""
    try:
        settings = SiteSettings.objects.first()
    except Exception:
        settings = None

    theme = request.COOKIES.get("theme", "light")
    language = request.COOKIES.get("django_language", "en")

    return {
        "site_settings": settings,
        "theme": theme,
        "lang": language,
        "current_theme": theme,
        "current_language": language,
    }
