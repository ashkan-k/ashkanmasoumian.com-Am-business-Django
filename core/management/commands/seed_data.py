from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from core.models import (
    SiteSettings, SocialLink, Navigation, HeroSection, Service,
    AboutSection, StatCounter, Feature, PricingPlan, Testimonial,
    TeamMember, EventCountdown, HomeSection
)

#: Fields that hold a translation. Used to backfill existing rows.
TRANSLATED_SUFFIXES = ("_en", "_fa", "_ar")


def apply_defaults(obj, defaults):
    """Fill in fields that are still empty on an existing row.

    ``get_or_create`` only writes ``defaults`` when it creates the record, so a
    database seeded before Arabic was introduced keeps empty ``*_ar`` columns.
    This helper completes those translations without ever overwriting content an
    editor has already filled in, which makes the command safe to re-run.
    """
    changed = []
    for field, value in defaults.items():
        if value in (None, ""):
            continue
        current = getattr(obj, field, None)
        if current not in (None, ""):
            continue
        setattr(obj, field, value)
        changed.append(field)
    if changed:
        obj.save(update_fields=changed)
    return changed


def upsert(model, lookup, defaults, label=None):
    """get_or_create + backfill empty translations. Returns the instance."""
    obj, created = model.objects.get_or_create(**lookup, defaults=defaults)
    filled = apply_defaults(obj, defaults)
    return obj, created, filled


class Command(BaseCommand):
    help = "Seed (and complete) the database with AM Business content in English, Persian and Arabic"

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")
        backfilled = 0

        # ── Site Settings ──
        defaults = {
            "site_name_en": "AM Business",
            "site_name_fa": "ای ام بیزینس",
            "site_name_ar": "إي إم بيزنس",
            "phone": "+968 94 749 749",
            "email": "info@ambusinessintl.com",
            "address_en": "Murtafaat Al Matar, Al Seeb, Muscat Governorate",
            "address_fa": "مطورفات المطار، السیب، استان مسقط",
            "address_ar": "مرتفعات المطار، السيب، محافظة مسقط",
            "copyright_text_en": "By Am Business Creative Division",
            "copyright_text_fa": "توسط تیم خلاق ای ام بیزینس",
            "copyright_text_ar": "من فريق إي إم بيزنس الإبداعي",
            "meta_description_en": "Integrated business growth and transformation company based in Muscat, Oman.",
            "meta_description_fa": "شرکت یکپارچه رشد و تحول کسب و کار در مسقط، عمان.",
            "meta_description_ar": "شركة متكاملة لنمو الأعمال والتحول مقرها مسقط، عُمان.",
            "footer_phone": "+968 94 749 749",
            "footer_location": "Murtafaat Al Matar, Al Seeb, Muscat Governorate",
            "footer_linkedin": "ambusinessintl",
            "footer_whatsapp": "+968 94 749 749",
            "footer_instagram": "ambusinessintl",
            "footer_email": "info@ambusinessintl.com",
        }
        settings_obj = SiteSettings.objects.first()
        if settings_obj is None:
            settings_obj = SiteSettings.objects.create(**defaults)
            self.stdout.write("  Site Settings: created")
        else:
            backfilled += len(apply_defaults(settings_obj, defaults))
            self.stdout.write("  Site Settings: kept")

        # ── Social Links ──
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

        # ── Navigation ──
        for order, (title_en, title_fa, title_ar, url) in enumerate([
            ("Home", "خانه", "الرئيسية", "/"),
            ("Services", "خدمات", "الخدمات", "/services/"),
            ("About", "درباره ما", "من نحن", "/about/"),
            ("Contact Us", "تماس با ما", "اتصل بنا", "/contact/"),
        ]):
            _obj, _created, filled = upsert(
                Navigation,
                {"title_en": title_en, "url": url},
                {"title_fa": title_fa, "title_ar": title_ar, "is_active": True, "order": order},
            )
            backfilled += len(filled)
        self.stdout.write("  Navigation: created")

        # ── Hero Sections ──
        heroes = [
            ("home", "AM BUSINESS", "ای ام بیزینس", "إي إم بيزنس",
             "From Vision To Success", "از بینش تا موفقیت", "من الرؤية إلى النجاح"),
            ("about", "About Us", "درباره ما", "من نحن",
             "Learn more about us", "بیشتر درباره ما بدانید", "اعرف المزيد عنا"),
            ("services", "Our Services", "خدمات ما", "خدماتنا",
             "What we offer", "خدمات ما", "ما نقدمه"),
            ("contact", "Contact Us", "تماس با ما", "اتصل بنا",
             "Get in touch", "با ما در تماس باشید", "تواصل معنا"),
        ]
        for page, h_en, h_fa, h_ar, s_en, s_fa, s_ar in heroes:
            _obj, _created, filled = upsert(
                HeroSection,
                {"page": page},
                {
                    "heading_en": h_en, "heading_fa": h_fa, "heading_ar": h_ar,
                    "subheading_en": s_en, "subheading_fa": s_fa, "subheading_ar": s_ar,
                    "cta_text_en": "Get In Touch", "cta_text_fa": "تماس بگیرید",
                    "cta_text_ar": "تواصل معنا",
                    "cta_url": "/contact/", "is_active": True,
                },
            )
            backfilled += len(filled)
        self.stdout.write("  Hero Sections: created")

        # ── Services ──
        services_data = [
            ("Strategy & Advisory", "استراتژی و مشاوره", "الاستراتيجية والاستشارات",
             "Research-driven strategic guidance to help businesses make better decisions and pursue sustainable growth.",
             "راهنمایی استراتژیک مبتنی بر تحقیق برای کمک به کسب و کارها در تصمیم‌گیری بهتر.",
             "إرشاد استراتيجي قائم على البحث لمساعدة الشركات على اتخاذ قرارات أفضل ونمو مستدام.",
             "bullseye"),
            ("Creative Studio", "استودیو خلاق", "الاستوديو الإبداعي",
             "Brand identity, visual design, and creative solutions that serve a business purpose.",
             "هویت برند، طراحی بصری و راهکارهای خلاقانه در خدمت اهداف کسب و کار.",
             "هوية العلامة والتصميم البصري وحلول إبداعية تخدم هدفًا تجاريًا.",
             "image"),
            ("Marketing & Growth", "بازاریابی و رشد", "التسويق والنمو",
             "Integrated marketing strategies to strengthen market position and drive meaningful growth.",
             "استراتژی‌های بازاریابی یکپارچه برای تقویت موقعیت بازار و رشد معنادار.",
             "استراتيجيات تسويق متكاملة لتعزيز موقعك في السوق وتحقيق نمو ملموس.",
             "layers"),
            ("Digital & AI Solutions", "راهکارهای دیجیتال و هوش مصنوعی", "الحلول الرقمية والذكاء الاصطناعي",
             "Practical technology and AI applications to improve efficiency, decision-making, and scalability.",
             "فناوری و هوش مصنوعی کاربردی برای بهبود بهره‌وری و مقیاس‌پذیری.",
             "تقنيات وتطبيقات ذكاء اصطناعي عملية لتحسين الكفاءة واتخاذ القرار وقابلية التوسع.",
             "gear"),
            ("Web Design", "طراحی وب", "تصميم المواقع",
             "Modern and responsive web design solutions that create impactful digital experiences.",
             "راهکارهای طراحی وب مدرن و ریسپانسیو برای تجربیات دیجیتال تأثیرگذار.",
             "حلول تصميم ويب حديثة ومتجاوبة تخلق تجارب رقمية مؤثرة.",
             "window"),
            ("eCommerce", "فروشگاهی", "التجارة الإلكترونية",
             "Complete e-commerce solutions for online stores and digital commerce.",
             "راهکارهای کامل فروشگاه آنلاین و تجارت دیجیتال.",
             "حلول تجارة إلكترونية متكاملة للمتاجر الإلكترونية والتجارة الرقمية.",
             "bag-check"),
            ("Mobile Apps", "اپلیکیشن", "تطبيقات الجوال",
             "Native and cross-platform mobile application development.",
             "توسعه اپلیکیشن موبایل بومی و چندپلتفرمی.",
             "تطوير تطبيقات جوال أصلية ومتعددة المنصات.",
             "phone"),
            ("Branding", "برندینگ", "العلامة التجارية",
             "Brand identity design and marketing strategies for lasting impact.",
             "طراحی هویت برند و استراتژی‌های بازاریابی برای تأثیر ماندگار.",
             "تصميم هوية العلامة واستراتيجيات تسويقية لأثر دائم.",
             "camera"),
        ]
        for i, (t_en, t_fa, t_ar, d_en, d_fa, d_ar, icon) in enumerate(services_data):
            _obj, _created, filled = upsert(
                Service,
                {"slug": t_en.lower().replace(" ", "-")},
                {
                    "title_en": t_en, "title_fa": t_fa, "title_ar": t_ar,
                    "description_en": d_en, "description_fa": d_fa, "description_ar": d_ar,
                    "icon": icon, "is_active": True, "order": i,
                },
            )
            backfilled += len(filled)
        self.stdout.write("  Services: created")

        # ── About ──
        about_en = """AM Business is an integrated business growth and transformation company based in Muscat, Oman, serving ambitious businesses, founders, organizations, and institutions across the GCC.

We bring together research, strategy, creativity, marketing, digital capabilities, and AI to help clients make better decisions, build stronger brands, strengthen their market position, develop smarter capabilities, and pursue sustainable growth.

AM Business was created from a clear belief: businesses do not always lose opportunities because of a lack of ambition or investment. They often lose valuable time, capital, and momentum through insufficient research, unclear strategy, fragmented execution, disconnected providers, and decisions made without the right knowledge or direction. Our purpose is to help reduce that gap by connecting strategic thinking with professional execution."""

        about_ar = """إي إم بيزنس شركة متكاملة لنمو الأعمال والتحول مقرها مسقط، عُمان، وتخدم الشركات الطموحة والمؤسسين والمنظمات والمؤسسات في دول مجلس التعاون الخليجي.

نجمع بين البحث والاستراتيجية والإبداع والتسويق والقدرات الرقمية والذكاء الاصطناعي لمساعدة عملائنا على اتخاذ قرارات أفضل وبناء علامات أقوى وتعزيز موقعهم في السوق وتطوير قدرات أكثر ذكاءً وتحقيق نمو مستدام.

وُلدت إي إم بيزنس من قناعة واضحة: الشركات لا تفقد الفرص دائمًا بسبب نقص الطموح أو الاستثمار، بل تفقد وقتًا ورأسمالًا وزخمًا ثمينًا بسبب البحث غير الكافي والاستراتيجية غير الواضحة والتنفيذ المجزأ ومقدمي الخدمات غير المتصلين وقرارات تُتخذ دون المعرفة أو التوجيه الصحيح. هدفنا هو تقليص هذه الفجوة بربط التفكير الاستراتيجي بالتنفيذ المهني."""

        about_defaults = {
            "title_en": "About AM Business",
            "title_fa": "درباره ای ام بیزینس",
            "title_ar": "عن إي إم بيزنس",
            "content_en": about_en,
            "content_fa": "ای ام بیزینس یک شرکت یکپارچه رشد و تحول کسب و کار مستقر در مسقط، عمان است که به کسب و کارهای بلندپرواز، بنیان‌گذاران، سازمان‌ها و نهادهای سراسر GCC خدمت رسانی می‌کند.",
            "content_ar": about_ar,
            "who_we_are_en": "AM Business was founded by Dr. Ashkan Masoumian as part of the AM International ecosystem.",
            "who_we_are_fa": "ای ام بیزینس توسط دکتر اشکان موسومیان به عنوان بخشی از اکوسیستم بین‌المللی تأسیس شده است.",
            "who_we_are_ar": "أسس إي إم بيزنس الدكتور أشكان معصوميان كجزء من منظومة إي إم الدولية.",
            "we_are_expert_en": "With Muscat as our base and the GCC as our primary strategic market, our ambition is to build AM Business into one of the region's most trusted and leading strategic growth partners.",
            "we_are_expert_fa": "با مسقط به عنوان پایگاه و GCC به عنوان بازار استراتژیک اصلی، هدف ما تبدیل ای ام بیزینس به یکی از معتبرترین شرکای رشد استراتژیک منطقه است.",
            "we_are_expert_ar": "انطلاقًا من مسقط كقاعدة لنا ومن دول مجلس التعاون الخليجي كسوقنا الاستراتيجي الأول، طموحنا أن نصبح أحد أكثر شركاء النمو الاستراتيجي ثقة وريادة في المنطقة.",
            "why_choose_us_title_en": "Why AM Business",
            "why_choose_us_title_fa": "چرا ای ام بیزینس",
            "why_choose_us_title_ar": "لماذا إي إم بيزنس",
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
            "why_choose_us_content_ar": """البحث قبل التوصية: نفهم النشاط والسوق والتحدي قبل أن نقترح حلًا.
الاستراتيجية قبل التنفيذ: التنفيذ يتبع اتجاهًا واضحًا ومنطقًا تجاريًا، لا العكس.
قدرات متكاملة: الاستراتيجية والإبداع والتسويق والرقمي والذكاء الاصطناعي تعمل كحل واحد منسّق.
إبداع يخدم الأعمال أولًا: العمل الإبداعي مصمم لخدمة هدف تجاري لا لإنتاج أصول جاذبة فقط.
الرقمي والذكاء الاصطناعي العملي: تُستخدم التقنية والذكاء الاصطناعي حيث تحسّن الكفاءة أو اتخاذ القرار أو تجربة العميل أو قابلية التوسع.
شراكة موجّهة بالنتائج: نركّز على قيمة الأعمال والنتائج الملموسة مع بناء علاقات طويلة الأمد.""",
            "cta_text_en": "Read More",
            "cta_text_fa": "بیشتر بخوانید",
            "cta_text_ar": "اقرأ المزيد",
            "cta_url": "/about/",
            "is_active": True,
        }
        about_obj = AboutSection.objects.first()
        if about_obj is None:
            AboutSection.objects.create(**about_defaults)
            self.stdout.write("  About: created")
        else:
            backfilled += len(apply_defaults(about_obj, about_defaults))
            self.stdout.write("  About: kept")

        # ── Home Sections ──
        _obj, _created, filled = upsert(
            HomeSection,
            {"section_type": "home_about"},
            {
                "title_en": "About AM Business",
                "title_fa": "درباره ای ام بیزینس",
                "title_ar": "عن إي إم بيزنس",
                "subheading_en": "About Us",
                "subheading_fa": "درباره ما",
                "subheading_ar": "من نحن",
                "content_en": about_en,
                "content_fa": "ای ام بیزینس یک شرکت یکپارچه رشد و تحول کسب و کار مستقر در مسقط، عمان است.",
                "content_ar": about_ar,
                "cta_text_en": "Read More",
                "cta_text_fa": "بیشتر بخوانید",
                "cta_text_ar": "اقرأ المزيد",
                "cta_url": "/about/",
                "is_active": True,
            },
        )
        backfilled += len(filled)
        self.stdout.write("  Home Sections: created")

        # ── Counters ──
        for i, (label_en, label_fa, label_ar, value) in enumerate([
            ("Projects Completed", "پروژه‌های تکمیل شده", "مشاريع مكتملة", 150),
            ("Happy Clients", "مشتریان راضی", "عملاء سعداء", 85),
            ("Team Members", "اعضای تیم", "أعضاء الفريق", 25),
            ("Awards", "جایزه‌ها", "جوائز", 12),
        ]):
            _obj, _created, filled = upsert(
                StatCounter,
                {"label_en": label_en},
                {"label_fa": label_fa, "label_ar": label_ar, "value": value,
                 "is_active": True, "order": i},
            )
            backfilled += len(filled)
        self.stdout.write("  Counters: created")

        # ── Features ──
        features_data = [
            ("Research", "تحقیق", "البحث",
             "Data-driven research to understand your market, competitors, and opportunities.",
             "تحقیق مبتنی بر داده برای درک بازار، رقبا و فرصت‌های شما.",
             "بحث قائم على البيانات لفهم سوقك ومنافسيك وفرصك."),
            ("Strategy", "استراتژی", "الاستراتيجية",
             "Clear strategic direction that aligns with your business goals.",
             "جهت استراتژیک روشن که با اهداف کسب و کار شما هماهنگ است.",
             "اتجاه استراتيجي واضح يتوافق مع أهداف عملك."),
            ("Execution", "اجرا", "التنفيذ",
             "Professional execution that turns strategy into measurable results.",
             "اجرای حرفه‌ای که استراتژی را به نتایج قابل اندازه‌گیری تبدیل می‌کند.",
             "تنفيذ مهني يحوّل الاستراتيجية إلى نتائج قابلة للقياس."),
        ]
        for i, (t_en, t_fa, t_ar, d_en, d_fa, d_ar) in enumerate(features_data):
            _obj, _created, filled = upsert(
                Feature,
                {"title_en": t_en},
                {"title_fa": t_fa, "title_ar": t_ar,
                 "description_en": d_en, "description_fa": d_fa, "description_ar": d_ar,
                 "is_active": True, "order": i},
            )
            backfilled += len(filled)
        self.stdout.write("  Features: created")

        # ── Pricing ──
        pricing_data = [
            ("Starter", "پایه", "المبتدئ",
             "Perfect for small projects and startups looking for a strong foundation.",
             "ایده‌آل برای پروژه‌های کوچک و استارتاپ‌ها.",
             "مثالية للمشاريع الصغيرة والشركات الناشئة التي تبحث عن أساس قوي.", "49"),
            ("Growth", "رشد", "النمو",
             "Ideal for growing businesses needing integrated capabilities.",
             "مناسب برای کسب و کارهای در حال رشد.",
             "مثالية للشركات النامية التي تحتاج إلى قدرات متكاملة.", "199"),
            ("Enterprise", "سازمانی", "المؤسسات",
             "Comprehensive solution for large organizations with complex needs.",
             "راهکار جامع برای سازمان‌های بزرگ.",
             "حل شامل للمؤسسات الكبيرة ذات الاحتياجات المعقدة.", "975"),
        ]
        for i, (n_en, n_fa, n_ar, d_en, d_fa, d_ar, price) in enumerate(pricing_data):
            _obj, _created, filled = upsert(
                PricingPlan,
                {"name_en": n_en},
                {
                    "name_fa": n_fa, "name_ar": n_ar,
                    "description_en": d_en, "description_fa": d_fa, "description_ar": d_ar,
                    "price": price, "currency": "$", "cents": ".99",
                    "button_text_en": "Get Started", "button_text_fa": "شروع کنید",
                    "button_text_ar": "ابدأ الآن",
                    "button_url": "/contact/", "is_active": True, "order": i,
                },
            )
            backfilled += len(filled)
        self.stdout.write("  Pricing: created")

        # ── Testimonials ──
        testimonials_data = [
            ("Dr. Ahmed Al-Rashid", "CEO @Gulf Ventures", "مدیرعامل @گالف ونچرز",
             "الرئيس التنفيذي @غلف فينتشرز",
             "AM Business brought clarity to our growth strategy. Their integrated approach saved us time and delivered results we didn't expect.",
             "ای ام بیزینس وضوح به استراتژی رشد ما بخشید. رویکرد یکپارچه آن‌ها زمان ما را ذخیره کرد.",
             "أضافت إي إم بيزنس وضوحًا إلى استراتيجية نموّنا. وفر منهجهم المتكامل وقتنا وحقق نتائج لم نكن نتوقعها."),
            ("Sarah Mitchell", "Marketing Director @TechHub Oman", "مدیر بازاریابی @تک‌هاب عمان",
             "مديرة التسويق @تك هب عُمان",
             "Outstanding strategic thinking combined with creative execution. AM Business is our trusted growth partner.",
             "تفکر استراتژیک برجسته همراه با اجرای خلاقانه. ای ام بیزینس شریک رشد قابل اعتماد ماست.",
             "تفكير استراتيجي متميز مقرون بتنفيذ إبداعي. إي إم بيزنس شريك النمو الموثوق لدينا."),
        ]
        for i, (name, role_en, role_fa, role_ar, q_en, q_fa, q_ar) in enumerate(testimonials_data):
            _obj, _created, filled = upsert(
                Testimonial,
                {"author_name": name},
                {
                    "quote_en": q_en, "quote_fa": q_fa, "quote_ar": q_ar,
                    "author_role_en": role_en, "author_role_fa": role_fa, "author_role_ar": role_ar,
                    "is_active": True, "order": i,
                },
            )
            backfilled += len(filled)
        self.stdout.write("  Testimonials: created")

        # ── Team ──
        team_data = [
            ("Dr. Ashkan Masoumian", "Founder & CEO", "بنیانگذار و مدیرعامل", "المؤسس والرئيس التنفيذي",
             "Executive and board-level experience in pharmaceutical and manufacturing business, international commercial experience, MBA, DBA, and Post-DBA studies.",
             "تجربه اجرایی و هیئت مدیره در کسب و کار دارویی و تولیدی.",
             "خبرة تنفيذية وعلى مستوى مجلس الإدارة في قطاع الأدوية والتصنيع، وخبرة تجارية دولية، وماجستير إدارة أعمال ودكتوراه ودراسات ما بعد الدكتوراه."),
        ]
        for i, (name, pos_en, pos_fa, pos_ar, bio_en, bio_fa, bio_ar) in enumerate(team_data):
            _obj, _created, filled = upsert(
                TeamMember,
                {"name": name},
                {
                    "position_en": pos_en, "position_fa": pos_fa, "position_ar": pos_ar,
                    "bio_en": bio_en, "bio_fa": bio_fa, "bio_ar": bio_ar,
                    "is_active": True, "order": i,
                },
            )
            backfilled += len(filled)
        self.stdout.write("  Team: created")

        # ── Event Countdown (kept inactive) ──
        event_defaults = {
            "title_en": "Event Countdown", "title_fa": "شمارش معکوس رویداد",
            "title_ar": "العد التنازلي للحدث",
            "subheading_en": "Don't wait", "subheading_fa": "منتظر نمانید",
            "subheading_ar": "لا تنتظر",
            "event_date": timezone.now() + timedelta(days=39, hours=27),
            "ended_message_en": "We are sorry, Event ended!",
            "ended_message_fa": "متأسفیم، رویداد تمام شده است!",
            "ended_message_ar": "نأسف، انتهى الحدث!",
            "cta_text_en": "Get Started", "cta_text_fa": "شروع کنید",
            "cta_text_ar": "ابدأ الآن",
            "cta_url": "#", "is_active": False,
        }
        countdown = EventCountdown.objects.first()
        if countdown is None:
            EventCountdown.objects.create(**event_defaults)
            self.stdout.write("  Countdown: created (inactive)")
        else:
            backfilled += len(apply_defaults(countdown, event_defaults))
            self.stdout.write("  Countdown: kept")

        if backfilled:
            self.stdout.write(self.style.WARNING(
                f"\n{backfilled} empty translation field(s) filled in on existing rows."))
        self.stdout.write(self.style.SUCCESS("Done! Database seeded with AM Business content."))
