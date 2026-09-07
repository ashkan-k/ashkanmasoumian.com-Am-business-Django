from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from .models import (
    SiteSettings, SocialLink, Navigation, HeroSection, Service,
    AboutSection, StatCounter, Feature, PricingPlan, Testimonial,
    TeamMember, ContactMessage, NewsletterSubscriber, EventCountdown,
    Page, HomeSection
)
from .serializers import (
    SiteSettingsSerializer, SocialLinkSerializer, NavigationSerializer,
    HeroSectionSerializer, ServiceSerializer, AboutSectionSerializer,
    StatCounterSerializer, FeatureSerializer, PricingPlanSerializer,
    TestimonialSerializer, TeamMemberSerializer, ContactMessageSerializer,
    NewsletterSubscriberSerializer, NewsletterSubscribeSerializer,
    EventCountdownSerializer, PageSerializer, HomeSectionSerializer
)


class SiteSettingsViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for site settings"""
    queryset = SiteSettings.objects.all()
    serializer_class = SiteSettingsSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        obj = SiteSettings.objects.first()
        if obj:
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        return Response({})


class SocialLinkViewSet(viewsets.ModelViewSet):
    """API endpoint for social links"""
    queryset = SocialLink.objects.filter(is_active=True)
    serializer_class = SocialLinkSerializer
    permission_classes = [AllowAny]


class NavigationViewSet(viewsets.ModelViewSet):
    """API endpoint for navigation menu items"""
    queryset = Navigation.objects.filter(is_active=True, parent=None)
    serializer_class = NavigationSerializer
    permission_classes = [AllowAny]


class HeroSectionViewSet(viewsets.ModelViewSet):
    """API endpoint for hero sections"""
    queryset = HeroSection.objects.filter(is_active=True)
    serializer_class = HeroSectionSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["get"])
    def by_page(self, request):
        page = request.query_params.get("page", "home")
        hero = HeroSection.objects.filter(page=page, is_active=True).first()
        if hero:
            serializer = self.get_serializer(hero)
            return Response(serializer.data)
        return Response({})


class ServiceViewSet(viewsets.ModelViewSet):
    """API endpoint for services"""
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]


class AboutSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for about section"""
    queryset = AboutSection.objects.filter(is_active=True)
    serializer_class = AboutSectionSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        obj = AboutSection.objects.filter(is_active=True).first()
        if obj:
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        return Response({})


class StatCounterViewSet(viewsets.ModelViewSet):
    """API endpoint for stat counters"""
    queryset = StatCounter.objects.filter(is_active=True)
    serializer_class = StatCounterSerializer
    permission_classes = [AllowAny]


class FeatureViewSet(viewsets.ModelViewSet):
    """API endpoint for features"""
    queryset = Feature.objects.filter(is_active=True)
    serializer_class = FeatureSerializer
    permission_classes = [AllowAny]


class PricingPlanViewSet(viewsets.ModelViewSet):
    """API endpoint for pricing plans"""
    queryset = PricingPlan.objects.filter(is_active=True)
    serializer_class = PricingPlanSerializer
    permission_classes = [AllowAny]


class TestimonialViewSet(viewsets.ModelViewSet):
    """API endpoint for testimonials"""
    queryset = Testimonial.objects.filter(is_active=True)
    serializer_class = TestimonialSerializer
    permission_classes = [AllowAny]


class TeamMemberViewSet(viewsets.ModelViewSet):
    """API endpoint for team members"""
    queryset = TeamMember.objects.filter(is_active=True)
    serializer_class = TeamMemberSerializer
    permission_classes = [AllowAny]


class ContactMessageViewSet(viewsets.ModelViewSet):
    """API endpoint for contact messages"""
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Message sent successfully!"},
            status=status.HTTP_201_CREATED
        )


class NewsletterViewSet(viewsets.ModelViewSet):
    """API endpoint for newsletter subscribers"""
    queryset = NewsletterSubscriber.objects.all()
    serializer_class = NewsletterSubscriberSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"])
    def subscribe(self, request):
        serializer = NewsletterSubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj, created = NewsletterSubscriber.objects.get_or_create(
            email=serializer.validated_data["email"],
            defaults={"name": serializer.validated_data["name"]}
        )
        if created:
            return Response({"detail": "Subscribed successfully!"}, status=status.HTTP_201_CREATED)
        return Response({"detail": "Already subscribed."}, status=status.HTTP_200_OK)


class EventCountdownViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for event countdown"""
    queryset = EventCountdown.objects.filter(is_active=True)
    serializer_class = EventCountdownSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        obj = EventCountdown.objects.filter(is_active=True).first()
        if obj:
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        return Response({})


class PageViewSet(viewsets.ModelViewSet):
    """API endpoint for CMS pages"""
    queryset = Page.objects.filter(is_active=True)
    serializer_class = PageSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    @action(detail=False, methods=["get"])
    def by_slug(self, request):
        slug = request.query_params.get("slug", "")
        page = Page.objects.filter(slug=slug, is_active=True).first()
        if page:
            serializer = self.get_serializer(page)
            return Response(serializer.data)
        return Response({"detail": "Page not found."}, status=status.HTTP_404_NOT_FOUND)


class HomeSectionViewSet(viewsets.ModelViewSet):
    """API endpoint for homepage sections"""
    queryset = HomeSection.objects.filter(is_active=True)
    serializer_class = HomeSectionSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["get"])
    def by_type(self, request):
        section_type = request.query_params.get("type", "")
        section = HomeSection.objects.filter(section_type=section_type, is_active=True).first()
        if section:
            serializer = self.get_serializer(section)
            return Response(serializer.data)
        return Response({})


@api_view(["GET"])
def api_overview(request):
    """API overview - list all available endpoints"""
    api_urls = {
        "Site Settings": "/api/v1/site-settings/",
        "Social Links": "/api/v1/social-links/",
        "Navigation": "/api/v1/navigation/",
        "Hero Sections": "/api/v1/hero-sections/",
        "Hero by Page": "/api/v1/hero-sections/by_page/?page=home",
        "Services": "/api/v1/services/",
        "About Section": "/api/v1/about/",
        "Stat Counters": "/api/v1/stat-counters/",
        "Features": "/api/v1/features/",
        "Pricing Plans": "/api/v1/pricing-plans/",
        "Testimonials": "/api/v1/testimonials/",
        "Team Members": "/api/v1/team-members/",
        "Contact Messages": "/api/v1/messages/",
        "Newsletter Subscribe": "/api/v1/newsletter/subscribe/",
        "Newsletter List": "/api/v1/newsletter/",
        "Event Countdown": "/api/v1/event-countdown/",
        "CMS Pages": "/api/v1/pages/",
        "Home Sections": "/api/v1/home-sections/",
    }
    return Response(api_urls)
