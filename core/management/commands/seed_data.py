from django.core.management.base import BaseCommand
from core.models import (
    SiteSettings, SocialLink, Navigation, HeroSection, Service,
    AboutSection, StatCounter, Feature, PricingPlan, Testimonial,
    TeamMember, EventCountdown, HomeSection
)
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Seed database with AM Business content"

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")

        # Site Settings
        site, _ = SiteSettings.objects.get_or_create(
            pk=1,
            defaults={
                "site_name_en": "AM Business",
                "site_name_fa": "ای ام بیزینس",
                "phone": "+968 94 749 749",
                "email": "info@ambusinessintl.com",
                "address_en": "Murtafaat Al Matar, Al Seeb, Muscat Governorate",
                "address_fa": "مطورفات المطار، السیب، استان مسقط",
                "copyright_text_en": "By Am Business Creative Division",
                "copyright_text_fa": "توسط تیم خلاق ای ام بیزینس",
                "meta_description_en": "Integrated business growth and transformation company based in Muscat, Oman.",
                "meta_description_fa": "شرکت یکپارچه رشد و تحول کسب و کار در مسقط، عمان.",
                "footer_phone": "+968 94 749 749",
                "footer_location": "Murtafaat Al Matar, Al Seeb, Muscat Governorate",
                "footer_linkedin": "ambusinessintl",
                "footer_whatsapp": "+968 94 749 749",
                "footer_instagram": "ambusinessintl",
                "footer_email": "info@ambusinessintl.com",
            }
        )
        self.stdout.write(f"  Site Settings: created={not _}")

        # Social Links
        for i, (platform, url) in enumerate([
            ("linkedin", "https://linkedin.com/company/ambusinessintl"),
            ("instagram", "https://instagram.com/ambusinessintl"),
            ("whatsapp", "https://wa.me/96894749749"),
            ("email", "mailto:info@ambusinessintl.com"),
        ]):
            SocialLink.objects.get_or_create(
                platform=platform, url=url,
                defaults={"is_active": True, "order": i}
            )
        self.stdout.write("  Social Links: created")

        # Navigation
        home_nav, _ = Navigation.objects.get_or_create(
            title_en="Home", title_fa="خانه", url="/",
            defaults={"is_active": True, "order": 0}
        )
        services_nav, _ = Navigation.objects.get_or_create(
            title_en="Services", title_fa="خدمات", url="/services/",
            defaults={"is_active": True, "order": 1}
        )
        about_nav, _ = Navigation.objects.get_or_create(
            title_en="About", title_fa="درباره ما", url="/about/",
            defaults={"is_active": True, "order": 2}
        )
        contact_nav, _ = Navigation.objects.get_or_create(
            title_en="Contact Us", title_fa="تماس با ما", url="/contact/",
            defaults={"is_active": True, "order": 3}
        )
        self.stdout.write("  Navigation: created")

        # Hero Sections
        for page, heading_en, heading_fa, sub_en, sub_fa in [
            ("home", "AM BUSINESS", "ای ام بیزینس", "From Vision To Success", "از بینش تا موفقیت"),
            ("about", "About Us", "درباره ما", "Learn more about us", "بیشتر درباره ما بدانید"),
            ("services", "Our Services", "خدمات ما", "What we offer", "خدمات ما"),
            ("contact", "Contact Us", "تماس با ما", "Get in touch", "با ما در تماس باشید"),
        ]:
            HeroSection.objects.get_or_create(
                page=page,
                defaults={
                    "heading_en": heading_en, "heading_fa": heading_fa,
                    "subheading_en": sub_en, "subheading_fa": sub_fa,
                    "cta_text_en": "Get In Touch", "cta_text_fa": "تماس بگیرید",
                    "cta_url": "/contact/", "is_active": True,
                }
            )
        self.stdout.write("  Hero Sections: created")

        # Services - AM Business specific
        services_data = [
            ("Strategy & Advisory", "استراتژی و مشاوره", "Research-driven strategic guidance to help businesses make better decisions and pursue sustainable growth.", "راهنمایی استراتژیک مبتنی بر تحقیق برای کمک به کسب و کارها در تصمیم‌گیری بهتر.", "bullseye"),
            ("Creative Studio", "استودیو خلاق", "Brand identity, visual design, and creative solutions that serve a business purpose.", "هویت برند، طراحی بصری و راهکارهای خلاقانه در خدمت اهداف کسب و کار.", "image"),
            ("Marketing & Growth", "بازاریابی و رشد", "Integrated marketing strategies to strengthen market position and drive meaningful growth.", "استراتژی‌های بازاریابی یکپارچه برای تقویت موقعیت بازار و رشد معنادار.", "layers"),
            ("Digital & AI Solutions", "راهکارهای دیجیتال و هوش مصنوعی", "Practical technology and AI applications to improve efficiency, decision-making, and scalability.", "فناوری و هوش مصنوعی کاربردی برای بهبود بهره‌وری و مقیاس‌پذیری.", "gear"),
            ("Web Design", "طراحی وب", "Modern and responsive web design solutions that create impactful digital experiences.", "راهکارهای طراحی وب مدرن و ریسپانسیو برای تجربیات دیجیتال تأثیرگذار.", "window"),
            ("eCommerce", "فروشگاهی", "Complete e-commerce solutions for online stores and digital commerce.", "راهکارهای کامل فروشگاه آنلاین و تجارت دیجیتال.", "bag-check"),
            ("Mobile Apps", "اپلیکیشن", "Native and cross-platform mobile application development.", "توسعه اپلیکیشن موبایل بومی و چندپلتفرمی.", "phone"),
            ("Branding", "برندینگ", "Brand identity design and marketing strategies for lasting impact.", "طراحی هویت برند و استراتژی‌های بازاریابی برای تأثیر ماندگار.", "camera"),
        ]
        for i, (t_en, t_fa, d_en, d_fa, icon) in enumerate(services_data):
            Service.objects.get_or_create(
                slug=t_en.lower().replace(" ", "-"),
                defaults={
                    "title_en": t_en, "title_fa": t_fa,
                    "description_en": d_en, "description_fa": d_fa,
                    "icon": icon, "is_active": True, "order": i,
                }
            )
        self.stdout.write("  Services: created")

        # About - Full AM Business content
        about_content_short = """AM Business is an integrated business growth and transformation company based in Muscat, Oman, serving ambitious businesses, founders, organizations, and institutions across the GCC.

We bring together research, strategy, creativity, marketing, digital capabilities, and AI to help clients make better decisions, build stronger brands, strengthen their market position, develop smarter capabilities, and pursue sustainable growth.

AM Business was created from a clear belief: businesses do not always lose opportunities because of a lack of ambition or investment. They often lose valuable time, capital, and momentum through insufficient research, unclear strategy, fragmented execution, disconnected providers, and decisions made without the right knowledge or direction. Our purpose is to help reduce that gap by connecting strategic thinking with professional execution."""

        AboutSection.objects.get_or_create(
            pk=1,
            defaults={
                "title_en": "About AM Business",
                "title_fa": "درباره ای ام بیزینس",
                "content_en": about_content_short,
                "content_fa": "ای ام بیزینس یک شرکت یکپارچه رشد و تحول کسب و کار مستقر در مسقط، عمان است که به کسب و کارهای بلندپرواز، بنیانگذاران، سازمان‌ها و نهادهای سراسر GCC خدمت رسانی می‌کند.",
                "who_we_are_en": "AM Business was founded by Dr. Ashkan Masoumian as part of the AM International ecosystem.",
                "who_we_are_fa": "ای ام بیزینس توسط دکتر اشکان موسومیان به عنوان بخشی از اکوسیستم بین‌المللی تأسیس شده است.",
                "we_are_expert_en": "With Muscat as our base and the GCC as our primary strategic market, our ambition is to build AM Business into one of the region's most trusted and leading strategic growth partners.",
                "we_are_expert_fa": "با مسقط به عنوان پایگاه و GCC به عنوان بازار استراتژیک اصلی، هدف ما تبدیل ای ام بیزینس به یکی از معتبرترین شرکای رشد استراتژیک منطقه است.",
                "why_choose_us_title_en": "Why AM Business",
                "why_choose_us_title_fa": "چرا ای ام بیزینس",
                "why_choose_us_content_en": """Research Before Recommendation: We understand the business, market, and challenge before recommending a solution.
Strategy Before Execution: Execution follows a clear direction and business logic—not the other way around.
Integrated Capabilities: Strategy, creative, marketing, digital, and AI capabilities can work together as one coordinated solution.
Business-First Creativity: Creative work is designed to serve a business purpose, not simply produce attractive assets.
Practical Digital & AI: Technology and AI are applied where they can improve efficiency, decision-making, customer experience, or scalability.
Outcome-Oriented Partnership: We focus on business value and meaningful outcomes while building relationships with a long-term perspective.""",
                "why_choose_us_content_fa": """تحقیق قبل از توصیه: ما کسب و کار، بازار و چالش را قبل از ارائه راهکار درک می‌کنیم.
استراتژی قبل از اجرا: اجرا از مسیر منطقی و منطق کسب و کار پیروی می‌کند—نه برعکس.
قابلیت‌های یکپارچه: استراتژی، خلاقیت، بازاریابی، دیجیتال و هوش مصنوعی می‌توانند به صورت هماهنگ کار کنند.
خلاقیت اول کسب و کار: کار خلاقانه برای خدمت به هدف کسب و کار طراحی شده است.
دیجیتال و هوش مصنوعی کاربردی: فناوری و AI در جایی استفاده می‌شوند که بهره‌وری را بهبود دهند.
مشارکت نتیجه‌محور: ما بر ارزش کسب و کار و نتایج معنادار تمرکز داریم.""",
                "cta_text_en": "Read More",
                "cta_text_fa": "بیشتر بخوانید",
                "cta_url": "/about/",
                "is_active": True,
            }
        )
        self.stdout.write("  About: created")

        # Home About Section
        HomeSection.objects.get_or_create(
            section_type="home_about",
            defaults={
                "title_en": "About AM Business",
                "title_fa": "درباره ای ام بیزینس",
                "subheading_en": "About Us",
                "subheading_fa": "درباره ما",
                "content_en": about_content_short,
                "content_fa": "ای ام بیزینس یک شرکت یکپارچه رشد و تحول کسب و کار مستقر در مسقط، عمان است.",
                "cta_text_en": "Read More",
                "cta_text_fa": "بیشتر بخوانید",
                "cta_url": "/about/",
                "is_active": True,
            }
        )
        self.stdout.write("  Home Sections: created")

        # Counters
        for label_en, label_fa, value in [
            ("Projects Completed", "پروژه‌های تکمیل شده", 150),
            ("Happy Clients", "مشتریان راضی", 85),
            ("Team Members", "اعضای تیم", 25),
            ("Awards", "جایزه‌ها", 12),
        ]:
            StatCounter.objects.get_or_create(
                label_en=label_en,
                defaults={"label_fa": label_fa, "value": value, "is_active": True, "order": 0}
            )
        self.stdout.write("  Counters: created")

        # Features
        features_data = [
            ("Research", "تحقیق", "Data-driven research to understand your market, competitors, and opportunities.", "تحقیق مبتنی بر داده برای درک بازار، رقبا و فرصت‌های شما."),
            ("Strategy", "استراتژی", "Clear strategic direction that aligns with your business goals.", "جهت استراتژیک روشن که با اهداف کسب و کار شما هماهنگ است."),
            ("Execution", "اجرا", "Professional execution that turns strategy into measurable results.", "اجرای حرفه‌ای که استراتژی را به نتایج قابل اندازه‌گیری تبدیل می‌کند."),
        ]
        for i, (t_en, t_fa, d_en, d_fa) in enumerate(features_data):
            Feature.objects.get_or_create(
                title_en=t_en,
                defaults={"title_fa": t_fa, "description_en": d_en, "description_fa": d_fa, "is_active": True, "order": i}
            )
        self.stdout.write("  Features: created")

        # Pricing
        pricing_data = [
            ("Starter", "پایه", "Perfect for small projects and startups looking for a strong foundation.", "ایده‌آل برای پروژه‌های کوچک و استارتاپ‌ها.", "49", ".99"),
            ("Growth", "رشد", "Ideal for growing businesses needing integrated capabilities.", "مناسب برای کسب و کارهای در حال رشد.", "199", ".99"),
            ("Enterprise", "سازمانی", "Comprehensive solution for large organizations with complex needs.", "راهکار جامع برای سازمان‌های بزرگ.", "975", ".99"),
        ]
        for i, (n_en, n_fa, d_en, d_fa, price, cents) in enumerate(pricing_data):
            PricingPlan.objects.get_or_create(
                name_en=n_en,
                defaults={
                    "name_fa": n_fa, "description_en": d_en, "description_fa": d_fa,
                    "price": price, "currency": "$", "cents": cents,
                    "button_text_en": "Get Started", "button_text_fa": "شروع کنید",
                    "button_url": "/contact/", "is_active": True, "order": i,
                }
            )
        self.stdout.write("  Pricing: created")

        # Testimonials
        testimonials_data = [
            ("Dr. Ahmed Al-Rashid", "CEO @Gulf Ventures", "مدیرعامل @گالف ونچرز",
             "AM Business brought clarity to our growth strategy. Their integrated approach saved us time and delivered results we didn't expect.",
             "ای ام بیزینس وضوح به استراتژی رشد ما بخشید. رویکرد یکپارچه آن‌ها زمان ما را ذخیره کرد."),
            ("Sarah Mitchell", "Marketing Director @TechHub Oman", "مدیر بازاریابی @تک‌هاب عمان",
             "Outstanding strategic thinking combined with creative execution. AM Business is our trusted growth partner.",
             "تفکر استراتژیک برجسته همراه با اجرای خلاقانه. ای ام بیزینس شریک رشد قابل اعتماد ماست."),
        ]
        for i, (name, role_en, role_fa, q_en, q_fa) in enumerate(testimonials_data):
            Testimonial.objects.get_or_create(
                author_name=name,
                defaults={
                    "quote_en": q_en, "quote_fa": q_fa,
                    "author_role_en": role_en, "author_role_fa": role_fa,
                    "is_active": True, "order": i,
                }
            )
        self.stdout.write("  Testimonials: created")

        # Team
        team_data = [
            ("Dr. Ashkan Masoumian", "Founder & CEO", "بنیانگذار و مدیرعامل",
             "Executive and board-level experience in pharmaceutical and manufacturing business, international commercial experience, MBA, DBA, and Post-DBA studies.",
             "تجربه اجرایی و هیئت مدیره در کسب و کار دارویی و تولیدی."),
        ]
        for i, (name, pos_en, pos_fa, bio_en, bio_fa) in enumerate(team_data):
            TeamMember.objects.get_or_create(
                name=name,
                defaults={
                    "position_en": pos_en, "position_fa": pos_fa,
                    "bio_en": bio_en, "bio_fa": bio_fa,
                    "is_active": True, "order": i,
                }
            )
        self.stdout.write("  Team: created")

        # Event Countdown (keep existing but inactive)
        EventCountdown.objects.get_or_create(
            pk=1,
            defaults={
                "title_en": "Event Countdown", "title_fa": "شمارش معکوس رویداد",
                "subheading_en": "Don't wait", "subheading_fa": "منتظر نمانید",
                "event_date": timezone.now() + timedelta(days=39, hours=27),
                "ended_message_en": "We are sorry, Event ended!", "ended_message_fa": "متأسفیم، رویداد تمام شده است!",
                "cta_text_en": "Get Started", "cta_text_fa": "شروع کنید",
                "cta_url": "#", "is_active": False,
            }
        )
        self.stdout.write("  Countdown: created (inactive)")

        self.stdout.write(self.style.SUCCESS("\nDone! Database seeded with AM Business content."))
