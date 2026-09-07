from django import template

register = template.Library()


@register.filter
def lang_field(obj, field_and_lang):
    """
    Usage: {{ object|lang_field:"title:lang" }}
    Resolves to obj.get_title(lang) or obj.title_en
    """
    parts = field_and_lang.split(":")
    if len(parts) != 2:
        return ""
    field_name, lang_var = parts
    lang = "en"  # default

    # Get lang from context if available
    if hasattr(obj, f"get_{field_name}"):
        method = getattr(obj, f"get_{field_name}")
        try:
            return method(lang)
        except Exception:
            pass

    # Fallback to _en or _fa
    fa_attr = f"{field_name}_{lang_var}"
    en_attr = f"{field_name}_en"

    if hasattr(obj, fa_attr):
        return getattr(obj, fa_attr, "")
    elif hasattr(obj, en_attr):
        return getattr(obj, en_attr, "")
    return ""


@register.simple_tag(takes_context=True)
def trans_field(context, obj, field_prefix):
    """
    Usage: {% trans_field obj "title" %}
    Uses the 'lang' variable from context to pick title_en or title_fa
    """
    lang = context.get("lang", "en")
    if lang == "fa":
        attr = f"{field_prefix}_fa"
    else:
        attr = f"{field_prefix}_en"
    return getattr(obj, attr, "")


@register.simple_tag(takes_context=True)
def get_heading(context, hero):
    """Get hero heading for current language"""
    lang = context.get("lang", "en")
    if lang == "fa":
        return hero.heading_fa
    return hero.heading_en


@register.simple_tag(takes_context=True)
def get_subheading(context, hero):
    """Get hero subheading for current language"""
    lang = context.get("lang", "en")
    if lang == "fa":
        return hero.subheading_fa
    return hero.subheading_en


@register.simple_tag(takes_context=True)
def get_cta_text(context, hero):
    """Get CTA text for current language"""
    lang = context.get("lang", "en")
    if lang == "fa":
        return hero.cta_text_fa
    return hero.cta_text_en


@register.simple_tag(takes_context=True)
def get_title(context, obj):
    """Get title for current language from any object with title_en/title_fa"""
    lang = context.get("lang", "en")
    if hasattr(obj, "get_title"):
        try: return obj.get_title(lang)
        except: pass
    if lang == "fa":
        return getattr(obj, "title_fa", getattr(obj, "title_en", ""))
    return getattr(obj, "title_en", "")


@register.simple_tag(takes_context=True)
def get_description(context, obj):
    """Get description for current language"""
    lang = context.get("lang", "en")
    if hasattr(obj, "get_description"):
        try: return obj.get_description(lang)
        except: pass
    if lang == "fa":
        return getattr(obj, "description_fa", getattr(obj, "description_en", ""))
    return getattr(obj, "description_en", "")


@register.simple_tag(takes_context=True)
def get_content(context, obj):
    """Get content for current language"""
    lang = context.get("lang", "en")
    if hasattr(obj, "get_content"):
        try: return obj.get_content(lang)
        except: pass
    if lang == "fa":
        return getattr(obj, "content_fa", getattr(obj, "content_en", ""))
    return getattr(obj, "content_en", "")


@register.simple_tag(takes_context=True)
def get_name(context, obj):
    """Get name for current language"""
    lang = context.get("lang", "en")
    if hasattr(obj, "get_name"):
        try: return obj.get_name(lang)
        except: pass
    if lang == "fa":
        return getattr(obj, "name_fa", getattr(obj, "name_en", ""))
    return getattr(obj, "name_en", "")


@register.simple_tag(takes_context=True)
def get_button_text(context, obj):
    """Get button text for current language"""
    lang = context.get("lang", "en")
    if hasattr(obj, "get_button_text"):
        try: return obj.get_button_text(lang)
        except: pass
    if lang == "fa":
        return getattr(obj, "button_text_fa", getattr(obj, "button_text_en", ""))
    return getattr(obj, "button_text_en", "")


@register.simple_tag(takes_context=True)
def get_position(context, obj):
    """Get position for current language"""
    lang = context.get("lang", "en")
    if hasattr(obj, "get_position"):
        try: return obj.get_position(lang)
        except: pass
    if lang == "fa":
        return getattr(obj, "position_fa", getattr(obj, "position_en", ""))
    return getattr(obj, "position_en", "")


@register.simple_tag(takes_context=True)
def get_bio(context, obj):
    """Get bio for current language"""
    lang = context.get("lang", "en")
    if hasattr(obj, "get_bio"):
        try: return obj.get_bio(lang)
        except: pass
    if lang == "fa":
        return getattr(obj, "bio_fa", getattr(obj, "bio_en", ""))
    return getattr(obj, "bio_en", "")


@register.simple_tag(takes_context=True)
def get_quote(context, obj):
    """Get quote for current language"""
    lang = context.get("lang", "en")
    if hasattr(obj, "get_quote"):
        try: return obj.get_quote(lang)
        except: pass
    if lang == "fa":
        return getattr(obj, "quote_fa", getattr(obj, "quote_en", ""))
    return getattr(obj, "quote_en", "")


@register.simple_tag(takes_context=True)
def get_role(context, obj):
    """Get role for current language"""
    lang = context.get("lang", "en")
    if hasattr(obj, "get_role"):
        try: return obj.get_role(lang)
        except: pass
    if lang == "fa":
        return getattr(obj, "author_role_fa", getattr(obj, "author_role_en", ""))
    return getattr(obj, "author_role_en", "")


@register.simple_tag(takes_context=True)
def get_label(context, obj):
    """Get label for current language"""
    lang = context.get("lang", "en")
    if lang == "fa":
        return getattr(obj, "label_fa", getattr(obj, "label_en", ""))
    return getattr(obj, "label_en", "")


@register.simple_tag(takes_context=True)
def get_ended_message(context, obj):
    """Get ended message for current language"""
    lang = context.get("lang", "en")
    if hasattr(obj, "get_ended_message"):
        try: return obj.get_ended_message(lang)
        except: pass
    if lang == "fa":
        return getattr(obj, "ended_message_fa", getattr(obj, "ended_message_en", ""))
    return getattr(obj, "ended_message_en", "")


@register.simple_tag(takes_context=True)
def get_why_title(context, obj):
    """Get why_choose_us title for current language"""
    lang = context.get("lang", "en")
    if lang == "fa":
        return getattr(obj, "why_choose_us_title_fa", getattr(obj, "why_choose_us_title_en", ""))
    return getattr(obj, "why_choose_us_title_en", "")


@register.simple_tag(takes_context=True)
def get_why_content(context, obj):
    """Get why_choose_us content for current language"""
    lang = context.get("lang", "en")
    if lang == "fa":
        return getattr(obj, "why_choose_us_content_fa", getattr(obj, "why_choose_us_content_en", ""))
    return getattr(obj, "why_choose_us_content_en", "")


@register.simple_tag(takes_context=True)
def get_who_we_are(context, obj):
    """Get who_we_are for current language"""
    lang = context.get("lang", "en")
    if lang == "fa":
        return getattr(obj, "who_we_are_fa", getattr(obj, "who_we_are_en", ""))
    return getattr(obj, "who_we_are_en", "")


@register.simple_tag(takes_context=True)
def get_we_are_expert(context, obj):
    """Get we_are_expert for current language"""
    lang = context.get("lang", "en")
    if lang == "fa":
        return getattr(obj, "we_are_expert_fa", getattr(obj, "we_are_expert_en", ""))
    return getattr(obj, "we_are_expert_en", "")


@register.simple_tag(takes_context=True)
def get_nav_title(context, obj):
    """Get navigation title for current language"""
    lang = context.get("lang", "en")
    if hasattr(obj, "get_title"):
        try: return obj.get_title(lang)
        except: pass
    if lang == "fa":
        return getattr(obj, "title_fa", getattr(obj, "title_en", ""))
    return getattr(obj, "title_en", "")


@register.simple_tag(takes_context=True)
def site_name(context):
    """Get site name for current language"""
    lang = context.get("lang", "en")
    site = context.get("site_settings")
    if site:
        if lang == "fa":
            return site.site_name_fa
        return site.site_name_en
    return "AM Business"
