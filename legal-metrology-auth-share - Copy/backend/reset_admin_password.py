from getpass import getpass

from app.db.database import SessionLocal
from app.db.models import UserModel
from app.security import hash_password


db = SessionLocal()

try:
    email = input("Admin email: ").strip().lower()

    user = (
        db.query(UserModel)
        .filter(UserModel.email == email)
        .first()
    )

    if user is None:
        print("User not found.")
    elif user.role != "admin":
        print("This user is not an admin.")
    else:
        new_password = getpass("New admin password: ")

        if len(new_password) < 8:
            print("Password must be at least 8 characters.")
        else:
            user.password_hash = hash_password(new_password)
            db.commit()

            print("Admin password changed successfully.")

finally:
    db.close()