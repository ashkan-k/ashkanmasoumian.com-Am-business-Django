from django.db import models
from django.utils.text import slugify
import os
import re


# ──────────────────────── Language helpers ────────────────────────
SUPPORTED_LANGUAGES = ("en", "fa", "ar")
DEFAULT_LANGUAGE = "en"

# Languages that are written right-to-left
RTL_LANGUAGES = ("fa", "ar")


def is_rtl(lang):
    """True when the given language code is right-to-left."""
    return (lang or DEFAULT_LANGUAGE) in RTL_LANGUAGES


def pick_lang(obj, field, lang):
    """Return the value of ``field_<lang>`` on ``obj``.

    Falls back to the English value when the requested translation is empty,
    so a partially translated record never renders as a blank field.
    """
    if obj is None:
        return ""
    lang = (lang or DEFAULT_LANGUAGE).split("-")[0]
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    value = getattr(obj, f"{field}_{lang}", "")
    if (value is None or value == "") and lang != DEFAULT_LANGUAGE:
        value = getattr(obj, f"{field}_{DEFAULT_LANGUAGE}", "")
    return "" if value is None else value


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        abstract = True


# ──────────────────────── Colour helpers ────────────────────────
# Dashboard colour fields accept either a palette entry or a hand-typed
# value, so everything is normalised before it reaches a template.
_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_RGB_RE = re.compile(r"^rgba?\(\s*[0-9]{1,3}\s*,\s*[0-9]{1,3}\s*,\s*[0-9]{1,3}\s*(?:,\s*(?:0|1|0?\.[0-9]{1,3})\s*)?\)$")
_NAME_RE = re.compile(r"^[a-zA-Z]{3,20}$")


def safe_css_color(value):
    """Return a CSS-safe colour string, or ``""`` when the value is unusable.

    Accepts ``#rgb``/``#rrggbb``/``#rrggbbaa`` hex codes, ``rgb()``/``rgba()``
    functions and plain colour names.  Anything else (including attempts to
    inject extra CSS declarations) is rejected.
    """
    value = (value or "").strip()
    if not value:
        return ""
    if _HEX_RE.match(value) or _RGB_RE.match(value) or _NAME_RE.match(value):
        return value
    return ""


#: Keys of the editable sections (used by :class:`SectionStyle`).
SECTION_KEYS = (
    "countdown",
    "pricing",
    "features",
    "testimonials",
    "why",
    "team",
    "services",
    "about_home",
    "newsletter",
)


# ──────────────────────── Icon library ────────────────────────
#: Icons offered to services and features: value → (English label, CSS class).
#: The classes come from the bundled icomoon icon font, which inherits
#: `currentColor`, so hover/colour changes work without extra markup.
ICON_LIBRARY = {
    "gear": ("Settings/Gear", "icon-cog"),
    "star": ("Star / Quality", "icon-star"),
    "chart": ("Growth chart", "icon-line-chart"),
    "bullseye": ("Branding / Target", "icon-bullseye"),
    "rocket": ("Launch / Startup", "icon-rocket"),
    "shield": ("Trust / Security", "icon-shield"),
    "idea": ("Idea / Strategy", "icon-lightbulb-o"),
    "handshake": ("Partnership", "icon-handshake-o"),
    "users": ("Team / People", "icon-users"),
    "globe": ("Global / Web", "icon-globe"),
    "briefcase": ("Business", "icon-briefcase"),
    "camera": ("Camera / Media", "icon-camera"),
    "image": ("Image / Design", "icon-image"),
    "layers": ("Layers / Stack", "icon-layers"),
    "window": ("Website / Window", "icon-window-maximize"),
    "bag-check": ("eCommerce", "icon-shopping-bag"),
    "phone": ("Mobile / App", "icon-mobile"),
    "check": ("Check / Approval", "icon-check-circle"),
    "clock": ("Speed / Delivery", "icon-clock-o"),
    "trophy": ("Award / Result", "icon-trophy"),
    "megaphone": ("Marketing", "icon-bullhorn"),
    "code": ("Development", "icon-code"),
    "paint": ("Creative / Brand", "icon-paint-brush"),
    "search": ("Research / Analysis", "icon-search"),
}


def icon_choices(values):
    """``[(value, label), …]`` for the given :data:`ICON_LIBRARY` keys."""
    return [(value, ICON_LIBRARY[value][0]) for value in values if value in ICON_LIBRARY]


def icon_css_class(value):
    """CSS class for an icon value (``""`` when the value is unknown)."""
    entry = ICON_LIBRARY.get((value or "").strip())
    return entry[1] if entry else ""


class SiteSettings(TimestampedModel):
    """Global site settings"""
    site_name_en = models.CharField(max_length=200, default="AM Business", verbose_name="Site Name (EN)")
    site_name_fa = models.CharField(max_length=200, default="ای ام بیزینس", verbose_name="Site Name (FA)")
    site_name_ar = models.CharField(max_length=200, default="إي إم بيزنس", verbose_name="Site Name (AR)")
    logo = models.ImageField(upload_to="site/", blank=True, null=True, verbose_name="Logo")
    favicon = models.ImageField(upload_to="site/", blank=True, null=True, verbose_name="Favicon")
    meta_description_en = models.TextField(blank=True, default="", verbose_name="Meta Description (EN)")
    meta_description_fa = models.TextField(blank=True, default="", verbose_name="Meta Description (FA)")
    meta_description_ar = models.TextField(blank=True, default="", verbose_name="Meta Description (AR)")
    phone = models.CharField(max_length=50, blank=True, default="", verbose_name="Phone")
    email = models.EmailField(blank=True, default="", verbose_name="Email")
    address_en = models.TextField(blank=True, default="", verbose_name="Address (EN)")
    address_fa = models.TextField(blank=True, default="", verbose_name="Address (FA)")
    address_ar = models.TextField(blank=True, default="", verbose_name="Address (AR)")
    copyright_text_en = models.CharField(max_length=500, blank=True, default="By Am Business Creative Division", verbose_name="Copyright (EN)")
    copyright_text_fa = models.CharField(max_length=500, blank=True, default="توسط تیم خلاق ای ام بیزینس", verbose_name="Copyright (FA)")
    copyright_text_ar = models.CharField(max_length=500, blank=True, default="من فريق إي إم بيزنس الإبداعي", verbose_name="Copyright (AR)")
    footer_phone = models.CharField(max_length=50, blank=True, default="+968 94 749 749", verbose_name="Footer Phone")
    footer_location = models.CharField(max_length=500, blank=True, default="Murtafaat Al Matar, Al Seeb, Muscat Governorate", verbose_name="Footer Location")
    footer_linkedin = models.CharField(max_length=200, blank=True, default="ambusinessintl", verbose_name="LinkedIn Username")
    footer_whatsapp = models.CharField(max_length=50, blank=True, default="+968 94 749 749", verbose_name="WhatsApp Number")
    footer_instagram = models.CharField(max_length=200, blank=True, default="ambusinessintl", verbose_name="Instagram Username")
    footer_email = models.EmailField(blank=True, default="info@ambusinessintl.com", verbose_name="Footer Email")

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name_en

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            raise ValueError("Only one SiteSettings instance is allowed.")
        super().save(*args, **kwargs)

    def get_site_name(self, lang='en'):
        return pick_lang(self, "site_name", lang)

    def get_meta_description(self, lang='en'):
        return pick_lang(self, "meta_description", lang)

    def get_address(self, lang='en'):
        return pick_lang(self, "address", lang)

    def get_copyright_text(self, lang='en'):
        return pick_lang(self, "copyright_text", lang)

    def get_footer_location(self, lang='en'):
        """Footer location is a single field, but Arabic/Persian locales may
        prefer a localized label. Kept for template symmetry."""
        return self.footer_location


class SocialLink(TimestampedModel):
    PLATFORM_CHOICES = [
        ("facebook", "Facebook"),
        ("twitter", "Twitter/X"),
        ("linkedin", "LinkedIn"),
        ("instagram", "Instagram"),
        ("dribbble", "Dribbble"),
        ("youtube", "YouTube"),
        ("telegram", "Telegram"),
        ("whatsapp", "WhatsApp"),
        ("github", "GitHub"),
        ("phone", "Phone"),
        ("location", "Location"),
        ("email", "Email"),
        ("other", "Other"),
    ]
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES, verbose_name="Platform")
    url = models.URLField(verbose_name="URL", blank=True, default="#")
    icon_class = models.CharField(max_length=100, blank=True, default="", verbose_name="Icon Class",
                                  help_text="Custom icon class (e.g., icon-facebook)")
    icon_image = models.ImageField(upload_to="social-icons/", blank=True, null=True, verbose_name="Custom Icon Image",
                                   help_text="Upload a custom icon image (overrides icon class)")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    order = models.PositiveIntegerField(default=0, verbose_name="Order")

    class Meta:
        verbose_name = "Social Link"
        verbose_name_plural = "Social Links"
        ordering = ["order"]

    #: Icon font class per platform, used by the footer when the editor has not
    #: supplied a custom `icon_class` or an uploaded `icon_image`.
    PLATFORM_ICON_CLASSES = {
        "facebook": "icon-facebook",
        "twitter": "icon-x-twitter",
        "linkedin": "icon-linkedin",
        "instagram": "icon-instagram",
        "dribbble": "icon-dribbble",
        "youtube": "icon-youtube",
        "telegram": "icon-telegram",
        "whatsapp": "icon-whatsapp",
        "github": "icon-github",
        "phone": "icon-phone",
        "location": "icon-pin_drop",
        "email": "icon-envelope",
        "other": "icon-link",
    }

    #: Platforms that should stay in the same tab (no target="_blank").
    SAME_TAB_PLATFORMS = ("phone", "email")

    def __str__(self):
        return f"{self.platform}: {self.url}"

    @property
    def icon_css_class(self):
        """The class the footer puts on the icon span."""
        return self.icon_class or self.PLATFORM_ICON_CLASSES.get(self.platform, "icon-link")

    @property
    def opens_new_tab(self):
        """False for tel:/mailto: style links."""
        return self.platform not in self.SAME_TAB_PLATFORMS


class Navigation(TimestampedModel):
    """Main navigation menu"""
    title_en = models.CharField(max_length=100, verbose_name="Title (EN)")
    title_fa = models.CharField(max_length=100, verbose_name="Title (FA)")
    title_ar = models.CharField(max_length=100, blank=True, default="", verbose_name="Title (AR)")
    url = models.CharField(max_length=500, default="#", verbose_name="URL")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    order = models.PositiveIntegerField(default=0, verbose_name="Order")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True,
                               related_name="children", verbose_name="Parent Menu")

    class Meta:
        verbose_name = "Navigation Item"
        verbose_name_plural = "Navigation Items"
        ordering = ["order"]

    def __str__(self):
        return self.title_en

    def get_title(self, lang='en'):
        return pick_lang(self, "title", lang)


class HeroSection(TimestampedModel):
    """Hero/banner section for a page.

    ``page`` is the key the frontend looks a hero up by
    (see ``core.views_frontend``):

    * one of :attr:`ROUTED_PAGES` — the four pages with a hard-coded route
    * a CMS page's **slug** — ``frontend_page`` looks up ``page=<slug>``, so a
      hero added for ``portfolio`` appears on ``/page/portfolio/``
    * :attr:`FALLBACK_PAGE` (``custom``) — used by any CMS page that has no
      hero of its own

    The dashboard builds its "Page" dropdown from exactly those values, so a
    hero can never be created for a page that does not exist.
    """
    #: Pages that have their own route in core.views_frontend.
    ROUTED_PAGES = [
        ("home", "Home"),
        ("about", "About"),
        ("services", "Services"),
        ("contact", "Contact"),
    ]
    #: Catch-all hero for CMS pages that have no hero of their own.
    FALLBACK_PAGE = ("custom", "Other / Custom Page")

    PAGE_CHOICES = ROUTED_PAGES + [FALLBACK_PAGE]

    page = models.CharField(max_length=50, choices=PAGE_CHOICES, unique=True, verbose_name="Page")
    heading_en = models.CharField(max_length=300, verbose_name="Heading (EN)")
    heading_fa = models.CharField(max_length=300, verbose_name="Heading (FA)")
    heading_ar = models.CharField(max_length=300, blank=True, default="", verbose_name="Heading (AR)")
    subheading_en = models.CharField(max_length=300, blank=True, default="", verbose_name="Subheading (EN)")
    subheading_fa = models.CharField(max_length=300, blank=True, default="", verbose_name="Subheading (FA)")
    subheading_ar = models.CharField(max_length=300, blank=True, default="", verbose_name="Subheading (AR)")
    background_image = models.ImageField(upload_to="hero/", blank=True, null=True, verbose_name="Background Image")
    cta_text_en = models.CharField(max_length=100, blank=True, default="", verbose_name="CTA Text (EN)")
    cta_text_fa = models.CharField(max_length=100, blank=True, default="", verbose_name="CTA Text (FA)")
    cta_text_ar = models.CharField(max_length=100, blank=True, default="", verbose_name="CTA Text (AR)")
    cta_url = models.CharField(max_length=500, blank=True, default="#", verbose_name="CTA URL")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        verbose_name = "Hero Section"
        verbose_name_plural = "Hero Sections"

    def __str__(self):
        return f"{self.page} Hero"

    def get_page_label(self):
        """Human label for ``page``, resolving a CMS slug to the page title."""
        labels = dict(self.PAGE_CHOICES)
        if self.page in labels:
            return labels[self.page]
        page = Page.objects.filter(slug=self.page).first()
        if page:
            return f"{page.title_en} (/page/{page.slug}/)"
        return self.page

    @property
    def page_exists(self):
        """False when this hero points at a page that no longer exists."""
        if self.page in dict(self.PAGE_CHOICES):
            return True
        return Page.objects.filter(slug=self.page).exists()

    def get_heading(self, lang='en'):
        return pick_lang(self, "heading", lang)

    def get_subheading(self, lang='en'):
        return pick_lang(self, "subheading", lang)

    def get_cta_text(self, lang='en'):
        return pick_lang(self, "cta_text", lang)


class Service(TimestampedModel):
    """Services offered"""
    ICON_CHOICES = [
        ("camera", "Camera"),
        ("gear", "Settings/Gear"),
        ("image", "Image"),
        ("layers", "Layers"),
        ("window", "Window/Web"),
        ("bag-check", "eCommerce"),
        ("bullseye", "Branding"),
        ("phone", "Mobile"),
    ]
    #: Icon-font class rendered for each choice. Font icons inherit
    #: `currentColor`, so the hover colour change works out of the box.
    ICON_CLASSES = {value: ICON_LIBRARY[value][1] for value in (
        "camera", "gear", "image", "layers", "window", "bag-check", "bullseye", "phone")}
    title_en = models.CharField(max_length=200, verbose_name="Title (EN)")
    title_fa = models.CharField(max_length=200, verbose_name="Title (FA)")
    title_ar = models.CharField(max_length=200, blank=True, default="", verbose_name="Title (AR)")
    description_en = models.TextField(verbose_name="Description (EN)")
    description_fa = models.TextField(verbose_name="Description (FA)")
    description_ar = models.TextField(blank=True, default="", verbose_name="Description (AR)")
    icon = models.CharField(max_length=50, choices=ICON_CHOICES, default="gear", verbose_name="Icon")
    custom_svg = models.TextField(blank=True, default="", verbose_name="Custom SVG Icon",
                                  help_text="Paste custom SVG code here (overrides icon selection)")
    custom_icon = models.ImageField(upload_to="services/icons/", blank=True, null=True, verbose_name="Custom Icon Image",
                                    help_text="Upload a custom icon image (overrides icon selection)")
    image = models.ImageField(upload_to="services/", blank=True, null=True, verbose_name="Image")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    order = models.PositiveIntegerField(default=0, verbose_name="Order")
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name="Slug")

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ["order"]

    def __str__(self):
        return self.title_en

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title_en)
        original_slug = self.slug
        counter = 1
        while Service.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
        super().save(*args, **kwargs)

    def get_title(self, lang='en'):
        return pick_lang(self, "title", lang)

    def get_description(self, lang='en'):
        return pick_lang(self, "description", lang)

    @property
    def icon_class(self):
        """Icon-font class for the selected icon (falls back to the gear)."""
        return self.ICON_CLASSES.get(self.icon or "", self.ICON_CLASSES["gear"])

    @property
    def has_custom_svg(self):
        return bool((self.custom_svg or "").strip())


class AboutSection(TimestampedModel):
    """About page section"""
    title_en = models.CharField(max_length=200, default="About Us", verbose_name="Title (EN)")
    title_fa = models.CharField(max_length=200, default="درباره ما", verbose_name="Title (FA)")
    title_ar = models.CharField(max_length=200, blank=True, default="من نحن", verbose_name="Title (AR)")
    content_en = models.TextField(verbose_name="Content (EN)")
    content_fa = models.TextField(verbose_name="Content (FA)")
    content_ar = models.TextField(blank=True, default="", verbose_name="Content (AR)")
    image = models.ImageField(upload_to="about/", blank=True, null=True, verbose_name="Image")
    who_we_are_en = models.TextField(blank=True, default="", verbose_name="Who We Are (EN)")
    who_we_are_fa = models.TextField(blank=True, default="", verbose_name="Who We Are (FA)")
    who_we_are_ar = models.TextField(blank=True, default="", verbose_name="Who We Are (AR)")
    we_are_expert_en = models.TextField(blank=True, default="", verbose_name="We Are Expert (EN)")
    we_are_expert_fa = models.TextField(blank=True, default="", verbose_name="We Are Expert (FA)")
    we_are_expert_ar = models.TextField(blank=True, default="", verbose_name="We Are Expert (AR)")
    why_choose_us_title_en = models.CharField(max_length=200, blank=True, default="Why Choose Us",
                                               verbose_name="Why Choose Us Title (EN)")
    why_choose_us_title_fa = models.CharField(max_length=200, blank=True, default="چرا ما را انتخاب کنید",
                                               verbose_name="Why Choose Us Title (FA)")
    why_choose_us_title_ar = models.CharField(max_length=200, blank=True, default="لماذا تختارنا",
                                               verbose_name="Why Choose Us Title (AR)")
    why_choose_us_content_en = models.TextField(blank=True, default="", verbose_name="Why Choose Us Content (EN)")
    why_choose_us_content_fa = models.TextField(blank=True, default="", verbose_name="Why Choose Us Content (FA)")
    why_choose_us_content_ar = models.TextField(blank=True, default="", verbose_name="Why Choose Us Content (AR)")
    why_choose_us_image = models.ImageField(upload_to="about/", blank=True, null=True,
                                            verbose_name="Why Choose Us Image")
    cta_text_en = models.CharField(max_length=100, blank=True, default="Get Started", verbose_name="CTA Text (EN)")
    cta_text_fa = models.CharField(max_length=100, blank=True, default="شروع کنید", verbose_name="CTA Text (FA)")
    cta_text_ar = models.CharField(max_length=100, blank=True, default="ابدأ الآن", verbose_name="CTA Text (AR)")
    cta_url = models.CharField(max_length=500, blank=True, default="#", verbose_name="CTA URL")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        verbose_name = "About Section"
        verbose_name_plural = "About Sections"

    def __str__(self):
        return self.title_en

    def get_title(self, lang='en'):
        return pick_lang(self, "title", lang)

    def get_content(self, lang='en'):
        return pick_lang(self, "content", lang)

    def get_who_we_are(self, lang='en'):
        return pick_lang(self, "who_we_are", lang)

    def get_we_are_expert(self, lang='en'):
        return pick_lang(self, "we_are_expert", lang)

    def get_why_title(self, lang='en'):
        return pick_lang(self, "why_choose_us_title", lang)

    def get_why_content(self, lang='en'):
        return pick_lang(self, "why_choose_us_content", lang)

    def get_cta_text(self, lang='en'):
        return pick_lang(self, "cta_text", lang)

    def save(self, *args, **kwargs):
        if not self.pk and AboutSection.objects.exists():
            raise ValueError("Only one AboutSection instance is allowed.")
        super().save(*args, **kwargs)


class StatCounter(TimestampedModel):
    """Statistics/counters on About page"""
    label_en = models.CharField(max_length=200, verbose_name="Label (EN)")
    label_fa = models.CharField(max_length=200, verbose_name="Label (FA)")
    label_ar = models.CharField(max_length=200, blank=True, default="", verbose_name="Label (AR)")
    value = models.PositiveIntegerField(default=0, verbose_name="Value")
    icon_class = models.CharField(max_length=100, blank=True, default="", verbose_name="Icon Class")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    order = models.PositiveIntegerField(default=0, verbose_name="Order")

    class Meta:
        verbose_name = "Stat Counter"
        verbose_name_plural = "Stat Counters"
        ordering = ["order"]

    def __str__(self):
        return f"{self.label_en}: {self.value}"

    def get_label(self, lang='en'):
        return pick_lang(self, "label", lang)


class Feature(TimestampedModel):
    """Feature items (More Features section)"""
    ICON_CHOICES = icon_choices([
        "star", "chart", "bullseye", "rocket", "shield", "idea", "handshake",
        "users", "globe", "briefcase", "camera", "image", "layers", "window",
        "bag-check", "phone", "check", "clock", "trophy", "megaphone", "code",
        "paint", "search", "gear",
        "",
    ])
    title_en = models.CharField(max_length=200, verbose_name="Title (EN)")
    title_fa = models.CharField(max_length=200, verbose_name="Title (FA)")
    title_ar = models.CharField(max_length=200, blank=True, default="", verbose_name="Title (AR)")
    description_en = models.TextField(verbose_name="Description (EN)")
    description_fa = models.TextField(verbose_name="Description (FA)")
    description_ar = models.TextField(blank=True, default="", verbose_name="Description (AR)")
    icon = models.CharField(max_length=100, choices=ICON_CHOICES, blank=True, default="",
                            verbose_name="Icon",
                            help_text="Pick one of the built-in icons, or upload/paste your own below.")
    custom_svg = models.TextField(blank=True, default="", verbose_name="Custom SVG Icon",
                                  help_text="Paste SVG code here — it takes precedence over the icon above.")
    custom_icon = models.ImageField(upload_to="features/icons/", blank=True, null=True,
                                    verbose_name="Custom Icon Image",
                                    help_text="Upload an icon image (PNG/SVG). Takes precedence over everything above.")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    order = models.PositiveIntegerField(default=0, verbose_name="Order")

    class Meta:
        verbose_name = "Feature"
        verbose_name_plural = "Features"
        ordering = ["order"]

    def __str__(self):
        return self.title_en

    def get_title(self, lang='en'):
        return pick_lang(self, "title", lang)

    def get_description(self, lang='en'):
        return pick_lang(self, "description", lang)

    @property
    def icon_class(self):
        """Icon-font class for the selected icon (``""`` when unusable).

        Older rows stored a bare name such as ``star`` that never resolved to
        a font class — those now simply render no icon box at all instead of
        an empty coloured square.
        """
        return icon_css_class(self.icon)

    @property
    def has_custom_svg(self):
        return bool((self.custom_svg or "").strip())

    @property
    def has_icon(self):
        """True when anything at all should be drawn above the title."""
        return bool(self.custom_icon or self.has_custom_svg or self.icon_class)


class PricingPlan(TimestampedModel):
    """Pricing plans"""
    name_en = models.CharField(max_length=200, verbose_name="Name (EN)")
    name_fa = models.CharField(max_length=200, verbose_name="Name (FA)")
    name_ar = models.CharField(max_length=200, blank=True, default="", verbose_name="Name (AR)")
    description_en = models.TextField(verbose_name="Description (EN)")
    description_fa = models.TextField(verbose_name="Description (FA)")
    description_ar = models.TextField(blank=True, default="", verbose_name="Description (AR)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    currency = models.CharField(max_length=10, default="$", verbose_name="Currency")
    cents = models.CharField(max_length=5, default=".99", verbose_name="Cents")
    is_popular = models.BooleanField(default=False, verbose_name="Is Popular (Highlighted)")
    button_text_en = models.CharField(max_length=100, default="Buy", verbose_name="Button Text (EN)")
    button_text_fa = models.CharField(max_length=100, default="خرید", verbose_name="Button Text (FA)")
    button_text_ar = models.CharField(max_length=100, blank=True, default="", verbose_name="Button Text (AR)")
    button_url = models.CharField(max_length=500, blank=True, default="#", verbose_name="Button URL")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    order = models.PositiveIntegerField(default=0, verbose_name="Order")

    class Meta:
        verbose_name = "Pricing Plan"
        verbose_name_plural = "Pricing Plans"
        ordering = ["order"]

    def __str__(self):
        return f"{self.name_en} - {self.currency}{self.price}"

    def get_name(self, lang='en'):
        return pick_lang(self, "name", lang)

    def get_description(self, lang='en'):
        return pick_lang(self, "description", lang)

    def get_button_text(self, lang='en'):
        return pick_lang(self, "button_text", lang)


class Testimonial(TimestampedModel):
    """Customer testimonials"""
    quote_en = models.TextField(blank=True, default="", verbose_name="Quote (EN)")
    quote_fa = models.TextField(blank=True, default="", verbose_name="Quote (FA)")
    quote_ar = models.TextField(blank=True, default="", verbose_name="Quote (AR)")
    author_name = models.CharField(max_length=200, verbose_name="Author Name")
    author_role_en = models.CharField(max_length=200, blank=True, default="", verbose_name="Author Role (EN)")
    author_role_fa = models.CharField(max_length=200, blank=True, default="", verbose_name="Author Role (FA)")
    author_role_ar = models.CharField(max_length=200, blank=True, default="", verbose_name="Author Role (AR)")
    author_image = models.ImageField(upload_to="testimonials/", blank=True, null=True, verbose_name="Author Image")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    order = models.PositiveIntegerField(default=0, verbose_name="Order")

    class Meta:
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"
        ordering = ["order"]

    def __str__(self):
        return f"{self.author_name}"

    def get_quote(self, lang='en'):
        return pick_lang(self, "quote", lang)

    def get_role(self, lang='en'):
        return pick_lang(self, "author_role", lang)


class TeamMember(TimestampedModel):
    """Team members"""
    name = models.CharField(max_length=200, verbose_name="Name")
    position_en = models.CharField(max_length=200, verbose_name="Position (EN)")
    position_fa = models.CharField(max_length=200, verbose_name="Position (FA)")
    position_ar = models.CharField(max_length=200, blank=True, default="", verbose_name="Position (AR)")
    bio_en = models.TextField(verbose_name="Bio (EN)")
    bio_fa = models.TextField(verbose_name="Bio (FA)")
    bio_ar = models.TextField(blank=True, default="", verbose_name="Bio (AR)")
    image = models.ImageField(upload_to="team/", blank=True, null=True, verbose_name="Photo")
    photo_square = models.ImageField(upload_to="team/", blank=True, null=True, verbose_name="Square Photo")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    order = models.PositiveIntegerField(default=0, verbose_name="Order")

    class Meta:
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"
        ordering = ["order"]

    def __str__(self):
        return self.name

    def get_position(self, lang='en'):
        return pick_lang(self, "position", lang)

    def get_bio(self, lang='en'):
        return pick_lang(self, "bio", lang)


class ContactMessage(TimestampedModel):
    """Contact form messages"""
    name = models.CharField(max_length=200, verbose_name="Name")
    email = models.EmailField(verbose_name="Email")
    subject = models.CharField(max_length=300, blank=True, default="", verbose_name="Subject")
    message = models.TextField(verbose_name="Message")
    is_read = models.BooleanField(default=False, verbose_name="Is Read")
    is_replied = models.BooleanField(default=False, verbose_name="Is Replied")

    class Meta:
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.subject or self.message[:50]}"


class NewsletterSubscriber(TimestampedModel):
    """Newsletter subscribers"""
    name = models.CharField(max_length=200, verbose_name="Name")
    email = models.EmailField(unique=True, verbose_name="Email")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.email})"


class EventCountdown(TimestampedModel):
    """Event countdown for homepage"""
    IMAGE_POSITION_CHOICES = [
        ("right", "Right side"),
        ("left", "Left side"),
    ]
    title_en = models.CharField(max_length=200, default="Event Countdown", verbose_name="Title (EN)")
    title_fa = models.CharField(max_length=200, default="شمارش معکوس رویداد", verbose_name="Title (FA)")
    title_ar = models.CharField(max_length=200, blank=True, default="العد التنازلي للحدث", verbose_name="Title (AR)")
    subheading_en = models.CharField(max_length=200, default="Don't wait", verbose_name="Subheading (EN)")
    subheading_fa = models.CharField(max_length=200, default="منتظر نمانید", verbose_name="Subheading (FA)")
    subheading_ar = models.CharField(max_length=200, blank=True, default="لا تنتظر", verbose_name="Subheading (AR)")
    event_date = models.DateTimeField(verbose_name="Event Date")
    ended_message_en = models.CharField(max_length=300, default="We are sorry, Event ended!",
                                         verbose_name="Ended Message (EN)")
    ended_message_fa = models.CharField(max_length=300, default="متأسفیم، رویداد تمام شده است!",
                                         verbose_name="Ended Message (FA)")
    ended_message_ar = models.CharField(max_length=300, blank=True, default="نأسف، انتهى الحدث!",
                                         verbose_name="Ended Message (AR)")
    cta_text_en = models.CharField(max_length=100, default="Get Started", verbose_name="CTA Text (EN)")
    cta_text_fa = models.CharField(max_length=100, default="شروع کنید", verbose_name="CTA Text (FA)")
    cta_text_ar = models.CharField(max_length=100, blank=True, default="ابدأ الآن", verbose_name="CTA Text (AR)")
    cta_url = models.CharField(max_length=500, blank=True, default="#", verbose_name="CTA URL")
    image = models.ImageField(upload_to="countdown/", blank=True, null=True, verbose_name="Image",
                              help_text="Shown next to the countdown text (for example the company or event photo)")
    image_position = models.CharField(max_length=10, choices=IMAGE_POSITION_CHOICES, default="right",
                                      verbose_name="Image Position")
    image_alt_en = models.CharField(max_length=200, blank=True, default="", verbose_name="Image Alt Text (EN)")
    image_alt_fa = models.CharField(max_length=200, blank=True, default="", verbose_name="Image Alt Text (FA)")
    image_alt_ar = models.CharField(max_length=200, blank=True, default="", verbose_name="Image Alt Text (AR)")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        verbose_name = "Event Countdown"
        verbose_name_plural = "Event Countdowns"

    def __str__(self):
        return f"{self.title_en} - {self.event_date}"

    def get_title(self, lang='en'):
        return pick_lang(self, "title", lang)

    def get_subheading(self, lang='en'):
        return pick_lang(self, "subheading", lang)

    def get_ended_message(self, lang='en'):
        return pick_lang(self, "ended_message", lang)

    def get_cta_text(self, lang='en'):
        return pick_lang(self, "cta_text", lang)

    def get_image_alt(self, lang='en'):
        return pick_lang(self, "image_alt", lang) or self.get_title(lang)

    def save(self, *args, **kwargs):
        if not self.pk and EventCountdown.objects.exists():
            raise ValueError("Only one EventCountdown instance is allowed.")
        super().save(*args, **kwargs)


class Page(TimestampedModel):
    """CMS Pages"""
    title_en = models.CharField(max_length=200, verbose_name="Title (EN)")
    title_fa = models.CharField(max_length=200, verbose_name="Title (FA)")
    title_ar = models.CharField(max_length=200, blank=True, default="", verbose_name="Title (AR)")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slug")
    content_en = models.TextField(verbose_name="Content (EN)")
    content_fa = models.TextField(verbose_name="Content (FA)")
    content_ar = models.TextField(blank=True, default="", verbose_name="Content (AR)")
    meta_title_en = models.CharField(max_length=200, blank=True, default="", verbose_name="Meta Title (EN)")
    meta_title_fa = models.CharField(max_length=200, blank=True, default="", verbose_name="Meta Title (FA)")
    meta_title_ar = models.CharField(max_length=200, blank=True, default="", verbose_name="Meta Title (AR)")
    meta_description_en = models.TextField(blank=True, default="", verbose_name="Meta Description (EN)")
    meta_description_fa = models.TextField(blank=True, default="", verbose_name="Meta Description (FA)")
    meta_description_ar = models.TextField(blank=True, default="", verbose_name="Meta Description (AR)")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    show_in_menu = models.BooleanField(default=False, verbose_name="Show in Navigation")

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title_en

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title_en)
        original_slug = self.slug
        counter = 1
        while Page.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
        super().save(*args, **kwargs)

    def get_title(self, lang='en'):
        return pick_lang(self, "title", lang)

    def get_content(self, lang='en'):
        return pick_lang(self, "content", lang)

    def get_meta_title(self, lang='en'):
        return pick_lang(self, "meta_title", lang)

    def get_meta_description(self, lang='en'):
        return pick_lang(self, "meta_description", lang)


class HomeSection(TimestampedModel):
    """Homepage custom sections (About us on home, Why Choose Us etc.)"""
    SECTION_TYPES = [
        ("home_about", "Home About Section"),
        ("home_why", "Home Why Choose Us"),
    ]
    section_type = models.CharField(max_length=50, choices=SECTION_TYPES, unique=True, verbose_name="Section Type")
    title_en = models.CharField(max_length=200, verbose_name="Title (EN)")
    title_fa = models.CharField(max_length=200, verbose_name="Title (FA)")
    title_ar = models.CharField(max_length=200, blank=True, default="", verbose_name="Title (AR)")
    subheading_en = models.CharField(max_length=200, blank=True, default="", verbose_name="Subheading (EN)")
    subheading_fa = models.CharField(max_length=200, blank=True, default="", verbose_name="Subheading (FA)")
    subheading_ar = models.CharField(max_length=200, blank=True, default="", verbose_name="Subheading (AR)")
    content_en = models.TextField(verbose_name="Content (EN)")
    content_fa = models.TextField(verbose_name="Content (FA)")
    content_ar = models.TextField(blank=True, default="", verbose_name="Content (AR)")
    image = models.ImageField(upload_to="home/", blank=True, null=True, verbose_name="Image")
    cta_text_en = models.CharField(max_length=100, blank=True, default="Get Started", verbose_name="CTA Text (EN)")
    cta_text_fa = models.CharField(max_length=100, blank=True, default="شروع کنید", verbose_name="CTA Text (FA)")
    cta_text_ar = models.CharField(max_length=100, blank=True, default="ابدأ الآن", verbose_name="CTA Text (AR)")
    cta_url = models.CharField(max_length=500, blank=True, default="#", verbose_name="CTA URL")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        verbose_name = "Home Section"
        verbose_name_plural = "Home Sections"

    def __str__(self):
        return f"{self.get_section_type_display()}"

    def get_title(self, lang='en'):
        return pick_lang(self, "title", lang)

    def get_subheading(self, lang='en'):
        return pick_lang(self, "subheading", lang)

    def get_content(self, lang='en'):
        return pick_lang(self, "content", lang)

    def get_cta_text(self, lang='en'):
        return pick_lang(self, "cta_text", lang)


class SectionStyle(TimestampedModel):
    """Appearance (background, colours) and headings of a homepage section.

    One row per section key.  Empty colour/heading fields mean "keep the
    theme default", so an untouched install renders exactly like before.
    """

    SECTION_CHOICES = [
        ("countdown", "Event Countdown"),
        ("pricing", "Pricing"),
        ("features", "More Features"),
        ("testimonials", "Testimonials"),
        ("why", "Why AM Business"),
        ("team", "Team"),
        ("services", "Services"),
        ("about_home", "Home About"),
        ("newsletter", "Newsletter"),
    ]

    section = models.CharField(max_length=50, choices=SECTION_CHOICES, unique=True, verbose_name="Section")

    # ── Headings (all optional — blank keeps the built-in default) ──
    subheading_en = models.CharField(max_length=200, blank=True, default="", verbose_name="Subheading (EN)")
    subheading_fa = models.CharField(max_length=200, blank=True, default="", verbose_name="Subheading (FA)")
    subheading_ar = models.CharField(max_length=200, blank=True, default="", verbose_name="Subheading (AR)")
    title_en = models.CharField(max_length=200, blank=True, default="", verbose_name="Title (EN)")
    title_fa = models.CharField(max_length=200, blank=True, default="", verbose_name="Title (FA)")
    title_ar = models.CharField(max_length=200, blank=True, default="", verbose_name="Title (AR)")
    subtitle_en = models.TextField(blank=True, default="", verbose_name="Description (EN)")
    subtitle_fa = models.TextField(blank=True, default="", verbose_name="Description (FA)")
    subtitle_ar = models.TextField(blank=True, default="", verbose_name="Description (AR)")

    # ── Background & colours ──
    background_color = models.CharField(max_length=20, blank=True, default="", verbose_name="Background Colour",
                                        help_text="Pick from the palette or type a value such as #530e69")
    background_image = models.ImageField(upload_to="sections/backgrounds/", blank=True, null=True,
                                         verbose_name="Background Image",
                                         help_text="Overrides the background colour")
    overlay_color = models.CharField(max_length=20, blank=True, default="", verbose_name="Overlay Colour")
    overlay_opacity = models.PositiveIntegerField(default=0, verbose_name="Overlay Opacity (%)",
                                                  help_text="0 = no overlay, 90 = almost opaque")
    text_color = models.CharField(max_length=20, blank=True, default="", verbose_name="Body Text Colour")
    heading_color = models.CharField(max_length=20, blank=True, default="", verbose_name="Heading Colour")
    card_background = models.CharField(max_length=20, blank=True, default="", verbose_name="Card Background")
    card_text_color = models.CharField(max_length=20, blank=True, default="", verbose_name="Card Text Colour")

    show_pattern = models.BooleanField(default=True, verbose_name="Show Decorative Pattern")
    item_limit = models.PositiveIntegerField(
        default=0, verbose_name="Items to Show",
        help_text="How many cards/items of this section appear on the website. 0 = show every active item.")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        verbose_name = "Section Appearance"
        verbose_name_plural = "Sections & Backgrounds"
        ordering = ["section"]

    def __str__(self):
        return self.get_section_display()

    # ── Heading helpers ──
    def get_title(self, lang='en'):
        return pick_lang(self, "title", lang)

    def get_subheading(self, lang='en'):
        return pick_lang(self, "subheading", lang)

    def get_subtitle(self, lang='en'):
        return pick_lang(self, "subtitle", lang)

    # ── Colour helpers (all sanitised) ──
    @property
    def bg_color(self):
        return safe_css_color(self.background_color)

    @property
    def overlay(self):
        return safe_css_color(self.overlay_color)

    @property
    def body_color(self):
        return safe_css_color(self.text_color)

    @property
    def title_color(self):
        return safe_css_color(self.heading_color)

    @property
    def card_bg(self):
        return safe_css_color(self.card_background)

    @property
    def card_text(self):
        return safe_css_color(self.card_text_color)

    def style_attribute(self):
        """CSS custom properties for the section wrapper (safe to inline).

        Only sanitised colour values are emitted, so the result contains no
        characters that HTML escaping would alter.
        """
        declarations = []
        if self.title_color:
            declarations.append(f"--am-heading:{self.title_color}")
        if self.body_color:
            declarations.append(f"--am-text:{self.body_color}")
        if self.card_bg:
            declarations.append(f"--am-card-bg:{self.card_bg}")
        if self.card_text:
            declarations.append(f"--am-card-text:{self.card_text}")
        if self.overlay:
            opacity = max(0, min(100, self.overlay_opacity or 0)) / 100
            declarations.append(f"--am-overlay:{self.overlay}")
            declarations.append(f"--am-overlay-opacity:{opacity}")
        return ";".join(declarations)


def get_sections(create_missing=False, active_only=False):
    """Return ``{section_key: SectionStyle}`` for every editable section.

    With ``active_only=True`` the rows switched off in the dashboard are left
    out, so the website falls back to the theme defaults for those sections.
    """
    queryset = SectionStyle.objects.all()
    if active_only:
        queryset = queryset.filter(is_active=True)
    existing = {style.section: style for style in queryset}
    if create_missing:
        for key in SECTION_KEYS:
            if key not in existing:
                existing[key] = SectionStyle.objects.create(section=key)
    return existing
