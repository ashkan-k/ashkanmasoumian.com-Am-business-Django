from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_frontend
from . import api

router = DefaultRouter()
router.register(r"site-settings", api.SiteSettingsViewSet, basename="api-site-settings")
router.register(r"social-links", api.SocialLinkViewSet, basename="api-social-links")
router.register(r"navigation", api.NavigationViewSet, basename="api-navigation")
router.register(r"hero-sections", api.HeroSectionViewSet, basename="api-hero-sections")
router.register(r"services", api.ServiceViewSet, basename="api-services")
router.register(r"about", api.AboutSectionViewSet, basename="api-about")
router.register(r"stat-counters", api.StatCounterViewSet, basename="api-stat-counters")
router.register(r"features", api.FeatureViewSet, basename="api-features")
router.register(r"pricing-plans", api.PricingPlanViewSet, basename="api-pricing-plans")
router.register(r"testimonials", api.TestimonialViewSet, basename="api-testimonials")
router.register(r"team-members", api.TeamMemberViewSet, basename="api-team-members")
router.register(r"messages", api.ContactMessageViewSet, basename="api-messages")
router.register(r"newsletter", api.NewsletterViewSet, basename="api-newsletter")
router.register(r"event-countdown", api.EventCountdownViewSet, basename="api-event-countdown")
router.register(r"pages", api.PageViewSet, basename="api-pages")
router.register(r"home-sections", api.HomeSectionViewSet, basename="api-home-sections")

urlpatterns = [
    # API
    path("api/", api.api_overview, name="api-overview"),
    path("api/v1/", include(router.urls)),

    # Admin Panel
    path("admin-panel/", views.dashboard, name="admin_dashboard"),
    path("admin-panel/settings/", views.site_settings_view, name="admin_site_settings"),
    path("admin-panel/social-links/", views.social_links_view, name="admin_social_links"),
    path("admin-panel/navigation/", views.navigation_view, name="admin_navigation"),
    path("admin-panel/hero/", views.hero_sections_view, name="admin_hero_sections"),
    path("admin-panel/services/", views.services_view, name="admin_services"),
    path("admin-panel/about/", views.about_view, name="admin_about"),
    path("admin-panel/counters/", views.stat_counters_view, name="admin_stat_counters"),
    path("admin-panel/features/", views.features_view, name="admin_features"),
    path("admin-panel/pricing/", views.pricing_view, name="admin_pricing"),
    path("admin-panel/testimonials/", views.testimonials_view, name="admin_testimonials"),
    path("admin-panel/team/", views.team_view, name="admin_team"),
    path("admin-panel/event-countdown/", views.event_countdown_view, name="admin_event_countdown"),
    path("admin-panel/home-sections/", views.home_sections_view, name="admin_home_sections"),
    path("admin-panel/messages/", views.messages_view, name="admin_messages"),
    path("admin-panel/messages/<int:pk>/", views.message_detail_view, name="admin_message_detail"),
    path("admin-panel/newsletter/", views.newsletter_view, name="admin_newsletter"),
    path("admin-panel/pages/", views.pages_view, name="admin_pages"),

    # Frontend Pages
    path("", views_frontend.frontend_home, name="frontend_home"),
    path("about/", views_frontend.frontend_about, name="frontend_about"),
    path("services/", views_frontend.frontend_services, name="frontend_services"),
    path("contact/", views_frontend.frontend_contact, name="frontend_contact"),
    path("newsletter/subscribe/", views_frontend.frontend_newsletter_subscribe, name="frontend_newsletter_subscribe"),
]
