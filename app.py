import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
    jsonify
)

from sqlalchemy import or_, text

from werkzeug.utils import secure_filename

from email_validator import (
    validate_email,
    EmailNotValidError
)

from config import Config
from database import db
from models import User, Trainer, Requirement, Project, ProjectTrainer, Application, Schedule, Notification, Attendance, Payment, Document, Communication, SystemSetting

from auth import (
    hash_password,
    verify_password,
    login_user,
    logout_user,
    get_current_user,
    login_required,
    roles_required
)


app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

# ============================================================
# INDIA TIMEZONE
# ============================================================

INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")


def format_india_time(dt):

    if not dt:
        return ""

    # Database timestamps are treated as UTC
    # when they are timezone-naive.
    if dt.tzinfo is None:

        dt = dt.replace(
            tzinfo=timezone.utc
        )

    india_time = dt.astimezone(
        INDIA_TIMEZONE
    )

    return india_time.strftime(
        "%d %b %Y, %I:%M %p"
    )


# Make the function available inside Jinja templates
app.jinja_env.globals["format_india_time"] = format_india_time
# ============================================================
# CSRF
# ============================================================

def get_csrf_token():

    token = session.get("csrf_token")

    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token

    return token


def validate_csrf():

    token = request.form.get("csrf_token")
    session_token = session.get("csrf_token")

    if not token or not session_token:
        return False

    return secrets.compare_digest(
        token,
        session_token
    )


# ============================================================
# GLOBAL TEMPLATE VARIABLES
# ============================================================

@app.context_processor
def inject_globals():

    current_user = get_current_user()

    unread_notification_count = 0

    recent_notifications = []

    if current_user:

        unread_notification_count = (
            Notification.query
            .filter_by(
                user_id=current_user.id,
                is_read=False
            )
            .count()
        )

        recent_notifications = (
            Notification.query
            .filter_by(
                user_id=current_user.id
            )
            .order_by(
                Notification.created_at.desc()
            )
            .limit(5)
            .all()
        )

    return {
        "user": current_user,
        "csrf_token": get_csrf_token(),
        "unread_notification_count":
            unread_notification_count,
        "recent_notifications":
            recent_notifications,
        "timedelta": timedelta,
        "today": datetime.now().date()
    }

# ============================================================
# HELPERS
# ============================================================

ALLOWED_ROLES = {
    "SUPER_ADMIN",
    "VENDOR",
    "TRAINER"
}


REQUIREMENT_STATUSES = {
    "OPEN",
    "IN_PROGRESS",
    "ASSIGNED",
    "COMPLETED",
    "CANCELLED"
}


PROJECT_STATUSES = {
    "PLANNING",
    "ACTIVE",
    "COMPLETED",
    "CANCELLED"
}


def vendor_can_access_requirement(requirement, current_user=None):
    if current_user is None:
        current_user = get_current_user()
    if not current_user:
        return False
    if current_user.role == "SUPER_ADMIN":
        return True
    if current_user.role == "VENDOR":
        return requirement.created_by == current_user.id
    return False


def vendor_can_access_project(project, current_user=None):
    if current_user is None:
        current_user = get_current_user()
    if not current_user:
        return False
    if current_user.role == "SUPER_ADMIN":
        return True
    if current_user.role == "VENDOR":
        return project.created_by == current_user.id
    return False


def vendor_can_access_application(application, current_user=None):
    if current_user is None:
        current_user = get_current_user()
    if not current_user:
        return False
    if current_user.role == "SUPER_ADMIN":
        return True
    if current_user.role == "VENDOR":
        return bool(application.requirement) and application.requirement.created_by == current_user.id
    return False


def clean_text(value, max_length=None):

    if value is None:
        return ""

    value = str(value).strip()

    if max_length:
        value = value[:max_length]

    return value


def validate_password(password):

    if not password:
        return False

    if len(password) < 8:
        return False

    return True


def validate_email_address(email):

    try:

        result = validate_email(
            email,
            check_deliverability=False
        )

        return result.normalized

    except EmailNotValidError:

        return None


def parse_non_negative_float(
    value,
    field_name
):

    try:

        number = float(value)

    except (TypeError, ValueError):

        raise ValueError(
            f"{field_name} must be a valid number."
        )

    if number < 0:

        raise ValueError(
            f"{field_name} cannot be negative."
        )

    return number


def parse_positive_integer(
    value,
    field_name
):

    try:

        number = int(value)

    except (TypeError, ValueError):

        raise ValueError(
            f"{field_name} must be a valid number."
        )

    if number <= 0:

        raise ValueError(
            f"{field_name} must be greater than zero."
        )

    return number


def parse_optional_date(value):

    value = clean_text(
        value,
        20
    )

    if not value:
        return None

    try:

        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        raise ValueError(
            "Date must be a valid date."
        )


def generate_requirement_code():

    last_requirement = (
        Requirement.query
        .order_by(Requirement.id.desc())
        .first()
    )

    if not last_requirement:
        next_number = 1

    else:

        next_number = (
            last_requirement.id + 1
        )

    return (
        f"QT-REQ-{next_number:04d}"
    )


def generate_project_code():

    last_project = (
        Project.query
        .order_by(Project.id.desc())
        .first()
    )

    if not last_project:
        next_number = 1
    else:
        next_number = last_project.id + 1

    return f"QT-PRJ-{next_number:04d}"


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def login():

    if request.method == "GET":

        user = get_current_user()

        if user and user.is_active:

            return redirect(
                url_for("dashboard")
            )

        return render_template(
            "login.html"
        )

    email = clean_text(
        request.form.get("email"),
        150
    ).lower()

    password = request.form.get(
        "password",
        ""
    )

    if not email or not password:

        flash(
            "Please enter email and password.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    user = User.query.filter_by(
        email=email
    ).first()

    if not user:

        flash(
            "Invalid email or password.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    if not user.is_active:

        flash(
            "Your account is inactive. Please contact the administrator.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    if not verify_password(
        password,
        user.password_hash
    ):

        flash(
            "Invalid email or password.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    login_user(user)

    flash(
        "Login successful.",
        "success"
    )

    return redirect(
        url_for("dashboard")
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("login")
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():

    total_users = User.query.count()

    active_users = (
        User.query
        .filter_by(is_active=True)
        .count()
    )

    total_trainers = Trainer.query.count()

    active_trainers = (
        Trainer.query
        .filter_by(
            trainer_status="ACTIVE"
        )
        .count()
    )

    total_requirements = (
        Requirement.query.count()
    )

    open_requirements = (
        Requirement.query
        .filter_by(status="OPEN")
        .count()
    )

    in_progress_requirements = (
        Requirement.query
        .filter_by(status="IN_PROGRESS")
        .count()
    )

    assigned_requirements = (
        Requirement.query
        .filter_by(status="ASSIGNED")
        .count()
    )

    completed_requirements = (
        Requirement.query
        .filter_by(status="COMPLETED")
        .count()
    )

    return render_template(
        "dashboard.html",

        total_users=total_users,
        active_users=active_users,

        total_trainers=total_trainers,
        active_trainers=active_trainers,

        total_requirements=total_requirements,
        open_requirements=open_requirements,
        in_progress_requirements=in_progress_requirements,
        assigned_requirements=assigned_requirements,
        completed_requirements=completed_requirements
    )


# ============================================================
# USER MANAGEMENT
# ============================================================

@app.route("/users")
@roles_required("SUPER_ADMIN")
def users():

    all_users = (
        User.query
        .order_by(
            User.created_at.desc()
        )
        .all()
    )

    available_trainers = (
        Trainer.query
        .filter(
            Trainer.user_id.is_(None),
            Trainer.trainer_status == "ACTIVE"
        )
        .order_by(
            Trainer.full_name.asc()
        )
        .all()
    )

    return render_template(
        "users.html",
        users=all_users,
        available_trainers=available_trainers
    )


# ============================================================
# CREATE USER
# ============================================================

@app.route(
    "/users/create",
    methods=["POST"]
)
@roles_required("SUPER_ADMIN")
def create_user():

    if not validate_csrf():

        flash(
            "Invalid security token. Please try again.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    full_name = clean_text(
        request.form.get("full_name"),
        150
    )

    email = clean_text(
        request.form.get("email"),
        150
    ).lower()

    password = request.form.get(
        "password",
        ""
    )

    role = clean_text(
        request.form.get("role"),
        30
    ).upper()

    trainer_id = request.form.get(
        "trainer_id"
    )

    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    if not full_name:

        flash(
            "Full name is required.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    normalized_email = (
        validate_email_address(email)
    )

    if not normalized_email:

        flash(
            "Please enter a valid email address.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    email = normalized_email

    if not validate_password(password):

        flash(
            "Password must contain at least 8 characters.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    if role not in ALLOWED_ROLES:

        flash(
            "Invalid user role.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    # --------------------------------------------------------
    # DUPLICATE EMAIL
    # --------------------------------------------------------

    existing_user = (
        User.query
        .filter_by(email=email)
        .first()
    )

    if existing_user:

        flash(
            "A user with this email already exists.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    trainer = None

    # --------------------------------------------------------
    # TRAINER ACCOUNT CREATION
    # --------------------------------------------------------

    if role == "TRAINER":

        if not trainer_id:

            flash(
                "Please select a trainer profile.",
                "error"
            )

            return redirect(
                url_for("users")
            )

        try:

            trainer_id_int = int(
                trainer_id
            )

        except (TypeError, ValueError):

            flash(
                "Invalid trainer selection.",
                "error"
            )

            return redirect(
                url_for("users")
            )

        trainer = db.session.get(
            Trainer,
            trainer_id_int
        )

        if not trainer:

            flash(
                "Selected trainer was not found.",
                "error"
            )

            return redirect(
                url_for("users")
            )

        if trainer.user_id is not None:

            flash(
                "This trainer already has a login account.",
                "error"
            )

            return redirect(
                url_for("users")
            )

        # Trainer profile is authoritative.
        full_name = trainer.full_name

    # --------------------------------------------------------
    # CREATE USER
    # --------------------------------------------------------

    new_user = User(
        full_name=full_name,
        email=email,
        password_hash=hash_password(
            password
        ),
        role=role,
        is_active=True
    )

    try:

        db.session.add(
            new_user
        )

        db.session.flush()

        if trainer:

            trainer.user_id = new_user.id

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to create the user. Please try again.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    if trainer:

        flash(
            f"Login account created and linked to trainer '{trainer.full_name}'.",
            "success"
        )

    else:

        flash(
            "User account created successfully.",
            "success"
        )

    return redirect(
        url_for("users")
    )


# ============================================================
# TOGGLE USER
# ============================================================

@app.route(
    "/users/<int:user_id>/toggle",
    methods=["POST"]
)
@roles_required("SUPER_ADMIN")
def toggle_user(user_id):

    if not validate_csrf():

        flash(
            "Invalid security token.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    current_user = get_current_user()

    if current_user.id == user_id:

        flash(
            "You cannot deactivate your own account.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    target_user = db.session.get(
        User,
        user_id
    )

    if not target_user:

        flash(
            "User not found.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    target_user.is_active = (
        not target_user.is_active
    )

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to update the user status.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    if target_user.is_active:

        flash(
            "User account activated.",
            "success"
        )

    else:

        flash(
            "User account deactivated.",
            "success"
        )

    return redirect(
        url_for("users")
    )


# ============================================================
# DELETE USER
# ============================================================

@app.route(
    "/users/<int:user_id>/delete",
    methods=["POST"]
)
@roles_required("SUPER_ADMIN")
def delete_user(user_id):

    if not validate_csrf():

        flash(
            "Invalid security token.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    current_user = get_current_user()

    if current_user.id == user_id:

        flash(
            "You cannot delete your own account.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    target_user = db.session.get(
        User,
        user_id
    )

    if not target_user:

        flash(
            "User not found.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    # --------------------------------------------------------
    # Keep trainer profile when trainer login is deleted.
    # --------------------------------------------------------

    linked_trainer = (
        Trainer.query
        .filter_by(
            user_id=target_user.id
        )
        .first()
    )

    if linked_trainer:

        linked_trainer.user_id = None

    try:

        db.session.delete(
            target_user
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to delete the user.",
            "error"
        )

        return redirect(
            url_for("users")
        )

    if linked_trainer:

        flash(
            f"User deleted. Trainer '{linked_trainer.full_name}' remains available without a login.",
            "success"
        )

    else:

        flash(
            "User deleted successfully.",
            "success"
        )

    return redirect(
        url_for("users")
    )


# ============================================================
# TRAINER MANAGEMENT
# ============================================================

@app.route("/trainers")
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def trainers():

    all_trainers = (
        Trainer.query
        .order_by(
            Trainer.created_at.desc()
        )
        .all()
    )

    return render_template(
        "trainers.html",
        trainers=all_trainers
    )


# ============================================================
# CREATE TRAINER PROFILE
# ============================================================

@app.route(
    "/trainers/create",
    methods=["POST"]
)
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def create_trainer():

    if not validate_csrf():

        flash(
            "Invalid security token. Please try again.",
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    full_name = clean_text(
        request.form.get("full_name"),
        150
    )

    phone = clean_text(
        request.form.get("phone"),
        30
    )

    location = clean_text(
        request.form.get("location"),
        150
    )

    skills = clean_text(
        request.form.get("skills"),
        500
    )

    bio = clean_text(
        request.form.get("bio"),
        2000
    )

    availability = clean_text(
        request.form.get("availability"),
        50
    ).upper()

    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    if not full_name:

        flash(
            "Trainer name is required.",
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    # --------------------------------------------------------
    # EXPERIENCE
    # --------------------------------------------------------

    try:

        experience_years = (
            parse_non_negative_float(
                request.form.get(
                    "experience_years",
                    0
                ),
                "Experience"
            )
        )

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    # --------------------------------------------------------
    # RATE
    # --------------------------------------------------------

    try:

        hourly_rate = (
            parse_non_negative_float(
                request.form.get(
                    "hourly_rate",
                    0
                ),
                "Hourly rate"
            )
        )

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    # --------------------------------------------------------
    # AVAILABILITY
    # --------------------------------------------------------

    allowed_availability = {
        "AVAILABLE",
        "BUSY",
        "UNAVAILABLE"
    }

    if availability not in allowed_availability:

        availability = "AVAILABLE"

    # --------------------------------------------------------
    # CREATE PROFILE
    # --------------------------------------------------------

    trainer = Trainer(
        full_name=full_name,
        user_id=None,
        phone=phone or None,
        location=location or None,
        bio=bio or None,
        skills=skills or None,
        experience_years=experience_years,
        hourly_rate=hourly_rate,
        availability=availability,
        trainer_status="ACTIVE"
    )

    try:

        db.session.add(
            trainer
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to create trainer profile.",
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    flash(
        "Trainer profile created successfully. You can create the login later from User Management.",
        "success"
    )

    return redirect(
        url_for("trainers")
    )



# ============================================================
# EDIT TRAINER
# ============================================================

@app.route(
    "/trainers/<int:trainer_id>/edit",
    methods=["POST"]
)
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def edit_trainer(trainer_id):

    if not validate_csrf():
        flash(
            "Invalid security token.",
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    trainer = db.session.get(
        Trainer,
        trainer_id
    )

    if not trainer:
        flash(
            "Trainer not found.",
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    full_name = clean_text(
        request.form.get("full_name"),
        150
    )

    phone = clean_text(
        request.form.get("phone"),
        30
    )

    location = clean_text(
        request.form.get("location"),
        150
    )

    skills = clean_text(
        request.form.get("skills"),
        500
    )

    bio = clean_text(
        request.form.get("bio"),
        2000
    )

    availability = clean_text(
        request.form.get("availability"),
        50
    ).upper()

    if not full_name:
        flash(
            "Trainer name is required.",
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    try:

        experience_years = parse_non_negative_float(
            request.form.get(
                "experience_years",
                0
            ),
            "Experience"
        )

        hourly_rate = parse_non_negative_float(
            request.form.get(
                "hourly_rate",
                0
            ),
            "Hourly rate"
        )

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    allowed_availability = {
        "AVAILABLE",
        "BUSY",
        "UNAVAILABLE"
    }

    if availability not in allowed_availability:
        flash(
            "Invalid availability selected.",
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    trainer.full_name = full_name
    trainer.phone = phone or None
    trainer.location = location or None
    trainer.skills = skills or None
    trainer.bio = bio or None
    trainer.experience_years = experience_years
    trainer.hourly_rate = hourly_rate
    trainer.availability = availability

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to update trainer profile.",
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    flash(
        "Trainer profile updated successfully.",
        "success"
    )

    return redirect(
        url_for("trainers")
    )


# ============================================================
# TOGGLE TRAINER STATUS
# ============================================================

@app.route(
    "/trainers/<int:trainer_id>/toggle",
    methods=["POST"]
)
@roles_required("SUPER_ADMIN")
def toggle_trainer(trainer_id):

    if not validate_csrf():
        flash(
            "Invalid security token.",
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    trainer = db.session.get(
        Trainer,
        trainer_id
    )

    if not trainer:
        flash(
            "Trainer not found.",
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    trainer.trainer_status = (
        "INACTIVE"
        if trainer.trainer_status == "ACTIVE"
        else "ACTIVE"
    )

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to update trainer status.",
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    flash(
        (
            "Trainer activated successfully."
            if trainer.trainer_status == "ACTIVE"
            else "Trainer deactivated successfully."
        ),
        "success"
    )

    return redirect(
        url_for("trainers")
    )


# ============================================================
# DELETE TRAINER
# ============================================================

@app.route(
    "/trainers/<int:trainer_id>/delete",
    methods=["POST"]
)
@roles_required("SUPER_ADMIN")
def delete_trainer(trainer_id):

    if not validate_csrf():
        flash(
            "Invalid security token.",
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    trainer = db.session.get(
        Trainer,
        trainer_id
    )

    if not trainer:
        flash(
            "Trainer not found.",
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    # Keep the login account if one is linked.
    # Deleting a trainer profile must not delete a User.
    linked_user_id = trainer.user_id

    try:

        trainer.user_id = None

        db.session.delete(
            trainer
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to delete trainer.",
            "error"
        )

        return redirect(
            url_for("trainers")
        )

    if linked_user_id:
        flash(
            "Trainer profile deleted. The linked login account remains available.",
            "success"
        )
    else:
        flash(
            "Trainer profile deleted successfully.",
            "success"
        )

    return redirect(
        url_for("trainers")
    )


@app.route("/requirements")
@login_required
@roles_required("SUPER_ADMIN", "VENDOR")
def requirements():

    current_user = get_current_user()

    if current_user.role == "SUPER_ADMIN":
        requirement_query = Requirement.query
    else:
        requirement_query = Requirement.query.filter(
            Requirement.created_by == current_user.id
        )

    all_requirements = requirement_query.order_by(
        Requirement.created_at.desc()
    ).all()

    total_requirements = len(all_requirements)
    open_requirements = sum(1 for item in all_requirements if item.status == "OPEN")
    in_progress_requirements = sum(1 for item in all_requirements if item.status == "IN_PROGRESS")
    assigned_requirements = sum(1 for item in all_requirements if item.status == "ASSIGNED")
    completed_requirements = sum(1 for item in all_requirements if item.status == "COMPLETED")

    return render_template(
        "requirements.html",
        requirements=all_requirements,
        total_requirements=total_requirements,
        open_requirements=open_requirements,
        in_progress_requirements=in_progress_requirements,
        assigned_requirements=assigned_requirements,
        completed_requirements=completed_requirements
    )

# ============================================================
# CREATE REQUIREMENT
# ============================================================

@app.route(
    "/requirements/create",
    methods=["GET", "POST"]
)
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def create_requirement():

    if request.method == "GET":

        return render_template(
            "requirement_form.html",
            requirement=None,
            form_title="Create Requirement"
        )

    # --------------------------------------------------------
    # CSRF
    # --------------------------------------------------------

    if not validate_csrf():

        flash(
            "Invalid security token. Please try again.",
            "error"
        )

        return redirect(
            url_for("requirements")
        )

    # --------------------------------------------------------
    # FORM DATA
    # --------------------------------------------------------

    title = clean_text(
        request.form.get("title"),
        200
    )

    client_name = clean_text(
        request.form.get("client_name"),
        150
    )

    skill = clean_text(
        request.form.get("skill"),
        150
    )

    location = clean_text(
        request.form.get("location"),
        150
    )

    duration = clean_text(
        request.form.get("duration"),
        100
    )

    notes = clean_text(
        request.form.get("notes"),
        5000
    )

    # --------------------------------------------------------
    # REQUIRED FIELDS
    # --------------------------------------------------------

    if not title:

        flash(
            "Requirement title is required.",
            "error"
        )

        return redirect(
            url_for("create_requirement")
        )

    if not client_name:

        flash(
            "Client name is required.",
            "error"
        )

        return redirect(
            url_for("create_requirement")
        )

    if not skill:

        flash(
            "Skill or technology is required.",
            "error"
        )

        return redirect(
            url_for("create_requirement")
        )

    # --------------------------------------------------------
    # TRAINER COUNT
    # --------------------------------------------------------

    try:

        trainer_count = (
            parse_positive_integer(
                request.form.get(
                    "trainer_count",
                    1
                ),
                "Trainer count"
            )
        )

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for("create_requirement")
        )

    # --------------------------------------------------------
    # BUDGET
    # --------------------------------------------------------

    try:

        budget = (
            parse_non_negative_float(
                request.form.get(
                    "budget",
                    0
                ),
                "Budget"
            )
        )

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for("create_requirement")
        )

    # --------------------------------------------------------
    # START DATE
    # --------------------------------------------------------

    try:

        start_date = parse_optional_date(
            request.form.get("start_date")
        )

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for("create_requirement")
        )

    # --------------------------------------------------------
    # CREATE REQUIREMENT
    # --------------------------------------------------------

    current_user = get_current_user()

    requirement = Requirement(
        requirement_code=generate_requirement_code(),

        title=title,

        client_name=client_name,

        skill=skill,

        trainer_count=trainer_count,

        location=location or None,

        start_date=start_date,

        duration=duration or None,

        budget=budget,

        status="OPEN",

        notes=notes or None,

        created_by=current_user.id
    )

    try:

        db.session.add(
            requirement
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to create the requirement. Please try again.",
            "error"
        )

        return redirect(
            url_for("requirements")
        )

    flash(
        f"Requirement {requirement.requirement_code} created successfully.",
        "success"
    )

    return redirect(
        url_for("requirements")
    )


# ============================================================
# VIEW REQUIREMENT
# ============================================================

@app.route(
    "/requirements/<int:requirement_id>"
)
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def view_requirement(requirement_id):

    requirement = db.session.get(
        Requirement,
        requirement_id
    )

    if not requirement:

        flash(
            "Requirement not found.",
            "error"
        )

        return redirect(
            url_for("requirements")
        )

    current_user = get_current_user()
    if not vendor_can_access_requirement(requirement, current_user):
        flash("You are not authorized to access this requirement.", "error")
        return redirect(url_for("requirements"))

    return render_template(
        "requirement_view.html",
        requirement=requirement
    )


# ============================================================
# EDIT REQUIREMENT
# ============================================================

@app.route(
    "/requirements/<int:requirement_id>/edit",
    methods=["GET", "POST"]
)
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def edit_requirement(requirement_id):

    requirement = db.session.get(
        Requirement,
        requirement_id
    )

    if not requirement:

        flash(
            "Requirement not found.",
            "error"
        )

        return redirect(
            url_for("requirements")
        )

    current_user = get_current_user()
    if not vendor_can_access_requirement(requirement, current_user):
        flash("You are not authorized to access this requirement.", "error")
        return redirect(url_for("requirements"))

    if request.method == "GET":

        return render_template(
            "requirement_form.html",
            requirement=requirement,
            form_title="Edit Requirement"
        )

    # --------------------------------------------------------
    # CSRF
    # --------------------------------------------------------

    if not validate_csrf():

        flash(
            "Invalid security token.",
            "error"
        )

        return redirect(
            url_for(
                "edit_requirement",
                requirement_id=requirement.id
            )
        )

    # --------------------------------------------------------
    # FORM DATA
    # --------------------------------------------------------

    title = clean_text(
        request.form.get("title"),
        200
    )

    client_name = clean_text(
        request.form.get("client_name"),
        150
    )

    skill = clean_text(
        request.form.get("skill"),
        150
    )

    location = clean_text(
        request.form.get("location"),
        150
    )

    duration = clean_text(
        request.form.get("duration"),
        100
    )

    notes = clean_text(
        request.form.get("notes"),
        5000
    )

    if not title:

        flash(
            "Requirement title is required.",
            "error"
        )

        return redirect(
            url_for(
                "edit_requirement",
                requirement_id=requirement.id
            )
        )

    if not client_name:

        flash(
            "Client name is required.",
            "error"
        )

        return redirect(
            url_for(
                "edit_requirement",
                requirement_id=requirement.id
            )
        )

    if not skill:

        flash(
            "Skill or technology is required.",
            "error"
        )

        return redirect(
            url_for(
                "edit_requirement",
                requirement_id=requirement.id
            )
        )

    try:

        trainer_count = (
            parse_positive_integer(
                request.form.get(
                    "trainer_count",
                    1
                ),
                "Trainer count"
            )
        )

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for(
                "edit_requirement",
                requirement_id=requirement.id
            )
        )

    try:

        budget = (
            parse_non_negative_float(
                request.form.get(
                    "budget",
                    0
                ),
                "Budget"
            )
        )

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for(
                "edit_requirement",
                requirement_id=requirement.id
            )
        )

    try:

        start_date = parse_optional_date(
            request.form.get("start_date")
        )

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for(
                "edit_requirement",
                requirement_id=requirement.id
            )
        )

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    requirement.title = title

    requirement.client_name = client_name

    requirement.skill = skill

    requirement.trainer_count = trainer_count

    requirement.location = (
        location or None
    )

    requirement.start_date = start_date

    requirement.duration = (
        duration or None
    )

    requirement.budget = budget

    requirement.notes = (
        notes or None
    )

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to update the requirement.",
            "error"
        )

        return redirect(
            url_for(
                "requirements"
            )
        )

    flash(
        f"Requirement {requirement.requirement_code} updated successfully.",
        "success"
    )

    return redirect(
        url_for("requirements")
    )


# ============================================================
# UPDATE REQUIREMENT STATUS
# ============================================================

@app.route(
    "/requirements/<int:requirement_id>/status",
    methods=["POST"]
)
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def update_requirement_status(
    requirement_id
):

    if not validate_csrf():

        flash(
            "Invalid security token.",
            "error"
        )

        return redirect(
            url_for("requirements")
        )

    requirement = db.session.get(
        Requirement,
        requirement_id
    )

    if not requirement:

        flash(
            "Requirement not found.",
            "error"
        )

        return redirect(
            url_for("requirements")
        )

    current_user = get_current_user()
    if not vendor_can_access_requirement(requirement, current_user):
        flash("You are not authorized to access this requirement.", "error")
        return redirect(url_for("requirements"))

    status = clean_text(
        request.form.get("status"),
        30
    ).upper()

    if status not in REQUIREMENT_STATUSES:

        flash(
            "Invalid requirement status.",
            "error"
        )

        return redirect(
            url_for("requirements")
        )

    requirement.status = status

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to update requirement status.",
            "error"
        )

        return redirect(
            url_for("requirements")
        )

    flash(
        f"Requirement {requirement.requirement_code} status updated.",
        "success"
    )

    return redirect(
        url_for("requirements")
    )


# ============================================================
# DELETE REQUIREMENT
# ============================================================

@app.route(
    "/requirements/<int:requirement_id>/delete",
    methods=["POST"]
)
@roles_required("SUPER_ADMIN", "VENDOR")
def delete_requirement(
    requirement_id
):

    if not validate_csrf():

        flash(
            "Invalid security token.",
            "error"
        )

        return redirect(
            url_for("requirements")
        )

    requirement = db.session.get(
        Requirement,
        requirement_id
    )

    if not requirement:

        flash(
            "Requirement not found.",
            "error"
        )

        return redirect(
            url_for("requirements")
        )

    current_user = get_current_user()
    if not vendor_can_access_requirement(requirement, current_user):
        flash("You are not authorized to access this requirement.", "error")
        return redirect(url_for("requirements"))

    requirement_code = (
        requirement.requirement_code
    )

    try:

        db.session.delete(
            requirement
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to delete the requirement.",
            "error"
        )

        return redirect(
            url_for("requirements")
        )

    flash(
        f"Requirement {requirement_code} deleted successfully.",
        "success"
    )

    return redirect(
        url_for("requirements")
    )


# ============================================================
# PROJECT MANAGEMENT
# ============================================================

@app.route("/projects")
@login_required
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def projects():

    current_user = get_current_user()

    if current_user.role == "SUPER_ADMIN":
        project_query = Project.query
        requirement_query = Requirement.query
    else:
        project_query = Project.query.filter(
            Project.created_by == current_user.id
        )
        requirement_query = Requirement.query.filter(
            Requirement.created_by == current_user.id
        )

    all_projects = (
        project_query
        .order_by(Project.created_at.desc())
        .all()
    )

    available_requirements = (
        requirement_query
        .filter(
            Requirement.status.in_([
                "OPEN",
                "IN_PROGRESS",
                "ASSIGNED"
            ])
        )
        .order_by(Requirement.created_at.desc())
        .all()
    )

    available_trainers = (
        Trainer.query
        .filter_by(trainer_status="ACTIVE")
        .order_by(Trainer.full_name.asc())
        .all()
    )

    total_projects = len(all_projects)
    planning_projects = sum(1 for item in all_projects if item.status == "PLANNING")
    active_projects = sum(1 for item in all_projects if item.status == "ACTIVE")
    completed_projects = sum(1 for item in all_projects if item.status == "COMPLETED")
    cancelled_projects = sum(1 for item in all_projects if item.status == "CANCELLED")

    return render_template(
        "projects.html",
        projects=all_projects,
        requirements=available_requirements,
        available_trainers=available_trainers,
        total_projects=total_projects,
        planning_projects=planning_projects,
        active_projects=active_projects,
        completed_projects=completed_projects,
        cancelled_projects=cancelled_projects,
        project_statuses=PROJECT_STATUSES
    )


# ============================================================
# CREATE PROJECT
# ============================================================

@app.route("/projects/create", methods=["POST"])
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def create_project():

    if not validate_csrf():
        flash(
            "Invalid security token. Please try again.",
            "error"
        )
        return redirect(url_for("projects"))

    project_name = clean_text(
        request.form.get("project_name"),
        200
    )

    requirement_id = clean_text(
        request.form.get("requirement_id"),
        20
    )

    location = clean_text(
        request.form.get("location"),
        150
    )

    notes = clean_text(
        request.form.get("notes"),
        5000
    )

    if not project_name:
        flash("Project name is required.", "error")
        return redirect(url_for("projects"))

    if not requirement_id:
        flash("Please select a requirement.", "error")
        return redirect(url_for("projects"))

    try:
        requirement_id = int(requirement_id)
    except (TypeError, ValueError):
        flash("Invalid requirement selection.", "error")
        return redirect(url_for("projects"))

    requirement = db.session.get(
        Requirement,
        requirement_id
    )

    if not requirement:
        flash(
            "Selected requirement was not found.",
            "error"
        )
        return redirect(url_for("projects"))

    current_user = get_current_user()
    if not vendor_can_access_requirement(requirement, current_user):
        flash("You are not authorized to use this requirement.", "error")
        return redirect(url_for("projects"))

    # Only active requirement stages can be converted into projects.
    if requirement.status not in {"OPEN", "IN_PROGRESS", "ASSIGNED"}:
        flash(
            "Only OPEN, IN_PROGRESS, or ASSIGNED requirements can be converted into a project.",
            "error"
        )
        return redirect(url_for("projects"))

    try:
        start_date = parse_optional_date(
            request.form.get("start_date")
        )
    except ValueError:
        flash(
            "Project start date must be a valid date.",
            "error"
        )
        return redirect(url_for("projects"))

    end_date_raw = clean_text(
        request.form.get("end_date"),
        20
    )

    end_date = None

    if end_date_raw:
        try:
            end_date = datetime.strptime(
                end_date_raw,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            flash(
                "Project end date must be a valid date.",
                "error"
            )
            return redirect(url_for("projects"))

    if (
        start_date
        and end_date
        and end_date < start_date
    ):
        flash(
            "End date cannot be before start date.",
            "error"
        )
        return redirect(url_for("projects"))

    try:
        budget = parse_non_negative_float(
            request.form.get("budget", 0),
            "Budget"
        )
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("projects"))

    current_user = get_current_user()

    project = Project(
        project_code=generate_project_code(),
        project_name=project_name,
        requirement_id=requirement.id,
        client_name=requirement.client_name,
        skill=requirement.skill,
        location=location or requirement.location or None,
        start_date=start_date,
        end_date=end_date,
        budget=budget,
        status="PLANNING",
        notes=notes or None,
        created_by=current_user.id
    )

    try:
        db.session.add(project)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(
            "Unable to create the project. Please try again.",
            "error"
        )
        return redirect(url_for("projects"))

    flash(
        f"Project {project.project_code} created successfully.",
        "success"
    )

    return redirect(url_for("projects"))


# ============================================================
# VIEW PROJECT
# ============================================================

@app.route("/projects/<int:project_id>")
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def view_project(project_id):

    project = db.session.get(
        Project,
        project_id
    )

    if not project:
        flash("Project not found.", "error")
        return redirect(url_for("projects"))

    current_user = get_current_user()
    if not vendor_can_access_project(project, current_user):
        flash("You are not authorized to access this project.", "error")
        return redirect(url_for("projects"))

    return render_template(
        "project_view.html",
        project=project
    )


# ============================================================
# ASSIGN TRAINER TO PROJECT
# ============================================================

@app.route(
    "/projects/<int:project_id>/trainers/assign",
    methods=["POST"]
)
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def assign_trainer_to_project(project_id):

    if not validate_csrf():
        flash("Invalid security token.", "error")
        return redirect(url_for("projects"))

    project = db.session.get(Project, project_id)

    if not project:
        flash("Project not found.", "error")
        return redirect(url_for("projects"))

    current_user = get_current_user()
    if not vendor_can_access_project(project, current_user):
        flash("You are not authorized to access this project.", "error")
        return redirect(url_for("projects"))

    trainer_id_raw = clean_text(
        request.form.get("trainer_id"),
        20
    )

    if not trainer_id_raw:
        flash("Please select a trainer.", "error")
        return redirect(url_for("projects"))

    try:
        trainer_id = int(trainer_id_raw)
    except (TypeError, ValueError):
        flash("Invalid trainer selection.", "error")
        return redirect(url_for("projects"))

    trainer = db.session.get(Trainer, trainer_id)

    if not trainer:
        flash("Selected trainer was not found.", "error")
        return redirect(url_for("projects"))

    if trainer.trainer_status != "ACTIVE":
        flash("Only active trainers can be assigned to a project.", "error")
        return redirect(url_for("projects"))

    existing = ProjectTrainer.query.filter_by(
        project_id=project.id,
        trainer_id=trainer.id
    ).first()

    if existing:
        flash(
            f"{trainer.full_name} is already linked to this project.",
            "error"
        )
        return redirect(url_for("projects"))

    current_user = get_current_user()

    assignment = ProjectTrainer(
        project_id=project.id,
        trainer_id=trainer.id,
        assigned_by=current_user.id,
        assignment_status="PENDING"
    )

    try:
        db.session.add(assignment)
        db.session.flush()

        if trainer.user_id:
            db.session.add(
                Notification(
                    user_id=trainer.user_id,
                    title="Project Assignment",
                    message=(
                        f"You have been assigned to project "
                        f"{project.project_code} - {project.project_name}."
                    ),
                    notification_type="PROJECT",
                    related_type="PROJECT",
                    related_id=project.id
                )
            )

        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(
            "Unable to assign the trainer to this project.",
            "error"
        )
        return redirect(url_for("projects"))

    flash(
        f"Trainer {trainer.full_name} has been added to {project.project_code}.",
        "success"
    )

    return redirect(url_for("projects"))


# ============================================================
# REMOVE TRAINER FROM PROJECT
# ============================================================

@app.route(
    "/projects/<int:project_id>/trainers/<int:assignment_id>/remove",
    methods=["POST"]
)
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def remove_trainer_from_project(project_id, assignment_id):

    if not validate_csrf():
        flash("Invalid security token.", "error")
        return redirect(url_for("projects"))

    project = db.session.get(Project, project_id)
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for("projects"))

    current_user = get_current_user()
    if not vendor_can_access_project(project, current_user):
        flash("You are not authorized to access this project.", "error")
        return redirect(url_for("projects"))

    assignment = db.session.get(ProjectTrainer, assignment_id)

    if not assignment or assignment.project_id != project_id:
        flash("Trainer assignment not found.", "error")
        return redirect(url_for("projects"))

    trainer_name = assignment.trainer.full_name if assignment.trainer else "Trainer"

    try:
        db.session.delete(assignment)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(
            "Unable to remove the trainer from this project.",
            "error"
        )
        return redirect(url_for("projects"))

    flash(
        f"{trainer_name} was removed from the project.",
        "success"
    )

    return redirect(url_for("projects"))


# ============================================================
# EDIT PROJECT
# ============================================================

@app.route(
    "/projects/<int:project_id>/edit",
    methods=["GET", "POST"]
)
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def edit_project(project_id):

    project = db.session.get(
        Project,
        project_id
    )

    if not project:
        flash("Project not found.", "error")
        return redirect(url_for("projects"))

    current_user = get_current_user()
    if not vendor_can_access_project(project, current_user):
        flash("You are not authorized to access this project.", "error")
        return redirect(url_for("projects"))

    if request.method == "GET":
        return render_template(
            "project_form.html",
            project=project,
            form_title="Edit Project"
        )

    if not validate_csrf():
        flash(
            "Invalid security token. Please try again.",
            "error"
        )
        return redirect(url_for("projects"))

    project_name = clean_text(
        request.form.get("project_name"),
        200
    )

    location = clean_text(
        request.form.get("location"),
        150
    )

    notes = clean_text(
        request.form.get("notes"),
        5000
    )

    status = clean_text(
        request.form.get(
            "status",
            project.status
        ),
        30
    ).upper()

    if not project_name:
        flash("Project name is required.", "error")
        return redirect(url_for("projects"))

    if status not in PROJECT_STATUSES:
        flash("Invalid project status.", "error")
        return redirect(url_for("projects"))

    try:
        start_date = parse_optional_date(
            request.form.get("start_date")
        )
    except ValueError:
        flash(
            "Project start date must be a valid date.",
            "error"
        )
        return redirect(url_for("projects"))

    end_date_raw = clean_text(
        request.form.get("end_date"),
        20
    )

    end_date = None

    if end_date_raw:
        try:
            end_date = datetime.strptime(
                end_date_raw,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            flash(
                "Project end date must be a valid date.",
                "error"
            )
            return redirect(url_for("projects"))

    if (
        start_date
        and end_date
        and end_date < start_date
    ):
        flash(
            "End date cannot be before start date.",
            "error"
        )
        return redirect(url_for("projects"))

    try:
        budget = parse_non_negative_float(
            request.form.get("budget", 0),
            "Budget"
        )
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("projects"))

    project.project_name = project_name
    project.location = location or None
    project.start_date = start_date
    project.end_date = end_date
    project.budget = budget
    project.status = status
    project.notes = notes or None

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(
            "Unable to update the project.",
            "error"
        )
        return redirect(url_for("projects"))

    flash(
        f"Project {project.project_code} updated successfully.",
        "success"
    )

    return redirect(url_for("projects"))


# ============================================================
# UPDATE PROJECT STATUS
# ============================================================

@app.route(
    "/projects/<int:project_id>/status",
    methods=["POST"]
)
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def update_project_status(project_id):

    if not validate_csrf():
        flash(
            "Invalid security token.",
            "error"
        )
        return redirect(url_for("projects"))

    project = db.session.get(
        Project,
        project_id
    )

    if not project:
        flash("Project not found.", "error")
        return redirect(url_for("projects"))

    current_user = get_current_user()
    if not vendor_can_access_project(project, current_user):
        flash("You are not authorized to access this project.", "error")
        return redirect(url_for("projects"))

    status = clean_text(
        request.form.get("status"),
        30
    ).upper()

    if status not in PROJECT_STATUSES:
        flash("Invalid project status.", "error")
        return redirect(url_for("projects"))

    project.status = status

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(
            "Unable to update project status.",
            "error"
        )
        return redirect(url_for("projects"))

    flash(
        f"Project {project.project_code} status updated.",
        "success"
    )

    return redirect(url_for("projects"))


# ============================================================
# DELETE PROJECT
# ============================================================

@app.route(
    "/projects/<int:project_id>/delete",
    methods=["POST"]
)
@roles_required("SUPER_ADMIN", "VENDOR")
def delete_project(project_id):

    if not validate_csrf():
        flash(
            "Invalid security token.",
            "error"
        )
        return redirect(url_for("projects"))

    project = db.session.get(
        Project,
        project_id
    )

    if not project:
        flash("Project not found.", "error")
        return redirect(url_for("projects"))

    current_user = get_current_user()
    if not vendor_can_access_project(project, current_user):
        flash("You are not authorized to access this project.", "error")
        return redirect(url_for("projects"))

    project_code = project.project_code

    try:
        db.session.delete(project)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash(
            "Unable to delete the project.",
            "error"
        )
        return redirect(url_for("projects"))

    flash(
        f"Project {project_code} deleted successfully.",
        "success"
    )

    return redirect(url_for("projects"))


# ============================================================
# APPLICATIONS
# ============================================================

APPLICATION_STATUSES = {
    "PENDING",
    "ACCEPTED",
    "REJECTED",
    "SELECTED",
    "WITHDRAWN"
}


@app.route("/applications")
@login_required
@roles_required(
    "SUPER_ADMIN",
    "VENDOR",
    "TRAINER"
)
def applications():

    current_user = get_current_user()

    if current_user.role == "TRAINER":

        trainer = Trainer.query.filter_by(
            user_id=current_user.id
        ).first()

        if trainer:
            applications_list = (
                Application.query
                .filter_by(trainer_id=trainer.id)
                .order_by(Application.created_at.desc())
                .all()
            )
        else:
            applications_list = []

    elif current_user.role == "SUPER_ADMIN":
        applications_list = (
            Application.query
            .order_by(Application.created_at.desc())
            .all()
        )
    else:
        applications_list = (
            Application.query
            .join(Requirement, Application.requirement_id == Requirement.id)
            .filter(Requirement.created_by == current_user.id)
            .order_by(Application.created_at.desc())
            .all()
        )

    if current_user.role == "SUPER_ADMIN":
        requirements = (
            Requirement.query
            .order_by(Requirement.created_at.desc())
            .all()
        )
    else:
        requirements = (
            Requirement.query
            .filter(Requirement.created_by == current_user.id)
            .order_by(Requirement.created_at.desc())
            .all()
        )

    trainers = (
        Trainer.query
        .filter_by(trainer_status="ACTIVE")
        .order_by(Trainer.full_name.asc())
        .all()
    )

    total_applications = len(applications_list)
    pending_applications = sum(
        1 for application in applications_list
        if application.status == "PENDING"
    )
    accepted_applications = sum(
        1 for application in applications_list
        if application.status == "ACCEPTED"
    )
    selected_applications = sum(
        1 for application in applications_list
        if application.status == "SELECTED"
    )

    return render_template(
        "applications.html",
        applications=applications_list,
        requirements=requirements,
        trainers=trainers,
        total_applications=total_applications,
        pending_applications=pending_applications,
        accepted_applications=accepted_applications,
        selected_applications=selected_applications
    )


# ============================================================
# CREATE APPLICATION
# ============================================================

@app.route("/applications/create", methods=["POST"])
@login_required
@roles_required("SUPER_ADMIN", "VENDOR")
def create_application():

    if not validate_csrf():
        flash("Invalid security token. Please try again.", "error")
        return redirect(url_for("applications"))

    requirement_id = request.form.get("requirement_id", type=int)
    trainer_id = request.form.get("trainer_id", type=int)
    match_score_raw = request.form.get("match_score", "").strip()
    message = clean_text(request.form.get("message"), 5000)

    if not requirement_id or not trainer_id:
        flash("Requirement and trainer are required.", "error")
        return redirect(url_for("applications"))

    requirement = db.session.get(Requirement, requirement_id)
    if not requirement:
        flash("Selected requirement was not found.", "error")
        return redirect(url_for("applications"))

    current_user = get_current_user()
    if not vendor_can_access_requirement(requirement, current_user):
        flash("You are not authorized to create an application for this requirement.", "error")
        return redirect(url_for("applications"))

    trainer = db.session.get(Trainer, trainer_id)
    if not trainer:
        flash("Selected trainer was not found.", "error")
        return redirect(url_for("applications"))

    if trainer.trainer_status != "ACTIVE":
        flash("The selected trainer is not active.", "error")
        return redirect(url_for("applications"))

    match_score = None
    if match_score_raw:
        try:
            match_score = float(match_score_raw)
        except (TypeError, ValueError):
            flash("Match score must be a number.", "error")
            return redirect(url_for("applications"))

        if match_score < 0 or match_score > 100:
            flash("Match score must be between 0 and 100.", "error")
            return redirect(url_for("applications"))

    existing_application = Application.query.filter_by(
        requirement_id=requirement_id,
        trainer_id=trainer_id
    ).first()

    if existing_application:
        flash(
            "An application already exists for this trainer and requirement.",
            "error"
        )
        return redirect(url_for("applications"))

    current_user = get_current_user()
    application = Application(
        requirement_id=requirement_id,
        trainer_id=trainer_id,
        created_by=current_user.id,
        source="VENDOR_INVITED",
        status="PENDING",
        match_score=match_score,
        message=message or None
    )

    try:
        db.session.add(application)
        db.session.flush()

        # Notify the trainer who received the application.
        if trainer.user_id:
            db.session.add(
                Notification(
                    user_id=trainer.user_id,
                    title="New Application Received",
                    message=(
                        f"You have received a new application for "
                        f"{requirement.title}."
                    ),
                    notification_type="APPLICATION",
                    related_type="APPLICATION",
                    related_id=application.id
                )
            )

        db.session.commit()
        flash("Trainer application created successfully.", "success")
    except Exception:
        db.session.rollback()
        flash("Unable to create application.", "error")

    return redirect(url_for("applications"))


# ============================================================
# UPDATE APPLICATION STATUS
# ============================================================

@app.route("/applications/<int:application_id>/status", methods=["POST"])
@login_required
@roles_required("SUPER_ADMIN", "VENDOR", "TRAINER")
def update_application_status(application_id):

    if not validate_csrf():
        flash("Invalid security token. Please try again.", "error")
        return redirect(url_for("applications"))

    application = db.session.get(Application, application_id)
    if not application:
        flash("Application not found.", "error")
        return redirect(url_for("applications"))

    new_status = clean_text(request.form.get("status", ""), 30).upper()
    response_note = clean_text(request.form.get("response_note", ""), 5000)

    if new_status not in APPLICATION_STATUSES:
        flash("Invalid application status.", "error")
        return redirect(url_for("applications"))

    current_user = get_current_user()

    if current_user.role == "VENDOR" and not vendor_can_access_application(application, current_user):
        flash("You are not authorized to update this application.", "error")
        return redirect(url_for("applications"))

    if current_user.role == "TRAINER":

        trainer = Trainer.query.filter_by(
            user_id=current_user.id
        ).first()

        if not trainer:
            flash("Trainer profile not found.", "error")
            return redirect(url_for("applications"))

        if application.trainer_id != trainer.id:
            flash("You are not authorized to update this application.", "error")
            return redirect(url_for("applications"))

        if application.status != "PENDING":
            flash("This application can no longer be responded to.", "error")
            return redirect(url_for("applications"))

        if new_status not in {"ACCEPTED", "REJECTED"}:
            flash(
                "Trainer can only accept or reject a pending application.",
                "error"
            )
            return redirect(url_for("applications"))

    else:

        current_status = application.status
        allowed_transitions = {
            "PENDING": {"REJECTED", "WITHDRAWN"},
            "ACCEPTED": {"SELECTED", "REJECTED", "WITHDRAWN"},
            "REJECTED": {"PENDING"},
            "WITHDRAWN": {"PENDING"},
            "SELECTED": set()
        }

        if new_status not in allowed_transitions.get(current_status, set()):
            flash(
                f"Cannot change application from {current_status} to {new_status}.",
                "error"
            )
            return redirect(url_for("applications"))

        if new_status == "SELECTED":

            requirement = application.requirement
            if not requirement:
                flash(
                    "Requirement associated with this application was not found.",
                    "error"
                )
                return redirect(url_for("applications"))

            selected_count = Application.query.filter(
                Application.requirement_id == requirement.id,
                Application.status == "SELECTED"
            ).count()

            trainer_count = requirement.trainer_count or 0
            if trainer_count > 0 and selected_count >= trainer_count:
                flash(
                    "The required number of trainers has already been selected.",
                    "error"
                )
                return redirect(url_for("applications"))

    application.status = new_status

    if response_note:
        application.response_note = response_note

    if new_status == "SELECTED":

        requirement = application.requirement

        if requirement:
            trainer_count = requirement.trainer_count or 0

            if trainer_count > 0:
                db.session.flush()

                selected_count = Application.query.filter(
                    Application.requirement_id == requirement.id,
                    Application.status == "SELECTED"
                ).count()

                if selected_count >= trainer_count:
                    requirement.status = "ASSIGNED"

    try:
        requirement = application.requirement
        trainer = application.trainer

        # --------------------------------------------------------
        # Notify the opposite party about the application update.
        # --------------------------------------------------------
        if current_user.role == "TRAINER":

            vendor_user_id = (
                requirement.created_by
                if requirement
                else None
            )

            if vendor_user_id and new_status in {"ACCEPTED", "REJECTED"}:
                title = (
                    "Application Accepted"
                    if new_status == "ACCEPTED"
                    else "Application Rejected"
                )
                message = (
                    f"{trainer.full_name} accepted the application for "
                    f"{requirement.title}."
                    if new_status == "ACCEPTED"
                    else
                    f"{trainer.full_name} rejected the application for "
                    f"{requirement.title}."
                )

                db.session.add(
                    Notification(
                        user_id=vendor_user_id,
                        title=title,
                        message=message,
                        notification_type="APPLICATION",
                        related_type="APPLICATION",
                        related_id=application.id
                    )
                )

        elif current_user.role in {"SUPER_ADMIN", "VENDOR"}:

            if trainer and trainer.user_id and new_status in {
                "SELECTED",
                "REJECTED",
                "WITHDRAWN",
                "PENDING"
            }:
                if new_status == "SELECTED":
                    title = "Trainer Selected"
                    message = (
                        f"You have been selected for "
                        f"{requirement.title}."
                    )
                elif new_status == "REJECTED":
                    title = "Application Rejected"
                    message = (
                        f"Your application for {requirement.title} "
                        f"has been rejected."
                    )
                elif new_status == "WITHDRAWN":
                    title = "Application Withdrawn"
                    message = (
                        f"Your application for {requirement.title} "
                        f"has been withdrawn."
                    )
                else:
                    title = "Application Reopened"
                    message = (
                        f"Your application for {requirement.title} "
                        f"has been reopened."
                    )

                db.session.add(
                    Notification(
                        user_id=trainer.user_id,
                        title=title,
                        message=message,
                        notification_type="APPLICATION",
                        related_type="APPLICATION",
                        related_id=application.id
                    )
                )

        db.session.commit()
        flash(
            f"Application status changed to {new_status.title()}.",
            "success"
        )
    except Exception:
        db.session.rollback()
        flash("Unable to update application status.", "error")

    return redirect(url_for("applications"))


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "service": "QT Platform"
    }


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    with app.app_context():

        # ====================================================
        # CREATE TABLES
        # ====================================================
        #
        # db.create_all() creates tables that do not exist.
        # It does not add newly introduced columns to an
        # already-existing SQLite table.
        #
        db.create_all()

        # ====================================================
        # UPDATE COMMUNICATION TABLE
        # ====================================================
        #
        # The Communication model now supports attachments.
        # Add the four attachment columns to older databases
        # automatically without deleting existing data.
        #
        try:

            result = db.session.execute(
                text("PRAGMA table_info(communications)")
            )

            existing_columns = {
                row[1]
                for row in result.fetchall()
            }

            if "attachment_name" not in existing_columns:

                db.session.execute(
                    text(
                        """
                        ALTER TABLE communications
                        ADD COLUMN attachment_name VARCHAR(255)
                        """
                    )
                )

                print(
                    "Added communications.attachment_name"
                )

            if "attachment_path" not in existing_columns:

                db.session.execute(
                    text(
                        """
                        ALTER TABLE communications
                        ADD COLUMN attachment_path VARCHAR(500)
                        """
                    )
                )

                print(
                    "Added communications.attachment_path"
                )

            if "attachment_type" not in existing_columns:

                db.session.execute(
                    text(
                        """
                        ALTER TABLE communications
                        ADD COLUMN attachment_type VARCHAR(100)
                        """
                    )
                )

                print(
                    "Added communications.attachment_type"
                )

            if "attachment_size" not in existing_columns:

                db.session.execute(
                    text(
                        """
                        ALTER TABLE communications
                        ADD COLUMN attachment_size INTEGER
                        """
                    )
                )

                print(
                    "Added communications.attachment_size"
                )

            db.session.commit()

            print(
                "Communication attachment columns checked successfully."
            )

        except Exception as error:

            db.session.rollback()

            print(
                "Communication database update failed:"
            )

            print(error)

        # ====================================================
        # CREATE DEFAULT SUPER ADMIN
        # ====================================================

        admin = (
            User.query
            .filter_by(
                email="admin@qtplatform.com"
            )
            .first()
        )

        if not admin:

            admin = User(
                full_name="System Administrator",

                email="admin@qtplatform.com",

                password_hash=hash_password(
                    "Admin@123"
                ),

                role="SUPER_ADMIN",

                is_active=True
            )

            db.session.add(
                admin
            )

            db.session.commit()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()


# SCHEDULE
# ============================================================

SCHEDULE_MODES = {
    "ONLINE",
    "OFFLINE",
    "HYBRID"
}

SCHEDULE_STATUSES = {
    "SCHEDULED",
    "COMPLETED",
    "CANCELLED"
}


def vendor_can_access_schedule(schedule_item, current_user=None):

    if current_user is None:
        current_user = get_current_user()

    if not current_user or not schedule_item:
        return False

    if current_user.role == "SUPER_ADMIN":
        return True

    if current_user.role == "VENDOR":
        return (
            schedule_item.project is not None
            and schedule_item.project.created_by == current_user.id
        )

    if current_user.role == "TRAINER":
        return (
            current_user.trainer_profile is not None
            and schedule_item.trainer_id == current_user.trainer_profile.id
        )

    return False


def parse_datetime_local(value, field_name):

    value = clean_text(value, 30)

    if not value:
        raise ValueError(
            f"{field_name} is required."
        )

    formats = (
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M"
    )

    for date_format in formats:

        try:
            return datetime.strptime(
                value,
                date_format
            )

        except ValueError:
            continue

    raise ValueError(
        f"{field_name} must be a valid date and time."
    )


def generate_schedule_code():

    last_schedule = (
        Schedule.query
        .order_by(Schedule.id.desc())
        .first()
    )

    next_number = (
        last_schedule.id + 1
        if last_schedule
        else 1
    )

    return f"QT-SCH-{next_number:04d}"


def get_schedule_projects(current_user):

    if current_user.role == "SUPER_ADMIN":

        return (
            Project.query
            .filter(
                Project.status != "CANCELLED"
            )
            .order_by(
                Project.project_code.asc()
            )
            .all()
        )

    if current_user.role == "VENDOR":

        return (
            Project.query
            .filter(
                Project.created_by == current_user.id,
                Project.status != "CANCELLED"
            )
            .order_by(
                Project.project_code.asc()
            )
            .all()
        )

    return []


def get_project_trainers(project_id):

    assignments = (
        ProjectTrainer.query
        .join(
            Trainer,
            ProjectTrainer.trainer_id == Trainer.id
        )
        .filter(
            ProjectTrainer.project_id == project_id,
            Trainer.trainer_status == "ACTIVE"
        )
        .order_by(
            Trainer.full_name.asc()
        )
        .all()
    )

    return [
        {
            "id": assignment.trainer_id,
            "name": assignment.trainer.full_name
        }
        for assignment in assignments
        if assignment.trainer
    ]


# ============================================================
# SCHEDULE LIST
# ============================================================

@app.route("/schedule")
@login_required
def schedule():

    current_user = get_current_user()

    if current_user.role == "SUPER_ADMIN":

        schedule_query = Schedule.query

    elif current_user.role == "VENDOR":

        schedule_query = (
            Schedule.query
            .join(
                Project,
                Schedule.project_id == Project.id
            )
            .filter(
                Project.created_by == current_user.id
            )
        )

    elif (
        current_user.role == "TRAINER"
        and current_user.trainer_profile
    ):

        schedule_query = (
            Schedule.query
            .filter(
                Schedule.trainer_id
                == current_user.trainer_profile.id
            )
        )

    else:

        schedule_query = Schedule.query.filter(False)

    schedules = (
        schedule_query
        .order_by(
            Schedule.start_datetime.asc()
        )
        .all()
    )

    today = datetime.now()

    upcoming_schedules = sum(
        1
        for item in schedules
        if (
            item.status == "SCHEDULED"
            and item.start_datetime >= today
        )
    )

    completed_schedules = sum(
        1
        for item in schedules
        if item.status == "COMPLETED"
    )

    cancelled_schedules = sum(
        1
        for item in schedules
        if item.status == "CANCELLED"
    )

    projects = []

    if current_user.role in {
        "SUPER_ADMIN",
        "VENDOR"
    }:

        projects = get_schedule_projects(
            current_user
        )

    trainer_map = {}

    for project in projects:

        trainer_map[str(project.id)] = (
            get_project_trainers(
                project.id
            )
        )

    return render_template(
        "schedule.html",
        schedules=schedules,
        projects=projects,
        trainer_map=trainer_map,
        total_schedules=len(schedules),
        upcoming_schedules=upcoming_schedules,
        completed_schedules=completed_schedules,
        cancelled_schedules=cancelled_schedules,
        form_mode="create",
        edit_schedule=None
    )


# ============================================================
# CREATE SCHEDULE
# ============================================================

@app.route(
    "/schedule/create",
    methods=["POST"]
)
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def create_schedule():

    current_user = get_current_user()

    if not validate_csrf():

        flash(
            "Invalid security token. Please try again.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    project_id_raw = clean_text(
        request.form.get("project_id"),
        20
    )

    trainer_id_raw = clean_text(
        request.form.get("trainer_id"),
        20
    )

    title = clean_text(
        request.form.get("title"),
        200
    )

    mode = clean_text(
        request.form.get("mode"),
        30
    ).upper()

    location = clean_text(
        request.form.get("location"),
        250
    )

    meeting_link = clean_text(
        request.form.get("meeting_link"),
        500
    )

    notes = clean_text(
        request.form.get("notes"),
        5000
    )

    if not project_id_raw or not trainer_id_raw:

        flash(
            "Project and trainer are required.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    try:

        project_id = int(
            project_id_raw
        )

        trainer_id = int(
            trainer_id_raw
        )

    except (TypeError, ValueError):

        flash(
            "Invalid project or trainer selection.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    project = db.session.get(
        Project,
        project_id
    )

    trainer = db.session.get(
        Trainer,
        trainer_id
    )

    if not project or not vendor_can_access_project(
        project,
        current_user
    ):

        flash(
            "You are not authorized to schedule this project.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if (
        project.status
        in {"CANCELLED", "COMPLETED"}
    ):

        flash(
            "Schedules cannot be created for this project.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if (
        not trainer
        or trainer.trainer_status != "ACTIVE"
    ):

        flash(
            "Only an active trainer can be scheduled.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    assignment = (
        ProjectTrainer.query
        .filter_by(
            project_id=project.id,
            trainer_id=trainer.id
        )
        .first()
    )

    if not assignment:

        flash(
            "The selected trainer is not assigned to this project.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if not title:

        title = project.project_name

    if mode not in SCHEDULE_MODES:

        flash(
            "Invalid training mode.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if (
        mode in {"ONLINE", "HYBRID"}
        and not meeting_link
    ):

        flash(
            "A meeting link is required for online or hybrid training.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if (
        mode == "OFFLINE"
        and not location
    ):

        flash(
            "A location is required for offline training.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    try:

        start_datetime = parse_datetime_local(
            request.form.get(
                "start_datetime"
            ),
            "Start date and time"
        )

        end_datetime = parse_datetime_local(
            request.form.get(
                "end_datetime"
            ),
            "End date and time"
        )

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if end_datetime <= start_datetime:

        flash(
            "End time must be after the start time.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if (
        project.start_date
        and start_datetime.date()
        < project.start_date
    ):

        flash(
            "Schedule cannot start before the project start date.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if (
        project.end_date
        and end_datetime.date()
        > project.end_date
    ):

        flash(
            "Schedule cannot extend beyond the project end date.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    conflict = (
        Schedule.query
        .filter(
            Schedule.trainer_id == trainer.id,
            Schedule.status != "CANCELLED",
            Schedule.start_datetime < end_datetime,
            Schedule.end_datetime > start_datetime
        )
        .first()
    )

    if conflict:

        flash(
            f"Trainer {trainer.full_name} already has an overlapping schedule.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    schedule_item = Schedule(

        schedule_code=generate_schedule_code(),

        project_id=project.id,

        trainer_id=trainer.id,

        title=title,

        start_datetime=start_datetime,

        end_datetime=end_datetime,

        mode=mode,

        location=(
            location
            if mode in {"OFFLINE", "HYBRID"}
            else None
        ),

        meeting_link=(
            meeting_link
            if mode in {"ONLINE", "HYBRID"}
            else None
        ),

        status="SCHEDULED",

        notes=notes or None,

        created_by=current_user.id
    )

    try:

        db.session.add(
            schedule_item
        )

        db.session.flush()

        if trainer.user_id:
            db.session.add(
                Notification(
                    user_id=trainer.user_id,
                    title="New Schedule Created",
                    message=(
                        f"A new training schedule has been created for "
                        f"{project.project_name} on "
                        f"{start_datetime.strftime('%d %b %Y at %I:%M %p')}."
                    ),
                    notification_type="SCHEDULE",
                    related_type="SCHEDULE",
                    related_id=schedule_item.id
                )
            )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to create the schedule.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    flash(
        f"Schedule {schedule_item.schedule_code} created successfully.",
        "success"
    )

    return redirect(
        url_for("schedule")
    )


# ============================================================
# EDIT SCHEDULE
# ============================================================

@app.route(
    "/schedule/<int:schedule_id>/edit",
    methods=["POST"]
)
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def edit_schedule(schedule_id):

    schedule_item = db.session.get(
        Schedule,
        schedule_id
    )

    if not schedule_item:

        flash(
            "Schedule not found.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    current_user = get_current_user()

    if not vendor_can_access_schedule(
        schedule_item,
        current_user
    ):

        flash(
            "You are not authorized to edit this schedule.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if not validate_csrf():

        flash(
            "Invalid security token.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    project_id_raw = clean_text(
        request.form.get("project_id"),
        20
    )

    trainer_id_raw = clean_text(
        request.form.get("trainer_id"),
        20
    )

    title = clean_text(
        request.form.get("title"),
        200
    )

    mode = clean_text(
        request.form.get("mode"),
        30
    ).upper()

    location = clean_text(
        request.form.get("location"),
        250
    )

    meeting_link = clean_text(
        request.form.get("meeting_link"),
        500
    )

    notes = clean_text(
        request.form.get("notes"),
        5000
    )

    try:

        project_id = int(
            project_id_raw
        )

        trainer_id = int(
            trainer_id_raw
        )

    except (TypeError, ValueError):

        flash(
            "Invalid project or trainer selection.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    project = db.session.get(
        Project,
        project_id
    )

    trainer = db.session.get(
        Trainer,
        trainer_id
    )

    if not project or not vendor_can_access_project(
        project,
        current_user
    ):

        flash(
            "You are not authorized to use this project.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if (
        not trainer
        or trainer.trainer_status != "ACTIVE"
    ):

        flash(
            "Only an active trainer can be scheduled.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    assignment = (
        ProjectTrainer.query
        .filter_by(
            project_id=project.id,
            trainer_id=trainer.id
        )
        .first()
    )

    if not assignment:

        flash(
            "The selected trainer is not assigned to this project.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if not title:

        title = project.project_name

    if mode not in SCHEDULE_MODES:

        flash(
            "Invalid training mode.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if (
        mode in {"ONLINE", "HYBRID"}
        and not meeting_link
    ):

        flash(
            "A meeting link is required for online or hybrid training.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if (
        mode == "OFFLINE"
        and not location
    ):

        flash(
            "A location is required for offline training.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    try:

        start_datetime = parse_datetime_local(
            request.form.get(
                "start_datetime"
            ),
            "Start date and time"
        )

        end_datetime = parse_datetime_local(
            request.form.get(
                "end_datetime"
            ),
            "End date and time"
        )

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if end_datetime <= start_datetime:

        flash(
            "End time must be after the start time.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if (
        project.start_date
        and start_datetime.date()
        < project.start_date
    ):

        flash(
            "Schedule cannot start before the project start date.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    if (
        project.end_date
        and end_datetime.date()
        > project.end_date
    ):

        flash(
            "Schedule cannot extend beyond the project end date.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    conflict = (
        Schedule.query
        .filter(
            Schedule.id != schedule_item.id,
            Schedule.trainer_id == trainer.id,
            Schedule.status != "CANCELLED",
            Schedule.start_datetime < end_datetime,
            Schedule.end_datetime > start_datetime
        )
        .first()
    )

    if conflict:

        flash(
            f"Trainer {trainer.full_name} already has an overlapping schedule.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    schedule_item.project_id = project.id
    schedule_item.trainer_id = trainer.id
    schedule_item.title = title
    schedule_item.start_datetime = start_datetime
    schedule_item.end_datetime = end_datetime
    schedule_item.mode = mode

    schedule_item.location = (
        location
        if mode in {"OFFLINE", "HYBRID"}
        else None
    )

    schedule_item.meeting_link = (
        meeting_link
        if mode in {"ONLINE", "HYBRID"}
        else None
    )

    schedule_item.notes = (
        notes or None
    )

    try:

        if trainer.user_id:
            db.session.add(
                Notification(
                    user_id=trainer.user_id,
                    title="Schedule Updated",
                    message=(
                        f"Your schedule for {project.project_name} "
                        f"has been updated."
                    ),
                    notification_type="SCHEDULE",
                    related_type="SCHEDULE",
                    related_id=schedule_item.id
                )
            )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to update the schedule.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    flash(
        f"Schedule {schedule_item.schedule_code} updated successfully.",
        "success"
    )

    return redirect(
        url_for("schedule")
    )


# ============================================================
# UPDATE STATUS
# ============================================================

@app.route(
    "/schedule/<int:schedule_id>/status",
    methods=["POST"]
)
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def update_schedule_status(schedule_id):

    if not validate_csrf():

        flash(
            "Invalid security token.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    schedule_item = db.session.get(
        Schedule,
        schedule_id
    )

    if not schedule_item:

        flash(
            "Schedule not found.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    current_user = get_current_user()

    if not vendor_can_access_schedule(
        schedule_item,
        current_user
    ):

        flash(
            "You are not authorized to update this schedule.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    status = clean_text(
        request.form.get("status"),
        30
    ).upper()

    if status not in SCHEDULE_STATUSES:

        flash(
            "Invalid schedule status.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    schedule_item.status = status

    try:

        if schedule_item.trainer and schedule_item.trainer.user_id:

            if status == "CANCELLED":
                db.session.add(
                    Notification(
                        user_id=schedule_item.trainer.user_id,
                        title="Schedule Cancelled",
                        message=(
                            f"Your schedule '{schedule_item.title}' "
                            f"has been cancelled."
                        ),
                        notification_type="SCHEDULE",
                        related_type="SCHEDULE",
                        related_id=schedule_item.id
                    )
                )

            elif status == "COMPLETED":
                db.session.add(
                    Notification(
                        user_id=schedule_item.trainer.user_id,
                        title="Schedule Completed",
                        message=(
                            f"Your schedule '{schedule_item.title}' "
                            f"has been marked as completed."
                        ),
                        notification_type="SCHEDULE",
                        related_type="SCHEDULE",
                        related_id=schedule_item.id
                    )
                )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to update schedule status.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    flash(
        "Schedule status updated successfully.",
        "success"
    )

    return redirect(
        url_for("schedule")
    )


# ============================================================
# DELETE SCHEDULE
# ============================================================

@app.route(
    "/schedule/<int:schedule_id>/delete",
    methods=["POST"]
)
@roles_required(
    "SUPER_ADMIN",
    "VENDOR"
)
def delete_schedule(schedule_id):

    if not validate_csrf():

        flash(
            "Invalid security token.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    schedule_item = db.session.get(
        Schedule,
        schedule_id
    )

    if not schedule_item:

        flash(
            "Schedule not found.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    current_user = get_current_user()

    if not vendor_can_access_schedule(
        schedule_item,
        current_user
    ):

        flash(
            "You are not authorized to delete this schedule.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    schedule_code = schedule_item.schedule_code
    trainer = schedule_item.trainer
    trainer_user_id = trainer.user_id if trainer else None
    schedule_title = schedule_item.title

    try:

        if trainer_user_id:
            db.session.add(
                Notification(
                    user_id=trainer_user_id,
                    title="Schedule Deleted",
                    message=(
                        f"Your schedule '{schedule_title}' "
                        f"({schedule_code}) has been deleted."
                    ),
                    notification_type="SCHEDULE",
                    related_type="SCHEDULE",
                    related_id=schedule_item.id
                )
            )

        db.session.delete(
            schedule_item
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to delete the schedule.",
            "error"
        )

        return redirect(
            url_for("schedule")
        )

    flash(
        f"Schedule {schedule_code} deleted successfully.",
        "success"
    )

    return redirect(
        url_for("schedule")
    )


# ============================================================
# ATTENDANCE
# ============================================================

@app.route(
    "/attendance",
    methods=["GET", "POST"],
    endpoint="attendance"
)
@login_required
def attendance_handler():

    current_user = get_current_user()

    attendance_statuses = [
        "PRESENT",
        "LATE",
        "ABSENT",
        "LEAVE"
    ]

    # =====================================================
    # POST - MARK / UPDATE ATTENDANCE
    # =====================================================

    if request.method == "POST":

        if not validate_csrf():
            flash("Invalid security token.", "error")
            return redirect(url_for("attendance"))

        schedule_id_raw = clean_text(
            request.form.get("schedule_id"), 20
        )

        attendance_date_raw = clean_text(
            request.form.get("attendance_date"), 20
        )

        status = clean_text(
            request.form.get("status"), 30
        ).upper()

        check_in_raw = clean_text(
            request.form.get("check_in"), 10
        )

        check_out_raw = clean_text(
            request.form.get("check_out"), 10
        )

        remarks = clean_text(
            request.form.get("remarks"), 2000
        )

        try:
            schedule_id = int(schedule_id_raw)
        except (TypeError, ValueError):
            flash("Invalid schedule.", "error")
            return redirect(url_for("attendance"))

        schedule_item = db.session.get(
            Schedule,
            schedule_id
        )

        if not schedule_item:
            flash("Schedule not found.", "error")
            return redirect(url_for("attendance"))

        # -------------------------------------------------
        # Parse date before permission redirect
        # -------------------------------------------------

        try:
            attendance_date = datetime.strptime(
                attendance_date_raw,
                "%Y-%m-%d"
            ).date()
        except (TypeError, ValueError):
            flash("Invalid attendance date.", "error")
            return redirect(url_for("attendance"))

        # -------------------------------------------------
        # PREVENT FUTURE ATTENDANCE
        # -------------------------------------------------
        # Attendance can only be marked/edited for today
        # or a past date. Tomorrow and any future date are
        # not allowed, even if someone bypasses the UI.
        # -------------------------------------------------

        today = datetime.now().date()

        if attendance_date > today:
            session["attendance_future_popup"] = (
                "Future Attendance Not Allowed",
                "Attendance cannot be marked or edited for a future date."
            )

            flash(
                "Attendance cannot be marked or edited for a future date.",
                "error"
            )

            return redirect(
                url_for(
                    "attendance",
                    date=attendance_date.strftime("%Y-%m-%d")
                )
            )

        # -------------------------------------------------
        # Role access
        # -------------------------------------------------
        # SUPER_ADMIN -> all projects
        # VENDOR      -> only own projects
        # TRAINER     -> only own assigned schedule
        # -------------------------------------------------

        allowed = False

        if current_user.role == "SUPER_ADMIN":
            allowed = True

        elif current_user.role == "VENDOR":
            allowed = bool(
                schedule_item.project
                and schedule_item.project.created_by == current_user.id
            )

        elif current_user.role == "TRAINER":
            allowed = bool(
                current_user.trainer_profile
                and schedule_item.trainer_id == current_user.trainer_profile.id
            )

        if not allowed:
            flash(
                "You are not authorized to manage this attendance.",
                "error"
            )
            return redirect(
                url_for(
                    "attendance",
                    date=attendance_date.strftime("%Y-%m-%d")
                )
            )

        # -------------------------------------------------
        # Trainer must exist
        # -------------------------------------------------

        if not schedule_item.trainer:
            flash(
                "This schedule has no trainer assigned.",
                "error"
            )
            return redirect(
                url_for(
                    "attendance",
                    date=attendance_date.strftime("%Y-%m-%d")
                )
            )

        # -------------------------------------------------
        # Attendance must belong to schedule date range
        # -------------------------------------------------

        schedule_start_date = schedule_item.start_datetime.date()
        schedule_end_date = schedule_item.end_datetime.date()

        if not (
            schedule_start_date
            <= attendance_date
            <= schedule_end_date
        ):
            flash(
                "Attendance date must be within the schedule period.",
                "error"
            )
            return redirect(
                url_for(
                    "attendance",
                    date=attendance_date.strftime("%Y-%m-%d")
                )
            )

        # -------------------------------------------------
        # Cancelled schedule
        # -------------------------------------------------

        if schedule_item.status == "CANCELLED":
            flash(
                "Attendance cannot be recorded for a cancelled schedule.",
                "error"
            )
            return redirect(
                url_for(
                    "attendance",
                    date=attendance_date.strftime("%Y-%m-%d")
                )
            )

        # -------------------------------------------------
        # Status
        # -------------------------------------------------

        if status not in attendance_statuses:
            flash("Invalid attendance status.", "error")
            return redirect(
                url_for(
                    "attendance",
                    date=attendance_date.strftime("%Y-%m-%d")
                )
            )

        # -------------------------------------------------
        # IMPORTANT:
        # Attendance is identified by:
        #
        # schedule_id + trainer_id + attendance_date
        #
        # Therefore the same trainer can have separate
        # attendance records for Project A and Project B.
        # -------------------------------------------------

        existing = Attendance.query.filter_by(
            schedule_id=schedule_item.id,
            trainer_id=schedule_item.trainer_id,
            attendance_date=attendance_date
        ).first()

        # -------------------------------------------------
        # Trainer can mark only once.
        # Admin/Vendor can update.
        # -------------------------------------------------

        if current_user.role == "TRAINER" and existing:
            flash(
                "Your attendance has already been recorded. You cannot edit it.",
                "error"
            )
            return redirect(
                url_for(
                    "attendance",
                    date=attendance_date.strftime("%Y-%m-%d")
                )
            )

        # -------------------------------------------------
        # Parse check-in / check-out
        # -------------------------------------------------

        check_in = None
        check_out = None

        if check_in_raw:
            try:
                check_in = datetime.strptime(
                    check_in_raw,
                    "%H:%M"
                ).time()
            except ValueError:
                flash("Invalid check-in time.", "error")
                return redirect(
                    url_for(
                        "attendance",
                        date=attendance_date.strftime("%Y-%m-%d")
                    )
                )

        if check_out_raw:
            try:
                check_out = datetime.strptime(
                    check_out_raw,
                    "%H:%M"
                ).time()
            except ValueError:
                flash("Invalid check-out time.", "error")
                return redirect(
                    url_for(
                        "attendance",
                        date=attendance_date.strftime("%Y-%m-%d")
                    )
                )

        if (
            check_in
            and check_out
            and check_out < check_in
        ):
            flash(
                "Check-out cannot be before check-in.",
                "error"
            )
            return redirect(
                url_for(
                    "attendance",
                    date=attendance_date.strftime("%Y-%m-%d")
                )
            )

        # -------------------------------------------------
        # Create / Update
        # -------------------------------------------------

        if existing:

            existing.status = status
            existing.check_in = check_in
            existing.check_out = check_out
            existing.remarks = remarks
            existing.marked_by = current_user.id

            attendance_record = existing
            message = "Attendance updated successfully."

        else:

            attendance_record = Attendance(
                schedule_id=schedule_item.id,
                trainer_id=schedule_item.trainer_id,
                attendance_date=attendance_date,
                status=status,
                check_in=check_in,
                check_out=check_out,
                remarks=remarks,
                marked_by=current_user.id
            )

            db.session.add(attendance_record)
            message = "Attendance marked successfully."

        # -------------------------------------------------
        # Save attendance
        # -------------------------------------------------

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "Unable to save attendance.",
                "error"
            )
            return redirect(
                url_for(
                    "attendance",
                    date=attendance_date.strftime("%Y-%m-%d")
                )
            )

        # -------------------------------------------------
        # Notify vendor when trainer marks attendance
        # -------------------------------------------------

        if current_user.role == "TRAINER":

            project_creator_id = None

            if schedule_item.project:
                project_creator_id = schedule_item.project.created_by

            if (
                project_creator_id
                and project_creator_id != current_user.id
            ):

                notification = Notification(
                    user_id=project_creator_id,
                    title="Attendance Updated",
                    message=(
                        f"{schedule_item.trainer.full_name} "
                        f"marked attendance as {status.title()} "
                        f"for {schedule_item.title} "
                        f"in project {schedule_item.project.project_code}."
                    ),
                    notification_type="ATTENDANCE",
                    related_type="ATTENDANCE",
                    related_id=attendance_record.id
                )

                db.session.add(notification)

                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()

        flash(message, "success")

        return redirect(
            url_for(
                "attendance",
                date=attendance_date.strftime("%Y-%m-%d")
            )
        )

    # =====================================================
    # GET
    # =====================================================

    date_raw = clean_text(
        request.args.get("date"),
        20
    )

    try:
        selected_date = datetime.strptime(
            date_raw,
            "%Y-%m-%d"
        ).date()
    except (TypeError, ValueError):
        selected_date = datetime.now().date()

    project_id_raw = clean_text(
        request.args.get("project_id"),
        20
    )

    trainer_id_raw = clean_text(
        request.args.get("trainer_id"),
        20
    )

    status_filter = clean_text(
        request.args.get("status"),
        30
    ).upper()

    # =====================================================
    # BASE ACCESSIBLE SCHEDULES
    # =====================================================

    if current_user.role == "SUPER_ADMIN":

        base_query = Schedule.query

    elif current_user.role == "VENDOR":

        base_query = (
            Schedule.query
            .join(
                Project,
                Schedule.project_id == Project.id
            )
            .filter(
                Project.created_by == current_user.id
            )
        )

    elif current_user.role == "TRAINER":

        if current_user.trainer_profile:

            base_query = Schedule.query.filter(
                Schedule.trainer_id ==
                current_user.trainer_profile.id
            )

        else:

            base_query = Schedule.query.filter(False)

    else:

        base_query = Schedule.query.filter(False)

    # =====================================================
    # DAILY SCHEDULES
    # =====================================================

    day_start = datetime.combine(
        selected_date,
        datetime.min.time()
    )

    day_end = datetime.combine(
        selected_date,
        datetime.max.time()
    )

    daily_query = base_query.filter(
        Schedule.start_datetime <= day_end,
        Schedule.end_datetime >= day_start
    )

    # -----------------------------------------------------
    # Project filter
    # -----------------------------------------------------

    if project_id_raw:

        try:
            project_id = int(project_id_raw)
            daily_query = daily_query.filter(
                Schedule.project_id == project_id
            )
        except ValueError:
            pass

    # -----------------------------------------------------
    # Trainer filter
    # -----------------------------------------------------

    if trainer_id_raw:

        try:
            trainer_id = int(trainer_id_raw)
            daily_query = daily_query.filter(
                Schedule.trainer_id == trainer_id
            )
        except ValueError:
            pass

    schedules = (
        daily_query
        .order_by(
            Schedule.start_datetime.asc()
        )
        .all()
    )

    # =====================================================
    # ATTENDANCE FOR SELECTED DATE
    # =====================================================

    attendance_by_schedule = {}

    for schedule_item in schedules:

        if not schedule_item.trainer_id:
            continue

        record = Attendance.query.filter_by(
            schedule_id=schedule_item.id,
            trainer_id=schedule_item.trainer_id,
            attendance_date=selected_date
        ).first()

        attendance_by_schedule[
            schedule_item.id
        ] = record

    # =====================================================
    # DAILY STATS
    # =====================================================

    total_sessions = len(schedules)

    marked_count = 0
    present_count = 0
    late_count = 0
    absent_count = 0
    leave_count = 0

    for record in attendance_by_schedule.values():

        if not record:
            continue

        marked_count += 1

        if record.status == "PRESENT":
            present_count += 1

        elif record.status == "LATE":
            late_count += 1

        elif record.status == "ABSENT":
            absent_count += 1

        elif record.status == "LEAVE":
            leave_count += 1

    if total_sessions:

        attendance_percentage = round(
            (
                present_count +
                late_count
            )
            /
            total_sessions
            * 100,
            1
        )

    else:

        attendance_percentage = 0.0

    # =====================================================
    # PROJECT FILTER OPTIONS
    # =====================================================

    projects = []

    if current_user.role in {
        "SUPER_ADMIN",
        "VENDOR"
    }:

        projects = get_schedule_projects(
            current_user
        )

    # =====================================================
    # TRAINER FILTER OPTIONS
    # =====================================================

    trainer_map = {}

    for schedule_item in schedules:

        if schedule_item.trainer:

            trainer_map[
                schedule_item.trainer.id
            ] = schedule_item.trainer

    trainers = list(
        trainer_map.values()
    )

    # =====================================================
    # PROJECT + TRAINER ATTENDANCE SUMMARY
    #
    # IMPORTANT:
    # A trainer may work on multiple projects.
    # Attendance is therefore NOT grouped by trainer alone.
    #
    # Example:
    #
    # Trainer: Ravi
    # Project A -> 80%
    # Project B -> 50%
    #
    # These remain separate.
    # =====================================================

    summary_query = base_query

    if project_id_raw:

        try:
            summary_project_id = int(project_id_raw)
            summary_query = summary_query.filter(
                Schedule.project_id == summary_project_id
            )
        except ValueError:
            pass

    if trainer_id_raw:

        try:
            summary_trainer_id = int(trainer_id_raw)
            summary_query = summary_query.filter(
                Schedule.trainer_id == summary_trainer_id
            )
        except ValueError:
            pass

    summary_schedules = (
        summary_query
        .order_by(
            Schedule.start_datetime.asc()
        )
        .all()
    )

    project_trainer_groups = {}

    for schedule_item in summary_schedules:

        if not schedule_item.trainer_id:
            continue

        if not schedule_item.project_id:
            continue

        if not schedule_item.trainer:
            continue

        group_key = (
            schedule_item.project_id,
            schedule_item.trainer_id
        )

        if group_key not in project_trainer_groups:
            project_trainer_groups[group_key] = {
                "project": schedule_item.project,
                "trainer": schedule_item.trainer,
                "schedules": []
            }

        project_trainer_groups[group_key][
            "schedules"
        ].append(schedule_item)

    project_trainer_summaries = []

    for group in project_trainer_groups.values():

        project = group["project"]
        trainer = group["trainer"]
        trainer_schedules = group["schedules"]

        total_days = 0
        present = 0
        late = 0
        absent = 0
        leave = 0

        for schedule_item in trainer_schedules:

            start_date = schedule_item.start_datetime.date()
            end_date = schedule_item.end_datetime.date()

            current_date = start_date

            while current_date <= end_date:

                total_days += 1

                record = Attendance.query.filter_by(
                    schedule_id=schedule_item.id,
                    trainer_id=trainer.id,
                    attendance_date=current_date
                ).first()

                if record:

                    if record.status == "PRESENT":
                        present += 1

                    elif record.status == "LATE":
                        late += 1

                    elif record.status == "ABSENT":
                        absent += 1

                    elif record.status == "LEAVE":
                        leave += 1

                current_date += timedelta(days=1)

        if total_days:

            percentage = round(
                (
                    present +
                    late
                )
                /
                total_days
                * 100,
                1
            )

        else:

            percentage = 0.0

        project_trainer_summaries.append({
            "project": project,
            "trainer": trainer,
            "total_days": total_days,
            "present": present,
            "late": late,
            "absent": absent,
            "leave": leave,
            "percentage": percentage
        })

    # Keep the old variable name as well so existing templates
    # do not immediately break. The new template should use
    # project_trainer_summaries because it contains project data.
    trainer_summaries = project_trainer_summaries

    attendance_future_popup = session.pop(
        "attendance_future_popup",
        None
    )

    return render_template(
        "attendance.html",
        schedules=schedules,
        attendance_future_popup=attendance_future_popup,
        attendance_by_schedule=attendance_by_schedule,
        selected_date=selected_date,
        total_sessions=total_sessions,
        marked_count=marked_count,
        present_count=present_count,
        late_count=late_count,
        absent_count=absent_count,
        leave_count=leave_count,
        attendance_percentage=attendance_percentage,
        projects=projects,
        trainers=trainers,
        trainer_summaries=trainer_summaries,
        project_trainer_summaries=project_trainer_summaries,
        status_filter=status_filter,
        attendance_statuses=attendance_statuses
    )


# ============================================================
# FEEDBACK
# ============================================================

@app.route(
    "/feedback",
    methods=["GET", "POST"],
    endpoint="feedback"
)
@login_required
def feedback_handler():

    current_user = get_current_user()

    # =====================================================
    # POST - TRAINER SUBMITS / UPDATES FEEDBACK
    # =====================================================

    if request.method == "POST":

        if not validate_csrf():
            flash("Invalid security token.", "error")
            return redirect(url_for("feedback"))

        # Only trainers can submit their own feedback.
        if current_user.role != "TRAINER":
            flash("Only trainers can submit feedback.", "error")
            return redirect(url_for("feedback"))

        if not current_user.trainer_profile:
            flash("Trainer profile not found.", "error")
            return redirect(url_for("feedback"))

        schedule_id_raw = clean_text(
            request.form.get("schedule_id"),
            20
        )

        rating_raw = clean_text(
            request.form.get("rating"),
            5
        )

        feedback_text = clean_text(
            request.form.get("feedback_text"),
            3000
        )

        try:
            schedule_id = int(schedule_id_raw)
            rating = int(rating_raw)
        except (TypeError, ValueError):
            flash("Invalid feedback details.", "error")
            return redirect(url_for("feedback"))

        if rating < 1 or rating > 5:
            flash("Rating must be between 1 and 5.", "error")
            return redirect(url_for("feedback"))

        schedule_item = db.session.get(
            Schedule,
            schedule_id
        )

        if not schedule_item:
            flash("Schedule not found.", "error")
            return redirect(url_for("feedback"))

        if schedule_item.trainer_id != current_user.trainer_profile.id:
            flash("You are not authorized to submit feedback for this session.", "error")
            return redirect(url_for("feedback"))

        if not schedule_item.project:
            flash("This schedule is not linked to a project.", "error")
            return redirect(url_for("feedback"))

        if schedule_item.end_datetime.date() >= datetime.now().date():
            flash("Feedback can be submitted only after the training session is completed.", "error")
            return redirect(url_for("feedback"))

        existing = Feedback.query.filter_by(
            schedule_id=schedule_item.id,
            trainer_id=current_user.trainer_profile.id
        ).first()

        if existing:
            existing.rating = rating
            existing.feedback_text = feedback_text or None
            existing.status = "SUBMITTED"
            success_message = "Feedback updated successfully."
        else:
            existing = Feedback(
                schedule_id=schedule_item.id,
                project_id=schedule_item.project_id,
                trainer_id=current_user.trainer_profile.id,
                submitted_by=current_user.id,
                rating=rating,
                feedback_text=feedback_text or None,
                status="SUBMITTED"
            )
            db.session.add(existing)
            success_message = "Feedback submitted successfully."

        try:
            db.session.commit()

            # Notify the project owner when feedback is submitted/updated.
            if schedule_item.project.created_by and schedule_item.project.created_by != current_user.id:
                db.session.add(
                    Notification(
                        user_id=schedule_item.project.created_by,
                        title="Training Feedback Submitted",
                        message=(
                            f"{current_user.trainer_profile.full_name} submitted "
                            f"feedback for {schedule_item.project.project_code} "
                            f"({rating}/5)."
                        ),
                        notification_type="FEEDBACK",
                        related_type="FEEDBACK",
                        related_id=existing.id
                    )
                )
                db.session.commit()

            flash(success_message, "success")

        except Exception:
            db.session.rollback()
            flash("Unable to save feedback.", "error")

        return redirect(url_for("feedback"))

    # =====================================================
    # GET - ROLE-SCOPED FEEDBACK
    # =====================================================

    feedback_query = (
        Feedback.query
        .join(Schedule, Feedback.schedule_id == Schedule.id)
        .join(Project, Feedback.project_id == Project.id)
        .join(Trainer, Feedback.trainer_id == Trainer.id)
    )

    if current_user.role == "VENDOR":
        feedback_query = feedback_query.filter(
            Project.created_by == current_user.id
        )

    elif current_user.role == "TRAINER":
        if not current_user.trainer_profile:
            feedback_query = feedback_query.filter(False)
        else:
            feedback_query = feedback_query.filter(
                Feedback.trainer_id == current_user.trainer_profile.id
            )

    elif current_user.role != "SUPER_ADMIN":
        feedback_query = feedback_query.filter(False)

    # -----------------------------------------------------
    # Filters
    # -----------------------------------------------------

    search = clean_text(
        request.args.get("search"),
        100
    )

    project_id_raw = clean_text(
        request.args.get("project_id"),
        20
    )

    trainer_id_raw = clean_text(
        request.args.get("trainer_id"),
        20
    )

    rating_raw = clean_text(
        request.args.get("rating"),
        5
    )

    if search:
        search_value = f"%{search}%"
        feedback_query = feedback_query.filter(
            db.or_(
                Project.project_code.ilike(search_value),
                Project.project_name.ilike(search_value),
                Trainer.full_name.ilike(search_value),
                Feedback.feedback_text.ilike(search_value)
            )
        )

    try:
        if project_id_raw:
            feedback_query = feedback_query.filter(
                Feedback.project_id == int(project_id_raw)
            )
    except ValueError:
        pass

    try:
        if trainer_id_raw:
            feedback_query = feedback_query.filter(
                Feedback.trainer_id == int(trainer_id_raw)
            )
    except ValueError:
        pass

    try:
        if rating_raw:
            rating_filter = int(rating_raw)
            if 1 <= rating_filter <= 5:
                feedback_query = feedback_query.filter(
                    Feedback.rating == rating_filter
                )
    except ValueError:
        pass

    feedback_records = (
        feedback_query
        .order_by(Feedback.created_at.desc())
        .all()
    )

    # -----------------------------------------------------
    # Stats
    # -----------------------------------------------------

    total_feedback = len(feedback_records)
    average_rating = (
        round(
            sum(item.rating for item in feedback_records) / total_feedback,
            1
        )
        if total_feedback
        else 0
    )

    rating_counts = {
        5: 0,
        4: 0,
        3: 0,
        2: 0,
        1: 0
    }

    for item in feedback_records:
        if item.rating in rating_counts:
            rating_counts[item.rating] += 1

    # -----------------------------------------------------
    # Filter dropdown data - role scoped
    # -----------------------------------------------------

    if current_user.role == "SUPER_ADMIN":
        projects = (
            Project.query
            .order_by(Project.project_name.asc())
            .all()
        )
        trainers = (
            Trainer.query
            .filter_by(trainer_status="ACTIVE")
            .order_by(Trainer.full_name.asc())
            .all()
        )

    elif current_user.role == "VENDOR":
        projects = (
            Project.query
            .filter_by(created_by=current_user.id)
            .order_by(Project.project_name.asc())
            .all()
        )

        trainer_ids = [
            row.trainer_id
            for row in ProjectTrainer.query
            .join(Project, ProjectTrainer.project_id == Project.id)
            .filter(Project.created_by == current_user.id)
            .all()
        ]

        trainers = (
            Trainer.query
            .filter(
                Trainer.id.in_(trainer_ids)
            )
            .filter_by(trainer_status="ACTIVE")
            .order_by(Trainer.full_name.asc())
            .all()
            if trainer_ids
            else []
        )

    else:
        projects = (
            Project.query
            .join(Schedule, Schedule.project_id == Project.id)
            .filter(
                Schedule.trainer_id == (
                    current_user.trainer_profile.id
                    if current_user.trainer_profile else -1
                )
            )
            .distinct()
            .order_by(Project.project_name.asc())
            .all()
        )

        trainers = [current_user.trainer_profile] if current_user.trainer_profile else []

    return render_template(
        "feedback.html",
        feedback_records=feedback_records,
        total_feedback=total_feedback,
        average_rating=average_rating,
        rating_counts=rating_counts,
        projects=projects,
        trainers=trainers,
        selected_search=search,
        selected_project_id=project_id_raw,
        selected_trainer_id=trainer_id_raw,
        selected_rating=rating_raw
    )


# ============================================================
# NOTIFICATIONS
# ============================================================

@app.route(
    "/notifications",
    methods=["GET", "POST"],
    endpoint="notifications"
)
@login_required
def notification_handler():

    current_user = get_current_user()


    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        # ----------------------------------------------------
        # Optional GET read action
        # ----------------------------------------------------

        action = clean_text(
            request.args.get("action"),
            30
        ).lower()

        notification_id = (
            request.args.get("notification_id")
        )


        # ----------------------------------------------------
        # MARK ONE AS READ
        # ----------------------------------------------------

        if (
            action == "read"
            and notification_id
        ):

            try:

                notification_id = int(
                    notification_id
                )

            except (
                TypeError,
                ValueError
            ):

                notification_id = None


            if notification_id:

                notification = (
                    Notification.query
                    .filter_by(
                        id=notification_id,
                        user_id=current_user.id
                    )
                    .first()
                )


                if notification:

                    if not notification.is_read:

                        notification.is_read = True

                        notification.read_at = (
                            datetime.now()
                        )

                        try:

                            db.session.commit()

                        except Exception:

                            db.session.rollback()


            return redirect(
                url_for("notifications")
            )


        # ----------------------------------------------------
        # LOAD NOTIFICATIONS
        # ----------------------------------------------------

        all_notifications = (
            Notification.query
            .filter_by(
                user_id=current_user.id
            )
            .order_by(
                Notification.created_at.desc()
            )
            .all()
        )


        # ----------------------------------------------------
        # UNREAD COUNT
        # ----------------------------------------------------

        unread_count = (
            Notification.query
            .filter_by(
                user_id=current_user.id,
                is_read=False
            )
            .count()
        )


        return render_template(
            "notifications.html",
            notifications=all_notifications,
            unread_count=unread_count
        )


    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        # ----------------------------------------------------
        # CSRF
        # ----------------------------------------------------

        if not validate_csrf():

            flash(
                "Invalid security token.",
                "error"
            )

            return redirect(
                url_for("notifications")
            )


        action = clean_text(
            request.form.get("action"),
            30
        ).lower()


        # ====================================================
        # MARK ONE AS READ
        # ====================================================

        if action == "read":

            notification_id = (
                request.form.get(
                    "notification_id"
                )
            )

            try:

                notification_id = int(
                    notification_id
                )

            except (
                TypeError,
                ValueError
            ):

                notification_id = None


            if not notification_id:

                flash(
                    "Invalid notification.",
                    "error"
                )

                return redirect(
                    url_for("notifications")
                )


            notification = (
                Notification.query
                .filter_by(
                    id=notification_id,
                    user_id=current_user.id
                )
                .first()
            )


            if not notification:

                flash(
                    "Notification not found.",
                    "error"
                )

                return redirect(
                    url_for("notifications")
                )


            if not notification.is_read:

                notification.is_read = True

                notification.read_at = (
                    datetime.now()
                )


                try:

                    db.session.commit()

                except Exception:

                    db.session.rollback()

                    flash(
                        "Unable to update notification.",
                        "error"
                    )


            return redirect(
                url_for("notifications")
            )


        # ====================================================
        # MARK ALL AS READ
        # ====================================================

        if action == "read-all":

            unread_notifications = (
                Notification.query
                .filter_by(
                    user_id=current_user.id,
                    is_read=False
                )
                .all()
            )


            now = datetime.now()


            for notification in unread_notifications:

                notification.is_read = True

                notification.read_at = now


            try:

                db.session.commit()

                flash(
                    "All notifications marked as read.",
                    "success"
                )

            except Exception:

                db.session.rollback()

                flash(
                    "Unable to mark notifications as read.",
                    "error"
                )


            return redirect(
                url_for("notifications")
            )


    # ========================================================
    # FALLBACK
    # ========================================================

    return redirect(
        url_for("notifications")
    )



# ============================================================
# PAYMENTS
# ============================================================

@app.route(
    "/payments",
    methods=["GET", "POST"],
    endpoint="payments"
)
@login_required
def payment_handler():

    current_user = get_current_user()

    if current_user.role not in {"SUPER_ADMIN", "VENDOR", "TRAINER"}:
        flash("You are not authorized to access payments.", "error")
        return redirect(url_for("dashboard"))

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        if not validate_csrf():
            flash("Invalid security token. Please try again.", "error")
            return redirect(url_for("payments"))

        action = clean_text(
            request.form.get("action"),
            30
        ).lower()

        # ----------------------------------------------------
        # MARK PAYMENT AS PAID
        # ----------------------------------------------------

        if action == "mark-paid":

            if current_user.role == "TRAINER":
                flash("Trainers cannot update payment status.", "error")
                return redirect(url_for("payments"))

            payment_id_raw = clean_text(
                request.form.get("payment_id"),
                20
            )

            try:
                payment_id = int(payment_id_raw)
            except (TypeError, ValueError):
                flash("Invalid payment selected.", "error")
                return redirect(url_for("payments"))

            payment = db.session.get(Payment, payment_id)

            if not payment:
                flash("Payment not found.", "error")
                return redirect(url_for("payments"))

            if payment.project and not vendor_can_access_project(
                payment.project,
                current_user
            ):
                flash("You are not authorized to update this payment.", "error")
                return redirect(url_for("payments"))

            if payment.status == "PAID":
                flash("This payment is already marked as paid.", "error")
                return redirect(url_for("payments"))

            if payment.status == "CANCELLED":
                flash("Cancelled payments cannot be marked as paid.", "error")
                return redirect(url_for("payments"))

            payment.status = "PAID"
            payment.payment_date = datetime.now().date()

            try:
                if payment.trainer and payment.trainer.user_id:
                    db.session.add(
                        Notification(
                            user_id=payment.trainer.user_id,
                            title="Payment Completed",
                            message=(
                                f"Payment {payment.payment_code} for "
                                f"{payment.project.project_code if payment.project else 'your project'} "
                                f"has been marked as paid."
                            ),
                            notification_type="PAYMENT",
                            related_type="PAYMENT",
                            related_id=payment.id
                        )
                    )

                db.session.commit()

                flash(
                    f"Payment {payment.payment_code} marked as paid.",
                    "success"
                )

            except Exception:
                db.session.rollback()
                flash("Unable to update the payment.", "error")

            return redirect(url_for("payments"))

        # ----------------------------------------------------
        # TRAINER CANNOT CREATE / EDIT
        # ----------------------------------------------------

        if current_user.role == "TRAINER":
            flash("Trainers cannot create or edit payment records.", "error")
            return redirect(url_for("payments"))

        # ----------------------------------------------------
        # CREATE / EDIT
        # ----------------------------------------------------

        if action not in {"create", "edit", "update"}:
            flash("Invalid payment action.", "error")
            return redirect(url_for("payments"))

        project_id_raw = clean_text(
            request.form.get("project_id"),
            20
        )
        trainer_id_raw = clean_text(
            request.form.get("trainer_id"),
            20
        )

        try:
            project_id = int(project_id_raw)
            trainer_id = int(trainer_id_raw)
        except (TypeError, ValueError):
            flash("Please select a valid project and trainer.", "error")
            return redirect(url_for("payments"))

        project = db.session.get(Project, project_id)
        trainer = db.session.get(Trainer, trainer_id)

        if not project:
            flash("Selected project was not found.", "error")
            return redirect(url_for("payments"))

        if not trainer:
            flash("Selected trainer was not found.", "error")
            return redirect(url_for("payments"))

        if not vendor_can_access_project(project, current_user):
            flash("You are not authorized to use this project.", "error")
            return redirect(url_for("payments"))

        # Trainer must actually be assigned to the project.
        assignment = (
            ProjectTrainer.query
            .filter_by(
                project_id=project.id,
                trainer_id=trainer.id
            )
            .first()
        )

        if not assignment:
            flash(
                "The selected trainer is not assigned to this project.",
                "error"
            )
            return redirect(url_for("payments"))

        rate_type = clean_text(
            request.form.get("rate_type"),
            30
        ).upper()

        if rate_type not in {"PER_DAY", "PER_HOUR", "FIXED"}:
            flash("Invalid rate type.", "error")
            return redirect(url_for("payments"))

        try:
            rate = float(
                request.form.get("rate") or 0
            )

            adjustment_amount = float(
                request.form.get("adjustment_amount") or 0
            )

            total_days = int(
                request.form.get("total_days") or 0
            )

            total_hours = float(
                request.form.get("total_hours") or 0
            )

        except (TypeError, ValueError):
            flash("Please enter valid payment values.", "error")
            return redirect(url_for("payments"))

        if rate < 0:
            flash("Rate cannot be negative.", "error")
            return redirect(url_for("payments"))

        if total_days < 0 or total_hours < 0:
            flash("Days and hours cannot be negative.", "error")
            return redirect(url_for("payments"))

        # ----------------------------------------------------
        # Attendance-linked day calculation
        # ----------------------------------------------------

        if rate_type == "PER_DAY":

            attendance_days = (
                db.session.query(Attendance.attendance_date)
                .join(
                    Schedule,
                    Attendance.schedule_id == Schedule.id
                )
                .filter(
                    Schedule.project_id == project.id,
                    Attendance.trainer_id == trainer.id,
                    Attendance.status.in_(["PRESENT", "LATE"]),
                    Attendance.attendance_date <= datetime.now().date()
                )
                .distinct()
                .count()
            )

            # Use actual attendance when available. If there is no
            # attendance yet, retain the manually entered day count.
            if attendance_days > 0:
                total_days = attendance_days

            if total_days <= 0:
                flash(
                    "No payable attendance days were found for this project and trainer.",
                    "error"
                )
                return redirect(url_for("payments"))

            gross_amount = rate * total_days

        elif rate_type == "PER_HOUR":

            if total_hours <= 0:
                flash("Please enter total payable hours.", "error")
                return redirect(url_for("payments"))

            gross_amount = rate * total_hours

        else:

            if rate <= 0:
                flash("Please enter a valid fixed payment amount.", "error")
                return redirect(url_for("payments"))

            gross_amount = rate

        final_amount = gross_amount + adjustment_amount

        if gross_amount < 0 or final_amount < 0:
            flash("Payment amount cannot be negative.", "error")
            return redirect(url_for("payments"))

        # ----------------------------------------------------
        # Optional dates / fields
        # ----------------------------------------------------

        due_date_raw = clean_text(
            request.form.get("due_date"),
            20
        )

        due_date = None

        if due_date_raw:
            try:
                due_date = datetime.strptime(
                    due_date_raw,
                    "%Y-%m-%d"
                ).date()
            except ValueError:
                flash("Due date must be a valid date.", "error")
                return redirect(url_for("payments"))

        status = clean_text(
            request.form.get("status"),
            30
        ).upper()

        if status not in {
            "PENDING",
            "PROCESSING",
            "PAID",
            "OVERDUE"
        }:
            status = "PENDING"

        payment_method = clean_text(
            request.form.get("payment_method"),
            50
        ).upper()

        transaction_reference = clean_text(
            request.form.get("transaction_reference"),
            150
        )

        notes = clean_text(
            request.form.get("notes"),
            2000
        )

        payment_id_raw = clean_text(
            request.form.get("payment_id"),
            20
        )

        # ----------------------------------------------------
        # EDIT
        # ----------------------------------------------------

        if action in {"edit", "update"}:

            try:
                payment_id = int(payment_id_raw)
            except (TypeError, ValueError):
                flash("Invalid payment selected.", "error")
                return redirect(url_for("payments"))

            payment = db.session.get(Payment, payment_id)

            if not payment:
                flash("Payment not found.", "error")
                return redirect(url_for("payments"))

            if payment.project and not vendor_can_access_project(
                payment.project,
                current_user
            ):
                flash("You are not authorized to edit this payment.", "error")
                return redirect(url_for("payments"))

            if payment.status == "PAID":
                flash("Paid payments cannot be edited.", "error")
                return redirect(url_for("payments"))

        # ----------------------------------------------------
        # CREATE
        # ----------------------------------------------------

        else:
            payment = Payment(
                payment_code="TEMP",
                project_id=project.id,
                trainer_id=trainer.id,
                payment_type="TRAINER_PAYMENT",
                created_by=current_user.id
            )

            db.session.add(payment)
            db.session.flush()

            payment.payment_code = f"QT-PAY-{payment.id:04d}"

        # ----------------------------------------------------
        # Save payment fields
        # ----------------------------------------------------

        payment.project_id = project.id
        payment.trainer_id = trainer.id
        payment.payment_type = "TRAINER_PAYMENT"
        payment.rate_type = rate_type
        payment.rate = round(rate, 2)
        payment.total_days = total_days
        payment.total_hours = round(total_hours, 2)
        payment.gross_amount = round(gross_amount, 2)
        payment.adjustment_amount = round(adjustment_amount, 2)
        payment.final_amount = round(final_amount, 2)
        payment.status = status
        payment.due_date = due_date
        payment.payment_method = payment_method or None
        payment.transaction_reference = transaction_reference or None
        payment.notes = notes or None

        if status == "PAID" and not payment.payment_date:
            payment.payment_date = datetime.now().date()

        if status != "PAID":
            payment.payment_date = None

        try:

            # Notify the trainer when a payment is created.
            if (
                action == "create"
                and trainer.user_id
            ):
                db.session.add(
                    Notification(
                        user_id=trainer.user_id,
                        title="New Payment Created",
                        message=(
                            f"A payment of ₹{final_amount:,.2f} has been created "
                            f"for project {project.project_code}."
                        ),
                        notification_type="PAYMENT",
                        related_type="PAYMENT",
                        related_id=payment.id
                    )
                )

            db.session.commit()

            flash(
                f"Payment {payment.payment_code} "
                f"{'updated' if action in {'edit', 'update'} else 'created'} successfully.",
                "success"
            )

        except Exception:

            db.session.rollback()

            flash(
                "Unable to save the payment. No changes were stored.",
                "error"
            )

        return redirect(url_for("payments"))

    # ========================================================
    # GET - ROLE SCOPED DATA
    # ========================================================

    search = clean_text(
        request.args.get("search"),
        100
    )

    status_filter = clean_text(
        request.args.get("status"),
        30
    ).upper()

    project_filter = clean_text(
        request.args.get("project"),
        20
    )

    trainer_filter = clean_text(
        request.args.get("trainer"),
        20
    )

    payment_query = Payment.query

    if current_user.role == "SUPER_ADMIN":

        projects = (
            Project.query
            .order_by(Project.project_name.asc())
            .all()
        )

        trainers = (
            Trainer.query
            .order_by(Trainer.full_name.asc())
            .all()
        )

    elif current_user.role == "VENDOR":

        payment_query = (
            payment_query
            .join(
                Project,
                Payment.project_id == Project.id
            )
            .filter(
                Project.created_by == current_user.id
            )
        )

        projects = (
            Project.query
            .filter(
                Project.created_by == current_user.id
            )
            .order_by(Project.project_name.asc())
            .all()
        )

        trainers = (
            Trainer.query
            .join(
                ProjectTrainer,
                Trainer.id == ProjectTrainer.trainer_id
            )
            .join(
                Project,
                ProjectTrainer.project_id == Project.id
            )
            .filter(
                Project.created_by == current_user.id
            )
            .distinct()
            .order_by(Trainer.full_name.asc())
            .all()
        )

    else:

        trainer = current_user.trainer_profile

        if not trainer:
            payment_query = Payment.query.filter(Payment.id == -1)
            projects = []
            trainers = []
        else:
            payment_query = payment_query.filter(
                Payment.trainer_id == trainer.id
            )

            projects = (
                Project.query
                .join(
                    ProjectTrainer,
                    Project.id == ProjectTrainer.project_id
                )
                .filter(
                    ProjectTrainer.trainer_id == trainer.id
                )
                .order_by(Project.project_name.asc())
                .all()
            )

            trainers = [trainer]

    # --------------------------------------------------------
    # Filters
    # --------------------------------------------------------

    if search:
        pattern = f"%{search}%"
        payment_query = payment_query.filter(
            db.or_(
                Payment.payment_code.ilike(pattern),
                Payment.transaction_reference.ilike(pattern),
                Payment.notes.ilike(pattern)
            )
        )

    if status_filter in {
        "PENDING",
        "PROCESSING",
        "PAID",
        "OVERDUE",
        "CANCELLED"
    }:
        payment_query = payment_query.filter(
            Payment.status == status_filter
        )

    try:
        if project_filter:
            payment_query = payment_query.filter(
                Payment.project_id == int(project_filter)
            )
    except ValueError:
        pass

    try:
        if trainer_filter:
            payment_query = payment_query.filter(
                Payment.trainer_id == int(trainer_filter)
            )
    except ValueError:
        pass

    payments = (
        payment_query
        .order_by(Payment.created_at.desc())
        .all()
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    total_payments = len(payments)

    pending_payments = sum(
        1 for payment in payments
        if payment.status in {"PENDING", "PROCESSING"}
    )

    paid_payments = sum(
        1 for payment in payments
        if payment.status == "PAID"
    )

    overdue_payments = sum(
        1 for payment in payments
        if payment.status == "OVERDUE"
    )

    total_amount = sum(
        float(payment.final_amount or 0)
        for payment in payments
    )

    paid_amount = sum(
        float(payment.final_amount or 0)
        for payment in payments
        if payment.status == "PAID"
    )

    return render_template(
        "payments.html",
        payments=payments,
        projects=projects,
        trainers=trainers,
        total_payments=total_payments,
        pending_payments=pending_payments,
        paid_payments=paid_payments,
        overdue_payments=overdue_payments,
        total_amount=total_amount,
        paid_amount=paid_amount
    )



# ============================================================
# DOCUMENT MANAGEMENT
# ============================================================

DOCUMENT_UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "uploads",
    "documents"
)

DOCUMENT_ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "csv",
    "ppt",
    "pptx",
    "txt",
    "jpg",
    "jpeg",
    "png"
}

DOCUMENT_ALLOWED_TYPES = {
    "GENERAL",
    "RESUME",
    "CERTIFICATE",
    "ID_PROOF",
    "REQUIREMENT",
    "CONTRACT",
    "AGREEMENT",
    "SOW",
    "INVOICE",
    "PAYMENT_PROOF",
    "REPORT",
    "PROJECT_DOCUMENT",
    "OTHER"
}

DOCUMENT_MAX_SIZE = 10 * 1024 * 1024

os.makedirs(
    DOCUMENT_UPLOAD_FOLDER,
    exist_ok=True
)


@app.route(
    "/documents",
    methods=["GET", "POST"],
    endpoint="documents"
)
@login_required
def document_handler():

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    # ========================================================
    # POST ACTIONS
    # ========================================================

    if request.method == "POST":

        if not validate_csrf():
            flash("Invalid security token.", "error")
            return redirect(url_for("documents"))

        action = clean_text(
            request.form.get("action"),
            30
        ).lower()

        # ----------------------------------------------------
        # DELETE
        # ----------------------------------------------------

        if action == "delete":

            if current_user.role not in {
                "SUPER_ADMIN",
                "VENDOR"
            }:
                flash(
                    "You are not authorized to delete documents.",
                    "error"
                )
                return redirect(url_for("documents"))

            try:
                document_id = int(
                    request.form.get("document_id", "0")
                )
            except (TypeError, ValueError):
                document_id = 0

            document = db.session.get(
                Document,
                document_id
            )

            if not document:
                flash("Document not found.", "error")
                return redirect(url_for("documents"))

            # Vendor can only delete documents belonging to
            # their own requirements/projects or uploaded by them.
            if current_user.role == "VENDOR":

                allowed = (
                    (
                        document.project is not None
                        and document.project.created_by == current_user.id
                    )
                    or
                    (
                        document.requirement is not None
                        and document.requirement.created_by == current_user.id
                    )
                    or
                    document.uploaded_by == current_user.id
                )

                if not allowed:
                    flash(
                        "You are not authorized to delete this document.",
                        "error"
                    )
                    return redirect(url_for("documents"))

            try:

                if document.file_path:
                    full_path = os.path.abspath(
                        os.path.join(
                            app.root_path,
                            document.file_path
                        )
                    )

                    upload_root = os.path.abspath(
                        DOCUMENT_UPLOAD_FOLDER
                    )

                    if (
                        full_path.startswith(upload_root + os.sep)
                        and os.path.isfile(full_path)
                    ):
                        os.remove(full_path)

                code = document.document_code

                db.session.delete(document)
                db.session.commit()

                flash(
                    f"Document {code} deleted successfully.",
                    "success"
                )

            except Exception as exc:

                db.session.rollback()

                app.logger.exception(
                    "Document deletion failed: %s",
                    exc
                )

                flash(
                    "Unable to delete document.",
                    "error"
                )

            return redirect(url_for("documents"))

        # ----------------------------------------------------
        # UPLOAD
        # ----------------------------------------------------

        if action == "upload":

            if current_user.role not in {
                "SUPER_ADMIN",
                "VENDOR",
                "TRAINER"
            }:
                flash(
                    "You are not authorized to upload documents.",
                    "error"
                )
                return redirect(url_for("documents"))

            uploaded_file = request.files.get(
                "document_file"
            )

            if not uploaded_file or not uploaded_file.filename:
                flash(
                    "Please select a document.",
                    "error"
                )
                return redirect(url_for("documents"))

            original_name = uploaded_file.filename.strip()
            safe_name = secure_filename(original_name)

            if not safe_name:
                flash(
                    "Invalid file name.",
                    "error"
                )
                return redirect(url_for("documents"))

            if "." not in safe_name:
                flash(
                    "File extension is required.",
                    "error"
                )
                return redirect(url_for("documents"))

            extension = safe_name.rsplit(
                ".", 1
            )[1].lower()

            if extension not in DOCUMENT_ALLOWED_EXTENSIONS:
                flash(
                    "This file type is not allowed.",
                    "error"
                )
                return redirect(url_for("documents"))

            # Check file size before saving.
            uploaded_file.stream.seek(0, os.SEEK_END)
            file_size = uploaded_file.stream.tell()
            uploaded_file.stream.seek(0)

            if file_size <= 0:
                flash(
                    "The selected file is empty.",
                    "error"
                )
                return redirect(url_for("documents"))

            if file_size > DOCUMENT_MAX_SIZE:
                flash(
                    "Document size cannot exceed 10 MB.",
                    "error"
                )
                return redirect(url_for("documents"))

            document_type = clean_text(
                request.form.get("document_type"),
                50
            ).upper()

            if document_type not in DOCUMENT_ALLOWED_TYPES:
                document_type = "GENERAL"

            description = clean_text(
                request.form.get("description"),
                2000
            )

            def optional_id(field_name):
                raw = clean_text(
                    request.form.get(field_name),
                    20
                )

                if not raw:
                    return None

                try:
                    value = int(raw)
                    return value if value > 0 else None
                except (TypeError, ValueError):
                    return None

            project_id = optional_id("project_id")
            requirement_id = optional_id("requirement_id")
            trainer_id = optional_id("trainer_id")
            application_id = optional_id("application_id")
            payment_id = optional_id("payment_id")

            # ------------------------------------------------
            # Validate project
            # ------------------------------------------------

            project = None

            if project_id:

                project = db.session.get(
                    Project,
                    project_id
                )

                if not project:
                    flash(
                        "Selected project was not found.",
                        "error"
                    )
                    return redirect(url_for("documents"))

                if (
                    current_user.role == "VENDOR"
                    and not vendor_can_access_project(
                        project,
                        current_user
                    )
                ):
                    flash(
                        "You are not authorized to use this project.",
                        "error"
                    )
                    return redirect(url_for("documents"))

            # ------------------------------------------------
            # Validate requirement
            # ------------------------------------------------

            requirement = None

            if requirement_id:

                requirement = db.session.get(
                    Requirement,
                    requirement_id
                )

                if not requirement:
                    flash(
                        "Selected requirement was not found.",
                        "error"
                    )
                    return redirect(url_for("documents"))

                if (
                    current_user.role == "VENDOR"
                    and not vendor_can_access_requirement(
                        requirement,
                        current_user
                    )
                ):
                    flash(
                        "You are not authorized to use this requirement.",
                        "error"
                    )
                    return redirect(url_for("documents"))

            # ------------------------------------------------
            # Validate trainer
            # ------------------------------------------------

            trainer = None

            if trainer_id:

                trainer = db.session.get(
                    Trainer,
                    trainer_id
                )

                if not trainer:
                    flash(
                        "Selected trainer was not found.",
                        "error"
                    )
                    return redirect(url_for("documents"))

            # ------------------------------------------------
            # Validate application
            # ------------------------------------------------

            application = None

            if application_id:

                application = db.session.get(
                    Application,
                    application_id
                )

                if not application:
                    flash(
                        "Selected application was not found.",
                        "error"
                    )
                    return redirect(url_for("documents"))

                if (
                    current_user.role == "VENDOR"
                    and not vendor_can_access_application(
                        application,
                        current_user
                    )
                ):
                    flash(
                        "You are not authorized to use this application.",
                        "error"
                    )
                    return redirect(url_for("documents"))

            # ------------------------------------------------
            # Validate payment
            # ------------------------------------------------

            payment = None

            if payment_id:

                payment = db.session.get(
                    Payment,
                    payment_id
                )

                if not payment:
                    flash(
                        "Selected payment was not found.",
                        "error"
                    )
                    return redirect(url_for("documents"))

                if (
                    current_user.role == "VENDOR"
                    and payment.project
                    and not vendor_can_access_project(
                        payment.project,
                        current_user
                    )
                ):
                    flash(
                        "You are not authorized to use this payment.",
                        "error"
                    )
                    return redirect(url_for("documents"))

            # ------------------------------------------------
            # Trainer can only attach/upload to own profile.
            # ------------------------------------------------

            if current_user.role == "TRAINER":

                trainer_profile = current_user.trainer_profile

                if not trainer_profile:
                    flash(
                        "Trainer profile not found.",
                        "error"
                    )
                    return redirect(url_for("documents"))

                if trainer_id and trainer_id != trainer_profile.id:
                    flash(
                        "You can only upload documents for your own trainer profile.",
                        "error"
                    )
                    return redirect(url_for("documents"))

                trainer_id = trainer_profile.id

            # ------------------------------------------------
            # Save file using random server-side name.
            # ------------------------------------------------

            stored_name = (
                f"{uuid.uuid4().hex}.{extension}"
            )

            stored_path = os.path.join(
                DOCUMENT_UPLOAD_FOLDER,
                stored_name
            )

            relative_path = os.path.join(
                "uploads",
                "documents",
                stored_name
            ).replace("\\", "/")

            try:

                uploaded_file.save(stored_path)

                document = Document(
                    document_code="TEMP",
                    original_name=original_name,
                    stored_name=stored_name,
                    file_path=relative_path,
                    document_type=document_type,
                    description=description or None,
                    mime_type=uploaded_file.mimetype,
                    file_size=file_size,
                    project_id=project_id,
                    requirement_id=requirement_id,
                    trainer_id=trainer_id,
                    application_id=application_id,
                    payment_id=payment_id,
                    uploaded_by=current_user.id
                )

                db.session.add(document)
                db.session.flush()

                document.document_code = (
                    f"QT-DOC-{document.id:04d}"
                )

                db.session.commit()

                flash(
                    f"Document {document.document_code} uploaded successfully.",
                    "success"
                )

            except Exception as exc:

                db.session.rollback()

                if os.path.isfile(stored_path):
                    try:
                        os.remove(stored_path)
                    except OSError:
                        pass

                app.logger.exception(
                    "Document upload failed: %s",
                    exc
                )

                flash(
                    "Unable to upload document. Please try again.",
                    "error"
                )

            return redirect(url_for("documents"))

        flash(
            "Invalid document action.",
            "error"
        )

        return redirect(url_for("documents"))

    # ========================================================
    # GET ACTIONS
    # ========================================================

    action = clean_text(
        request.args.get("action"),
        30
    ).lower()

    if action == "download":

        try:
            document_id = int(
                request.args.get("id", "0")
            )
        except (TypeError, ValueError):
            document_id = 0

        document = db.session.get(
            Document,
            document_id
        )

        if not document:
            flash("Document not found.", "error")
            return redirect(url_for("documents"))

        # Access check.
        if current_user.role == "TRAINER":

            trainer_profile = current_user.trainer_profile

            if (
                not trainer_profile
                or document.trainer_id != trainer_profile.id
            ):
                flash(
                    "You are not authorized to access this document.",
                    "error"
                )
                return redirect(url_for("documents"))

        elif current_user.role == "VENDOR":

            allowed = (
                document.uploaded_by == current_user.id
                or (
                    document.project is not None
                    and document.project.created_by == current_user.id
                )
                or (
                    document.requirement is not None
                    and document.requirement.created_by == current_user.id
                )
            )

            if not allowed:
                flash(
                    "You are not authorized to access this document.",
                    "error"
                )
                return redirect(url_for("documents"))

        full_path = os.path.abspath(
            os.path.join(
                app.root_path,
                document.file_path
            )
        )

        upload_root = os.path.abspath(
            DOCUMENT_UPLOAD_FOLDER
        )

        if not full_path.startswith(upload_root + os.sep):
            flash(
                "Invalid document path.",
                "error"
            )
            return redirect(url_for("documents"))

        if not os.path.isfile(full_path):
            flash(
                "The document file is missing from storage.",
                "error"
            )
            return redirect(url_for("documents"))

        return send_file(
            full_path,
            as_attachment=True,
            download_name=document.original_name,
            mimetype=document.mime_type or None
        )

    # ========================================================
    # DOCUMENT LIST
    # ========================================================

    query = Document.query

    if current_user.role == "TRAINER":

        trainer_profile = current_user.trainer_profile

        if trainer_profile:
            query = query.filter(
                Document.trainer_id == trainer_profile.id
            )
        else:
            query = query.filter(False)

    elif current_user.role == "VENDOR":

        vendor_project_ids = [
            project.id
            for project in Project.query.filter_by(
                created_by=current_user.id
            ).all()
        ]

        vendor_requirement_ids = [
            requirement.id
            for requirement in Requirement.query.filter_by(
                created_by=current_user.id
            ).all()
        ]

        conditions = [
            Document.uploaded_by == current_user.id
        ]

        if vendor_project_ids:
            conditions.append(
                Document.project_id.in_(
                    vendor_project_ids
                )
            )

        if vendor_requirement_ids:
            conditions.append(
                Document.requirement_id.in_(
                    vendor_requirement_ids
                )
            )

        query = query.filter(
            or_(*conditions)
        )

    search = clean_text(
        request.args.get("search"),
        100
    )

    document_type_filter = clean_text(
        request.args.get("document_type"),
        50
    ).upper()

    project_filter = clean_text(
        request.args.get("project_id"),
        20
    )

    trainer_filter = clean_text(
        request.args.get("trainer_id"),
        20
    )

    if search:
        query = query.filter(
            or_(
                Document.document_code.ilike(
                    f"%{search}%"
                ),
                Document.original_name.ilike(
                    f"%{search}%"
                ),
                Document.description.ilike(
                    f"%{search}%"
                )
            )
        )

    if document_type_filter in DOCUMENT_ALLOWED_TYPES:
        query = query.filter(
            Document.document_type
            == document_type_filter
        )

    if project_filter:
        try:
            query = query.filter(
                Document.project_id
                == int(project_filter)
            )
        except (TypeError, ValueError):
            pass

    if trainer_filter:
        try:
            query = query.filter(
                Document.trainer_id
                == int(trainer_filter)
            )
        except (TypeError, ValueError):
            pass

    documents = (
        query
        .order_by(
            Document.created_at.desc()
        )
        .all()
    )

    # --------------------------------------------------------
    # Dropdown data
    # --------------------------------------------------------

    if current_user.role == "VENDOR":

        projects = (
            Project.query
            .filter_by(created_by=current_user.id)
            .order_by(Project.project_name.asc())
            .all()
        )

        requirements = (
            Requirement.query
            .filter_by(created_by=current_user.id)
            .order_by(Requirement.title.asc())
            .all()
        )

    else:

        projects = (
            Project.query
            .order_by(Project.project_name.asc())
            .all()
        )

        requirements = (
            Requirement.query
            .order_by(Requirement.title.asc())
            .all()
        )

    if current_user.role == "TRAINER":

        trainers = []

        if current_user.trainer_profile:
            trainers = [
                current_user.trainer_profile
            ]

    else:

        trainers = (
            Trainer.query
            .order_by(Trainer.full_name.asc())
            .all()
        )

    total_documents = len(documents)

    document_type_counts = {}

    for document in documents:
        document_type_counts[
            document.document_type
        ] = document_type_counts.get(
            document.document_type,
            0
        ) + 1

    return render_template(
        "documents.html",
        documents=documents,
        projects=projects,
        requirements=requirements,
        trainers=trainers,
        document_types=sorted(
            DOCUMENT_ALLOWED_TYPES
        ),
        search=search,
        document_type_filter=document_type_filter,
        project_filter=project_filter,
        trainer_filter=trainer_filter,
        total_documents=total_documents,
        document_type_counts=document_type_counts
    )

# ============================================================
# DOCUMENT VIEW / DOWNLOAD
# ============================================================

@app.route(
    "/documents/<int:document_id>/download",
    endpoint="download_document"
)
@login_required
def download_document(document_id):

    current_user = get_current_user()

    document = db.session.get(
        Document,
        document_id
    )

    if not document:
        flash(
            "Document not found.",
            "error"
        )
        return redirect(
            url_for("documents")
        )

    # --------------------------------------------------------
    # ACCESS CONTROL
    # --------------------------------------------------------

    allowed = False

    # SUPER ADMIN
    if current_user.role == "SUPER_ADMIN":

        allowed = True

    # TRAINER
    elif current_user.role == "TRAINER":

        trainer_profile = (
            current_user.trainer_profile
        )

        if trainer_profile:

            allowed = (
                document.trainer_id
                == trainer_profile.id
                or
                document.uploaded_by
                == current_user.id
            )

    # VENDOR
    elif current_user.role == "VENDOR":

        # Document uploaded by the vendor
        if document.uploaded_by == current_user.id:

            allowed = True

        # Document belongs to vendor's project
        elif (
            document.project
            and document.project.created_by
            == current_user.id
        ):

            allowed = True

        # Document belongs to vendor's requirement
        elif (
            document.requirement
            and document.requirement.created_by
            == current_user.id
        ):

            allowed = True

        # Document belongs to a payment
        elif (
            document.payment
            and document.payment.project
            and document.payment.project.created_by
            == current_user.id
        ):

            allowed = True

        # Document belongs to an application
        elif (
            document.application
            and document.application.requirement
            and document.application.requirement.created_by
            == current_user.id
        ):

            allowed = True

    if not allowed:

        flash(
            "You are not authorized to access this document.",
            "error"
        )

        return redirect(
            url_for("documents")
        )

    # --------------------------------------------------------
    # FILE PATH
    # --------------------------------------------------------

    relative_path = (
        document.file_path or ""
    ).replace("\\", "/")

    if not relative_path:

        flash(
            "Document file path is missing.",
            "error"
        )

        return redirect(
            url_for("documents")
        )

    # Prevent path traversal
    safe_relative_path = os.path.normpath(
        relative_path
    )

    if (
        safe_relative_path.startswith("..")
        or os.path.isabs(safe_relative_path)
    ):

        flash(
            "Invalid document path.",
            "error"
        )

        return redirect(
            url_for("documents")
        )

    full_path = os.path.abspath(
        os.path.join(
            app.root_path,
            safe_relative_path
        )
    )

    upload_root = os.path.abspath(
        os.path.join(
            app.root_path,
            "uploads"
        )
    )

    # Ensure requested file stays inside uploads/
    if not (
        full_path == upload_root
        or full_path.startswith(
            upload_root + os.sep
        )
    ):

        flash(
            "Invalid document location.",
            "error"
        )

        return redirect(
            url_for("documents")
        )

    if not os.path.isfile(full_path):

        flash(
            "The document file could not be found on the server.",
            "error"
        )

        return redirect(
            url_for("documents")
        )

    # --------------------------------------------------------
    # SEND FILE
    # --------------------------------------------------------

    return send_file(
        full_path,
        mimetype=document.mime_type or None,
        as_attachment=False,
        download_name=document.original_name
    )

# ============================================================
# COMMUNICATION
# ============================================================

@app.route(
    "/communication",
    methods=["GET", "POST"],
    endpoint="communication"
)
@login_required
def communication_handler():

    current_user = User.query.get(
        session["user_id"]
    )

    if not current_user:

        return redirect(
            url_for("login")
        )

    # ========================================================
    # AJAX HELPER
    # ========================================================

    is_ajax = (
        request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest"
    )

    # ========================================================
    # POST ACTIONS
    # ========================================================

    if request.method == "POST":

        action = request.form.get(
            "action",
            ""
        ).strip()

        # ====================================================
        # SEND MESSAGE
        # ====================================================

        if action == "send":

            # ------------------------------------------------
            # ROLE CHECK
            # ------------------------------------------------

            if current_user.role not in [
                "SUPER_ADMIN",
                "VENDOR",
                "TRAINER"
            ]:

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "You are not authorized to send messages."
                    }), 403

                flash(
                    "You are not authorized to send messages.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            # ------------------------------------------------
            # CSRF
            # ------------------------------------------------

            if not validate_csrf():

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "Invalid security token. Please refresh the page and try again."
                    }), 400

                flash(
                    "Invalid security token. Please try again.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            # ------------------------------------------------
            # FORM DATA
            # ------------------------------------------------

            receiver_id = request.form.get(
                "receiver_id",
                type=int
            )

            subject = request.form.get(
                "subject",
                "Chat Message"
            ).strip()

            message = request.form.get(
                "message",
                ""
            ).strip()

            priority = request.form.get(
                "priority",
                "NORMAL"
            ).strip().upper()

            attachment = request.files.get(
                "attachment"
            )

            # ------------------------------------------------
            # RECEIVER VALIDATION
            # ------------------------------------------------

            if not receiver_id:

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "Please select a recipient."
                    }), 400

                flash(
                    "Please select a recipient.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            if not subject:

                subject = "Chat Message"

            if priority not in [
                "NORMAL",
                "IMPORTANT",
                "URGENT"
            ]:

                priority = "NORMAL"

            receiver = User.query.get(
                receiver_id
            )

            if not receiver:

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "Recipient not found."
                    }), 404

                flash(
                    "Recipient not found.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            if not receiver.is_active:

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "The selected user is inactive."
                    }), 400

                flash(
                    "The selected user is inactive.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            if receiver.id == current_user.id:

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "You cannot send a message to yourself."
                    }), 400

                flash(
                    "You cannot send a message to yourself.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            # ------------------------------------------------
            # ATTACHMENT VARIABLES
            # ------------------------------------------------

            attachment_name = None
            attachment_path = None
            attachment_type = None
            attachment_size = None

            # ------------------------------------------------
            # PROCESS ATTACHMENT
            # ------------------------------------------------

            if (
                attachment
                and
                attachment.filename
            ):

                original_filename = secure_filename(
                    attachment.filename
                )

                if not original_filename:

                    if is_ajax:

                        return jsonify({
                            "success": False,
                            "message":
                                "Invalid attachment filename."
                        }), 400

                    flash(
                        "Invalid attachment filename.",
                        "error"
                    )

                    return redirect(
                        url_for("communication")
                    )

                # --------------------------------------------
                # FILE SIZE
                # --------------------------------------------

                attachment.seek(
                    0,
                    os.SEEK_END
                )

                file_size = attachment.tell()

                attachment.seek(
                    0
                )

                if (
                    file_size >
                    COMMUNICATION_MAX_FILE_SIZE
                ):

                    if is_ajax:

                        return jsonify({
                            "success": False,
                            "message":
                                "Attachment must be 25 MB or smaller."
                        }), 400

                    flash(
                        "Attachment must be 25 MB or smaller.",
                        "error"
                    )

                    return redirect(
                        url_for("communication")
                    )

                # --------------------------------------------
                # EXTENSION
                # --------------------------------------------

                extension = ""

                if "." in original_filename:

                    extension = (
                        "."
                        +
                        original_filename.rsplit(
                            ".",
                            1
                        )[1].lower()
                    )

                # --------------------------------------------
                # UNIQUE FILE NAME
                # --------------------------------------------

                unique_filename = (
                    uuid.uuid4().hex
                    +
                    extension
                )

                full_save_path = os.path.join(
                    COMMUNICATION_UPLOAD_FOLDER,
                    unique_filename
                )

                # --------------------------------------------
                # SAVE FILE
                # --------------------------------------------

                try:

                    attachment.save(
                        full_save_path
                    )

                except Exception as error:

                    print(
                        "Communication attachment error:",
                        error
                    )

                    if is_ajax:

                        return jsonify({
                            "success": False,
                            "message":
                                "Unable to save the attachment."
                        }), 500

                    flash(
                        "Unable to save the attachment.",
                        "error"
                    )

                    return redirect(
                        url_for("communication")
                    )

                # --------------------------------------------
                # DATABASE VALUES
                # --------------------------------------------

                attachment_name = (
                    original_filename
                )

                attachment_path = (
                    "uploads/communication/"
                    +
                    unique_filename
                )

                attachment_type = (
                    attachment.content_type
                    or
                    "application/octet-stream"
                )

                attachment_size = os.path.getsize(
                    full_save_path
                )

            # ------------------------------------------------
            # MESSAGE VALIDATION
            # ------------------------------------------------

            if (
                not message
                and
                not attachment_name
            ):

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "Please type a message or attach a file."
                    }), 400

                flash(
                    "Please type a message or attach a file.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            # ------------------------------------------------
            # ATTACHMENT ONLY
            # ------------------------------------------------

            if (
                not message
                and
                attachment_name
            ):

                message = (
                    "📎 "
                    +
                    attachment_name
                )

            # ------------------------------------------------
            # CREATE COMMUNICATION
            # ------------------------------------------------

            communication = Communication(

                communication_code="TEMP",

                sender_id=current_user.id,

                receiver_id=receiver.id,

                communication_type="MESSAGE",

                subject=subject,

                message=message,

                priority=priority,

                status="SENT",

                is_read=False,

                attachment_name=attachment_name,

                attachment_path=attachment_path,

                attachment_type=attachment_type,

                attachment_size=attachment_size

            )

            # ------------------------------------------------
            # SAVE TO DATABASE
            # ------------------------------------------------

            try:

                db.session.add(
                    communication
                )

                db.session.flush()

                communication.communication_code = (
                    f"QT-COM-{communication.id:04d}"
                )

                db.session.commit()

            except Exception as error:

                db.session.rollback()

                print(
                    "================================================"
                )

                print(
                    "COMMUNICATION DATABASE ERROR:"
                )

                print(
                    repr(error)
                )

                print(
                    "================================================"
                )

                # --------------------------------------------
                # DELETE FILE IF DATABASE SAVE FAILED
                # --------------------------------------------

                if attachment_path:

                    failed_file = os.path.join(
                        app.root_path,
                        attachment_path
                    )

                    if os.path.isfile(
                        failed_file
                    ):

                        try:

                            os.remove(
                                failed_file
                            )

                        except OSError:
                            pass

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "Unable to send the message. Please try again."
                    }), 500

                flash(
                    "Unable to send the message. Please try again.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            # =================================================
            # AJAX SUCCESS
            # =================================================

            if is_ajax:

                return jsonify({

                    "success": True,

                    "message":
                        "Message sent successfully.",

                    "message_data": {

                        "id":
                            communication.id,

                        "type":
                            "sent",

                        "partnerId":
                            receiver.id,

                        "partnerName":
                            receiver.full_name,

                        "partnerRole":
                            receiver.role,

                        "subject":
                            communication.subject,

                        "message":
                            communication.message,

                        "priority":
                            communication.priority,

                        "read":
                            True,

                        "created":
                            (
                                format_india_time(
                                    communication.created_at
                                )
                                if communication.created_at
                                else ""
                            ),

                        "attachmentName":
                            (
                                communication.attachment_name
                                or ""
                            ),

                        "attachmentPath":
                            (
                                communication.attachment_path
                                or ""
                            ),

                        "attachmentType":
                            (
                                communication.attachment_type
                                or ""
                            ),

                        "attachmentSize":
                            (
                                communication.attachment_size
                                or 0
                            )

                    }

                })

            # =================================================
            # NORMAL FORM FALLBACK
            # =================================================

            flash(
                "Message sent successfully.",
                "success"
            )

            return redirect(
                url_for("communication")
            )

        # ====================================================
        # MARK MESSAGE AS READ
        # ====================================================

        elif action == "read":

            if not validate_csrf():

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "Invalid security token."
                    }), 400

                flash(
                    "Invalid security token.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            communication_id = request.form.get(
                "communication_id",
                type=int
            )

            communication = Communication.query.get(
                communication_id
            )

            if not communication:

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "Communication not found."
                    }), 404

                flash(
                    "Communication not found.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            if communication.receiver_id != current_user.id:

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "You are not authorized."
                    }), 403

                flash(
                    "You are not authorized to update this message.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            communication.is_read = True

            db.session.commit()

            if is_ajax:

                return jsonify({
                    "success": True
                })

            return redirect(
                url_for("communication")
            )

        # ====================================================
        # MARK ALL READ
        # ====================================================

        elif action == "read-all":

            if not validate_csrf():

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "Invalid security token."
                    }), 400

                flash(
                    "Invalid security token.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            Communication.query.filter_by(
                receiver_id=current_user.id,
                is_read=False
            ).update(
                {
                    "is_read": True
                },
                synchronize_session=False
            )

            db.session.commit()

            if is_ajax:

                return jsonify({
                    "success": True
                })

            flash(
                "All messages marked as read.",
                "success"
            )

            return redirect(
                url_for("communication")
            )

        # ====================================================
        # ARCHIVE
        # ====================================================

        elif action == "archive":

            if not validate_csrf():

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "Invalid security token."
                    }), 400

                flash(
                    "Invalid security token.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            communication_id = request.form.get(
                "communication_id",
                type=int
            )

            communication = Communication.query.get(
                communication_id
            )

            if not communication:

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "Communication not found."
                    }), 404

                flash(
                    "Communication not found.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            if (
                communication.sender_id != current_user.id
                and
                communication.receiver_id != current_user.id
            ):

                if is_ajax:

                    return jsonify({
                        "success": False,
                        "message":
                            "You are not authorized to archive this message."
                    }), 403

                flash(
                    "You are not authorized to archive this message.",
                    "error"
                )

                return redirect(
                    url_for("communication")
                )

            communication.status = "ARCHIVED"

            db.session.commit()

            if is_ajax:

                return jsonify({
                    "success": True
                })

            flash(
                "Message archived.",
                "success"
            )

            return redirect(
                url_for("communication")
            )

    # ========================================================
    # GET — LOAD COMMUNICATIONS
    # ========================================================

    received_messages = (
        Communication.query
        .filter(
            Communication.receiver_id ==
            current_user.id,

            Communication.status !=
            "ARCHIVED"
        )
        .order_by(
            Communication.created_at.desc()
        )
        .all()
    )

    sent_messages = (
        Communication.query
        .filter(
            Communication.sender_id ==
            current_user.id,

            Communication.status !=
            "ARCHIVED"
        )
        .order_by(
            Communication.created_at.desc()
        )
        .all()
    )

    # ========================================================
    # UNREAD
    # ========================================================

    unread_count = (
        Communication.query
        .filter_by(
            receiver_id=current_user.id,
            is_read=False,
            status="SENT"
        )
        .count()
    )

    # ========================================================
    # TOTALS
    # ========================================================

    total_received = (
        Communication.query
        .filter_by(
            receiver_id=current_user.id
        )
        .count()
    )

    total_sent = (
        Communication.query
        .filter_by(
            sender_id=current_user.id
        )
        .count()
    )

    # ========================================================
    # MESSAGE USERS
    # ========================================================

    if current_user.role == "SUPER_ADMIN":

        message_users = (
            User.query
            .filter(
                User.id != current_user.id,
                User.is_active == True
            )
            .order_by(
                User.full_name.asc()
            )
            .all()
        )

    elif current_user.role == "VENDOR":

        message_users = (
            User.query
            .filter(
                User.id != current_user.id,
                User.role == "TRAINER",
                User.is_active == True
            )
            .order_by(
                User.full_name.asc()
            )
            .all()
        )

    elif current_user.role == "TRAINER":

        message_users = (
            User.query
            .filter(
                User.id != current_user.id,
                User.role == "VENDOR",
                User.is_active == True
            )
            .order_by(
                User.full_name.asc()
            )
            .all()
        )

    else:

        message_users = []

    # ========================================================
    # RENDER
    # ========================================================

    return render_template(

        "communication.html",

        communications=received_messages,

        received_messages=received_messages,

        sent_messages=sent_messages,

        message_users=message_users,

        unread_count=unread_count,

        total_received=total_received,

        total_sent=total_sent,

        current_user=current_user

    )


# ============================================================
# COMMUNICATION ATTACHMENT
# ============================================================

@app.route(
    "/communication/attachment/<int:communication_id>"
)
@login_required
def communication_attachment(
    communication_id
):

    current_user = User.query.get(
        session["user_id"]
    )

    if not current_user:

        return redirect(
            url_for("login")
        )

    communication = Communication.query.get(
        communication_id
    )

    if not communication:

        flash(
            "Attachment not found.",
            "error"
        )

        return redirect(
            url_for("communication")
        )

    # --------------------------------------------------------
    # SECURITY
    # --------------------------------------------------------

    if (
        communication.sender_id != current_user.id
        and
        communication.receiver_id != current_user.id
    ):

        flash(
            "You are not authorized to access this attachment.",
            "error"
        )

        return redirect(
            url_for("communication")
        )

    if not communication.attachment_path:

        flash(
            "This message does not contain an attachment.",
            "error"
        )

        return redirect(
            url_for("communication")
        )

    # --------------------------------------------------------
    # STORED FILENAME
    # --------------------------------------------------------

    stored_filename = os.path.basename(
        communication.attachment_path
    )

    full_path = os.path.join(
        COMMUNICATION_UPLOAD_FOLDER,
        stored_filename
    )

    if not os.path.isfile(
        full_path
    ):

        flash(
            "The attachment file could not be found.",
            "error"
        )

        return redirect(
            url_for("communication")
        )

    # --------------------------------------------------------
    # SEND FILE
    # --------------------------------------------------------

    return send_file(

        full_path,

        mimetype=(
            communication.attachment_type
            or
            "application/octet-stream"
        ),

        as_attachment=True,

        download_name=(
            communication.attachment_name
            or
            "attachment"
        )
    )


# ============================================================
# COMMUNICATION UPLOADS
# ============================================================

COMMUNICATION_UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "uploads",
    "communication"
)

os.makedirs(
    COMMUNICATION_UPLOAD_FOLDER,
    exist_ok=True
)

COMMUNICATION_MAX_FILE_SIZE = (
    25 * 1024 * 1024
)

# ============================================================
# ADMIN SETTINGS
# ============================================================

@app.route(
    "/settings",
    methods=["GET", "POST"],
    endpoint="settings"
)
@login_required
def settings_handler():

    current_user = get_current_user()

    # --------------------------------------------------------
    # SUPER ADMIN ONLY
    # --------------------------------------------------------

    if not current_user or current_user.role != "SUPER_ADMIN":

        flash(
            "You are not authorized to access system settings.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )


    # ========================================================
    # POST - SAVE SETTINGS
    # ========================================================

    if request.method == "POST":

        if not validate_csrf():

            flash(
                "Invalid security token. Please try again.",
                "error"
            )

            return redirect(
                url_for("settings")
            )


        action = clean_text(
            request.form.get("action"),
            30
        ).lower()


        if action == "save":

            settings_data = {

                # --------------------------------------------
                # GENERAL
                # --------------------------------------------

                "platform_name": (
                    clean_text(
                        request.form.get("platform_name"),
                        150
                    )
                    or "QT Platform"
                ),

                "company_name": (
                    clean_text(
                        request.form.get("company_name"),
                        150
                    )
                ),

                "company_email": (
                    clean_text(
                        request.form.get("company_email"),
                        150
                    )
                ),

                "company_phone": (
                    clean_text(
                        request.form.get("company_phone"),
                        50
                    )
                ),

                "company_address": (
                    clean_text(
                        request.form.get("company_address"),
                        500
                    )
                ),

                "timezone": (
                    clean_text(
                        request.form.get("timezone"),
                        100
                    )
                    or "Asia/Kolkata"
                ),

                "date_format": (
                    clean_text(
                        request.form.get("date_format"),
                        50
                    )
                    or "DD MMM YYYY"
                ),


                # --------------------------------------------
                # SECURITY
                # --------------------------------------------

                "session_timeout": (
                    clean_text(
                        request.form.get("session_timeout"),
                        20
                    )
                    or "60"
                ),

                "password_min_length": (
                    clean_text(
                        request.form.get("password_min_length"),
                        20
                    )
                    or "8"
                ),

                "login_attempt_limit": (
                    clean_text(
                        request.form.get("login_attempt_limit"),
                        20
                    )
                    or "5"
                ),


                # --------------------------------------------
                # NOTIFICATIONS
                # --------------------------------------------

                "email_notifications": (
                    "1"
                    if request.form.get("email_notifications")
                    else "0"
                ),

                "requirement_notifications": (
                    "1"
                    if request.form.get("requirement_notifications")
                    else "0"
                ),

                "application_notifications": (
                    "1"
                    if request.form.get("application_notifications")
                    else "0"
                ),

                "schedule_notifications": (
                    "1"
                    if request.form.get("schedule_notifications")
                    else "0"
                ),

                "payment_notifications": (
                    "1"
                    if request.form.get("payment_notifications")
                    else "0"
                ),

                "communication_notifications": (
                    "1"
                    if request.form.get("communication_notifications")
                    else "0"
                ),


                # --------------------------------------------
                # COMMUNICATION
                # --------------------------------------------

                "communication_enabled": (
                    "1"
                    if request.form.get("communication_enabled")
                    else "0"
                ),

                "project_chat_enabled": (
                    "1"
                    if request.form.get("project_chat_enabled")
                    else "0"
                ),

                "communication_attachments": (
                    "1"
                    if request.form.get("communication_attachments")
                    else "0"
                ),

                "max_attachment_size": (
                    clean_text(
                        request.form.get("max_attachment_size"),
                        20
                    )
                    or "10"
                ),


                # --------------------------------------------
                # DOCUMENTS
                # --------------------------------------------

                "max_upload_size": (
                    clean_text(
                        request.form.get("max_upload_size"),
                        20
                    )
                    or "10"
                ),

                "document_storage": (
                    clean_text(
                        request.form.get("document_storage"),
                        250
                    )
                    or "uploads/documents"
                ),


                # --------------------------------------------
                # APPEARANCE
                # --------------------------------------------

                "theme": (
                    clean_text(
                        request.form.get("theme"),
                        30
                    )
                    or "light"
                ),

                "primary_color": (
                    clean_text(
                        request.form.get("primary_color"),
                        30
                    )
                    or "#176FF2"
                )

            }


            try:

                for key, value in settings_data.items():

                    setting = (
                        SystemSetting.query
                        .filter_by(
                            setting_key=key
                        )
                        .first()
                    )


                    if setting:

                        setting.setting_value = value

                    else:

                        setting = SystemSetting(

                            setting_key=key,

                            setting_value=value,

                            category=(
                                "GENERAL"
                                if key in {
                                    "platform_name",
                                    "company_name",
                                    "company_email",
                                    "company_phone",
                                    "company_address",
                                    "timezone",
                                    "date_format"
                                }

                                else
                                "SECURITY"
                                if key in {
                                    "session_timeout",
                                    "password_min_length",
                                    "login_attempt_limit"
                                }

                                else
                                "NOTIFICATIONS"
                                if "notifications" in key
                                else
                                "COMMUNICATION"
                                if "communication" in key
                                or "chat" in key
                                or "attachment" in key
                                else
                                "DOCUMENTS"
                                if key in {
                                    "max_upload_size",
                                    "document_storage"
                                }

                                else
                                "APPEARANCE"
                            )
                        )

                        db.session.add(setting)


                db.session.commit()


                flash(
                    "Settings saved successfully.",
                    "success"
                )


            except Exception:

                db.session.rollback()

                flash(
                    "Unable to save settings.",
                    "error"
                )


            return redirect(
                url_for("settings")
            )


    # ========================================================
    # GET SETTINGS
    # ========================================================

    saved_settings = (
        SystemSetting.query
        .all()
    )


    settings = {

        item.setting_key:
            item.setting_value

        for item in saved_settings

    }


    # ========================================================
    # DEFAULT VALUES
    # ========================================================

    DEFAULT_SETTINGS = {

    # --------------------------------------------------------
    # GENERAL
    # --------------------------------------------------------

    "platform_name": {
        "value": "QT Platform",
        "category": "GENERAL",
        "description": "Platform display name"
    },

    "company_name": {
        "value": "Hyfii Solutions",
        "category": "GENERAL",
        "description": "Company name"
    },

    "company_email": {
        "value": "",
        "category": "GENERAL",
        "description": "Company email address"
    },

    "company_phone": {
        "value": "",
        "category": "GENERAL",
        "description": "Company phone number"
    },

    "company_address": {
        "value": "",
        "category": "GENERAL",
        "description": "Company address"
    },

    "timezone": {
        "value": "Asia/Kolkata",
        "category": "GENERAL",
        "description": "Platform timezone"
    },

    "date_format": {
        "value": "DD MMM YYYY",
        "category": "GENERAL",
        "description": "Platform date format"
    },

    # --------------------------------------------------------
    # USERS & ROLES
    # --------------------------------------------------------

    "user_registration": {
        "value": "0",
        "category": "USERS",
        "description": "Allow public user registration"
    },

    "allow_vendor_registration": {
        "value": "0",
        "category": "USERS",
        "description": "Allow vendor registration"
    },

    "allow_trainer_registration": {
        "value": "0",
        "category": "USERS",
        "description": "Allow trainer registration"
    },

    # --------------------------------------------------------
    # SECURITY
    # --------------------------------------------------------

    "session_timeout": {
        "value": "60",
        "category": "SECURITY",
        "description": "Session timeout in minutes"
    },

    "password_min_length": {
        "value": "8",
        "category": "SECURITY",
        "description": "Minimum password length"
    },

    "login_attempt_limit": {
        "value": "5",
        "category": "SECURITY",
        "description": "Maximum login attempts"
    },

    "force_password_change": {
        "value": "0",
        "category": "SECURITY",
        "description": "Force users to change password"
    },

    # --------------------------------------------------------
    # NOTIFICATIONS
    # --------------------------------------------------------

    "email_notifications": {
        "value": "1",
        "category": "NOTIFICATIONS",
        "description": "Enable email notifications"
    },

    "requirement_notifications": {
        "value": "1",
        "category": "NOTIFICATIONS",
        "description": "Requirement notifications"
    },

    "application_notifications": {
        "value": "1",
        "category": "NOTIFICATIONS",
        "description": "Application notifications"
    },

    "schedule_notifications": {
        "value": "1",
        "category": "NOTIFICATIONS",
        "description": "Schedule notifications"
    },

    "payment_notifications": {
        "value": "1",
        "category": "NOTIFICATIONS",
        "description": "Payment notifications"
    },

    "communication_notifications": {
        "value": "1",
        "category": "NOTIFICATIONS",
        "description": "Communication notifications"
    },

    # --------------------------------------------------------
    # COMMUNICATION
    # --------------------------------------------------------

    "communication_enabled": {
        "value": "1",
        "category": "COMMUNICATION",
        "description": "Enable communication"
    },

    "project_chat_enabled": {
        "value": "1",
        "category": "COMMUNICATION",
        "description": "Enable project chat"
    },

    "communication_attachments": {
        "value": "1",
        "category": "COMMUNICATION",
        "description": "Allow communication attachments"
    },

    "max_attachment_size": {
        "value": "10",
        "category": "COMMUNICATION",
        "description": "Maximum attachment size in MB"
    },

    # --------------------------------------------------------
    # DOCUMENTS
    # --------------------------------------------------------

    "max_upload_size": {
        "value": "10",
        "category": "DOCUMENTS",
        "description": "Maximum document upload size in MB"
    },

    "document_storage": {
        "value": "uploads/documents",
        "category": "DOCUMENTS",
        "description": "Document storage location"
    },

    "allowed_file_types": {
        "value": "pdf,doc,docx,xls,xlsx,csv,ppt,pptx,txt,jpg,jpeg,png",
        "category": "DOCUMENTS",
        "description": "Allowed document extensions"
    },

    # --------------------------------------------------------
    # APPEARANCE
    # --------------------------------------------------------

    "theme": {
        "value": "light",
        "category": "APPEARANCE",
        "description": "Platform theme"
    },

    "primary_color": {
        "value": "#176FF2",
        "category": "APPEARANCE",
        "description": "Primary platform color"
    },

    "compact_mode": {
        "value": "0",
        "category": "APPEARANCE",
        "description": "Compact interface mode"
    },

    # --------------------------------------------------------
    # SYSTEM
    # --------------------------------------------------------

    "maintenance_mode": {
        "value": "0",
        "category": "SYSTEM",
        "description": "Enable maintenance mode"
    }
}


    for key, value in defaults.items():

        settings.setdefault(
            key,
            value
        )


    return render_template(
        "settings.html",
        settings=settings
    )
    
# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )

