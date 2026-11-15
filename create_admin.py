
from app import app
from models import db, Admin
from getpass import getpass

with app.app_context():

    username = input("Enter admin username: ").strip()

    if not username:
        print("Username cannot be empty.")

    elif Admin.query.filter_by(username=username).first():
        print("This username already exists.")

    else:
        password = getpass("Enter admin password: ")
        confirm_password = getpass("Confirm admin password: ")

        if len(password) < 10:
            print("Password must contain at least 10 characters.")

        elif password != confirm_password:
            print("Passwords do not match.")

        else:
            admin = Admin(username=username)
            admin.set_password(password)

            db.session.add(admin)
            db.session.commit()

            print("Admin account created successfully!")
