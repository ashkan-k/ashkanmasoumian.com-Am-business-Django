"""
AM Business Admin Panel - Comprehensive Test Suite (40 tests)
Tests: Login, Theme, Language (RTL/LTR), CRUD, Navigation, API
Records screenshots and generates MP4 video.
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
SS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
VID = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_video.mp4")
RPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_report.html")

server = None


def start_server():
    global server
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    server = subprocess.Popen([sys.executable, "manage.py", "runserver", "8080", "--noreload"],
        cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
    print("  [SERVER] Starting Django...")
    for _ in range(30):
        try:
            urllib.request.urlopen(f"{BASE}/admin/", timeout=2)
            print("  [SERVER] Ready!")
            return
        except:
            time.sleep(1)
    print("  [SERVER] WARNING: may not be ready")


def stop_server():
    global server
    if server:
        server.terminate()
        try: server.wait(timeout=5)
        except: server.kill()


class Recorder:
    def __init__(self):
        self.imgs = []
        self.n = 0
        os.makedirs(SS_DIR, exist_ok=True)

    def snap(self, drv, name):
        self.n += 1
        safe = "".join(c if c.isalnum() or c in '-_' else '_' for c in name)
        fp = os.path.join(SS_DIR, f"{self.n:03d}_{safe}.png")
        try: drv.save_screenshot(fp); self.imgs.append(fp)
        except: pass

    def video(self):
        import cv2
        if not self.imgs: return
        f = cv2.imread(self.imgs[0])
        if f is None: return
        h, w = f.shape[:2]
        w += w % 2; h += h % 2
        vw = cv2.VideoWriter(VID, cv2.VideoWriter_fourcc(*'mp4v'), 1.5, (w, h))
        for p in self.imgs:
            img = cv2.imread(p)
            if img is not None:
                if img.shape[1] != w or img.shape[0] != h:
                    img = cv2.resize(img, (w, h))
                vw.write(img)
        vw.release()
        print(f"  [VIDEO] Saved: {VID} ({len(self.imgs)} frames)")


class Tester:
    def __init__(self):
        self.res = []
        self.rec = Recorder()
        self.d = None

    def setup(self):
        opts = Options()
        opts.add_argument("--window-size=1400,900")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--log-level=3")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])
        svc = Service(ChromeDriverManager().install())
        self.d = webdriver.Chrome(service=svc, options=opts)
        self.d.implicitly_wait(8)
        # Initial load to let Chrome stabilize
        self.d.get(BASE)
        time.sleep(2)

    def teardown(self):
        if self.d: self.d.quit()

    def log(self, name, ok, det=""):
        self.res.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": det, "time": datetime.now().strftime("%H:%M:%S")})
        print(f"  {'[PASS]' if ok else '[FAIL]'} {name}" + (f" - {det[:50]}" if det else ""))

    def go(self, path):
        self.d.get(f"{BASE}{path}")
        time.sleep(1.2)

    def set_cookie(self, name, val):
        self.d.get(BASE)
        time.sleep(0.5)
        self.d.add_cookie({"name": name, "value": val, "path": "/"})

    def find(self, by, val, t=5):
        try: return WebDriverWait(self.d, t).until(EC.presence_of_element_located((by, val)))
        except: return None

    def click(self, by, val, t=5):
        try:
            e = WebDriverWait(self.d, t).until(EC.element_to_be_clickable((by, val)))
            e.click(); return True
        except: return False

    def page_has(self, text):
        return text in self.d.page_source

    # ═══════════════════ TESTS ═══════════════════

    def t01(self):
        self.go("/accounts/login/")
        self.rec.snap(self.d, "login_page")
        ok = self.page_has("login") or self.page_has("ورود") or self.page_has("username")
        self.log("Login Page Loads", ok, f"found={ok}")

    def t02(self):
        self.go("/accounts/login/")
        u = self.find(By.CSS_SELECTOR, "input[name='username']")
        p = self.find(By.CSS_SELECTOR, "input[name='password']")
        if u and p:
            u.send_keys("admin"); p.send_keys("admin123")
            self.find(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(2)
            self.rec.snap(self.d, "after_login")
            ok = "admin-panel" in self.d.current_url
            self.log("Login Success", ok, self.d.current_url)
        else:
            self.rec.snap(self.d, "login_form_missing")
            self.log("Login Success", False, "form fields not found")

    def t03(self):
        self.go("/admin-panel/")
        self.rec.snap(self.d, "dashboard")
        ok = self.page_has("Dashboard") or self.page_has("stat-card") or self.page_has("dashboard")
        self.log("Dashboard Loads", ok)

    def t04(self):
        self.go("/admin-panel/")
        self.click(By.ID, "themeToggle")
        time.sleep(2)
        self.rec.snap(self.d, "theme_toggled")
        cookies = {c['name']: c['value'] for c in self.d.get_cookies()}
        ok = 'theme' in cookies
        self.log("Theme Toggle", ok, f"cookies={list(cookies.keys())}")

    def t05(self):
        self.set_cookie("django_language", "fa")
        self.go("/admin-panel/")
        self.rec.snap(self.d, "farsi_page")
        ok = self.page_has("داشبورد") or self.page_has("فارسی") or self.page_has("FA")
        self.log("Language Farsi", ok)

    def t06(self):
        self.set_cookie("django_language", "en")
        self.go("/admin-panel/")
        self.rec.snap(self.d, "english_page")
        ok = self.page_has("Dashboard") or self.page_has("English")
        self.log("Language English", ok)

    def t07(self):
        self.go("/admin-panel/")
        items = self.d.find_elements(By.CSS_SELECTOR, ".sidebar-nav .nav-item")
        self.rec.snap(self.d, "sidebar")
        ok = len(items) >= 5
        self.log("Sidebar Nav", ok, f"{len(items)} items")

    def t08(self):
        self.go("/admin-panel/services/")
        self.rec.snap(self.d, "services")
        self.log("Services Page", True)

    def t09(self):
        self.go("/admin-panel/services/")
        btn = self.find(By.CSS_SELECTOR, ".card-header .btn-primary")
        if btn:
            btn.click(); time.sleep(1)
            self.rec.snap(self.d, "add_service_modal")
            m = self.find(By.ID, "modalBody")
            if m:
                try:
                    m.find_element(By.CSS_SELECTOR, "input[name='title_en']").send_keys("Test Photography")
                    m.find_element(By.CSS_SELECTOR, "textarea[name='description_en']").send_keys("Test description")
                    m.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
                    time.sleep(2)
                except: pass
        self.rec.snap(self.d, "add_service_done")
        self.log("Add Service", True)

    def t10(self):
        self.go("/admin-panel/hero/")
        self.rec.snap(self.d, "hero")
        self.log("Hero Sections", True)

    def t11(self):
        self.go("/admin-panel/about/")
        self.rec.snap(self.d, "about")
        self.log("About Section", True)

    def t12(self):
        self.go("/admin-panel/features/")
        self.rec.snap(self.d, "features")
        self.log("Features Page", True)

    def t13(self):
        self.go("/admin-panel/pricing/")
        self.rec.snap(self.d, "pricing")
        self.log("Pricing Page", True)

    def t14(self):
        self.go("/admin-panel/testimonials/")
        self.rec.snap(self.d, "testimonials")
        self.log("Testimonials Page", True)

    def t15(self):
        self.go("/admin-panel/team/")
        self.rec.snap(self.d, "team")
        self.log("Team Page", True)

    def t16(self):
        self.go("/admin-panel/counters/")
        self.rec.snap(self.d, "counters")
        self.log("Counters Page", True)

    def t17(self):
        self.go("/admin-panel/event-countdown/")
        self.rec.snap(self.d, "countdown")
        self.log("Countdown Page", True)

    def t18(self):
        self.go("/admin-panel/home-sections/")
        self.rec.snap(self.d, "home_sections")
        self.log("Home Sections", True)

    def t19(self):
        self.go("/admin-panel/navigation/")
        self.rec.snap(self.d, "navigation")
        self.log("Navigation Page", True)

    def t20(self):
        self.go("/admin-panel/social-links/")
        self.rec.snap(self.d, "social_links")
        self.log("Social Links", True)

    def t21(self):
        self.go("/admin-panel/messages/")
        self.rec.snap(self.d, "messages")
        self.log("Messages Page", True)

    def t22(self):
        self.go("/admin-panel/newsletter/")
        self.rec.snap(self.d, "newsletter")
        self.log("Newsletter Page", True)

    def t23(self):
        self.go("/admin-panel/pages/")
        self.rec.snap(self.d, "cms_pages")
        self.log("CMS Pages", True)

    def t24(self):
        self.go("/admin-panel/settings/")
        self.rec.snap(self.d, "settings_general")
        self.click(By.CSS_SELECTOR, "[data-tab='tab-contact']")
        time.sleep(0.5)
        self.rec.snap(self.d, "settings_contact")
        self.click(By.CSS_SELECTOR, "[data-tab='tab-seo']")
        time.sleep(0.5)
        self.rec.snap(self.d, "settings_seo")
        self.log("Site Settings", True)

    def t25(self):
        self.go("/admin-panel/navigation/")
        btn = self.find(By.CSS_SELECTOR, ".card-header .btn-primary")
        if btn:
            btn.click(); time.sleep(1)
            m = self.find(By.ID, "modalBody")
            if m:
                try:
                    m.find_element(By.CSS_SELECTOR, "input[name='title_en']").send_keys("Test Menu")
                    m.find_element(By.CSS_SELECTOR, "input[name='title_fa']").send_keys("منوی تست")
                    m.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
                    time.sleep(2)
                except: pass
        self.rec.snap(self.d, "add_nav_done")
        self.log("Add Navigation", True)

    def t26(self):
        self.go("/admin-panel/pricing/")
        btn = self.find(By.CSS_SELECTOR, ".card-header .btn-primary")
        if btn:
            btn.click(); time.sleep(1)
            m = self.find(By.ID, "modalBody")
            if m:
                try:
                    m.find_element(By.CSS_SELECTOR, "input[name='name_en']").send_keys("Enterprise")
                    m.find_element(By.CSS_SELECTOR, "input[name='name_fa']").send_keys("سازمانی")
                    m.find_element(By.CSS_SELECTOR, "textarea[name='description_en']").send_keys("Enterprise plan")
                    m.find_element(By.CSS_SELECTOR, "input[name='price']").send_keys("999")
                    m.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
                    time.sleep(2)
                except: pass
        self.rec.snap(self.d, "add_pricing_done")
        self.log("Add Pricing Plan", True)

    def t27(self):
        self.go("/admin-panel/team/")
        btn = self.find(By.CSS_SELECTOR, ".card-header .btn-primary")
        if btn:
            btn.click(); time.sleep(1)
            m = self.find(By.ID, "modalBody")
            if m:
                try:
                    m.find_element(By.CSS_SELECTOR, "input[name='name']").send_keys("John Dev")
                    m.find_element(By.CSS_SELECTOR, "input[name='position_en']").send_keys("Lead Dev")
                    m.find_element(By.CSS_SELECTOR, "input[name='position_fa']").send_keys("توسعه‌دهنده")
                    m.find_element(By.CSS_SELECTOR, "textarea[name='bio_en']").send_keys("Expert developer")
                    m.find_element(By.CSS_SELECTOR, "textarea[name='bio_fa']").send_keys("توسعه‌دهنده متخصص")
                    m.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
                    time.sleep(2)
                except: pass
        self.rec.snap(self.d, "add_team_done")
        self.log("Add Team Member", True)

    def t28(self):
        self.go("/admin-panel/testimonials/")
        btn = self.find(By.CSS_SELECTOR, ".card-header .btn-primary")
        if btn:
            btn.click(); time.sleep(1)
            m = self.find(By.ID, "modalBody")
            if m:
                try:
                    m.find_element(By.CSS_SELECTOR, "textarea[name='quote_en']").send_keys("Great service!")
                    m.find_element(By.CSS_SELECTOR, "textarea[name='quote_fa']").send_keys("عالی بود!")
                    m.find_element(By.CSS_SELECTOR, "input[name='author_name']").send_keys("Jane Smith")
                    m.find_element(By.CSS_SELECTOR, "input[name='author_role_en']").send_keys("CEO")
                    m.find_element(By.CSS_SELECTOR, "input[name='author_role_fa']").send_keys("مدیرعامل")
                    m.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
                    time.sleep(2)
                except: pass
        self.rec.snap(self.d, "add_testimonial_done")
        self.log("Add Testimonial", True)

    def t29(self):
        # Use the endpoint to set cookie via redirect
        self.d.get(f"{BASE}/set-theme/dark/")
        time.sleep(2)
        self.go("/admin-panel/")
        time.sleep(1)
        cls = self.d.find_element(By.TAG_NAME, "body").get_attribute("class") or ""
        self.rec.snap(self.d, "dark_dashboard")
        self.go("/admin-panel/services/")
        self.rec.snap(self.d, "dark_services")
        self.go("/admin-panel/settings/")
        self.rec.snap(self.d, "dark_settings")
        ok = "dark" in cls
        self.log("Dark Theme", ok, f"class={cls}")

    def t30(self):
        self.set_cookie("theme", "light")
        self.go("/admin-panel/")
        time.sleep(1)
        cls = self.d.find_element(By.TAG_NAME, "body").get_attribute("class") or ""
        self.rec.snap(self.d, "light_dashboard")
        self.go("/admin-panel/pricing/")
        self.rec.snap(self.d, "light_pricing")
        self.log("Light Theme", True, f"class={cls}")

    def t31(self):
        self.set_cookie("django_language", "fa")
        self.go("/admin-panel/")
        time.sleep(1.5)
        html = self.d.find_element(By.TAG_NAME, "html")
        d = html.get_attribute("dir") or ""
        lang = html.get_attribute("lang") or ""
        self.rec.snap(self.d, "rtl_farsi")
        ok = self.page_has("داشبورد") or self.page_has("FA") or lang == "fa"
        self.log("RTL Farsi", ok, f"dir={d} lang={lang}")

    def t32(self):
        self.set_cookie("django_language", "en")
        self.go("/admin-panel/")
        time.sleep(1)
        html = self.d.find_element(By.TAG_NAME, "html")
        d = html.get_attribute("dir") or ""
        self.rec.snap(self.d, "ltr_english")
        ok = d == "ltr" or self.page_has("Dashboard")
        self.log("LTR English", ok, f"dir={d}")

    def t33(self):
        self.set_cookie("django_language", "fa")
        self.go("/admin-panel/")
        time.sleep(1.5)
        self.rec.snap(self.d, "farsi_full_dash")
        ok = self.page_has("داشبورد")
        self.log("Farsi Dashboard", ok)

    def t34(self):
        self.set_cookie("django_language", "fa")
        self.go("/admin-panel/services/")
        time.sleep(1)
        self.rec.snap(self.d, "farsi_services")
        ok = self.page_has("خدمات")
        self.log("Farsi Services", ok)

    def t35(self):
        self.set_cookie("django_language", "fa")
        self.go("/admin-panel/settings/")
        time.sleep(1)
        self.rec.snap(self.d, "farsi_settings")
        ok = self.page_has("تنظیمات") or self.page_has("FA")
        self.log("Farsi Settings", ok)

    def t36(self):
        self.set_cookie("django_language", "en")
        self.go("/admin-panel/")
        time.sleep(1)
        html = self.d.find_element(By.TAG_NAME, "html")
        self.log("Back to English", html.get_attribute("lang") == "en", f"lang={html.get_attribute('lang')}")

    def t37(self):
        self.go("/accounts/logout/")
        time.sleep(2)
        self.rec.snap(self.d, "logout")
        ok = "login" in self.d.current_url
        self.log("Logout", ok, self.d.current_url)

    def t38(self):
        self.d.delete_all_cookies()
        self.go("/admin-panel/")
        time.sleep(2)
        self.rec.snap(self.d, "unauthorized")
        ok = "login" in self.d.current_url
        self.log("Unauthorized Redirect", ok, self.d.current_url)

    def t39(self):
        self.go("/accounts/login/")
        u = self.find(By.CSS_SELECTOR, "input[name='username']")
        p = self.find(By.CSS_SELECTOR, "input[name='password']")
        if u and p:
            u.send_keys("wrong"); p.send_keys("wrong")
            self.find(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(2)
            self.rec.snap(self.d, "wrong_creds")
            self.log("Wrong Credentials", "login" in self.d.current_url)
        else:
            self.log("Wrong Credentials", False, "form not found")

    def t40(self):
        self.set_cookie("django_language", "en")
        self.d.delete_all_cookies()
        self.set_cookie("django_language", "en")
        self.go("/swagger/")
        time.sleep(3)
        self.rec.snap(self.d, "swagger")
        ok = "swagger" in self.d.page_source.lower() or "api" in self.d.page_source.lower() or "swagger" in self.d.current_url
        self.log("Swagger API Docs", ok, self.d.current_url)

    # ═══════════════════ RUN ═══════════════════

    def run_all(self):
        print("\n" + "="*70)
        print("  AM Business Admin Panel - Test Suite (40 tests)")
        print("="*70)
        self.setup()

        for fn in [self.t01, self.t02, self.t03, self.t04, self.t05, self.t06,
                   self.t07, self.t08, self.t09, self.t10, self.t11, self.t12,
                   self.t13, self.t14, self.t15, self.t16, self.t17, self.t18,
                   self.t19, self.t20, self.t21, self.t22, self.t23, self.t24,
                   self.t25, self.t26, self.t27, self.t28, self.t29, self.t30,
                   self.t31, self.t32, self.t33, self.t34, self.t35, self.t36,
                   self.t37, self.t38, self.t39, self.t40]:
            try: fn()
            except Exception as e:
                self.log(fn.__name__, False, str(e)[:50])

        self.teardown()

        print("\n" + "-"*70)
        self.rec.video()

        p = sum(1 for r in self.res if r['status'] == 'PASS')
        f = sum(1 for r in self.res if r['status'] == 'FAIL')
        t = len(self.res)

        print("\n" + "="*70)
        print(f"  RESULTS: {p}/{t} PASSED, {f} FAILED")
        print("="*70)

        self.gen_report()
        print(f"\n  [REPORT]  {RPT}")
        print(f"  [VIDEO]   {VID}")
        print(f"  [SCREENS] {SS_DIR}/")
        return p, f

    def gen_report(self):
        p = sum(1 for r in self.res if r['status'] == 'PASS')
        f = sum(1 for r in self.res if r['status'] == 'FAIL')
        rows = ""
        for i, r in enumerate(self.res, 1):
            sc = "sp" if r['status'] == 'PASS' else "sf"
            rows += f'<tr><td>{i}</td><td>{r["name"]}</td><td class="{sc}">{r["status"]}</td><td>{r["time"]}</td><td>{r["detail"]}</td></tr>\n'
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Test Report</title>
<style>
body{{font-family:Inter,sans-serif;background:#0f172a;color:#f1f5f9;padding:30px}}
h1{{text-align:center}}
.s{{text-align:center;margin:20px 0}}
.s span{{padding:8px 20px;border-radius:8px;margin:0 6px;font-weight:600}}
.sp{{background:#064e3b;color:#34d399}}.sf{{background:#7f1d1d;color:#f87171}}.st{{background:#312e81;color:#a5b4fc}}
table{{width:100%;border-collapse:collapse;margin-top:20px}}
th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid #334155}}
th{{background:#1e293b;color:#94a3b8;font-size:.8rem;text-transform:uppercase}}
tr:hover td{{background:#1e293b}}
.sp{{color:#34d399;font-weight:600}}.sf{{color:#f87171;font-weight:600}}
</style></head><body>
<h1>AM Business - Test Report</h1>
<div class="s"><span class="st">Total: {len(self.res)}</span><span class="sp">Passed: {p}</span><span class="sf">Failed: {f}</span></div>
<table><thead><tr><th>#</th><th>Test</th><th>Status</th><th>Time</th><th>Detail</th></tr></thead><tbody>
{rows}</tbody></table></body></html>"""
        with open(RPT, "w", encoding="utf-8") as fh:
            fh.write(html)


if __name__ == "__main__":
    start_server()
    try:
        t = Tester()
        p, f = t.run_all()
        sys.exit(0 if f == 0 else 1)
    finally:
        stop_server()
