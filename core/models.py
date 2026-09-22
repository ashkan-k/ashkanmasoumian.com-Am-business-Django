from django.db import models
from django.utils.text import slugify
import os


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

    def __str__(self):
        return f"{self.platform}: {self.url}"


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
    """Hero/banner section for pages"""
    PAGE_CHOICES = [
        ("home", "Home"),
        ("about", "About"),
        ("services", "Services"),
        ("contact", "Contact"),
    ]
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
    title_en = models.CharField(max_length=200, verbose_name="Title (EN)")
    title_fa = models.CharField(max_length=200, verbose_name="Title (FA)")
    title_ar = models.CharField(max_length=200, blank=True, default="", verbose_name="Title (AR)")
    description_en = models.TextField(verbose_name="Description (EN)")
    description_fa = models.TextField(verbose_name="Description (FA)")
    description_ar = models.TextField(blank=True, default="", verbose_name="Description (AR)")
    icon = models.CharField(max_length=100, blank=True, default="", verbose_name="Icon")
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
    quote_en = models.TextField(verbose_name="Quote (EN)")
    quote_fa = models.TextField(verbose_name="Quote (FA)")
    quote_ar = models.TextField(blank=True, default="", verbose_name="Quote (AR)")
    author_name = models.CharField(max_length=200, verbose_name="Author Name")
    author_role_en = models.CharField(max_length=200, verbose_name="Author Role (EN)")
    author_role_fa = models.CharField(max_length=200, verbose_name="Author Role (FA)")
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
