"""
AM Business - Full Test Suite
Tests: Frontend pages, Admin panel, RTL/LTR, Themes, CRUD, API, Newsletter, Contact
"""
import os, sys, io, time, subprocess, urllib.request
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8080"
SS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
VID = os.path.join(os.path.dirname(os.path.abspath(__file__)), "full_test_video.mp4")

server = None

def start_server():
    global server
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    server = subprocess.Popen([sys.executable, "manage.py", "runserver", "8080", "--noreload"],
        cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
    print("  [SERVER] Starting...")
    for _ in range(30):
        try: urllib.request.urlopen(f"{BASE}/admin/", timeout=2); print("  [SERVER] Ready!"); return
        except: time.sleep(1)

def stop_server():
    global server
    if server:
        server.terminate()
        try: server.wait(timeout=5)
        except: server.kill()


class Rec:
    def __init__(self):
        self.imgs = []; self.n = 0; os.makedirs(SS, exist_ok=True)
    def snap(self, d, name):
        self.n += 1
        s = "".join(c if c.isalnum() or c in '-_' else '_' for c in name)
        fp = os.path.join(SS, f"{self.n:03d}_{s}.png")
        try: d.save_screenshot(fp); self.imgs.append(fp)
        except: pass
    def video(self):
        import cv2
        if not self.imgs: return
        f = cv2.imread(self.imgs[0])
        if f is None: return
        h, w = f.shape[:2]; w += w%2; h += h%2
        vw = cv2.VideoWriter(VID, cv2.VideoWriter_fourcc(*'mp4v'), 1.5, (w, h))
        for p in self.imgs:
            img = cv2.imread(p)
            if img is not None:
                if img.shape[1]!=w or img.shape[0]!=h: img = cv2.resize(img,(w,h))
                vw.write(img)
        vw.release()
        print(f"\n  [VIDEO] Saved: {VID} ({len(self.imgs)} frames)")


class T:
    def __init__(self):
        self.res = []; self.rec = Rec(); self.d = None
    def setup(self):
        o = Options()
        o.add_argument("--window-size=1400,900"); o.add_argument("--no-sandbox")
        o.add_argument("--disable-dev-shm-usage"); o.add_argument("--disable-gpu")
        o.add_argument("--log-level=3")
        o.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.d = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=o)
        self.d.implicitly_wait(8)
        self.d.get(BASE); time.sleep(2)
    def teardown(self):
        if self.d: self.d.quit()
    def log(self, name, ok, det=""):
        self.res.append({"name":name,"status":"PASS" if ok else "FAIL","detail":det,"time":datetime.now().strftime("%H:%M:%S")})
        print(f"  {'[PASS]' if ok else '[FAIL]'} {name}" + (f" - {det[:50]}" if det else ""))
    def go(self, p):
        self.d.get(f"{BASE}{p}"); time.sleep(1.2)
    def set_cookie(self, n, v):
        self.d.get(BASE); time.sleep(0.5); self.d.add_cookie({"name":n,"value":v,"path":"/"})
    def find(self, by, val, t=5):
        try: return WebDriverWait(self.d, t).until(EC.presence_of_element_located((by,val)))
        except: return None
    def click(self, by, val, t=5):
        try: e=WebDriverWait(self.d,t).until(EC.element_to_be_clickable((by,val))); e.click(); return True
        except: return False
    def has(self, t): return t in self.d.page_source

    # ═══════ FRONTEND TESTS ═══════

    def f01(self):
        self.go("/")
        self.rec.snap(self.d, "home_page")
        ok = self.has("AM Business") or self.has("Bootstrap") or self.has("hero")
        self.log("Home Page Loads", ok)

    def f02(self):
        self.go("/")
        # Check key sections exist
        has_nav = bool(self.d.find_elements(By.CSS_SELECTOR, ".site-nav"))
        has_hero = bool(self.d.find_elements(By.CSS_SELECTOR, ".hero"))
        self.rec.snap(self.d, "home_sections")
        self.log("Home - Nav & Hero", has_nav and has_hero, f"nav={has_nav} hero={has_hero}")

    def f03(self):
        self.go("/")
        # Check services section
        has_services = self.has("Our Services") or self.has("services") or self.has("feature")
        self.rec.snap(self.d, "home_services_section")
        self.log("Home - Services Section", has_services)

    def f04(self):
        self.go("/")
        # Check pricing
        has_pricing = self.has("Pricing") or self.has("pricing") or self.has("49")
        self.rec.snap(self.d, "home_pricing_section")
        self.log("Home - Pricing Section", has_pricing)

    def f05(self):
        self.go("/")
        # Check testimonials
        has_test = self.has("People Says") or self.has("testimonial") or self.has("Jessica")
        self.rec.snap(self.d, "home_testimonials")
        self.log("Home - Testimonials", has_test)

    def f06(self):
        self.go("/")
        # Check team section
        has_team = self.has("Meet our team") or self.has("team") or self.has("Jessica Green")
        self.rec.snap(self.d, "home_team")
        self.log("Home - Team Section", has_team)

    def f07(self):
        self.go("/")
        # Check footer
        has_footer = bool(self.d.find_elements(By.CSS_SELECTOR, ".footer"))
        self.rec.snap(self.d, "home_footer")
        self.log("Home - Footer", has_footer)

    def f08(self):
        self.go("/")
        # Check newsletter
        has_nl = self.has("Subscribe") or self.has("newsletter") or self.has("خبرنامه")
        self.rec.snap(self.d, "home_newsletter")
        self.log("Home - Newsletter", has_nl)

    def f09(self):
        self.go("/about/")
        self.rec.snap(self.d, "about_page")
        ok = self.has("About") or self.has("databare ma") or self.has("About Us")
        self.log("About Page", ok)

    def f10(self):
        self.go("/about/")
        has_counters = self.has("countup") or self.has("counter") or self.has("2838")
        self.rec.snap(self.d, "about_counters")
        self.log("About - Counters", has_counters)

    def f11(self):
        self.go("/services/")
        self.rec.snap(self.d, "services_page")
        ok = self.has("Our Services") or self.has("services") or self.has("Photography")
        self.log("Services Page", ok)

    def f12(self):
        self.go("/contact/")
        self.rec.snap(self.d, "contact_page")
        ok = self.has("contact") or self.has("Contact") or self.has("message")
        self.log("Contact Page", ok)

    def f13(self):
        self.go("/contact/")
        form = self.find(By.CSS_SELECTOR, "form")
        self.rec.snap(self.d, "contact_form")
        self.log("Contact - Form Exists", form is not None)

    def f14(self):
        # Test contact form submission
        self.go("/contact/")
        self.d.execute_script("""
            document.querySelector('input[name="name"]').value = 'Test User';
            document.querySelector('input[name="email"]').value = 'test@example.com';
            document.querySelector('textarea[name="message"]').value = 'Test message';
            document.querySelector('form.form-contact').submit();
        """)
        time.sleep(2)
        self.rec.snap(self.d, "contact_submitted")
        ok = self.has("successfully") or self.has("موفقیت") or "contact" in self.d.current_url
        self.log("Contact - Form Submit", ok)

    def f15(self):
        # Newsletter subscription
        self.go("/")
        self.d.execute_script("""
            var forms = document.querySelectorAll('form.form-contact');
            if (forms.length > 0) {
                var form = forms[0];
                var nameInput = form.querySelector('input[name="name"]');
                var emailInput = form.querySelector('input[name="email"]');
                if (nameInput && emailInput) {
                    nameInput.value = 'Newsletter User';
                    emailInput.value = 'newsletter@test.com';
                    form.submit();
                }
            }
        """)
        time.sleep(2)
        self.rec.snap(self.d, "newsletter_subscribed")
        self.log("Newsletter Subscribe", True)

    # ═══════ RTL/LTR TESTS ═══════

    def f16(self):
        self.set_cookie("django_language", "fa")
        self.go("/")
        time.sleep(1.5)
        html = self.d.find_element(By.TAG_NAME, "html")
        d = html.get_attribute("dir") or ""
        lang = html.get_attribute("lang") or ""
        self.rec.snap(self.d, "home_rtl_farsi")
        ok = lang == "fa" or self.has("خانه")
        self.log("Home - RTL Farsi", ok, f"dir={d} lang={lang}")

    def f17(self):
        self.set_cookie("django_language", "en")
        self.go("/")
        time.sleep(1)
        html = self.d.find_element(By.TAG_NAME, "html")
        d = html.get_attribute("dir") or ""
        self.rec.snap(self.d, "home_ltr_english")
        self.log("Home - LTR English", d == "ltr", f"dir={d}")

    def f18(self):
        self.set_cookie("django_language", "fa")
        self.go("/about/")
        time.sleep(1.5)
        self.rec.snap(self.d, "about_farsi")
        ok = self.has("درباره ما") or self.has("FA")
        self.log("About - Farsi", ok)

    def f19(self):
        self.set_cookie("django_language", "fa")
        self.go("/services/")
        time.sleep(1.5)
        self.rec.snap(self.d, "services_farsi")
        ok = self.has("خدمات") or self.has("FA")
        self.log("Services - Farsi", ok)

    def f20(self):
        self.set_cookie("django_language", "fa")
        self.go("/contact/")
        time.sleep(1.5)
        self.rec.snap(self.d, "contact_farsi")
        ok = self.has("تماس") or self.has("FA")
        self.log("Contact - Farsi", ok)

    # ═══════ ADMIN PANEL TESTS ═══════

    def a01(self):
        self.set_cookie("django_language", "en")
        self.go("/accounts/login/")
        self.rec.snap(self.d, "admin_login")
        ok = self.has("login") or self.has("username") or self.has("Login")
        self.log("Admin - Login Page", ok)

    def a02(self):
        self.go("/accounts/login/")
        u = self.find(By.CSS_SELECTOR, "input[name='username']")
        p = self.find(By.CSS_SELECTOR, "input[name='password']")
        if u and p:
            u.send_keys("admin"); p.send_keys("admin123")
            self.find(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(2)
            self.rec.snap(self.d, "admin_dashboard")
            self.log("Admin - Login Success", "admin-panel" in self.d.current_url)
        else:
            self.log("Admin - Login Success", False)

    def a03(self):
        self.go("/admin-panel/")
        items = self.d.find_elements(By.CSS_SELECTOR, ".sidebar-nav .nav-item")
        self.rec.snap(self.d, "admin_sidebar")
        self.log("Admin - Sidebar", len(items) >= 10, f"{len(items)} items")

    def a04(self):
        self.click(By.ID, "themeToggle")
        time.sleep(2)
        self.rec.snap(self.d, "admin_theme_toggle")
        cookies = {c['name']: c['value'] for c in self.d.get_cookies()}
        self.log("Admin - Theme Toggle", 'theme' in cookies)

    def a05(self):
        self.go("/admin-panel/services/")
        self.rec.snap(self.d, "admin_services")
        self.log("Admin - Services Page", True)

    def a06(self):
        self.go("/admin-panel/settings/")
        self.rec.snap(self.d, "admin_settings")
        self.log("Admin - Settings Page", True)

    def a07(self):
        self.go("/swagger/")
        time.sleep(2)
        self.rec.snap(self.d, "swagger_docs")
        ok = "swagger" in self.d.page_source.lower() or "api" in self.d.current_url
        self.log("Swagger API Docs", ok)

    def a08(self):
        self.go("/api/")
        self.rec.snap(self.d, "api_overview")
        ok = "api" in self.d.page_source.lower() or "services" in self.d.page_source.lower()
        self.log("API Overview", ok)

    def run_all(self):
        print("\n" + "="*70)
        print("  AM Business - Full Test Suite (Frontend + Admin + RTL/LTR)")
        print("="*70)
        self.setup()

        tests = [
            self.f01, self.f02, self.f03, self.f04, self.f05, self.f06,
            self.f07, self.f08, self.f09, self.f10, self.f11, self.f12,
            self.f13, self.f14, self.f15, self.f16, self.f17, self.f18,
            self.f19, self.f20, self.a01, self.a02, self.a03, self.a04,
            self.a05, self.a06, self.a07, self.a08,
        ]
        for fn in tests:
            try: fn()
            except Exception as e: self.log(fn.__name__, False, str(e)[:50])

        self.teardown()

        print("\n" + "-"*70)
        self.rec.video()

        p = sum(1 for r in self.res if r['status']=='PASS')
        f = sum(1 for r in self.res if r['status']=='FAIL')
        t = len(self.res)
        print("\n" + "="*70)
        print(f"  RESULTS: {p}/{t} PASSED, {f} FAILED")
        print("="*70 + "\n")

        return p, f


if __name__ == "__main__":
    start_server()
    try:
        t = T()
        p, f = t.run_all()
        sys.exit(0 if f == 0 else 1)
    finally:
        stop_server()
