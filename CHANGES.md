# Online Voting System — Setup & Changes Guide

## What Was Updated

### 1. Login Page — Animated Ballot Box Background
`voting-frontend/login.html` now has a full animated scene:
- Dark forest-green background
- 12 ballot papers drifting down continuously
- SVG ballot box at the bottom-centre with a paper sliding into the slot on loop
- Login card floats above the scene with a drop-shadow

### 2. Themed Backgrounds on Every Tab
Each page now has a subtle background image/overlay related to its purpose:
| Page | Theme |
|------|-------|
| `index.html` | Election rally crowd photo |
| `vote.html` | Voting booth texture + gradient overlays |
| `candidates.html` | Parliament building backdrop |
| `results.html` | Data chart visualization backdrop |

All images are loaded via Unsplash CDN at low opacity (6–9%) so readability is unaffected.

### 3. Candidate Photo + Cover Photo Support

#### Django Backend Changes
- **`voting/models.py`** — `Candidate` model now has two new fields:
  - `photo` — candidate portrait (shown as a circular thumbnail on cards)
  - `cover_photo` — wide banner image (shown as the card's top cover strip)
- **`voting/migrations/0005_candidate_photo_cover_photo.py`** — migration for the above
- **`voting/views.py`** — `get_candidates()` now returns `photo_url` and `cover_photo_url`
- **`online_voting/settings.py`** — `MEDIA_URL` and `MEDIA_ROOT` added
- **`online_voting/urls.py`** — `static(MEDIA_URL, ...)` added so Django serves uploaded images

#### Frontend Changes
- **`voting-frontend/vote.html`** — card template now renders `<img>` tags when photos exist,
  falling back to colour gradient + letter avatar when they don't
- **`voting-frontend/candidates.html`** — same photo/cover logic on the mini-cards


## First-Time Setup After Applying These Changes

```bash
# 1. Install Pillow (required for ImageField)
pip install Pillow

# 2. Run the new migration
python manage.py migrate

# 3. Start the server
python manage.py runserver
```

## Uploading Candidate Photos

1. Go to `http://127.0.0.1:8000/admin/`
2. Log in with your superuser account
   ```bash
   python create_superuser.py   # or: python manage.py createsuperuser
   ```
3. Click **Voting → Candidates**
4. Click on any candidate
5. You will see two new fields:
   - **Photo** — upload a square portrait (e.g. 400×400 px)
   - **Cover photo** — upload a wide landscape image (e.g. 800×300 px)
6. Click **Save**

The card on the voting page and candidates page will immediately show the real photos.
If no photo is uploaded, the previous colour-gradient + letter fallback is shown automatically.

## Recommended Image Sizes
| Field | Recommended size | Notes |
|-------|-----------------|-------|
| `photo` | 400 × 400 px | Will be cropped to a circle |
| `cover_photo` | 800 × 300 px | Top-of-card banner strip |

## File Structure of Changes
```
Online-Voting-main/
├── voting/
│   ├── models.py                          ← +photo, +cover_photo fields
│   ├── views.py                           ← +photo_url, +cover_photo_url in API
│   └── migrations/
│       └── 0005_candidate_photo_cover_photo.py   ← NEW migration
├── online_voting/
│   ├── settings.py                        ← +MEDIA_URL, MEDIA_ROOT
│   └── urls.py                            ← +static(MEDIA_URL, ...)
└── voting-frontend/
    ├── login.html                         ← NEW animated ballot box background
    ├── index.html                         ← +election rally background
    ├── vote.html                          ← +voting booth bg + real photo/cover on cards
    ├── candidates.html                    ← +parliament bg + real photo/cover on cards
    └── results.html                       ← +data viz background
```
