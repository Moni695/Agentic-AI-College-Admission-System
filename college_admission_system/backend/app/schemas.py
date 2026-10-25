from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(pattern=r"^\d{10}$")
    degree: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=6, max_length=72)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password must match")
        return self


class FacultyRegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(pattern=r"^\d{10}$")
    college_id: int
    course_id: int
    designation: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=6, max_length=72)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password must match")
        return self


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


class ProfileIn(BaseModel):
    qualification: str | None = None
    percentage: float | None = Field(default=None, ge=0, le=100)
    interests: str | None = None
    budget: float | None = Field(default=None, ge=0)
    preferred_location: str | None = None


class CourseIn(BaseModel):
    course_name: str
    duration: str
    minimum_qualification: str
    minimum_percentage: float = Field(ge=0, le=100)
    fees: float = Field(ge=0)
    description: str


class CollegeIn(BaseModel):
    college_name: str
    location: str
    description: str
    offerings: list[dict] = []


class ChatIn(BaseModel):
    message: str = Field(min_length=2, max_length=2000)


class AdmissionIn(BaseModel):
    course_id: int
    college_id: int
    address: str = Field(min_length=5)
    previous_institution: str = Field(min_length=2)


class StatusIn(BaseModel):
    status: str


class DocumentReviewIn(BaseModel):
    verification_status: str
    verification_note: str | None = None


class ApprovalIn(BaseModel):
    approval_status: str


class MeritListReleaseIn(BaseModel):
    course_id: int
    limit: int = Field(default=10, ge=1, le=100)


class PaymentOut(BaseModel):
    amount: float
    payment_status: str
    transaction_id: str | None = None
    payment_date: datetime | None = None
