# Rollback Guide - AM Business Django Bug Fixes

## Overview

This file documents all changes made on **2026-09-17** to fix 9 bugs in the AM Business Django project.

- **Pre-fix commit hash:** `0715f050d04f429cbed4a0dc150116eafb9e9e7a`
- **Branch:** `master`
- **Remote:** `git@github.com:ashkan-k/ashkanmasoumian.com-Am-business-Django.git`

---

## Quick Revert (Recommended)

If you want to revert ALL changes back to the state before fixes:

```bash
# Option A: Revert to the pre-fix commit (keeps history)
git revert 0715f050d04f429cbed4a0dc150116eafb9e9e7a..HEAD --no-edit

# Option B: Hard reset to pre-fix commit (DELETES fix commits from history)
git reset --hard 0715f050d04f429cbed4a0dc150116eafb9e9e7a
git push origin master --force
```

## Revert Individual Files Only

If you want to revert specific files back to pre-fix state:

```bash
# Revert ALL 4 modified files at once:
git checkout 0715f050d04f429cbed4a0dc150116eafb9e9e7a -- core/views.py core/models.py core/views_frontend.py core/admin.py

# Or revert one file at a time:
git checkout 0715f050d04f429cbed4a0dc150116eafb9e9e7a -- core/views.py
git checkout 0715f050d04f429cbed4a0dc150116eafb9e9e7a -- core/models.py
git checkout 0715f050d04f429cbed4a0dc150116eafb9e9e7a -- core/views_frontend.py
git checkout 0715f050d04f429cbed4a0dc150116eafb9e9e7a -- core/admin.py
```

---

## Files Changed (4 modified, 2 new)

| File | Status | Lines Changed |
|------|--------|---------------|
| `core/views.py` | Modified | +82 / -26 |
| `core/models.py` | Modified | +11 |
| `core/views_frontend.py` | Modified | +11 / -1 |
| `core/admin.py` | Modified (was empty) | +132 |
| `comprehensive_test.py` | New file | — |
| `test_dashboard.html` | New file | — |

---

## Detailed Change Log

### 1. `core/views.py` - 6 Changes

#### Change 1.1: Added `safe_int()` and `safe_float()` helper functions
**Location:** After `get_lang()` function (line ~19)

**Added code:**
```python
def safe_int(value, default=0):
    """Safely convert a value to int, returning default on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """Safely convert a value to float, returning default on failure."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
```

**Also added import at top:**
```python
from django.core.exceptions import ValidationError
```

#### Change 1.2: Replaced all `int(request.POST.get(...))` with `safe_int(...)`
**Affected views:** `social_links_view`, `navigation_view`, `services_view`, `stat_counters_view`, `features_view`, `pricing_view`, `testimonials_view`, `team_view`

**Before (example):**
```python
order=int(request.POST.get("order", 0)),
value=int(request.POST.get("value", 0)),
```

**After:**
```python
order=safe_int(request.POST.get("order", 0)),
value=safe_int(request.POST.get("value", 0)),
```

#### Change 1.3: Replaced all `float(request.POST.get(...))` with `safe_float(...)`
**Affected view:** `pricing_view`

**Before:**
```python
price=float(request.POST.get("price", 0)),
```

**After:**
```python
price=safe_float(request.POST.get("price", 0)),
```

#### Change 1.4: Fixed EventCountdown date handling
**View:** `event_countdown_view`

**Before:**
```python
def event_countdown_view(request):
    lang = get_lang(request)
    obj = EventCountdown.objects.first()
    if request.method == "POST":
        if not obj:
            obj = EventCountdown.objects.create(
                event_date=request.POST.get("event_date", ""),
            )
        ...
        obj.event_date = request.POST.get("event_date", obj.event_date)
        ...
```

**After:**
```python
def event_countdown_view(request):
    lang = get_lang(request)
    obj = EventCountdown.objects.first()
    if request.method == "POST":
        event_date_str = request.POST.get("event_date", "").strip()
        if not event_date_str:
            messages.error(request, "Event date is required.")
            return redirect("admin_event_countdown")
        from django.utils.dateparse import parse_datetime
        from django.utils.timezone import make_aware, is_aware
        parsed_date = parse_datetime(event_date_str)
        if parsed_date is None:
            messages.error(request, "Invalid event date format. Use YYYY-MM-DD HH:MM.")
            return redirect("admin_event_countdown")
        if not is_aware(parsed_date):
            parsed_date = make_aware(parsed_date)
        if not obj:
            obj = EventCountdown.objects.create(
                event_date=parsed_date,
            )
        ...
        obj.event_date = parsed_date
        ...
```

#### Change 1.5: Fixed Page slug uniqueness in `pages_view` add action
**Before:**
```python
if action == "add":
    from django.utils.text import slugify
    Page.objects.create(
        ...
        slug=slugify(request.POST.get("title_en", "page")),
        ...
    )
```

**After:**
```python
if action == "add":
    from django.utils.text import slugify
    base_slug = slugify(request.POST.get("title_en", "page")) or "page"
    slug = base_slug
    counter = 1
    while Page.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    Page.objects.create(
        ...
        slug=slug,
        ...
    )
```

#### Change 1.6: Added `@login_required` to `message_detail_view`
**Before:**
```python
def message_detail_view(request, pk):
```

**After:**
```python
@login_required(login_url="/accounts/login/")
def message_detail_view(request, pk):
```

---

### 2. `core/models.py` - 3 Changes

#### Change 2.1: Service slug uniqueness in `save()`
**Before:**
```python
def save(self, *args, **kwargs):
    if not self.slug:
        self.slug = slugify(self.title_en)
    super().save(*args, **kwargs)
```

**After:**
```python
def save(self, *args, **kwargs):
    if not self.slug:
        self.slug = slugify(self.title_en)
    original_slug = self.slug
    counter = 1
    while Service.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
        self.slug = f"{original_slug}-{counter}"
        counter += 1
    super().save(*args, **kwargs)
```

#### Change 2.2: Page slug uniqueness in `save()`
**Before:**
```python
def save(self, *args, **kwargs):
    if not self.slug:
        self.slug = slugify(self.title_en)
    super().save(*args, **kwargs)
```

**After:**
```python
def save(self, *args, **kwargs):
    if not self.slug:
        self.slug = slugify(self.title_en)
    original_slug = self.slug
    counter = 1
    while Page.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
        self.slug = f"{original_slug}-{counter}"
        counter += 1
    super().save(*args, **kwargs)
```

#### Change 2.3: Added ordering to Page Meta
**Before:**
```python
class Meta:
    verbose_name = "Page"
    verbose_name_plural = "Pages"
```

**After:**
```python
class Meta:
    verbose_name = "Page"
    verbose_name_plural = "Pages"
    ordering = ["-created_at"]
```

---

### 3. `core/views_frontend.py` - 1 Change

#### Change 3.1: Contact form Post/Redirect/Get pattern
**View:** `frontend_contact`

**Before:**
```python
def frontend_contact(request):
    ...
    contact_success = False

    if request.method == "POST":
        ...
        if name and email and message:
            ContactMessage.objects.create(
                name=name, email=email, subject=subject, message=message
            )
            contact_success = True

    ctx.update({
        ...
        "contact_success": contact_success,
        ...
    })
    return render(request, "frontend/contact.html", ctx)
```

**After:**
```python
def frontend_contact(request):
    ...
    contact_success = False

    if request.method == "POST":
        ...
        if name and email and message:
            ContactMessage.objects.create(
                name=name, email=email, subject=subject, message=message
            )
            # Post/Redirect/Get pattern: redirect to avoid resubmission on refresh
            from django.contrib import messages as django_messages
            django_messages.success(request, "contact_form_success")
            return redirect(f"{request.path}?sent=1")
        else:
            # Missing required fields
            from django.contrib import messages as django_messages
            django_messages.error(request, "contact_form_error")

    ctx.update({
        ...
        "contact_success": request.GET.get("sent") == "1",
        ...
    })
    return render(request, "frontend/contact.html", ctx)
```

---

### 4. `core/admin.py` - 1 Change

#### Change 4.1: Registered all 16 models in Django admin
**Before (empty file):**
```python
from django.contrib import admin

# Register your models here.
```

**After:** Full registration of all models (SiteSettings, SocialLink, Navigation, HeroSection, Service, AboutSection, StatCounter, Feature, PricingPlan, Testimonial, TeamMember, ContactMessage, NewsletterSubscriber, EventCountdown, Page, HomeSection) with list_display, list_filter, list_editable, search_fields, and prepopulated_fields.

---

## Bugs Fixed Summary

| # | Bug | Severity | Files |
|---|-----|----------|-------|
| 1 | `int("abc")` crashes 8 admin views | 500 Error | views.py |
| 2 | `float("text")` crashes pricing view | 500 Error | views.py |
| 3 | Empty/invalid date crashes EventCountdown | 500 Error | views.py |
| 4 | `message_detail_view` accessible without login | Security | views.py |
| 5 | Duplicate Service titles cause IntegrityError | 500 Error | models.py |
| 6 | Duplicate Page titles cause IntegrityError | 500 Error | models.py, views.py |
| 7 | Contact form allows resubmission on refresh | UX Bug | views_frontend.py |
| 8 | Django admin has no models registered | Improvement | admin.py |
| 9 | Page model missing default ordering | Warning | models.py |

---

## New Files (can be deleted safely)

- `comprehensive_test.py` - Test script for regression testing
- `test_dashboard.html` - HTML dashboard with all test links

---

## Environment Notes

- A new venv `.venv_new` was created with Python 3.13.12 (original `.venv` had broken Python 3.9 path)
- Superuser created: `admin` / `admin12345`
- Database was seeded with `python manage.py seed_data`
- These environment changes are NOT in git (excluded by .gitignore)

---

## Revert Specific Bug Fixes (Selective)

If you want to revert only specific fixes (not all), use `git diff` to find the exact lines and manually revert them. Here are the most critical ones to be aware of:

### Revert just the safe_int/safe_float changes (Bug 1 & 2):
This would re-introduce 500 errors on invalid numeric input. Find and replace:
- `safe_int(` back to `int(`
- `safe_float(` back to `float(`

### Revert just the EventCountdown date fix (Bug 3):
This would re-introduce 500 error on empty event date. Remove the `parse_datetime` block and restore the original code.

### Revert just the @login_required (Bug 4):
This would re-expose message detail to unauthenticated users. Remove the decorator line above `message_detail_view`.

---

## Phase 4 Changes - Client Feedback (2026-09-19)

**4 items requested by employer/client feedback:**

### Phase 4 Overview

| Item | Description | Files Changed |
|------|-------------|---------------|
| 4.1 | Logo upload hint on Hero Sections admin page + fix delete bug + add background_image to add action | `templates/admin_panel/hero_sections.html`, `core/views.py` |
| 4.2 | Navigation admin: clear top-level vs child labeling + info banner | `templates/admin_panel/navigation.html` |
| 4.3 | Event Countdown section added to home page with live JS timer | `templates/frontend/index.html` |
| 4.4 | Image preview before upload - global JS on all admin file inputs | `static/admin_panel/js/main.js` |

### Phase 4 Detailed Changes

#### 4.1: Hero Sections Admin Page

**`templates/admin_panel/hero_sections.html`:**
- Added info banner at top explaining: (a) logo is uploaded in Site Settings, not here; (b) where Hero Sections render on the site (Home `/`, About `/about/`, Services `/services/`, Contact `/contact/`)
- Added link to Site Settings page
- Fixed delete form: was `<input type="hidden" name="action" value="add">` (bug! should be `delete`)
- Added delete button with `confirmDelete()` handler
- `background_image` file input now handled in add action (was missing)

**`core/views.py` — `hero_sections_view`:**
- Add action: changed from `HeroSection.objects.create(...)` (which ignored files) to creating object then setting `hero.background_image = request.FILES["background_image"]` before save
- Added delete action handler (was completely missing)

#### 4.2: Navigation Admin Page

**`templates/admin_panel/navigation.html`:**
- Added info banner explaining how to add top-level header menu items
- Changed parent dropdown "None" option to "None (Top-level / Header menu)" in both add and edit forms
- Added help text under parent dropdown: "Select 'None' to show this item in the site header. Select a parent to show it as a dropdown sub-item."
- Changed URL field default value from `#` to `/`
- Added URL field help text with examples

#### 4.3: Event Countdown on Home Page

**`templates/frontend/index.html`:**
- Added `{% if countdown %}` section between Hero and "About AM Business" sections
- Countdown displays: title, subheading, 4 countdown boxes (Days/Hours/Minutes/Seconds), CTA button
- Uses `trans_field` template tag for bilingual title/subheading/ended_message/cta_text
- Added `{% block extra_js %}` with JavaScript countdown timer that:
  - Parses event date from `data-event-date` attribute
  - Updates every second
  - Shows "ended message" when event has passed
  - Bilingual labels (روز/ساعت/دقیقه/ثانیه for FA, Days/Hours/Minutes/Seconds for EN)

#### 4.4: Image Preview Before Upload (Global)

**`static/admin_panel/js/main.js`:**
- Added document-level `change` event listener (event delegation) that catches ALL `input[type="file"]` changes across the entire admin panel
- When a file is selected: creates a preview `<img>` element right after the file input, sets its `src` to `URL.createObjectURL(file)`
- When no file selected or file is not an image: hides the preview
- Works with dynamically injected modal forms (openModal uses innerHTML injection)
- Revokes object URLs after image load to free memory
- No template changes needed — the JS automatically finds all file inputs on every page

### Phase 4 Revert Instructions

To revert Phase 4 changes only (keeping Phase 1-3 bug fixes):

```bash
# Revert Phase 4 files to the Phase 3 commit (4bfb26c):
git checkout 4bfb26c -- templates/admin_panel/hero_sections.html templates/admin_panel/navigation.html templates/frontend/index.html static/admin_panel/js/main.js core/views.py
```

Note: `core/views.py` has changes from both Phase 1 and Phase 4. If you revert it to `4bfb26c`, you'll keep Phase 1 changes but lose Phase 4's hero_sections_view delete action and background_image handling. If you want to revert ALL changes (Phase 1-4), use the pre-fix commit `0715f050d04f429cbed4a0dc150116eafb9e9e7a` instead.

---

## Phase 5 Changes - Frontend Toast Success Messages (2026-09-17)

**Request:** When "Subscribe to Newsletter" or the contact form is submitted successfully, display a language-aware toast success message on the site. Also audit all user-facing forms and apply the same treatment.

### Phase 5 Overview

| Item | Description | Files Changed |
|------|-------------|---------------|
| 5.1 | Self-contained toast container (CSS + JS + bilingual) added to frontend base template | `templates/frontend/base.html` |
| 5.2 | Language-aware success/error/info messages in contact and newsletter views | `core/views_frontend.py` |
| 5.3 | Removed old hardcoded inline success banner from contact page | `templates/frontend/contact.html` |

### Phase 5 Detailed Changes

#### 5.1: Frontend Toast Container (`templates/frontend/base.html`)

**Added** a `{% if messages %}` block immediately after `<body>`, before the mobile menu, containing:
- Self-contained inline `<style>` with `.fe-toast-container`, `.fe-toast`, `.fe-toast-success/error/info` classes
- RTL support: `[dir="rtl"]` overrides for position, animation direction, and border side
- Font family switches between Vazirmatn (FA) and Montserrat (EN) via `{% if lang == 'fa' %}`
- Toast icons: checkmark for success, X for error, "i" for info
- Auto-dismiss JS: 5s timeout, adds `.fe-hide` class (opacity/transform transition), then removes element after 300ms
- Close button on each toast for manual dismissal
- `z-index: 99999` to overlay all site content

**Key design:** The toast uses `fe-` prefix CSS classes to avoid collisions with the site's existing CSS framework.

#### 5.2: Language-Aware Messages in Views (`core/views_frontend.py`)

**`frontend_contact` view — changes:**
- Removed inline `from django.contrib import messages as django_messages` imports (already imported at top as `messages`)
- Success: now sends actual translated text instead of message key "contact_form_success"
  - EN: `"Your message has been sent successfully!"`
  - FA: `"پیام شما با موفقیت ارسال شد!"`
- Error (missing fields): now sends translated text instead of key "contact_form_error"
  - EN: `"Please fill in all required fields."`
  - FA: `"لطفاً تمام فیلدهای ضروری را پر کنید."`

**`frontend_newsletter_subscribe` view — changes:**
- Was: silently redirecting back with no message at all
- Now: reads `lang` via `get_lang(request)` and sends language-aware messages:
  - New subscriber (success): EN `"You have successfully subscribed to our newsletter!"` / FA `"شما با موفقیت در خبرنامه ما عضو شدید!"`
  - Already subscribed (info): EN `"You are already subscribed with this email address."` / FA `"شما قبلاً با این ایمیل عضو خبرنامه شده‌اید."`
  - Empty email (error): EN `"Please provide a valid email address."` / FA `"لطفاً یک آدرس ایمیل معتبر وارد کنید."`
- Uses `get_or_create` return value `(obj, created)` to distinguish new vs existing subscribers

#### 5.3: Removed Inline Banner (`templates/frontend/contact.html`)

**Removed** the hardcoded inline success banner:
```html
{% if contact_success %}
<div style="background:#d1fae5;color:#065f46;padding:16px 20px;border-radius:10px;margin-bottom:20px;font-weight:500">
    {% if lang == 'fa' %}پیام شما با موفقیت ارسال شد!{% else %}Your message has been sent successfully!{% endif %}
</div>
{% endif %}
```
The unified toast in `base.html` now handles all success/error display. The `contact_success` context variable is kept in the view for backward compatibility but no longer rendered inline.

### Frontend Form Audit

All `templates/frontend/*.html` files were searched for `<form>`, `method="post"`, `<textarea>`, and `type="submit"`. Only two user-facing forms exist:

1. **Newsletter subscribe form** — in `base.html` (appears on all pages via `{% block newsletter %}`)
2. **Contact form** — in `contact.html`

No other forms were found in `index.html`, `about.html`, or `services.html`. Both forms now have language-aware toast messages.

### Phase 5 Test Results

All 7 test scenarios passed:
1. Contact form POST (EN) — 302 redirect, success toast present
2. Newsletter subscribe (EN) — 302 redirect, success toast present
3. Newsletter duplicate email (EN) — info toast "already subscribed"
4. Contact form POST (FA) — 302 redirect, Persian success text present
5. Newsletter POST (FA) — Persian success text present
6. Newsletter empty email (EN) — error toast present
7. Contact missing fields (EN) — 200 (no redirect), error toast present

All 4 frontend pages verified returning 200: `/`, `/about/`, `/services/`, `/contact/`.

### Phase 5 Revert Instructions

To revert Phase 5 changes only (keeping Phases 1-4):

```bash
# Find the commit hash before Phase 5 (use: git log --oneline -5)
# Then revert these 3 files to that commit:
git checkout <phase4_commit> -- templates/frontend/base.html core/views_frontend.py templates/frontend/contact.html
```

To revert ALL changes (Phases 1-5), use the pre-fix commit:
```bash
git reset --hard 0715f050d04f429cbed4a0dc150116eafb9e9e7a
```
