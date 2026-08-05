# Leafmail (Django)

Simple Django web app with an email-based custom user model, registration, email verification, and login.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

## Run

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000/register/](http://127.0.0.1:8000/register/).

Verification emails are printed in the terminal (console email backend).

## Flow

1. Register with email and password
2. Copy the verification link from the terminal
3. Open the link to activate the account
4. Log in and visit the home page

## Notes

- Custom user model: `accounts.User` (`USERNAME_FIELD = email`)
- New users start inactive until they verify email
- Django admin is available at `/admin/`
