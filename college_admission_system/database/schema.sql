-- Create this database first, then configure backend/.env with its credentials.
CREATE DATABASE IF NOT EXISTS college_admission CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE college_admission;

-- SQLAlchemy creates the same tables automatically when the API starts.
-- This schema is included for academic documentation and manual MySQL setup.
CREATE TABLE IF NOT EXISTS users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  phone VARCHAR(20) NOT NULL,
  password VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'student',
  created_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS students (
  student_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  qualification VARCHAR(120) NULL,
  percentage FLOAT NULL,
  interests TEXT NULL,
  budget FLOAT NULL,
  preferred_location VARCHAR(120) NULL,
  CONSTRAINT fk_students_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS chat_messages (
  chat_message_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  message TEXT NOT NULL,
  response TEXT NOT NULL,
  extracted_data TEXT NULL,
  created_at DATETIME NOT NULL,
  CONSTRAINT fk_chat_messages_student FOREIGN KEY (student_id) REFERENCES students(student_id)
);
CREATE TABLE IF NOT EXISTS notifications (
  notification_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  title VARCHAR(160) NOT NULL,
  message TEXT NOT NULL,
  is_read BOOLEAN NOT NULL DEFAULT FALSE,
  created_at DATETIME NOT NULL,
  CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS student_documents (
  document_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  document_type VARCHAR(80) NOT NULL,
  original_filename VARCHAR(255) NOT NULL,
  stored_filename VARCHAR(255) NOT NULL UNIQUE,
  file_path VARCHAR(500) NOT NULL,
  file_data MEDIUMBLOB NOT NULL,
  verification_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  verification_note TEXT NULL,
  uploaded_at DATETIME NOT NULL,
  verified_at DATETIME NULL,
  CONSTRAINT fk_student_documents_student FOREIGN KEY (student_id) REFERENCES students(student_id)
);
CREATE TABLE IF NOT EXISTS courses (
  course_id INT AUTO_INCREMENT PRIMARY KEY,
  course_name VARCHAR(160) NOT NULL UNIQUE,
  duration VARCHAR(60) NOT NULL,
  minimum_qualification VARCHAR(160) NOT NULL,
  minimum_percentage FLOAT NOT NULL,
  fees FLOAT NOT NULL,
  description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS colleges (
  college_id INT AUTO_INCREMENT PRIMARY KEY,
  college_name VARCHAR(180) NOT NULL UNIQUE,
  location VARCHAR(120) NOT NULL,
  description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS college_courses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  college_id INT NOT NULL,
  course_id INT NOT NULL,
  fees FLOAT NOT NULL,
  CONSTRAINT fk_college_courses_college FOREIGN KEY (college_id) REFERENCES colleges(college_id),
  CONSTRAINT fk_college_courses_course FOREIGN KEY (course_id) REFERENCES courses(course_id)
);
CREATE TABLE IF NOT EXISTS admissions (
  admission_id INT AUTO_INCREMENT PRIMARY KEY,
  application_number VARCHAR(40) NOT NULL UNIQUE,
  student_id INT NOT NULL,
  college_id INT NOT NULL,
  course_id INT NOT NULL,
  address TEXT NOT NULL,
  previous_institution VARCHAR(180) NOT NULL,
  application_date DATETIME NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  CONSTRAINT fk_admissions_student FOREIGN KEY (student_id) REFERENCES students(student_id),
  CONSTRAINT fk_admissions_college FOREIGN KEY (college_id) REFERENCES colleges(college_id),
  CONSTRAINT fk_admissions_course FOREIGN KEY (course_id) REFERENCES courses(course_id)
);
CREATE TABLE IF NOT EXISTS admission_status_history (
  history_id INT AUTO_INCREMENT PRIMARY KEY,
  admission_id INT NOT NULL,
  status VARCHAR(30) NOT NULL,
  note TEXT NOT NULL,
  changed_by INT NULL,
  changed_at DATETIME NOT NULL,
  CONSTRAINT fk_status_history_admission FOREIGN KEY (admission_id) REFERENCES admissions(admission_id),
  CONSTRAINT fk_status_history_user FOREIGN KEY (changed_by) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS payments (
  payment_id INT AUTO_INCREMENT PRIMARY KEY,
  admission_id INT NOT NULL UNIQUE,
  amount FLOAT NOT NULL,
  transaction_id VARCHAR(50) NULL,
  payment_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  payment_date DATETIME NULL,
  CONSTRAINT fk_payments_admission FOREIGN KEY (admission_id) REFERENCES admissions(admission_id)
);
CREATE TABLE IF NOT EXISTS faculty (
  faculty_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  college_id INT NOT NULL,
  course_id INT NULL,
  designation VARCHAR(120) NOT NULL,
  approval_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  created_at DATETIME NOT NULL,
  CONSTRAINT fk_faculty_user FOREIGN KEY (user_id) REFERENCES users(user_id),
  CONSTRAINT fk_faculty_college FOREIGN KEY (college_id) REFERENCES colleges(college_id),
  CONSTRAINT fk_faculty_course FOREIGN KEY (course_id) REFERENCES courses(course_id)
);
CREATE TABLE IF NOT EXISTS merit_lists (
  merit_list_id INT AUTO_INCREMENT PRIMARY KEY,
  college_id INT NOT NULL,
  faculty_id INT NOT NULL,
  course_id INT NULL,
  published_at DATETIME NOT NULL,
  CONSTRAINT fk_merit_list_college FOREIGN KEY (college_id) REFERENCES colleges(college_id),
  CONSTRAINT fk_merit_list_faculty FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id),
  CONSTRAINT fk_merit_list_course FOREIGN KEY (course_id) REFERENCES courses(course_id)
);
CREATE TABLE IF NOT EXISTS merit_list_entries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  merit_list_id INT NOT NULL,
  admission_id INT NOT NULL,
  merit_rank INT NOT NULL,
  CONSTRAINT fk_merit_entry_list FOREIGN KEY (merit_list_id) REFERENCES merit_lists(merit_list_id),
  CONSTRAINT fk_merit_entry_admission FOREIGN KEY (admission_id) REFERENCES admissions(admission_id)
);
