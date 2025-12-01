<!-- e9ca4ed3-f6a9-4f17-89d6-51ce3ab99109 3a427f8c-d63e-4b30-ad12-100a2a306432 -->
# Django Persecution Tracking App Implementation Plan

## Overview

Build a Django web app within the existing `catholic_persecution` project to track modern Christian persecution and provide a prayer list. The app will have a minimal, reverent "digital chapel" aesthetic using Tailwind CSS.

## Implementation Steps

### 1. Create the `martyrs` Django App

- Create the app using Django's app structure
- Add `martyrs` to `INSTALLED_APPS` in `catholic_persecution/settings.py`

### 2. Create Models

**File: `martyrs/models.py`**

- `Martyr` model with fields:
- `name` (CharField)
- `country` (CharField)
- `date` (DateField)
- `source_url` (URLField)
- `description` (TextField)
- `created_at` (DateTimeField, auto_now_add)
- `PrayerIntention` model with fields:
- `title` (CharField)
- `details` (TextField)
- `created_at` (DateTimeField, auto_now_add)

### 3. Database Migrations

- Create initial migrations for the models
- Ensure migrations are ready to run cleanly

### 4. Admin Panel Registration

**File: `martyrs/admin.py`**

- Register `Martyr` and `PrayerIntention` models
- Configure admin display with list_display, search_fields, and date_hierarchy

### 5. Views

**File: `martyrs/views.py`**

- Create a homepage view that:
- Fetches latest martyrs (ordered by date, most recent first)
- Fetches latest prayer intentions (ordered by created_at, most recent first)
- Passes both to template context

### 6. URLs Configuration

- Create `martyrs/urls.py` with homepage route
- Update `catholic_persecution/urls.py` to include martyrs URLs

### 7. Templates

**Files:**

- `martyrs/templates/base.html` - Base template with Tailwind CSS CDN, minimal reverent styling
- `martyrs/templates/martyrs/home.html` - Homepage displaying martyrs and prayer intentions

**Design approach:**

- Clean, minimal layout
- Serif fonts for reverent feel
- Subtle colors (whites, soft grays, muted tones)
- Simple card-based layout for listings

### 8. Static Files Configuration

- Ensure `STATIC_URL` and `STATICFILES_DIRS` are properly configured in settings if needed

### 9. Data Fetching Management Command

**File: `martyrs/management/commands/fetch_persecution_data.py`**

- Create management command using web scraping (requests + beautifulsoup4)
- Implement starter scraping logic that can be extended for multiple sources
- Command runnable via `python manage.py fetch_persecution_data`
- No code comments - keep code self-documenting and pragmatic

## Files to Create/Modify

### New Files:

- `martyrs/__init__.py`
- `martyrs/apps.py`
- `martyrs/models.py`
- `martyrs/admin.py`
- `martyrs/views.py`
- `martyrs/urls.py`
- `martyrs/migrations/0001_initial.py`
- `martyrs/templates/base.html`
- `martyrs/templates/martyrs/home.html`
- `martyrs/management/__init__.py`
- `martyrs/management/commands/__init__.py`
- `martyrs/management/commands/fetch_persecution_data.py`

### Modified Files:

- `catholic_persecution/settings.py` - Add `martyrs` to INSTALLED_APPS
- `catholic_persecution/urls.py` - Include martyrs URLs

## Key Design Decisions

- Use Tailwind CSS via CDN for styling (no build process needed)
- Keep templates simple and maintainable
- Follow Django best practices (apps structure, model organization)
- Management command uses web scraping (requests + BeautifulSoup) as primary data fetching method
- No code comments - keep code self-documenting and pragmatic
- Focus on working, maintainable code over documentation

### To-dos

- [ ] Create the martyrs Django app and add it to INSTALLED_APPS
- [ ] Create Martyr and PrayerIntention models with all required fields
- [ ] Generate and prepare initial migrations for the models
- [ ] Register models in admin.py with appropriate display options
- [ ] Create homepage view that fetches and displays latest martyrs and prayer intentions
- [ ] Create URL routing for martyrs app and integrate with main urls.py
- [ ] Create base template and homepage template with Tailwind CSS styling (minimal, reverent aesthetic)
- [ ] Create fetch_persecution_data management command with starter/mock implementation