from app import app
from database import db
from models import User
from auth import hash_password


with app.app_context():

    existing_user = User.query.filter_by(
        email="admin@qtplatform.com"
    ).first()

    if existing_user:

        print("Admin user already exists.")

    else:

        admin = User(
            full_name="QT Platform Administrator",
            email="admin@qtplatform.com",
            password_hash=hash_password(
                "Admin@123"
            ),
            role="SUPER_ADMIN",
            is_active=True
        )

        db.session.add(admin)
        db.session.commit()

        print("Admin user created successfully.")
        print("Email: admin@qtplatform.com")
        print("Password: Admin@123")