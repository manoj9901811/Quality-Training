from database import db


# ============================================================
# USER MODEL
# ============================================================

class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    full_name = db.Column(
        db.String(150),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(30),
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    # --------------------------------------------------------
    # Trainer profile relationship
    # --------------------------------------------------------

    trainer_profile = db.relationship(
        "Trainer",
        back_populates="user",
        uselist=False
    )

    # --------------------------------------------------------
    # Requirements created by this user
    # --------------------------------------------------------

    created_requirements = db.relationship(
        "Requirement",
        back_populates="creator",
        foreign_keys="Requirement.created_by"
    )

    def __repr__(self):

        return f"<User {self.email}>"


# ============================================================
# TRAINER MODEL
# ============================================================

class Trainer(db.Model):

    __tablename__ = "trainers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # --------------------------------------------------------
    # Trainer name
    # --------------------------------------------------------

    full_name = db.Column(
        db.String(150),
        nullable=False
    )

    # --------------------------------------------------------
    # Optional login account
    #
    # A trainer profile can exist without a login account.
    # --------------------------------------------------------

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        unique=True,
        nullable=True
    )

    phone = db.Column(
        db.String(30)
    )

    location = db.Column(
        db.String(150)
    )

    bio = db.Column(
        db.Text
    )

    skills = db.Column(
        db.Text
    )

    experience_years = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    hourly_rate = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    availability = db.Column(
        db.String(50),
        default="AVAILABLE",
        nullable=False
    )

    trainer_status = db.Column(
        db.String(30),
        default="ACTIVE",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    # --------------------------------------------------------
    # Login relationship
    # --------------------------------------------------------

    user = db.relationship(
        "User",
        back_populates="trainer_profile"
    )

    def __repr__(self):

        return f"<Trainer {self.id}>"


# ============================================================
# REQUIREMENT MODEL
# ============================================================

class Requirement(db.Model):

    __tablename__ = "requirements"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # --------------------------------------------------------
    # Requirement identification
    #
    # Example:
    # QT-REQ-0001
    # QT-REQ-0002
    # --------------------------------------------------------

    requirement_code = db.Column(
        db.String(30),
        unique=True,
        nullable=False,
        index=True
    )

    # --------------------------------------------------------
    # Basic requirement information
    # --------------------------------------------------------

    title = db.Column(
        db.String(200),
        nullable=False
    )

    client_name = db.Column(
        db.String(150),
        nullable=False
    )

    skill = db.Column(
        db.String(150),
        nullable=False
    )

    # --------------------------------------------------------
    # Trainer requirement
    # --------------------------------------------------------

    trainer_count = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    # --------------------------------------------------------
    # Training details
    # --------------------------------------------------------

    location = db.Column(
        db.String(150)
    )

    start_date = db.Column(
        db.Date
    )

    duration = db.Column(
        db.String(100)
    )

    # --------------------------------------------------------
    # Budget
    # --------------------------------------------------------

    budget = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    # --------------------------------------------------------
    # Requirement status
    #
    # OPEN
    # IN_PROGRESS
    # ASSIGNED
    # COMPLETED
    # CANCELLED
    # --------------------------------------------------------

    status = db.Column(
        db.String(30),
        nullable=False,
        default="OPEN"
    )

    # --------------------------------------------------------
    # Additional information
    # --------------------------------------------------------

    notes = db.Column(
        db.Text
    )

    # --------------------------------------------------------
    # User who created the requirement
    # --------------------------------------------------------

    created_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # --------------------------------------------------------
    # Timestamps
    # --------------------------------------------------------

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    # --------------------------------------------------------
    # Creator relationship
    # --------------------------------------------------------

    creator = db.relationship(
        "User",
        back_populates="created_requirements",
        foreign_keys=[created_by]
    )

    def __repr__(self):

        return f"<Requirement {self.requirement_code}>"
    
class Project(db.Model):

    __tablename__ = "projects"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    project_code = db.Column(
        db.String(30),
        unique=True,
        nullable=False,
        index=True
    )

    project_name = db.Column(
        db.String(200),
        nullable=False
    )

    requirement_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "requirements.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    client_name = db.Column(
        db.String(150),
        nullable=False
    )

    skill = db.Column(
        db.String(150),
        nullable=False
    )

    location = db.Column(
        db.String(150)
    )

    start_date = db.Column(
        db.Date
    )

    end_date = db.Column(
        db.Date
    )

    budget = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="PLANNING"
    )

    notes = db.Column(
        db.Text
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    requirement = db.relationship(
        "Requirement",
        backref=db.backref(
            "projects",
            lazy=True
        )
    )

    creator = db.relationship(
        "User",
        foreign_keys=[created_by]
    )

    # Trainers assigned to this project.
    trainer_assignments = db.relationship(
        "ProjectTrainer",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<Project {self.project_code}>"
    
class ProjectTrainer(db.Model):

    __tablename__ = "project_trainers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "projects.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    trainer_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "trainers.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    assigned_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    assigned_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    assignment_status = db.Column(
        db.String(30),
        nullable=False,
        default="ASSIGNED"
    )

    notes = db.Column(
        db.Text
    )


    project = db.relationship(
        "Project",
        back_populates="trainer_assignments"
    )


    trainer = db.relationship(
        "Trainer",
        backref=db.backref(
            "project_assignments",
            lazy=True
        )
    )


    assigner = db.relationship(
        "User",
        foreign_keys=[assigned_by]
    )


    __table_args__ = (
        db.UniqueConstraint(
            "project_id",
            "trainer_id",
            name="uq_project_trainer"
        ),
    )


    def __repr__(self):

        return (
            f"<ProjectTrainer "
            f"project={self.project_id} "
            f"trainer={self.trainer_id}>"
        )
        
# ============================================================
# APPLICATION MODEL
# ============================================================

class Application(db.Model):

    __tablename__ = "applications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # --------------------------------------------------------
    # Requirement
    # --------------------------------------------------------

    requirement_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "requirements.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # --------------------------------------------------------
    # Trainer
    # --------------------------------------------------------

    trainer_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "trainers.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # --------------------------------------------------------
    # User who created the application
    #
    # Usually SUPER_ADMIN or VENDOR
    # --------------------------------------------------------

    created_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # --------------------------------------------------------
    # Application source
    #
    # VENDOR_INVITED
    # AI_RECOMMENDED
    # TRAINER_APPLIED
    # --------------------------------------------------------

    source = db.Column(
        db.String(30),
        nullable=False,
        default="VENDOR_INVITED"
    )

    # --------------------------------------------------------
    # Application status
    #
    # PENDING
    # ACCEPTED
    # REJECTED
    # SELECTED
    # WITHDRAWN
    # --------------------------------------------------------

    status = db.Column(
        db.String(30),
        nullable=False,
        default="PENDING",
        index=True
    )

    # --------------------------------------------------------
    # AI / matching score
    #
    # Example:
    # 87.5
    # --------------------------------------------------------

    match_score = db.Column(
        db.Float,
        nullable=True
    )

    # --------------------------------------------------------
    # Message sent to trainer
    # --------------------------------------------------------

    message = db.Column(
        db.Text
    )

    # --------------------------------------------------------
    # Trainer/vendor response note
    # --------------------------------------------------------

    response_note = db.Column(
        db.Text
    )

    # --------------------------------------------------------
    # Timestamps
    # --------------------------------------------------------

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    # Requirement associated with application
    requirement = db.relationship(
        "Requirement",
        backref=db.backref(
            "applications",
            lazy=True
        )
    )

    # Trainer associated with application
    trainer = db.relationship(
        "Trainer",
        backref=db.backref(
            "applications",
            lazy=True
        )
    )

    # User who created application
    creator = db.relationship(
        "User",
        foreign_keys=[created_by]
    )

    # ========================================================
    # CONSTRAINTS
    # ========================================================

    # One trainer cannot have multiple applications
    # for the same requirement.
    __table_args__ = (
        db.UniqueConstraint(
            "requirement_id",
            "trainer_id",
            name="uq_requirement_trainer_application"
        ),
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self):

        return (
            f"<Application "
            f"requirement={self.requirement_id} "
            f"trainer={self.trainer_id} "
            f"status={self.status}>"
        )
        
# ============================================================
# SCHEDULE MODEL
# ============================================================

class Schedule(db.Model):

    __tablename__ = "schedules"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    schedule_code = db.Column(
        db.String(30),
        unique=True,
        nullable=False,
        index=True
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "projects.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    trainer_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "trainers.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    start_datetime = db.Column(
        db.DateTime,
        nullable=False,
        index=True
    )

    end_datetime = db.Column(
        db.DateTime,
        nullable=False
    )

    mode = db.Column(
        db.String(30),
        nullable=False,
        default="OFFLINE"
    )

    location = db.Column(
        db.String(250),
        nullable=True
    )

    meeting_link = db.Column(
        db.String(500),
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="SCHEDULED",
        index=True
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    project = db.relationship(
        "Project",
        backref=db.backref(
            "schedules",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    trainer = db.relationship(
        "Trainer",
        backref=db.backref(
            "schedules",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    creator = db.relationship(
        "User",
        foreign_keys=[created_by]
    )

    def __repr__(self):

        return (
            f"<Schedule "
            f"{self.schedule_code} "
            f"project={self.project_id} "
            f"trainer={self.trainer_id}>"
        )
        
# ============================================================
# NOTIFICATION MODEL
# ============================================================

class Notification(db.Model):

    __tablename__ = "notifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    notification_type = db.Column(
        db.String(50),
        nullable=False,
        default="SYSTEM"
    )

    related_type = db.Column(
        db.String(50),
        nullable=True
    )

    related_id = db.Column(
        db.Integer,
        nullable=True
    )

    is_read = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        index=True
    )

    read_at = db.Column(
        db.DateTime,
        nullable=True
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "notifications",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    def __repr__(self):

        return (
            f"<Notification "
            f"id={self.id} "
            f"user={self.user_id}>"
        )

# ============================================================
# ATTENDANCE MODEL
# ============================================================

class Attendance(db.Model):

    __tablename__ = "attendance"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    schedule_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "schedules.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    trainer_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "trainers.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    attendance_date = db.Column(
        db.Date,
        nullable=False,
        index=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="PRESENT",
        index=True
    )

    check_in = db.Column(
        db.Time,
        nullable=True
    )

    check_out = db.Column(
        db.Time,
        nullable=True
    )

    remarks = db.Column(
        db.Text,
        nullable=True
    )

    marked_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    # --------------------------------------------------------
    # Relationships
    # --------------------------------------------------------

    schedule = db.relationship(
        "Schedule",
        backref=db.backref(
            "attendance_records",
            lazy=True
        )
    )

    trainer = db.relationship(
        "Trainer",
        backref=db.backref(
            "attendance_records",
            lazy=True
        )
    )

    marker = db.relationship(
        "User",
        foreign_keys=[marked_by]
    )

    # --------------------------------------------------------
    # Prevent duplicate attendance
    # --------------------------------------------------------

    __table_args__ = (
        db.UniqueConstraint(
            "schedule_id",
            "trainer_id",
            "attendance_date",
            name="uq_attendance_schedule_trainer_date"
        ),
    )

    def __repr__(self):

        return (
            f"<Attendance "
            f"schedule={self.schedule_id} "
            f"trainer={self.trainer_id} "
            f"date={self.attendance_date}>"
        )
        
# ============================================================
# PAYMENT MODEL
# ============================================================

class Payment(db.Model):

    __tablename__ = "payments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    payment_code = db.Column(
        db.String(30),
        unique=True,
        nullable=False,
        index=True
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "projects.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    trainer_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "trainers.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # --------------------------------------------------------
    # BILLING DETAILS
    # --------------------------------------------------------

    payment_type = db.Column(
        db.String(30),
        nullable=False,
        default="TRAINER_PAYMENT"
    )

    rate_type = db.Column(
        db.String(30),
        nullable=False,
        default="PER_DAY"
    )

    rate = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    total_days = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    total_hours = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    gross_amount = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    adjustment_amount = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    final_amount = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    # --------------------------------------------------------
    # PAYMENT STATUS
    # --------------------------------------------------------

    status = db.Column(
        db.String(30),
        nullable=False,
        default="PENDING",
        index=True
    )

    payment_date = db.Column(
        db.Date,
        nullable=True
    )

    due_date = db.Column(
        db.Date,
        nullable=True,
        index=True
    )

    payment_method = db.Column(
        db.String(50),
        nullable=True
    )

    transaction_reference = db.Column(
        db.String(150),
        nullable=True
    )

    # --------------------------------------------------------
    # NOTES
    # --------------------------------------------------------

    notes = db.Column(
        db.Text,
        nullable=True
    )

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    created_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    project = db.relationship(
        "Project",
        backref=db.backref(
            "payments",
            lazy=True
        )
    )

    trainer = db.relationship(
        "Trainer",
        backref=db.backref(
            "payments",
            lazy=True
        )
    )

    creator = db.relationship(
        "User",
        foreign_keys=[created_by]
    )

    # --------------------------------------------------------
    # CONSTRAINTS
    # --------------------------------------------------------

    __table_args__ = (
        db.CheckConstraint(
            "rate >= 0",
            name="ck_payment_rate_non_negative"
        ),

        db.CheckConstraint(
            "gross_amount >= 0",
            name="ck_payment_gross_non_negative"
        ),

        db.CheckConstraint(
            "final_amount >= 0",
            name="ck_payment_final_non_negative"
        ),

        db.CheckConstraint(
            "total_days >= 0",
            name="ck_payment_days_non_negative"
        ),

        db.CheckConstraint(
            "total_hours >= 0",
            name="ck_payment_hours_non_negative"
        ),
    )

    def __repr__(self):
        return (
            f"<Payment "
            f"{self.payment_code} "
            f"project={self.project_id} "
            f"trainer={self.trainer_id}>"
        )
        
class Document(db.Model):

    __tablename__ = "documents"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    document_code = db.Column(
        db.String(30),
        unique=True,
        nullable=False,
        index=True
    )

    original_name = db.Column(
        db.String(255),
        nullable=False
    )

    stored_name = db.Column(
        db.String(255),
        nullable=False
    )

    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    document_type = db.Column(
        db.String(50),
        nullable=False,
        default="GENERAL",
        index=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    mime_type = db.Column(
        db.String(100),
        nullable=True
    )

    file_size = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "projects.id",
            ondelete="CASCADE"
        ),
        nullable=True,
        index=True
    )

    requirement_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "requirements.id",
            ondelete="CASCADE"
        ),
        nullable=True,
        index=True
    )

    trainer_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "trainers.id",
            ondelete="CASCADE"
        ),
        nullable=True,
        index=True
    )

    application_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "applications.id",
            ondelete="CASCADE"
        ),
        nullable=True,
        index=True
    )

    payment_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "payments.id",
            ondelete="CASCADE"
        ),
        nullable=True,
        index=True
    )

    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        index=True
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    project = db.relationship(
        "Project",
        backref=db.backref(
            "documents",
            lazy=True
        )
    )

    requirement = db.relationship(
        "Requirement",
        backref=db.backref(
            "documents",
            lazy=True
        )
    )

    trainer = db.relationship(
        "Trainer",
        backref=db.backref(
            "documents",
            lazy=True
        )
    )

    application = db.relationship(
        "Application",
        backref=db.backref(
            "documents",
            lazy=True
        )
    )

    payment = db.relationship(
        "Payment",
        backref=db.backref(
            "documents",
            lazy=True
        )
    )

    uploader = db.relationship(
        "User",
        foreign_keys=[uploaded_by]
    )

# ============================================================
# COMMUNICATION MODEL
# ============================================================

class Communication(db.Model):

    __tablename__ = "communications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    communication_code = db.Column(
        db.String(30),
        unique=True,
        nullable=False,
        index=True
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=True,
        index=True
    )

    # --------------------------------------------------------
    # COMMUNICATION TYPE
    # --------------------------------------------------------

    # ANNOUNCEMENT / MESSAGE / BROADCAST

    communication_type = db.Column(
        db.String(30),
        nullable=False,
        default="MESSAGE",
        index=True
    )

    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    subject = db.Column(
        db.String(250),
        nullable=False,
        default="Chat Message"
    )

    message = db.Column(
        db.Text,
        nullable=False,
        default=""
    )

    # --------------------------------------------------------
    # PRIORITY
    # --------------------------------------------------------

    # NORMAL / IMPORTANT / URGENT

    priority = db.Column(
        db.String(20),
        nullable=False,
        default="NORMAL"
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    # SENT / DRAFT / ARCHIVED

    status = db.Column(
        db.String(20),
        nullable=False,
        default="SENT",
        index=True
    )

    # --------------------------------------------------------
    # READ STATUS
    # --------------------------------------------------------

    is_read = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True
    )

    # --------------------------------------------------------
    # ATTACHMENT
    # --------------------------------------------------------

    attachment_name = db.Column(
        db.String(255),
        nullable=True
    )

    attachment_path = db.Column(
        db.String(500),
        nullable=True
    )

    attachment_type = db.Column(
        db.String(100),
        nullable=True
    )

    attachment_size = db.Column(
        db.Integer,
        nullable=True
    )

    # --------------------------------------------------------
    # TIMESTAMPS
    # --------------------------------------------------------

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        index=True
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    sender = db.relationship(
        "User",
        foreign_keys=[sender_id],
        backref=db.backref(
            "sent_communications",
            lazy=True
        )
    )

    receiver = db.relationship(
        "User",
        foreign_keys=[receiver_id],
        backref=db.backref(
            "received_communications",
            lazy=True
        )
    )

    def __repr__(self):

        return (
            f"<Communication "
            f"{self.communication_code}>"
        )
        
class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)

    setting_key = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    setting_value = db.Column(
        db.Text,
        nullable=True
    )

    category = db.Column(
        db.String(50),
        nullable=False,
        default="GENERAL",
        index=True
    )

    description = db.Column(
        db.String(255),
        nullable=True
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    def __repr__(self):
        return f"<SystemSetting {self.setting_key}>"