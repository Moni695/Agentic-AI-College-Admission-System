import json
import re
from sqlalchemy.orm import Session
from .config import get_settings
from .models import Student
from .services import college_recommendations, course_recommendations, recommendation_message


def extract_locally(message: str) -> dict:
    text = message.lower()
    data = {}
    qualification = re.search(r"\b(bca|bsc(?:\s+\w+)?|bcom|bba|ba|be|b\.e\.?|btech|b\.tech\.?|bachelor(?:'s)?(?:\s+\w+)?)\b", text, re.I)
    percentage = re.search(r"\b(\d{2}(?:\.\d+)?)\s*(?:%|percent|percentage)\b", text, re.I)
    budget = re.search(r"(?:budget(?:\s+is|\s+of)?|₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(?:k|lakh)?", text, re.I)
    location = re.search(r"(?:in|near|location(?:\s+is)?|prefer(?:red)?\s+(?:location|area)\s*(?:is)?)[\s:]+([a-z ]{3,30}?)(?:[.,;]|$)", text, re.I)
    if qualification: data["qualification"] = qualification.group(1).upper().replace(".", "")
    if percentage: data["percentage"] = float(percentage.group(1))
    if budget:
        value = float(budget.group(1).replace(",", ""))
        if budget.group(0).lower().endswith("k"): value *= 1000
        if budget.group(0).lower().endswith("lakh"): value *= 100000
        data["budget"] = value
    interest_words = [word for word in ("artificial intelligence", "ai", "data science", "data", "cyber security", "security", "business analytics", "analytics", "management") if word in text]
    if interest_words: data["interests"] = ", ".join(dict.fromkeys(interest_words))
    if location: data["preferred_location"] = location.group(1).strip().title()
    return data


def extract_with_openai(message: str) -> dict:
    settings = get_settings()
    if not settings.openai_api_key:
        return {}
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        tool = {"type": "function", "function": {"name": "extract_student_profile", "description": "Extract only facts explicitly stated by the student. Omit unknown values.", "parameters": {"type": "object", "properties": {"qualification": {"type": "string"}, "percentage": {"type": "number"}, "interests": {"type": "string"}, "budget": {"type": "number"}, "preferred_location": {"type": "string"}}, "additionalProperties": False}}}
        response = client.chat.completions.create(model=settings.openai_model, messages=[{"role": "system", "content": "You are an admission data extractor. Never invent facts."}, {"role": "user", "content": message}], tools=[tool], tool_choice={"type": "function", "function": {"name": "extract_student_profile"}})
        calls = response.choices[0].message.tool_calls or []
        return json.loads(calls[0].function.arguments) if calls else {}
    except Exception:
        return {}


def run_admission_agent(db: Session, student: Student, message: str) -> dict:
    extracted = extract_locally(message)
    extracted.update({key: value for key, value in extract_with_openai(message).items() if value not in (None, "")})
    for field, value in extracted.items():
        if field in {"qualification", "percentage", "interests", "budget", "preferred_location"}:
            setattr(student, field, value)
    db.commit()
    db.refresh(student)
    missing = [label for field, label in [("qualification", "your undergraduate qualification"), ("percentage", "your percentage/CGPA converted to percentage"), ("interests", "your interests or preferred course"), ("budget", "your annual course-fee budget"), ("preferred_location", "your preferred Bengaluru location")] if not getattr(student, field)]
    if missing:
        return {"reply": "I have saved the details you shared. To make reliable eligibility and college recommendations, please tell me " + ", ".join(missing) + ".", "extracted": extracted, "missing": missing, "courses": [], "colleges": []}
    courses = course_recommendations(db, student)
    colleges = college_recommendations(db, student, courses[0]["course_id"]) if courses else []
    if not courses:
        reply = recommendation_message(db, student, courses)
    else:
        reply = f"Based on the details saved in your profile, you are eligible for {len(courses)} postgraduate course option(s). I recommend {courses[0]['course_name']} first because {courses[0]['reason']} The listed fees and colleges are demo academic data, not official admissions information."
    return {"reply": reply, "extracted": extracted, "missing": [], "courses": courses[:3], "colleges": colleges[:3], "message": recommendation_message(db, student, courses)}
