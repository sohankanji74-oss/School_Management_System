
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Admin(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # Convert password into a secure hash
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Check entered password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Student Model
class Student(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    admission_no = db.Column(
        db.String(30), unique=True, nullable=False
    )

    name = db.Column(db.String(100), nullable=False)

    gender = db.Column(db.String(10))

    dob = db.Column(db.Date)

    phone = db.Column(db.String(15))

    address = db.Column(db.String(200))

    class_id = db.Column(
        db.Integer, db.ForeignKey('school_class.id')
    )


# Teacher Model
class Teacher(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    subject = db.Column(db.String(100))

    phone = db.Column(db.String(15))

    email = db.Column(db.String(100), unique=True)


# Class Model
class SchoolClass(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    class_name = db.Column(db.String(50), nullable=False)

    section = db.Column(db.String(10))

    class_teacher = db.Column(db.String(100))


# Attendance Model
class Attendance(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer, db.ForeignKey('student.id'),
        nullable=False
    )

    attendance_date = db.Column(db.Date, nullable=False)

    status = db.Column(db.String(10), nullable=False)

class StudentFee(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey('student.id'),
        unique=True,
        nullable=False
    )

    total_fee = db.Column(db.Float, nullable=False, default=0)


class FeePayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    fee_id = db.Column(
        db.Integer,
        db.ForeignKey('student_fee.id'),
        nullable=False
    )

    amount = db.Column(db.Float, nullable=False)

    payment_date = db.Column(db.Date, nullable=False)

    note = db.Column(db.String(200))

class Examination(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    exam_name = db.Column(db.String(100), nullable=False)

    class_id = db.Column(
        db.Integer,
        db.ForeignKey('school_class.id'),
        nullable=False
    )

    exam_date = db.Column(db.Date, nullable=False)


class ExamResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    examination_id = db.Column(
        db.Integer,
        db.ForeignKey('examination.id'),
        nullable=False
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey('student.id'),
        nullable=False
    )

    subject = db.Column(db.String(100), nullable=False)

    total_marks = db.Column(db.Float, nullable=False)

    marks_obtained = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            'examination_id',
            'student_id',
            'subject',
            name='unique_exam_student_subject'
        ),
    )
