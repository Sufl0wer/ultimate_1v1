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

## Auth flow

1. Register with email and password
2. Copy the verification link from the terminal
3. Open the link to activate the account
4. Log in and visit the home page

## Tournament flow

1. User A clicks **Create tournament** and copies the invite code from the lobby
2. User B pastes the code into **Join tournament** on the home page
3. Both players pick disciplines and press **Ready**
4. When both are ready, they are sent to the shared tournament page (also listed on home)

Lobby pages poll `/tournaments/<id>/status/` so the UI updates when the opponent joins or the match becomes active.

## Notes

- Custom user model: `accounts.User` (`USERNAME_FIELD = email`)
- New users start inactive until they verify email
- `Discipline` is a global catalog; tournaments store the union of both players’ picks
- Django admin is available at `/admin/`
