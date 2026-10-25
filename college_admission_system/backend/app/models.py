from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column("user_id", Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column("password", String(255))
    role: Mapped[str] = mapped_column(String(20), default="student")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    student: Mapped["Student | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    faculty: Mapped["Faculty | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column("notification_id", Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    title: Mapped[str] = mapped_column(String(160))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[User] = relationship(back_populates="notifications")


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column("student_id", Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), unique=True)
    qualification: Mapped[str | None] = mapped_column(String(120), nullable=True)
    percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    interests: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    preferred_location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    user: Mapped[User] = relationship(back_populates="student")
    admissions: Mapped[list["Admission"]] = relationship(back_populates="student")
    chat_messages: Mapped[list["ChatMessage"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    documents: Mapped[list["StudentDocument"]] = relationship(back_populates="student", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column("chat_message_id", Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.student_id"))
    message: Mapped[str] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
    extracted_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    student: Mapped[Student] = relationship(back_populates="chat_messages")


class StudentDocument(Base):
    __tablename__ = "student_documents"
    id: Mapped[int] = mapped_column("document_id", Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.student_id"))
    document_type: Mapped[str] = mapped_column(String(80))
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True)
    file_path: Mapped[str] = mapped_column(String(500))
    file_data: Mapped[bytes] = mapped_column(LargeBinary(16 * 1024 * 1024), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(20), default="PENDING")
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    student: Mapped[Student] = relationship(back_populates="documents")


class Faculty(Base):
    __tablename__ = "faculty"
    id: Mapped[int] = mapped_column("faculty_id", Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), unique=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.college_id"))
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.course_id"), nullable=True)
    designation: Mapped[str] = mapped_column(String(120))
    approval_status: Mapped[str] = mapped_column(String(20), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[User] = relationship(back_populates="faculty")
    college: Mapped["College"] = relationship()
    course: Mapped["Course | None"] = relationship()
    merit_lists: Mapped[list["MeritList"]] = relationship(back_populates="faculty")


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column("course_id", Integer, primary_key=True)
    course_name: Mapped[str] = mapped_column(String(160), unique=True)
    duration: Mapped[str] = mapped_column(String(60))
    minimum_qualification: Mapped[str] = mapped_column(String(160))
    minimum_percentage: Mapped[float] = mapped_column(Float)
    fees: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(Text)
    college_courses: Mapped[list["CollegeCourse"]] = relationship(back_populates="course", cascade="all, delete-orphan")


class College(Base):
    __tablename__ = "colleges"
    id: Mapped[int] = mapped_column("college_id", Integer, primary_key=True)
    college_name: Mapped[str] = mapped_column(String(180), unique=True)
    location: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    college_courses: Mapped[list["CollegeCourse"]] = relationship(back_populates="college", cascade="all, delete-orphan")


class CollegeCourse(Base):
    __tablename__ = "college_courses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.college_id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.course_id"))
    fees: Mapped[float] = mapped_column(Float)
    college: Mapped[College] = relationship(back_populates="college_courses")
    course: Mapped[Course] = relationship(back_populates="college_courses")


class Admission(Base):
    __tablename__ = "admissions"
    id: Mapped[int] = mapped_column("admission_id", Integer, primary_key=True)
    application_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.student_id"))
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.college_id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.course_id"))
    address: Mapped[str] = mapped_column(Text)
    previous_institution: Mapped[str] = mapped_column(String(180))
    application_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    student: Mapped[Student] = relationship(back_populates="admissions")
    college: Mapped[College] = relationship()
    course: Mapped[Course] = relationship()
    payment: Mapped["Payment | None"] = relationship(back_populates="admission", uselist=False, cascade="all, delete-orphan")
    status_history: Mapped[list["AdmissionStatusHistory"]] = relationship(back_populates="admission", cascade="all, delete-orphan", order_by="AdmissionStatusHistory.changed_at")


class AdmissionStatusHistory(Base):
    __tablename__ = "admission_status_history"
    id: Mapped[int] = mapped_column("history_id", Integer, primary_key=True)
    admission_id: Mapped[int] = mapped_column(ForeignKey("admissions.admission_id"))
    status: Mapped[str] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(Text)
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    admission: Mapped[Admission] = relationship(back_populates="status_history")


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column("payment_id", Integer, primary_key=True)
    admission_id: Mapped[int] = mapped_column(ForeignKey("admissions.admission_id"), unique=True)
    amount: Mapped[float] = mapped_column(Float)
    transaction_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(20), default="PENDING")
    payment_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    admission: Mapped[Admission] = relationship(back_populates="payment")


class MeritList(Base):
    __tablename__ = "merit_lists"
    id: Mapped[int] = mapped_column("merit_list_id", Integer, primary_key=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.college_id"))
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.faculty_id"))
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.course_id"), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    college: Mapped[College] = relationship()
    faculty: Mapped[Faculty] = relationship(back_populates="merit_lists")
    course: Mapped["Course | None"] = relationship()
    entries: Mapped[list["MeritListEntry"]] = relationship(back_populates="merit_list", cascade="all, delete-orphan")


class MeritListEntry(Base):
    __tablename__ = "merit_list_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merit_list_id: Mapped[int] = mapped_column(ForeignKey("merit_lists.merit_list_id"))
    admission_id: Mapped[int] = mapped_column(ForeignKey("admissions.admission_id"))
    merit_rank: Mapped[int] = mapped_column(Integer)
    merit_list: Mapped[MeritList] = relationship(back_populates="entries")
    admission: Mapped[Admission] = relationship()
