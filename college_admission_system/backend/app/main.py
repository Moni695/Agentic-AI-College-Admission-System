from contextlib import asynccontextmanager
import json
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, inspect, text
from sqlalchemy.orm import Session, joinedload
from .database import Base, engine, get_db
from .models import Admission, AdmissionStatusHistory, ChatMessage, College, CollegeCourse, Course, Faculty, MeritList, MeritListEntry, Notification, Payment, Student, StudentDocument, User
from .schemas import AdmissionIn, ApprovalIn, ChatIn, CollegeIn, CourseIn, DocumentReviewIn, FacultyRegisterIn, LoginIn, MeritListReleaseIn, ProfileIn, RegisterIn, StatusIn, TokenOut
from .security import admin_user, approved_faculty, create_access_token, current_user, hash_password, verify_password
from .services import POSTGRADUATE_REQUIREMENT, canonical_course_key, college_recommendations, course_department_key, course_recommendations, eligibility, recommendation_message, seed_database
from .agent import run_admission_agent
from .config import get_settings
from .email_service import send_merit_selection_email


UPLOAD_ROOT = Path(__file__).resolve().parents[1] / "uploads"
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    # Keep existing installations compatible when new course-assignment fields
    # are added after the first database startup.  The columns are nullable so
    # older faculty and merit-list records continue to work.
    with engine.begin() as connection:
        inspector = inspect(connection)
        if inspector.has_table("faculty") and "course_id" not in {column["name"] for column in inspector.get_columns("faculty")}:
            connection.execute(text("ALTER TABLE faculty ADD COLUMN course_id INTEGER NULL"))
        if inspector.has_table("merit_lists") and "course_id" not in {column["name"] for column in inspector.get_columns("merit_lists")}:
            connection.execute(text("ALTER TABLE merit_lists ADD COLUMN course_id INTEGER NULL"))
    db = next(get_db())
    try:
        seed_database(db)
        sync_merit_admission_status(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Bangalore University Intelligent Admission System", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def notify(db: Session, user_id: int, title: str, message: str) -> None:
    db.add(Notification(user_id=user_id, title=title, message=message))


def sync_merit_admission_status(db: Session) -> None:
    """Keep already released merit selections consistent with admission status."""
    entries = db.query(MeritListEntry).options(joinedload(MeritListEntry.merit_list)).all()
    changed = False
    for entry in entries:
        admission = db.get(Admission, entry.admission_id)
        if admission and admission.status != "APPROVED":
            admission.status = "APPROVED"
            db.add(AdmissionStatusHistory(admission_id=admission.id, status="APPROVED", note="Admission approved after merit-list selection.", changed_by=None))
            changed = True
    if changed:
        db.commit()


def notification_data(record: Notification) -> dict:
    return {"id": record.id, "title": record.title, "message": record.message, "is_read": record.is_read, "created_at": record.created_at}


def document_data(record: StudentDocument) -> dict:
    return {"id": record.id, "document_type": record.document_type, "original_filename": record.original_filename,
            "verification_status": record.verification_status, "verification_note": record.verification_note,
            "uploaded_at": record.uploaded_at, "verified_at": record.verified_at}


def status_history_data(record: AdmissionStatusHistory) -> dict:
    return {"status": record.status, "note": record.note, "changed_at": record.changed_at}


def user_data(user: User) -> dict:
    profile = user.student
    faculty = user.faculty
    return {"id": user.id, "name": user.name, "email": user.email, "phone": user.phone, "role": user.role,
            "profile": {"qualification": profile.qualification, "percentage": profile.percentage, "interests": profile.interests, "budget": profile.budget, "preferred_location": profile.preferred_location} if profile else None,
            "faculty": {"id": faculty.id, "college_id": faculty.college_id, "college_name": faculty.college.college_name,
                        "course_id": faculty.course_id, "course_name": faculty.course.course_name if faculty.course else None,
                        "designation": faculty.designation, "approval_status": faculty.approval_status} if faculty else None}


def course_data(course: Course) -> dict:
    return {"id": course.id, "course_name": course.course_name, "duration": course.duration, "minimum_qualification": course.minimum_qualification, "minimum_percentage": course.minimum_percentage, "fees": course.fees, "description": course.description}


def college_data(college: College, include_offerings: bool = True) -> dict:
    data = {"id": college.id, "college_name": college.college_name, "location": college.location, "description": college.description}
    if include_offerings:
        seen_course_keys = set()
        data["offerings"] = []
        for link in sorted(college.college_courses, key=lambda item: (canonical_course_key(item.course.course_name), item.course.course_name, item.course_id)):
            if link.course.minimum_qualification != POSTGRADUATE_REQUIREMENT:
                continue
            course_key = canonical_course_key(link.course.course_name)
            if course_key in seen_course_keys:
                continue
            seen_course_keys.add(course_key)
            data["offerings"].append({"course_id": link.course_id, "course_name": link.course.course_name, "fees": link.fees})
    return data


def admission_data(admission: Admission) -> dict:
    return {"id": admission.id, "application_number": admission.application_number, "application_date": admission.application_date,
            "status": admission.status, "student_name": admission.student.user.name, "student_email": admission.student.user.email, "student_phone": admission.student.user.phone,
            "student_degree": admission.student.qualification, "student_percentage": admission.student.percentage,
            "college_id": admission.college_id, "college_name": admission.college.college_name, "course_id": admission.course_id,
            "course_name": admission.course.course_name, "address": admission.address, "previous_institution": admission.previous_institution,
            "payment": {"amount": admission.payment.amount, "payment_status": admission.payment.payment_status, "transaction_id": admission.payment.transaction_id, "payment_date": admission.payment.payment_date} if admission.payment else None}


@app.get("/api/health")
def health():
    return {"status": "ok", "message": "BCU admission API is running"}


@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(func.lower(User.email) == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(name=payload.name, email=payload.email.lower(), phone=payload.phone, password_hash=hash_password(payload.password), role="student")
    db.add(user)
    db.flush()
    db.add(Student(user_id=user.id, qualification=payload.degree))
    notify(db, user.id, "Welcome to Bangalore University Admissions", "Your student account was created successfully. Complete your profile to receive course recommendations.")
    db.commit()
    return {"message": "Registration successful. Please log in with your email and password."}


@app.post("/api/auth/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if user.role == "faculty" and (not user.faculty or user.faculty.college.college_name != "Bangalore University" or user.faculty.approval_status != "APPROVED"):
        raise HTTPException(status_code=403, detail="Your Bangalore University faculty registration is awaiting administrator approval")
    return TokenOut(access_token=create_access_token(user), role=user.role, name=user.name)


@app.post("/api/faculty/register", status_code=status.HTTP_201_CREATED)
def register_faculty(payload: FacultyRegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(func.lower(User.email) == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    college = db.get(College, payload.college_id)
    if not college or college.college_name != "Bangalore University":
        raise HTTPException(status_code=422, detail="Please select Bangalore University")
    course = db.get(Course, payload.course_id)
    if not course or course.minimum_qualification != POSTGRADUATE_REQUIREMENT:
        raise HTTPException(status_code=404, detail="Postgraduate course not found")
    offering = db.query(CollegeCourse).filter_by(college_id=college.id, course_id=course.id).first()
    if not offering:
        raise HTTPException(status_code=422, detail="Please select a course offered by Bangalore University")
    user = User(name=payload.name, email=payload.email.lower(), phone=payload.phone, password_hash=hash_password(payload.password), role="faculty")
    db.add(user)
    db.flush()
    faculty = Faculty(user_id=user.id, college_id=payload.college_id, course_id=course.id, designation=payload.designation, approval_status="PENDING")
    db.add(faculty)
    for admin in db.query(User).filter(User.role == "admin").all():
        notify(db, admin.id, "Faculty approval required", f"{payload.name} submitted a faculty registration for Bangalore University.")
    db.commit()
    return {"message": "Faculty registration submitted. You can log in after an administrator approves your account."}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return user_data(user)


@app.put("/api/student/profile")
def update_profile(payload: ProfileIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only student accounts have an admission profile")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user.student, field, value)
    db.commit()
    db.refresh(user)
    return user_data(user)["profile"]


@app.get("/api/notifications")
def list_notifications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    records = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(50).all()
    return [notification_data(record) for record in records]


@app.patch("/api/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    record = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Notification not found")
    record.is_read = True
    db.commit()
    return notification_data(record)


@app.post("/api/student/documents", status_code=status.HTTP_201_CREATED)
async def upload_student_document(document_type: str = Form(...), file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "student" or not user.student:
        raise HTTPException(status_code=403, detail="Student access required")
    original_filename = Path(file.filename or "").name
    extension = Path(original_filename).suffix.lower()
    if not original_filename or extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Upload a PDF, PNG, JPG, JPEG, or WEBP document")
    data = await file.read(MAX_DOCUMENT_BYTES + 1)
    if len(data) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="Each document must be 10 MB or smaller")
    student_folder = UPLOAD_ROOT / str(user.student.id)
    student_folder.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid4().hex}{extension}"
    destination = student_folder / stored_filename
    destination.write_bytes(data)
    record = StudentDocument(student_id=user.student.id, document_type=document_type.strip()[:80], original_filename=original_filename,
                             stored_filename=stored_filename, file_path=str(destination.relative_to(UPLOAD_ROOT)), file_data=data, verification_status="PENDING")
    db.add(record)
    db.commit()
    db.refresh(record)
    notify(db, user.id, "Document uploaded", f"Your {record.document_type} is awaiting administrator verification.")
    db.commit()
    return document_data(record)


@app.get("/api/student/documents")
def list_student_documents(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "student" or not user.student:
        raise HTTPException(status_code=403, detail="Student access required")
    records = db.query(StudentDocument).filter(StudentDocument.student_id == user.student.id).order_by(StudentDocument.uploaded_at.desc()).all()
    return [document_data(record) for record in records]


@app.get("/api/courses")
def list_courses(db: Session = Depends(get_db)):
    result = []
    seen_course_keys = set()
    for course in db.query(Course).filter(Course.minimum_qualification == POSTGRADUATE_REQUIREMENT).order_by(Course.course_name).all():
        course_key = canonical_course_key(course.course_name)
        if course_key in seen_course_keys:
            continue
        seen_course_keys.add(course_key)
        result.append(course_data(course))
    return result


@app.get("/api/courses/{course_id}/eligibility")
def check_course_eligibility(course_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course or course.minimum_qualification != POSTGRADUATE_REQUIREMENT: raise HTTPException(status_code=404, detail="Postgraduate course not found")
    return eligibility(course, user.student.qualification, user.student.percentage)


@app.get("/api/colleges")
def list_colleges(db: Session = Depends(get_db)):
    colleges = db.query(College).options(joinedload(College.college_courses).joinedload(CollegeCourse.course)).filter(College.college_name == "Bangalore University").order_by(College.college_name).all()
    return [college_data(college) for college in colleges]


@app.get("/api/recommendations")
def recommendations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    courses = course_recommendations(db, user.student)
    college_course_id = courses[0]["course_id"] if courses else None
    colleges = college_recommendations(db, user.student, college_course_id) if courses else []
    return {"courses": courses, "colleges": colleges, "message": recommendation_message(db, user.student, courses)}


@app.post("/api/ai/chat")
def ai_chat(payload: ChatIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "student": raise HTTPException(status_code=403, detail="Sign in with a student account to use the admission assistant")
    result = run_admission_agent(db, user.student, payload.message)
    db.add(ChatMessage(student_id=user.student.id, message=payload.message, response=result["reply"], extracted_data=json.dumps(result.get("extracted", {}))))
    db.commit()
    return result


@app.get("/api/student/chat-history")
def student_chat_history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    records = db.query(ChatMessage).filter(ChatMessage.student_id == user.student.id).order_by(ChatMessage.created_at.asc()).all()
    return [{"id": record.id, "message": record.message, "response": record.response, "created_at": record.created_at} for record in records]


@app.post("/api/admissions", status_code=status.HTTP_201_CREATED)
def create_admission(payload: AdmissionIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "student": raise HTTPException(status_code=403, detail="Only students can submit applications")
    course, college = db.get(Course, payload.course_id), db.get(College, payload.college_id)
    if not course or course.minimum_qualification != POSTGRADUATE_REQUIREMENT or not college or college.college_name != "Bangalore University": raise HTTPException(status_code=404, detail="Only Bangalore University postgraduate applications are available")
    offering = db.query(CollegeCourse).filter_by(course_id=course.id, college_id=college.id).first()
    if not offering: raise HTTPException(status_code=422, detail="This college does not offer the selected course")
    check = eligibility(course, user.student.qualification, user.student.percentage)
    if not check["eligible"]: raise HTTPException(status_code=422, detail=check["reason"])
    application_number = f"BCU-{datetime.now():%Y%m%d}-{uuid4().hex[:6].upper()}"
    admission = Admission(application_number=application_number, student_id=user.student.id, college_id=college.id, course_id=course.id, address=payload.address, previous_institution=payload.previous_institution, status="PENDING")
    db.add(admission)
    db.flush()
    db.add(Payment(admission_id=admission.id, amount=get_settings().application_fee, payment_status="PENDING"))
    db.add(AdmissionStatusHistory(admission_id=admission.id, status="SUBMITTED", note="Application submitted by the student.", changed_by=user.id))
    notify(db, user.id, "Application submitted", f"Your application {application_number} was submitted and is awaiting review.")
    db.commit()
    admission = db.query(Admission).options(joinedload(Admission.student).joinedload(Student.user), joinedload(Admission.course), joinedload(Admission.college), joinedload(Admission.payment)).get(admission.id)
    return admission_data(admission)


@app.get("/api/admissions/my")
def my_admissions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    records = db.query(Admission).join(College).options(joinedload(Admission.student).joinedload(Student.user), joinedload(Admission.course), joinedload(Admission.college), joinedload(Admission.payment)).filter(Admission.student_id == user.student.id, College.college_name == "Bangalore University").order_by(Admission.application_date.desc()).all()
    return [admission_data(record) for record in records]


@app.post("/api/payments/{admission_id}/simulate")
def simulate_payment(admission_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    admission = db.query(Admission).options(joinedload(Admission.payment), joinedload(Admission.student)).get(admission_id)
    if not admission: raise HTTPException(status_code=404, detail="Application not found")
    if user.role != "admin" and admission.student_id != user.student.id: raise HTTPException(status_code=403, detail="This is not your application")
    if admission.payment.payment_status == "SUCCESS": return {"message": "Demo payment was already successful", "payment_status": "SUCCESS", "transaction_id": admission.payment.transaction_id}
    admission.payment.payment_status = "SUCCESS"
    admission.payment.transaction_id = f"DEMO-{uuid4().hex[:10].upper()}"
    admission.payment.payment_date = datetime.utcnow()
    notify(db, admission.student.user_id, "Payment confirmed", f"Your demo application payment for {admission.application_number} was recorded successfully.")
    db.commit()
    return {"message": "Demo payment successful. No real money was charged.", "payment_status": "SUCCESS", "transaction_id": admission.payment.transaction_id}


@app.get("/api/confirmation/{admission_id}")
def confirmation(admission_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    admission = db.query(Admission).options(joinedload(Admission.student).joinedload(Student.user), joinedload(Admission.course), joinedload(Admission.college), joinedload(Admission.payment)).get(admission_id)
    if not admission: raise HTTPException(status_code=404, detail="Application not found")
    if user.role != "admin" and admission.student_id != user.student.id: raise HTTPException(status_code=403, detail="This is not your application")
    return {"message": "Your admission application has been successfully submitted." if admission.payment.payment_status == "SUCCESS" else "Please complete the demo payment to finish your application.", "admission": admission_data(admission)}


@app.get("/api/admin/dashboard")
def admin_dashboard(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    return {"total_students": db.query(Student).count(), "total_courses": db.query(Course).filter(Course.minimum_qualification == POSTGRADUATE_REQUIREMENT).count(), "total_colleges": db.query(College).count(), "total_applications": db.query(Admission).count(), "pending_faculty": db.query(Faculty).filter(Faculty.approval_status == "PENDING").count()}


def faculty_data(faculty: Faculty) -> dict:
    return {"id": faculty.id, "name": faculty.user.name, "email": faculty.user.email, "phone": faculty.user.phone,
            "college_id": faculty.college_id, "college_name": faculty.college.college_name, "designation": faculty.designation,
            "course_id": faculty.course_id, "course_name": faculty.course.course_name if faculty.course else None,
            "approval_status": faculty.approval_status, "created_at": faculty.created_at}


@app.get("/api/admin/faculty")
def admin_faculty(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    records = db.query(Faculty).join(College).options(joinedload(Faculty.user), joinedload(Faculty.college), joinedload(Faculty.course)).filter(College.college_name == "Bangalore University").order_by(Faculty.created_at.desc()).all()
    return [faculty_data(record) for record in records]


@app.get("/api/admin/documents")
def admin_documents(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    records = db.query(StudentDocument).join(Student).join(User).order_by(StudentDocument.uploaded_at.desc()).all()
    return [{**document_data(record), "student_id": record.student_id, "student_name": record.student.user.name, "student_email": record.student.user.email} for record in records]


@app.patch("/api/admin/documents/{document_id}")
def review_document(document_id: int, payload: DocumentReviewIn, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    if payload.verification_status not in {"PENDING", "VERIFIED", "REJECTED"}:
        raise HTTPException(status_code=422, detail="Verification status must be PENDING, VERIFIED, or REJECTED")
    record = db.get(StudentDocument, document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    record.verification_status = payload.verification_status
    record.verification_note = payload.verification_note
    record.verified_at = datetime.utcnow() if payload.verification_status != "PENDING" else None
    notify(db, record.student.user_id, "Document review updated", f"Your {record.document_type} was marked {record.verification_status.lower()} by the administrator.")
    db.commit()
    return document_data(record)


@app.patch("/api/admin/faculty/{faculty_id}/approval")
def update_faculty_approval(faculty_id: int, payload: ApprovalIn, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    if payload.approval_status not in {"APPROVED", "REJECTED"}:
        raise HTTPException(status_code=422, detail="Approval status must be APPROVED or REJECTED")
    faculty = db.get(Faculty, faculty_id)
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty registration not found")
    faculty.approval_status = payload.approval_status
    notify(db, faculty.user_id, "Faculty registration updated", f"Your Bangalore University faculty registration was {payload.approval_status.lower()}.")
    db.commit()
    return {"id": faculty.id, "approval_status": faculty.approval_status}


@app.get("/api/admin/admissions")
def admin_admissions(completed_only: bool = False, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    records = db.query(Admission).join(College).options(joinedload(Admission.student).joinedload(Student.user), joinedload(Admission.course), joinedload(Admission.college), joinedload(Admission.payment)).filter(College.college_name == "Bangalore University").order_by(Admission.application_date.desc()).all()
    if completed_only:
        records = [record for record in records if record.payment and record.payment.payment_status == "SUCCESS" and record.status == "APPROVED"]
    return [admission_data(record) for record in records]


@app.get("/api/faculty/applications")
def faculty_applications(user: User = Depends(approved_faculty), db: Session = Depends(get_db)):
    admission_filters = [Admission.college_id == user.faculty.college_id]
    records = db.query(Admission).options(joinedload(Admission.student).joinedload(Student.user), joinedload(Admission.course), joinedload(Admission.college), joinedload(Admission.payment)).filter(*admission_filters).order_by(Admission.application_date.desc()).all()
    department = course_department_key(user.faculty.course.course_name) if user.faculty.course else None
    if department:
        records = [record for record in records if course_department_key(record.course.course_name) == department]
    merit_records = db.query(MeritListEntry).join(MeritList).options(joinedload(MeritListEntry.merit_list).joinedload(MeritList.course)).filter(MeritList.college_id == user.faculty.college_id).all()
    merit_ids = {entry.admission_id for entry in merit_records if not department or (entry.merit_list.course and course_department_key(entry.merit_list.course.course_name) == department)}
    result = []
    for record in records:
        item = admission_data(record)
        item["merit_listed"] = record.id in merit_ids
        item["admission_pending"] = record.id in merit_ids
        result.append(item)
    return result


def merit_list_data(record: MeritList) -> dict:
    entries = sorted(record.entries, key=lambda entry: entry.merit_rank)
    return {"id": record.id, "college_id": record.college_id, "college_name": record.college.college_name,
            "course_id": record.course_id, "course_name": record.course.course_name if record.course else None, "published_at": record.published_at,
            "released_by": record.faculty.user.name, "entries": [{"rank": entry.merit_rank, **admission_data(entry.admission)} for entry in entries]}


@app.get("/api/faculty/courses")
def faculty_courses(user: User = Depends(approved_faculty), db: Session = Depends(get_db)):
    course_filters = [CollegeCourse.college_id == user.faculty.college_id]
    links = db.query(CollegeCourse).options(joinedload(CollegeCourse.course)).filter(*course_filters).all()
    department = course_department_key(user.faculty.course.course_name) if user.faculty.course else None
    if department:
        links = [link for link in links if course_department_key(link.course.course_name) == department]
    result = []
    seen_course_keys = set()
    for link in sorted(links, key=lambda item: (canonical_course_key(item.course.course_name), item.course.course_name, item.course_id)):
        if link.course.minimum_qualification != POSTGRADUATE_REQUIREMENT:
            continue
        course_key = canonical_course_key(link.course.course_name)
        if course_key in seen_course_keys:
            continue
        seen_course_keys.add(course_key)
        result.append({"course_id": link.course_id, "course_name": link.course.course_name, "fees": link.fees})
    return result


@app.post("/api/faculty/merit-list/release", status_code=201)
def release_merit_list(payload: MeritListReleaseIn, user: User = Depends(approved_faculty), db: Session = Depends(get_db)):
    selected_course = db.get(Course, payload.course_id)
    if not selected_course or selected_course.minimum_qualification != POSTGRADUATE_REQUIREMENT:
        raise HTTPException(status_code=422, detail="Only postgraduate courses can have a merit list")
    department = course_department_key(user.faculty.course.course_name) if user.faculty.course else None
    if department and course_department_key(selected_course.course_name) != department:
        raise HTTPException(status_code=403, detail="You can release a merit list only for your assigned department")
    offering = db.query(CollegeCourse).filter_by(college_id=user.faculty.college_id, course_id=payload.course_id).first()
    if not offering:
        raise HTTPException(status_code=422, detail="This course is not offered by your college")
    admissions = db.query(Admission).join(Student).join(Payment).options(joinedload(Admission.student).joinedload(Student.user), joinedload(Admission.course), joinedload(Admission.college), joinedload(Admission.payment)).filter(Admission.college_id == user.faculty.college_id, Admission.course_id == payload.course_id, Payment.payment_status == "SUCCESS", Admission.status != "REJECTED").order_by(Student.percentage.desc(), Admission.application_date.asc()).limit(payload.limit).all()
    if not admissions:
        raise HTTPException(status_code=422, detail="No paid applications are available for this course's merit list")
    merit_list = MeritList(college_id=user.faculty.college_id, faculty_id=user.faculty.id, course_id=payload.course_id)
    db.add(merit_list)
    db.flush()
    for rank, admission in enumerate(admissions, start=1):
        if admission.status != "APPROVED":
            admission.status = "APPROVED"
            db.add(AdmissionStatusHistory(admission_id=admission.id, status="APPROVED", note="Admission approved after the student was selected in the department merit list.", changed_by=user.id))
        db.add(MeritListEntry(merit_list_id=merit_list.id, admission_id=admission.id, merit_rank=rank))
        notify(db, admission.student.user_id, "Merit list released", f"Your application {admission.application_number} was included in the Bangalore University merit list at rank #{rank}.")
    db.commit()

    email_results = []
    for rank, admission in enumerate(admissions, start=1):
        try:
            send_merit_selection_email(
                student_name=admission.student.user.name,
                student_email=admission.student.user.email,
                course_name=admission.course.course_name,
                college_name=admission.college.college_name,
                application_number=admission.application_number,
                merit_rank=rank,
            )
            email_results.append({"email": admission.student.user.email, "sent": True})
        except Exception as exc:
            # The merit list is already published; expose delivery problems to faculty
            # without hiding the selection result from the student portal.
            email_results.append({"email": admission.student.user.email, "sent": False, "error": str(exc)})
    saved = db.query(MeritList).options(joinedload(MeritList.college), joinedload(MeritList.course), joinedload(MeritList.faculty).joinedload(Faculty.user), joinedload(MeritList.entries).joinedload(MeritListEntry.admission).joinedload(Admission.student).joinedload(Student.user), joinedload(MeritList.entries).joinedload(MeritListEntry.admission).joinedload(Admission.course), joinedload(MeritList.entries).joinedload(MeritListEntry.admission).joinedload(Admission.college), joinedload(MeritList.entries).joinedload(MeritListEntry.admission).joinedload(Admission.payment)).get(merit_list.id)
    return {**merit_list_data(saved), "email_delivery": email_results}


@app.get("/api/faculty/merit-list")
def latest_merit_list(user: User = Depends(approved_faculty), db: Session = Depends(get_db)):
    records = db.query(MeritList).options(joinedload(MeritList.college), joinedload(MeritList.course), joinedload(MeritList.faculty).joinedload(Faculty.user), joinedload(MeritList.entries).joinedload(MeritListEntry.admission).joinedload(Admission.student).joinedload(Student.user), joinedload(MeritList.entries).joinedload(MeritListEntry.admission).joinedload(Admission.course), joinedload(MeritList.entries).joinedload(MeritListEntry.admission).joinedload(Admission.college), joinedload(MeritList.entries).joinedload(MeritListEntry.admission).joinedload(Admission.payment)).filter(MeritList.college_id == user.faculty.college_id).order_by(MeritList.published_at.desc()).all()
    department = course_department_key(user.faculty.course.course_name) if user.faculty.course else None
    record = next((item for item in records if not department or (item.course and course_department_key(item.course.course_name) == department)), None)
    return merit_list_data(record) if record else None


@app.get("/api/student/selection-status")
def student_selection_status(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    records = db.query(Admission).join(College).options(joinedload(Admission.student).joinedload(Student.user), joinedload(Admission.course), joinedload(Admission.college), joinedload(Admission.payment)).filter(Admission.student_id == user.student.id, College.college_name == "Bangalore University").order_by(Admission.application_date.desc()).all()
    response = []
    for admission in records:
        entry = db.query(MeritListEntry).join(MeritList).filter(MeritListEntry.admission_id == admission.id).order_by(MeritList.published_at.desc()).first()
        item = admission_data(admission)
        item["selection_status"] = "SELECTED / MERIT LISTED" if entry else (admission.status if admission.status != "PENDING" else "UNDER REVIEW")
        item["merit_rank"] = entry.merit_rank if entry else None
        item["admission_pending"] = bool(entry)
        item["selection_message"] = f"You are merit rank #{entry.merit_rank} for this course." if entry else "The college has not released your selection result yet."
        timeline = db.query(AdmissionStatusHistory).filter(AdmissionStatusHistory.admission_id == admission.id).order_by(AdmissionStatusHistory.changed_at.asc()).all()
        item["timeline"] = [status_history_data(record) for record in timeline] or [{"status": admission.status, "note": "Current application status.", "changed_at": admission.application_date}]
        response.append(item)
    return response


@app.patch("/api/admin/admissions/{admission_id}")
def update_admission_status(admission_id: int, payload: StatusIn, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    if payload.status not in {"PENDING", "APPROVED", "REJECTED"}: raise HTTPException(status_code=422, detail="Status must be PENDING, APPROVED, or REJECTED")
    record = db.get(Admission, admission_id)
    if not record: raise HTTPException(status_code=404, detail="Application not found")
    record.status = payload.status
    db.add(AdmissionStatusHistory(admission_id=record.id, status=payload.status, note=f"Application status updated to {payload.status.lower()} by the administrator.", changed_by=_.id))
    notify(db, record.student.user_id, "Application status updated", f"Your application {record.application_number} is now {payload.status.lower()}.")
    db.commit()
    return {"id": record.id, "status": record.status}


@app.post("/api/admin/courses", status_code=201)
def add_course(payload: CourseIn, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    course = Course(**payload.model_dump())
    db.add(course); db.commit(); db.refresh(course)
    return course_data(course)


@app.put("/api/admin/courses/{course_id}")
def edit_course(course_id: int, payload: CourseIn, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course: raise HTTPException(status_code=404, detail="Course not found")
    for field, value in payload.model_dump().items(): setattr(course, field, value)
    db.commit(); return course_data(course)


@app.delete("/api/admin/courses/{course_id}", status_code=204)
def delete_course(course_id: int, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course: raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course); db.commit()


@app.post("/api/admin/colleges", status_code=201)
def add_college(payload: CollegeIn, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    college = College(college_name=payload.college_name, location=payload.location, description=payload.description)
    db.add(college); db.flush()
    for offering in payload.offerings:
        if not db.get(Course, offering.get("course_id")): raise HTTPException(status_code=422, detail="Offering includes an unknown course")
        db.add(CollegeCourse(college_id=college.id, course_id=offering["course_id"], fees=offering["fees"]))
    db.commit(); db.refresh(college)
    return college_data(college)


@app.put("/api/admin/colleges/{college_id}")
def edit_college(college_id: int, payload: CollegeIn, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    college = db.get(College, college_id)
    if not college: raise HTTPException(status_code=404, detail="College not found")
    college.college_name, college.location, college.description = payload.college_name, payload.location, payload.description
    db.query(CollegeCourse).filter_by(college_id=college.id).delete()
    for offering in payload.offerings: db.add(CollegeCourse(college_id=college.id, course_id=offering["course_id"], fees=offering["fees"]))
    db.commit(); db.refresh(college)
    return college_data(college)


@app.delete("/api/admin/colleges/{college_id}", status_code=204)
def delete_college(college_id: int, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    college = db.get(College, college_id)
    if not college: raise HTTPException(status_code=404, detail="College not found")
    db.delete(college); db.commit()


FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
if not FRONTEND.exists():
    candidate = Path(__file__).resolve().parents[1] / "frontend"
    if candidate.exists():
        FRONTEND = candidate
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
