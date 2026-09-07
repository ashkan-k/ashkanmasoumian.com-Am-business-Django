from rest_framework import serializers
from .models import (
    SiteSettings, SocialLink, Navigation, HeroSection, Service,
    AboutSection, StatCounter, Feature, PricingPlan, Testimonial,
    TeamMember, ContactMessage, NewsletterSubscriber, EventCountdown,
    Page, HomeSection
)


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = "__all__"


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = "__all__"


class NavigationSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Navigation
        fields = "__all__"

    def get_children(self, obj):
        if obj.children.exists():
            return NavigationSerializer(obj.children.all(), many=True).data
        return []


class HeroSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = "__all__"


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"


class AboutSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutSection
        fields = "__all__"


class StatCounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatCounter
        fields = "__all__"


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = "__all__"


class PricingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingPlan
        fields = "__all__"


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = "__all__"


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = "__all__"


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = "__all__"
        read_only_fields = ["is_read", "is_replied"]


class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = "__all__"


class NewsletterSubscribeSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()


class EventCountdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventCountdown
        fields = "__all__"


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = "__all__"


class HomeSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeSection
        fields = "__all__"
