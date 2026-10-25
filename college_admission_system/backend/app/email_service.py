"""Email delivery for student-facing admission updates."""

import smtplib
from email.message import EmailMessage

from .config import get_settings


class EmailNotConfiguredError(RuntimeError):
    """Raised when the application has no SMTP sender configuration."""


def send_merit_selection_email(
    *, student_name: str, student_email: str, course_name: str,
    college_name: str, application_number: str, merit_rank: int,
) -> None:
    """Send the selected student's merit-list congratulations email."""
    settings = get_settings()
    required = {
        "SMTP_HOST": settings.smtp_host,
        "SMTP_USERNAME": settings.smtp_username,
        "SMTP_PASSWORD": settings.smtp_password,
        "SMTP_FROM_EMAIL": settings.smtp_from_email,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise EmailNotConfiguredError("Email is not configured. Set " + ", ".join(missing) + " in backend/.env.")

    message = EmailMessage()
    message["Subject"] = f"Congratulations! You have been selected for {course_name}"
    message["From"] = settings.smtp_from_email
    message["To"] = student_email
    message.set_content(
        f"Dear {student_name},\n\n"
        f"Congratulations! You have been selected for {course_name} at {college_name}. "
        f"Your merit-list rank is #{merit_rank}.\n\n"
        f"Application number: {application_number}\n\n"
        "Please sign in to the Student Portal to view your selection status and the next admission steps.\n\n"
        "Regards,\n"
        f"{college_name} Admissions"
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
