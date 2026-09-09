from django import template
from django.utils.translation import get_language
import jdatetime

register = template.Library()


# Django date format → Python strftime format mapping
DJANGO_TO_STRFTIME = {
    "Y": "%Y",   # 4-digit year
    "y": "%y",   # 2-digit year
    "m": "%m",   # month (01-12)
    "n": "%-m",  # month without leading zero (not portable, fallback)
    "d": "%d",   # day (01-31)
    "j": "%-j",  # day without leading zero (not portable, fallback)
    "H": "%H",   # hour 24-hr (00-23)
    "h": "%I",   # hour 12-hr (01-12)
    "i": "%M",   # minute (00-59)
    "s": "%S",   # second (00-59)
    "A": "%p",   # AM/PM
    "a": "%P",   # am/pm
    "D": "%a",   # short weekday name
    "l": "%A",   # full weekday name
    "w": "%w",   # weekday number
    "N": "%u",   # ISO weekday
    "M": "%b",   # short month name
    "F": "%B",   # full month name
    "t": "%d",   # days in month (not meaningful for display)
    "L": "",     # leap year flag
    "z": "%j",   # day of year
    "P": "%I:%M %p",  # 12-hr time with AM/PM
}


def django_to_strftime(fmt):
    """Convert Django date format string to Python strftime format string."""
    result = []
    i = 0
    while i < len(fmt):
        if fmt[i] == "%" and i + 1 < len(fmt) and fmt[i + 1] in "YymdHhilsaADECw":
            # Already a strftime format, pass through
            result.append(fmt[i:i+2])
            i += 2
        elif fmt[i] in DJANGO_TO_STRFTIME:
            result.append(DJANGO_TO_STRFTIME[fmt[i]])
            i += 1
        elif fmt[i] in ("\\",):
            # Django escape character, skip
            i += 1
            if i < len(fmt):
                result.append(fmt[i])
                i += 1
        else:
            # Literal character
            result.append(fmt[i])
            i += 1
    return "".join(result)


@register.filter
def jalali(value, fmt=None):
    """Convert a datetime to Jalali format if current language is Farsi, else keep Gregorian.

    Usage in templates:
        {% load jalali_filters %}
        {{ obj.created_at|jalali }}
        {{ obj.created_at|jalali:"Y/m/d" }}
        {{ obj.created_at|jalali:"Y/m/d H:i" }}

    Uses Django date format syntax (Y, m, d, H, i, etc.)
    """
    if value is None:
        return ""

    if fmt is None:
        fmt = "Y/m/d H:i"

    # LocaleMiddleware activates language from the django_language cookie
    lang = get_language() or "en"

    if lang.startswith("fa"):
        try:
            jalali_dt = jdatetime.datetime.fromgregorian(datetime=value)
            strftime_fmt = django_to_strftime(fmt)
            return jalali_dt.strftime(strftime_fmt)
        except Exception:
            return str(value)
    else:
        # For English, format using Django-compatible strftime
        try:
            strftime_fmt = django_to_strftime(fmt)
            return value.strftime(strftime_fmt)
        except Exception:
            return str(value)
