import re
from sqlalchemy.orm import Session
from .models import Admission, College, CollegeCourse, Course, Faculty, MeritList, Student, User

UNDERGRADUATE_KEYWORDS = ("bca", "bsc", "bcom", "bba", "ba", "be", "btech", "b.e", "b.tech", "bachelor")
POSTGRADUATE_REQUIREMENT = "Bachelor's Degree"
REMOVED_UNDERGRADUATE_COURSES = (
    "BCA - Computer Applications", "BBA - Business Administration", "BSc - Computer Science",
    "BCom - Commerce", "BA - Economics",
)


def is_bachelors(qualification: str | None) -> bool:
    return bool(qualification and any(term in qualification.lower() for term in UNDERGRADUATE_KEYWORDS))


def canonical_course_key(name: str | None) -> str:
    """Return a stable key so legacy hyphen/dash variants count as one course."""
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def course_department_key(name: str | None) -> str:
    """Treat MCA/MBA/etc. specialisations as one teaching department."""
    return re.split(r"\s*[-–—]\s*", (name or ""), maxsplit=1)[0].strip().lower()


def qualification_matches(course: Course, qualification: str | None) -> bool:
    value = (qualification or "").lower()
    if not is_bachelors(value):
        return False
    # A generic "Bachelor's Degree" is accepted when the student has not
    # supplied a stream, but named courses require a related previous degree.
    if "bachelor" in value and len(value.split()) <= 2:
        return True
    name = course.course_name.lower()
    computer_terms = ("computer", "bca", "bsc", "be", "btech", "information technology", "it")
    business_terms = ("business", "commerce", "bcom", "bba", "bbm", "management", "economics", "finance", "accounting")
    economics_terms = ("economics", "commerce", "bcom", "business", "management", "finance", "arts", "ba")
    def has_term(terms: tuple[str, ...]) -> bool:
        return any(re.search(rf"\b{re.escape(term)}\b", value) for term in terms)
    if name.startswith("mca") or "computer science" in name:
        return has_term(computer_terms)
    if name.startswith("mba") or "business analytics" in name:
        return has_term(business_terms)
    if name.startswith("mcom"):
        return has_term(business_terms)
    if "economics" in name:
        return has_term(economics_terms)
    return True


def eligibility(course: Course, qualification: str | None, percentage: float | None) -> dict:
    qualification_ok = qualification_matches(course, qualification)
    percentage_ok = percentage is not None and percentage >= course.minimum_percentage
    reasons = []
    if not qualification_ok:
        reasons.append(f"{course.course_name} requires {course.minimum_qualification}; please provide a matching qualification.")
    if not percentage_ok:
        shown = "not provided" if percentage is None else f"{percentage:.1f}%"
        reasons.append(f"Minimum required percentage is {course.minimum_percentage:.0f}%; your percentage is {shown}.")
    return {"course_id": course.id, "course_name": course.course_name, "eligible": qualification_ok and percentage_ok,
            "minimum_qualification": course.minimum_qualification, "minimum_percentage": course.minimum_percentage,
            "reason": "You meet the published demo eligibility requirements." if qualification_ok and percentage_ok else " ".join(reasons)}


def _terms(value: str | None) -> set[str]:
    ignored = {"a", "an", "and", "at", "for", "in", "interested", "interest", "my", "of", "or", "the", "to", "with"}
    terms = {term for term in re.findall(r"[a-zA-Z]+", (value or "").lower()) if term not in ignored and len(term) > 2}
    value_lower = (value or "").lower()
    if re.search(r"\bai\b", value_lower): terms.update({"artificial", "intelligence"})
    if re.search(r"\bml\b", value_lower): terms.update({"machine", "learning"})
    if "cybersecurity" in terms: terms.update({"cyber", "security"})
    return terms


def course_recommendations(db: Session, profile: Student) -> list[dict]:
    answers = []
    seen_course_keys = set()
    interest_terms = _terms(profile.interests)
    for course in db.query(Course).filter(Course.minimum_qualification == POSTGRADUATE_REQUIREMENT).order_by(Course.course_name, Course.id).all():
        course_key = canonical_course_key(course.course_name)
        if course_key in seen_course_keys:
            continue
        check = eligibility(course, profile.qualification, profile.percentage)
        if not check["eligible"]:
            continue
        overlap = interest_terms & _terms(f"{course.course_name} {course.description}")
        # A course is recommended only when its name/description matches at
        # least one term from the student's stated interest. Eligibility alone
        # must not make unrelated courses appear as recommendations.
        if not overlap:
            continue
        score = 45
        if is_bachelors(profile.qualification): score += 15
        if profile.percentage and profile.percentage >= course.minimum_percentage + 15: score += 8
        score += min(28, len(overlap) * 10)
        if profile.budget and course.fees <= profile.budget: score += 7
        score = min(score, 99)
        focus = ", ".join(sorted(overlap)[:3]) if overlap else "your postgraduate qualification goal"
        budget_note = " and fits your stated budget" if profile.budget and course.fees <= profile.budget else ""
        answers.append({"course_id": course.id, "course_name": course.course_name, "duration": course.duration, "fees": course.fees,
                        "match_score": score, "reason": f"Eligible based on your academic details and matched to your interest in {focus}{budget_note}.", "matched_interest": sorted(overlap), "eligibility": check})
        seen_course_keys.add(course_key)
    return sorted(answers, key=lambda item: item["match_score"], reverse=True)


def recommendation_message(db: Session, profile: Student, courses: list[dict]) -> str:
    if courses:
        return f"Found {len(courses)} postgraduate course option(s) matching your qualification and interest."
    eligible_count = 0
    for course in db.query(Course).filter(Course.minimum_qualification == POSTGRADUATE_REQUIREMENT).all():
        if eligibility(course, profile.qualification, profile.percentage)["eligible"]:
            eligible_count += 1
    if eligible_count and profile.interests:
        return "Course is not available for this interest. Please check with another interest."
    return "No eligible postgraduate course was found for the academic details provided."


def college_recommendations(db: Session, profile: Student, course_id: int | None = None) -> list[dict]:
    query = db.query(CollegeCourse).join(College).join(Course).filter(College.college_name == "Bangalore University", Course.minimum_qualification == POSTGRADUATE_REQUIREMENT).order_by(Course.course_name, Course.id)
    if course_id:
        query = query.filter(CollegeCourse.course_id == course_id)
    location = (profile.preferred_location or "").lower()
    result = []
    seen_course_keys = set()
    for row in query.all():
        course_key = canonical_course_key(row.course.course_name)
        if course_key in seen_course_keys:
            continue
        seen_course_keys.add(course_key)
        if profile.budget is not None and row.fees > profile.budget:
            continue
        location_match = bool(location and location in row.college.location.lower())
        reason = f"Bangalore University offers {row.course.course_name} for ₹{row.fees:,.0f}."
        if location_match: reason += f" It matches your preferred location ({row.college.location})."
        if profile.budget is not None: reason += " It is within your stated budget."
        result.append({"college_id": row.college.id, "college_name": row.college.college_name, "location": row.college.location,
                       "description": row.college.description, "course_id": row.course.id, "course_name": row.course.course_name,
                       "fees": row.fees, "reason": reason, "location_match": location_match})
    return sorted(result, key=lambda item: (not item["location_match"], item["fees"]))


def seed_database(db: Session) -> None:
    from .security import hash_password

    if db.query(User).filter_by(email="admin@bcu-demo.edu").first() is None:
        db.add(User(name="System Administrator", email="admin@bcu-demo.edu", phone="9000000000", password_hash=hash_password("Admin@123"), role="admin"))

    catalogue = [
        ("MCA - Artificial Intelligence", "2 Years", "Bachelor's Degree", 50, 80000, "Postgraduate computer applications programme with artificial intelligence, Python and machine learning foundations."),
        ("MCA - Data Science", "2 Years", "Bachelor's Degree", 50, 85000, "Postgraduate programme focused on data analysis, databases, statistics and data science."),
        ("MCA - Cyber Security", "2 Years", "Bachelor's Degree", 55, 90000, "Postgraduate programme covering network security, ethical hacking and secure software."),
        ("MBA - Business Analytics", "2 Years", "Bachelor's Degree", 50, 95000, "Management programme combining business strategy, analytics and decision making."),
        ("MSc - Computer Science", "2 Years", "Bachelor's Degree", 50, 78000, "Advanced computer science programme covering algorithms, software engineering and systems."),
        ("MCA - Cloud Computing", "2 Years", "Bachelor's Degree", 50, 88000, "Postgraduate programme focused on cloud architecture, DevOps and distributed applications."),
        ("MCom - Finance and Analytics", "2 Years", "Bachelor's Degree", 50, 70000, "Commerce programme combining accounting, finance, business intelligence and analytics."),
        ("MA - Economics", "2 Years", "Bachelor's Degree", 45, 65000, "Postgraduate economics programme covering policy, markets, statistics and development."),
    ]
    for name, duration, qualification, minimum_percentage, fees, description in catalogue:
        if not db.query(Course).filter_by(course_name=name).first():
            db.add(Course(course_name=name, duration=duration, minimum_qualification=qualification,
                          minimum_percentage=minimum_percentage, fees=fees, description=description))
    db.flush()

    # Remove undergraduate demo rows introduced by an earlier catalogue. Keep
    # any course that already has admission/faculty history so records remain
    # intact; those legacy rows are excluded from new catalogue recommendations.
    for course in db.query(Course).filter(Course.course_name.in_(REMOVED_UNDERGRADUATE_COURSES)).all():
        has_history = db.query(Admission).filter(Admission.course_id == course.id).first()
        has_faculty = db.query(Faculty).filter(Faculty.course_id == course.id).first()
        has_merit = db.query(MeritList).filter(MeritList.course_id == course.id).first()
        if not has_history and not has_faculty and not has_merit:
            db.query(CollegeCourse).filter(CollegeCourse.course_id == course.id).delete(synchronize_session=False)
            db.delete(course)
    db.flush()

    university = db.query(College).filter_by(college_name="Bangalore University").first()
    if not university:
        university = db.query(College).order_by(College.id).first()
        if university:
            university.college_name = "Bangalore University"
            university.location = "Jnanabharathi, Bengaluru"
            university.description = "Bangalore University demo admission data for this academic project."
        else:
            university = College(college_name="Bangalore University", location="Jnanabharathi, Bengaluru", description="Bangalore University demo admission data for this academic project.")
            db.add(university)
            db.flush()
    for course in db.query(Course).all():
        if not db.query(CollegeCourse).filter_by(college_id=university.id, course_id=course.id).first():
            db.add(CollegeCourse(college_id=university.id, course_id=course.id, fees=course.fees))

    students = [
        ("Kavya Nair", "kavya.nair.demo@bcu.edu", "9000000101", "BCA", 82, "Artificial Intelligence, Python, Machine Learning", 90000),
        ("Rohan Mehta", "rohan.mehta.demo@bcu.edu", "9000000102", "BSc Computer Science", 68, "Data Science, Cloud Computing", 85000),
        ("Sneha Iyer", "sneha.iyer.demo@bcu.edu", "9000000103", "BCom", 76, "Business Analytics, Finance", 100000),
    ]
    for name, email, phone, qualification, percentage, interests, budget in students:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(name=name, email=email, phone=phone, password_hash=hash_password("Student@123"), role="student")
            db.add(user)
            db.flush()
            db.add(Student(user_id=user.id, qualification=qualification, percentage=percentage,
                            interests=interests, budget=budget, preferred_location="Bengaluru"))

    faculty_rows = [
        ("Dr. Ananya Rao", "ananya.rao.faculty@bcu.edu", "9000000201", "MCA - Artificial Intelligence", "Professor"),
        ("Prof. Vikram Shetty", "vikram.shetty.faculty@bcu.edu", "9000000202", "MCA - Data Science", "Admission Coordinator"),
        ("Dr. Meera Joshi", "meera.joshi.faculty@bcu.edu", "9000000203", "MBA - Business Analytics", "Associate Professor"),
    ]
    for name, email, phone, course_name, designation in faculty_rows:
        course = db.query(Course).filter_by(course_name=course_name).first()
        user = db.query(User).filter_by(email=email).first()
        if not course:
            continue
        if not user:
            user = User(name=name, email=email, phone=phone, password_hash=hash_password("Faculty@123"), role="faculty")
            db.add(user)
            db.flush()
        faculty = db.query(Faculty).filter_by(user_id=user.id).first()
        if not faculty:
            db.add(Faculty(user_id=user.id, college_id=university.id, course_id=course.id,
                           designation=designation, approval_status="APPROVED"))
        elif faculty.course_id is None:
            faculty.course_id = course.id
    db.commit()
