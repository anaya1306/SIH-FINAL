import os
from getpass import getpass

from dotenv import load_dotenv

from app.db.database import SessionLocal
from app.db.models import UserModel
from app.security import hash_password


load_dotenv()


def get_admin_emails():
    value = os.getenv("ADMIN_EMAILS", "")

    return {
        email.strip().lower()
        for email in value.split(",")
        if email.strip()
    }


admin_emails = get_admin_emails()

if not admin_emails:
    print("No admin emails configured in .env")
    raise SystemExit


db = SessionLocal()

try:
    email = input("Admin email: ").strip().lower()

    if email not in admin_emails:
        print("This email is not authorized to be an admin.")
        raise SystemExit

    user = (
        db.query(UserModel)
        .filter(UserModel.email == email)
        .first()
    )

    if user:
        if user.role == "admin":
            print("This user is already an admin.")
        else:
            user.role = "admin"
            user.is_active = True

            db.commit()

            print("Existing user promoted to admin.")

    else:
        name = input("Admin name: ").strip()
        password = getpass("Admin password: ")

        if len(password) < 8:
            print("Password must be at least 8 characters.")
            raise SystemExit

        user = UserModel(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print("Admin account created successfully.")

finally:
    db.close()