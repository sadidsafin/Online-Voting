# 🗳️ Bangladesh Election 2026 — Online Voting System

A Django-based online voting system built for CSE 299 Junior Design Project at North South University.

---

## ⚙️ Prerequisites

Before you begin, make sure the following are installed on your PC:

- **Python 3.10 or higher** → https://www.python.org/downloads/
  - During installation, check ✅ **"Add Python to PATH"**
- **Git** (optional, if cloning from GitHub) → https://git-scm.com/

---

## 🚀 Setup Instructions (Step by Step)

### 1. Get the Project

Either unzip the provided folder or clone the repo:

```bash
git clone <your-repo-url>
cd Online-Voting-main
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **Mac/Linux:**
  ```bash
  source venv/bin/activate
  ```

You should see `(venv)` in your terminal prompt.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs: Django, django-cors-headers, Pillow, scikit-learn, numpy.

### 4. Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create an Admin Superuser

```bash
python create_superuser.py
```

This creates:
- **Username:** `admin`
- **Password:** `admin`

You can log in at `http://127.0.0.1:8000/admin/`

### 6. Populate Candidates (if starting fresh)

```bash
python populate_candidates.py
```

This seeds the database with all 267 candidates.

### 7. Run the Development Server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000** in your browser.

---

## 📁 Project Structure

```
Online-Voting-main/
├── manage.py               # Django entry point
├── requirements.txt        # Python dependencies
├── db.sqlite3              # SQLite database
├── create_superuser.py     # Script to create admin user
├── populate_candidates.py  # Script to seed candidate data
├── media/                  # Uploaded candidate photos
├── online_voting/          # Project settings & URLs
└── voting/                 # Main app (models, views, templates)
```

---

## 🔑 Default Credentials

| Role  | Username | Password |
|-------|----------|----------|
| Admin | `admin`  | `admin`  |

Voter login uses a **Voter ID + OTP** system. In development mode, the OTP is printed directly in the terminal — no SMS is sent.

---

## ⚠️ Known Notes

- The project uses **SQLite** — no external database setup needed.
- In development, OTPs appear in the terminal as `[DEV] Auto-OTP for voter <id>: <otp>`.
- The `media/` folder must exist for candidate photos to load. It is included in the zip.
- Do **not** use this development server in production. Use a proper WSGI/ASGI server (e.g. Gunicorn + Nginx).

---

## 🛠️ Troubleshooting

**`ModuleNotFoundError`** → Make sure your virtual environment is activated and you ran `pip install -r requirements.txt`.

**`FieldError` or migration errors** → Always run `python manage.py makemigrations` before `python manage.py migrate` on a fresh setup.

**Candidate photos not showing** → Make sure the `media/` folder from the zip is present in the project root.

**Port already in use** → Run on a different port: `python manage.py runserver 8080`
