from functools import wraps

from flask import (
    session,
    redirect,
    url_for
)

from pwdlib import PasswordHash

from database import db
from models import User


password_hash = PasswordHash.recommended()


def hash_password(password):
    return password_hash.hash(password)


def verify_password(password, hashed_password):
    try:
        return password_hash.verify(
            password,
            hashed_password
        )
    except Exception:
        return False


def get_current_user():

    user_id = session.get("user_id")

    if not user_id:
        return None

    return db.session.get(
        User,
        user_id
    )


def login_user(user):

    session.clear()

    session["user_id"] = user.id
    session["role"] = user.role


def logout_user():

    session.clear()


def login_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        user = get_current_user()

        if not user:
            logout_user()

            return redirect(
                url_for("login")
            )

        if not user.is_active:

            logout_user()

            return redirect(
                url_for("login")
            )

        return view(
            *args,
            **kwargs
        )

    return wrapped_view


def roles_required(*allowed_roles):

    def decorator(view):

        @wraps(view)
        def wrapped_view(*args, **kwargs):

            user = get_current_user()

            if not user:

                logout_user()

                return redirect(
                    url_for("login")
                )

            if not user.is_active:

                logout_user()

                return redirect(
                    url_for("login")
                )

            if user.role not in allowed_roles:

                return (
                    "Access Denied",
                    403
                )

            return view(
                *args,
                **kwargs
            )

        return wrapped_view

    return decorator