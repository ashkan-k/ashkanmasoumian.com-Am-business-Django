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
