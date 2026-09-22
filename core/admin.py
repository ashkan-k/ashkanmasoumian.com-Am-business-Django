from django.contrib import admin
from .models import (
    SiteSettings, SocialLink, Navigation, HeroSection, Service,
    AboutSection, StatCounter, Feature, PricingPlan, Testimonial,
    TeamMember, ContactMessage, NewsletterSubscriber, EventCountdown,
    Page, HomeSection
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ["site_name_en", "site_name_fa", "site_name_ar", "email", "phone"]
    search_fields = ["site_name_en", "site_name_fa", "site_name_ar"]


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ["platform", "url", "is_active", "order"]
    list_filter = ["platform", "is_active"]
    list_editable = ["is_active", "order"]
    search_fields = ["platform", "url"]


@admin.register(Navigation)
class NavigationAdmin(admin.ModelAdmin):
    list_display = ["title_en", "title_fa", "title_ar", "url", "is_active", "order", "parent"]
    list_filter = ["is_active", "parent"]
    list_editable = ["is_active", "order"]
    search_fields = ["title_en", "title_fa", "title_ar", "url"]


@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = ["page", "heading_en", "heading_ar", "is_active"]
    list_filter = ["page", "is_active"]
    search_fields = ["heading_en", "heading_fa", "heading_ar"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["title_en", "title_fa", "title_ar", "icon", "is_active", "order", "slug"]
    list_filter = ["is_active", "icon"]
    list_editable = ["is_active", "order"]
    search_fields = ["title_en", "title_fa", "title_ar", "description_en"]
    prepopulated_fields = {"slug": ["title_en"]}


@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ["title_en", "title_fa", "title_ar", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["title_en", "title_fa", "title_ar"]


@admin.register(StatCounter)
class StatCounterAdmin(admin.ModelAdmin):
    list_display = ["label_en", "label_fa", "label_ar", "value", "is_active", "order"]
    list_filter = ["is_active"]
    list_editable = ["is_active", "order", "value"]
    search_fields = ["label_en", "label_fa", "label_ar"]


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ["title_en", "title_fa", "title_ar", "icon", "is_active", "order"]
    list_filter = ["is_active"]
    list_editable = ["is_active", "order"]
    search_fields = ["title_en", "title_fa", "title_ar"]


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ["name_en", "name_fa", "name_ar", "price", "currency", "is_popular", "is_active", "order"]
    list_filter = ["is_active", "is_popular"]
    list_editable = ["is_active", "order", "is_popular"]
    search_fields = ["name_en", "name_fa", "name_ar"]


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ["author_name", "author_role_en", "author_role_ar", "is_active", "order"]
    list_filter = ["is_active"]
    list_editable = ["is_active", "order"]
    search_fields = ["author_name", "quote_en", "quote_ar"]


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ["name", "position_en", "position_ar", "is_active", "order"]
    list_filter = ["is_active"]
    list_editable = ["is_active", "order"]
    search_fields = ["name", "position_en", "position_fa", "position_ar"]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "subject", "is_read", "is_replied", "created_at"]
    list_filter = ["is_read", "is_replied"]
    list_editable = ["is_read", "is_replied"]
    search_fields = ["name", "email", "subject", "message"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "is_active", "created_at"]
    list_filter = ["is_active"]
    list_editable = ["is_active"]
    search_fields = ["name", "email"]


@admin.register(EventCountdown)
class EventCountdownAdmin(admin.ModelAdmin):
    list_display = ["title_en", "title_fa", "title_ar", "event_date", "is_active"]
    list_filter = ["is_active"]
    list_editable = ["is_active"]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["title_en", "title_fa", "title_ar", "slug", "is_active", "show_in_menu"]
    list_filter = ["is_active", "show_in_menu"]
    list_editable = ["is_active", "show_in_menu"]
    search_fields = ["title_en", "title_fa", "title_ar", "slug"]
    prepopulated_fields = {"slug": ["title_en"]}


@admin.register(HomeSection)
class HomeSectionAdmin(admin.ModelAdmin):
    list_display = ["section_type", "title_en", "title_fa", "title_ar", "is_active"]
    list_filter = ["section_type", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["title_en", "title_fa", "title_ar"]
