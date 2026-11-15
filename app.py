
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from models import db, Admin, Student, Teacher, SchoolClass, Attendance, StudentFee, FeePayment, Examination, ExamResult
from datetime import datetime
import os
app = Flask(__name__)

# Application configuration
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'temporary-local-development-key'
)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
csrf = CSRFProtect(app)
# Initialize database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Load logged-in admin
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))


# Home page
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    return redirect(url_for('login'))


# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):

            login_user(admin)

            flash('Login successful!', 'success')

            return redirect(url_for('dashboard'))

        else:
            flash('Invalid username or password!', 'error')

    return render_template('login.html')


# Admin dashboard
# Admin dashboard
@app.route('/dashboard')
@login_required
def dashboard():

    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_classes = SchoolClass.query.count()

    total_attendance = Attendance.query.count()

    return render_template(
        'dashboard.html',
        total_students=total_students,
        total_teachers=total_teachers,
        total_classes=total_classes,
        total_attendance=total_attendance
    )


@app.route('/students')
@login_required
def students():
    search = request.args.get('search', '').strip()

    query = Student.query

    if search:
        query = query.filter(
            db.or_(
                Student.name.ilike(f'%{search}%'),
                Student.admission_no.ilike(f'%{search}%')
            )
        )

    all_students = query.order_by(Student.id.desc()).all()

    class_names = {
        school_class.id: (
            f"{school_class.class_name} {school_class.section or ''}".strip()
        )
        for school_class in SchoolClass.query.all()
    }

    return render_template(
        'students.html',
        students=all_students,
        class_names=class_names,
        search=search
    )


@app.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():

    if request.method == 'POST':

        admission_no = request.form.get('admission_no', '').strip()
        name = request.form.get('name', '').strip()
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        class_id = request.form.get('class_id')

        if not admission_no or not name:
            flash('Admission number and name are required.', 'error')
            return redirect(url_for('add_student'))

        existing_student = Student.query.filter_by(
            admission_no=admission_no
        ).first()

        if existing_student:
            flash('This admission number already exists.', 'error')
            return redirect(url_for('add_student'))

        student = Student(
            admission_no=admission_no,
            name=name,
            gender=gender or None,
            dob=datetime.strptime(dob, '%Y-%m-%d').date() if dob else None,
            phone=phone or None,
            address=address or None,
            class_id=int(class_id) if class_id else None
        )

        db.session.add(student)
        db.session.commit()

        flash('Student registered successfully!', 'success')
        return redirect(url_for('students'))

    all_classes = SchoolClass.query.order_by(SchoolClass.class_name).all()

    return render_template(
        'add_student.html',
        classes=all_classes
    )

@app.route('/classes/add', methods=['GET', 'POST'])
@login_required
def add_class():

    if request.method == 'POST':

        class_name = request.form.get('class_name', '').strip()
        section = request.form.get('section', '').strip()
        class_teacher = request.form.get('class_teacher', '').strip()

        if not class_name:
            flash('Class name is required.', 'error')
            return redirect(url_for('add_class'))

        new_class = SchoolClass(
            class_name=class_name,
            section=section or None,
            class_teacher=class_teacher or None
        )

        db.session.add(new_class)
        db.session.commit()

        flash('Class added successfully!', 'success')
        return redirect(url_for('add_class'))

    return render_template('add_class.html')

@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        admission_no = request.form.get('admission_no', '').strip()
        name = request.form.get('name', '').strip()
        gender = request.form.get('gender') or None
        dob = request.form.get('dob')
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        class_id = request.form.get('class_id')

        if not admission_no or not name:
            flash('Admission number and name are required.', 'error')
            return redirect(url_for('edit_student', student_id=student.id))

        duplicate = Student.query.filter(
            Student.admission_no == admission_no,
            Student.id != student.id
        ).first()

        if duplicate:
            flash('This admission number already exists.', 'error')
            return redirect(url_for('edit_student', student_id=student.id))

        student.admission_no = admission_no
        student.name = name
        student.gender = gender
        student.dob = datetime.strptime(dob, '%Y-%m-%d').date() if dob else None
        student.phone = phone or None
        student.address = address or None
        student.class_id = int(class_id) if class_id else None

        db.session.commit()

        flash('Student details updated successfully!', 'success')
        return redirect(url_for('students'))

    all_classes = SchoolClass.query.order_by(SchoolClass.class_name).all()

    return render_template(
        'edit_student.html',
        student=student,
        classes=all_classes
    )


@app.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)

    db.session.delete(student)
    db.session.commit()

    flash('Student deleted successfully!', 'success')
    return redirect(url_for('students'))

@app.route('/teachers')
@login_required
def teachers():
    search = request.args.get('search', '').strip()

    query = Teacher.query

    if search:
        query = query.filter(
            db.or_(
                Teacher.name.ilike(f'%{search}%'),
                Teacher.subject.ilike(f'%{search}%')
            )
        )

    all_teachers = query.order_by(Teacher.id.desc()).all()

    return render_template(
        'teachers.html',
        teachers=all_teachers,
        search=search
    )


@app.route('/teachers/add', methods=['GET', 'POST'])
@login_required
def add_teacher():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        subject = request.form.get('subject', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()

        if not name:
            flash('Teacher name is required.', 'error')
            return redirect(url_for('add_teacher'))

        if email and Teacher.query.filter_by(email=email).first():
            flash('This email is already registered.', 'error')
            return redirect(url_for('add_teacher'))

        teacher = Teacher(
            name=name,
            subject=subject or None,
            phone=phone or None,
            email=email or None
        )

        db.session.add(teacher)
        db.session.commit()

        flash('Teacher added successfully!', 'success')
        return redirect(url_for('teachers'))

    return render_template('add_teacher.html')


@app.route('/teachers/edit/<int:teacher_id>', methods=['GET', 'POST'])
@login_required
def edit_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        subject = request.form.get('subject', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()

        if not name:
            flash('Teacher name is required.', 'error')
            return redirect(url_for('edit_teacher', teacher_id=teacher.id))

        duplicate = Teacher.query.filter(
            Teacher.email == email,
            Teacher.id != teacher.id
        ).first() if email else None

        if duplicate:
            flash('This email is already registered.', 'error')
            return redirect(url_for('edit_teacher', teacher_id=teacher.id))

        teacher.name = name
        teacher.subject = subject or None
        teacher.phone = phone or None
        teacher.email = email or None

        db.session.commit()

        flash('Teacher details updated successfully!', 'success')
        return redirect(url_for('teachers'))

    return render_template('edit_teacher.html', teacher=teacher)


@app.route('/teachers/delete/<int:teacher_id>', methods=['POST'])
@login_required
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)

    db.session.delete(teacher)
    db.session.commit()

    flash('Teacher deleted successfully!', 'success')
    return redirect(url_for('teachers'))

@app.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():

    all_classes = SchoolClass.query.order_by(
        SchoolClass.class_name
    ).all()

    selected_class_id = request.values.get('class_id', '')
    selected_date = request.values.get(
        'attendance_date',
        datetime.today().strftime('%Y-%m-%d')
    )

    students = []
    attendance_map = {}

    try:
        attendance_date = datetime.strptime(
            selected_date, '%Y-%m-%d'
        ).date()
    except ValueError:
        flash('Invalid attendance date.', 'error')
        return redirect(url_for('attendance'))

    if selected_class_id:
        try:
            class_id = int(selected_class_id)
        except ValueError:
            flash('Invalid class selected.', 'error')
            return redirect(url_for('attendance'))

        students = Student.query.filter_by(
            class_id=class_id
        ).order_by(Student.name).all()

        if request.method == 'POST':

            if not students:
                flash('No students found in this class.', 'error')
                return redirect(url_for(
                    'attendance',
                    class_id=class_id,
                    attendance_date=selected_date
                ))

            for student in students:

                status = request.form.get(
                    f'status_{student.id}'
                )

                if status not in ['Present', 'Absent']:
                    continue

                record = Attendance.query.filter_by(
                    student_id=student.id,
                    attendance_date=attendance_date
                ).first()

                if record:
                    record.status = status
                else:
                    record = Attendance(
                        student_id=student.id,
                        attendance_date=attendance_date,
                        status=status
                    )
                    db.session.add(record)

            db.session.commit()

            flash('Attendance saved successfully!', 'success')

            return redirect(url_for(
                'attendance',
                class_id=class_id,
                attendance_date=selected_date
            ))

        existing_records = Attendance.query.filter_by(
            attendance_date=attendance_date
        ).all()

        attendance_map = {
            record.student_id: record.status
            for record in existing_records
        }

    return render_template(
        'attendance.html',
        classes=all_classes,
        students=students,
        attendance_map=attendance_map,
        selected_class_id=selected_class_id,
        selected_date=selected_date
    )


# Logout
@app.route('/logout', methods=['POST'])
@login_required
def logout():

    logout_user()

    flash('You have logged out successfully.', 'success')

    return redirect(url_for('login'))


# Create database tables
with app.app_context():
    db.create_all()




@app.route('/classes')
@login_required
def classes():
    all_classes = SchoolClass.query.order_by(
        SchoolClass.class_name
    ).all()

    class_data = []

    for school_class in all_classes:
        student_count = Student.query.filter_by(
            class_id=school_class.id
        ).count()

        class_data.append({
            'class': school_class,
            'student_count': student_count
        })

    return render_template(
        'classes.html',
        class_data=class_data
    )


@app.route('/classes/edit/<int:class_id>', methods=['GET', 'POST'])
@login_required
def edit_class(class_id):
    school_class = SchoolClass.query.get_or_404(class_id)

    if request.method == 'POST':
        class_name = request.form.get('class_name', '').strip()
        section = request.form.get('section', '').strip()
        class_teacher = request.form.get('class_teacher', '').strip()

        if not class_name:
            flash('Class name is required.', 'error')
            return redirect(url_for('edit_class', class_id=class_id))

        school_class.class_name = class_name
        school_class.section = section or None
        school_class.class_teacher = class_teacher or None

        db.session.commit()

        flash('Class updated successfully!', 'success')
        return redirect(url_for('classes'))

    return render_template(
        'edit_class.html',
        school_class=school_class
    )


@app.route('/classes/delete/<int:class_id>', methods=['POST'])
@login_required
def delete_class(class_id):
    school_class = SchoolClass.query.get_or_404(class_id)

    assigned_students = Student.query.filter_by(
        class_id=class_id
    ).count()

    if assigned_students > 0:
        flash(
            'Cannot delete this class because students are assigned to it.',
            'error'
        )
        return redirect(url_for('classes'))

    db.session.delete(school_class)
    db.session.commit()

    flash('Class deleted successfully!', 'success')
    return redirect(url_for('classes'))

@app.route('/fees')
@login_required
def fees():
    all_students = Student.query.order_by(Student.name).all()

    fee_data = []

    for student in all_students:
        fee_record = StudentFee.query.filter_by(
            student_id=student.id
        ).first()

        total_fee = fee_record.total_fee if fee_record else 0

        total_paid = 0

        if fee_record:
            payments = FeePayment.query.filter_by(
                fee_id=fee_record.id
            ).all()

            total_paid = sum(payment.amount for payment in payments)

        fee_data.append({
            'student': student,
            'total_fee': total_fee,
            'total_paid': total_paid,
            'pending': total_fee - total_paid
        })

    return render_template('fees.html', fee_data=fee_data)


@app.route('/fees/manage/<int:student_id>', methods=['GET', 'POST'])
@login_required
def manage_fee(student_id):
    student = Student.query.get_or_404(student_id)

    fee_record = StudentFee.query.filter_by(
        student_id=student.id
    ).first()

    if not fee_record:
        fee_record = StudentFee(
            student_id=student.id,
            total_fee=0
        )
        db.session.add(fee_record)
        db.session.commit()

    if request.method == 'POST':

        action = request.form.get('action')

        if action == 'set_fee':
            try:
                new_total = float(request.form.get('total_fee', ''))
                if new_total < 0:
                    raise ValueError
            except (ValueError, TypeError):
                flash('Enter a valid non-negative fee amount.', 'error')
                return redirect(url_for('manage_fee', student_id=student.id))

            total_paid = sum(
                payment.amount
                for payment in FeePayment.query.filter_by(
                    fee_id=fee_record.id
                ).all()
            )

            if new_total < total_paid:
                flash('Total fee cannot be less than the amount already paid.', 'error')
            else:
                fee_record.total_fee = new_total
                db.session.commit()
                flash('Total fee updated successfully!', 'success')

            return redirect(url_for('manage_fee', student_id=student.id))

        elif action == 'add_payment':
            try:
                amount = float(request.form.get('amount', ''))
                if amount <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                flash('Enter a valid payment amount greater than zero.', 'error')
                return redirect(url_for('manage_fee', student_id=student.id))

            total_paid = sum(
                payment.amount
                for payment in FeePayment.query.filter_by(
                    fee_id=fee_record.id
                ).all()
            )

            if fee_record.total_fee <= 0:
                flash('Set the total fee before recording a payment.', 'error')
                return redirect(url_for('manage_fee', student_id=student.id))

            if total_paid + amount > fee_record.total_fee:
                flash('Payment exceeds the pending fee amount.', 'error')
                return redirect(url_for('manage_fee', student_id=student.id))

            date_text = request.form.get('payment_date', '')

            try:
                payment_date = datetime.strptime(
                    date_text, '%Y-%m-%d'
                ).date()
            except ValueError:
                flash('Please select a valid payment date.', 'error')
                return redirect(url_for('manage_fee', student_id=student.id))

            payment = FeePayment(
                fee_id=fee_record.id,
                amount=amount,
                payment_date=payment_date,
                note=request.form.get('note', '').strip() or None
            )

            db.session.add(payment)
            db.session.commit()

            flash('Payment recorded successfully!', 'success')
            return redirect(url_for('manage_fee', student_id=student.id))

    payments = FeePayment.query.filter_by(
        fee_id=fee_record.id
    ).order_by(FeePayment.payment_date.desc(), FeePayment.id.desc()).all()

    total_paid = sum(payment.amount for payment in payments)
    pending = fee_record.total_fee - total_paid

    return render_template(
        'manage_fee.html',
        student=student,
        fee_record=fee_record,
        payments=payments,
        total_paid=total_paid,
        pending=pending,
        today=datetime.today().strftime('%Y-%m-%d')
    )

@app.route('/exams')
@login_required
def exams():
    all_exams = Examination.query.order_by(
        Examination.exam_date.desc()
    ).all()

    exam_data = []

    for exam in all_exams:
        school_class = db.session.get(SchoolClass, exam.class_id)

        exam_data.append({
            'exam': exam,
            'class_name': (
                f"{school_class.class_name} {school_class.section or ''}".strip()
                if school_class else 'Unknown'
            )
        })

    return render_template(
        'exams.html',
        exam_data=exam_data
    )


@app.route('/exams/add', methods=['GET', 'POST'])
@login_required
def add_exam():

    if request.method == 'POST':
        exam_name = request.form.get('exam_name', '').strip()
        class_id = request.form.get('class_id', '')
        exam_date = request.form.get('exam_date', '')

        if not exam_name or not class_id or not exam_date:
            flash('Please fill in all examination details.', 'error')
            return redirect(url_for('add_exam'))

        try:
            class_id = int(class_id)
            exam_date = datetime.strptime(
                exam_date, '%Y-%m-%d'
            ).date()
        except ValueError:
            flash('Please enter valid examination details.', 'error')
            return redirect(url_for('add_exam'))

        if not db.session.get(SchoolClass, class_id):
            flash('Selected class does not exist.', 'error')
            return redirect(url_for('add_exam'))

        new_exam = Examination(
            exam_name=exam_name,
            class_id=class_id,
            exam_date=exam_date
        )

        db.session.add(new_exam)
        db.session.commit()

        flash('Examination created successfully!', 'success')
        return redirect(url_for('exams'))

    all_classes = SchoolClass.query.order_by(
        SchoolClass.class_name
    ).all()

    return render_template(
        'add_exam.html',
        classes=all_classes
    )


@app.route('/exams/<int:exam_id>/results', methods=['GET', 'POST'])
@login_required
def exam_results(exam_id):

    exam = Examination.query.get_or_404(exam_id)

    students = Student.query.filter_by(
        class_id=exam.class_id
    ).order_by(Student.name).all()

    selected_subject = request.values.get(
        'subject', ''
    ).strip()

    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()

        try:
            total_marks = float(request.form.get('total_marks', ''))
        except (ValueError, TypeError):
            flash('Enter a valid total marks value.', 'error')
            return redirect(url_for(
                'exam_results',
                exam_id=exam.id,
                subject=subject
            ))

        if not subject or total_marks <= 0:
            flash('Enter a subject and valid total marks.', 'error')
            return redirect(url_for(
                'exam_results',
                exam_id=exam.id
            ))

        if not students:
            flash('No students are assigned to this class.', 'error')
            return redirect(url_for('exams'))

        for student in students:
            marks_text = request.form.get(
                f'marks_{student.id}', ''
            ).strip()

            if not marks_text:
                continue

            try:
                marks = float(marks_text)
            except ValueError:
                flash('Marks must be valid numbers.', 'error')
                return redirect(url_for(
                    'exam_results',
                    exam_id=exam.id,
                    subject=subject
                ))

            if marks < 0 or marks > total_marks:
                flash(
                    f'Marks for {student.name} must be between 0 and {total_marks}.',
                    'error'
                )
                return redirect(url_for(
                    'exam_results',
                    exam_id=exam.id,
                    subject=subject
                ))

            result = ExamResult.query.filter_by(
                examination_id=exam.id,
                student_id=student.id,
                subject=subject
            ).first()

            if result:
                result.total_marks = total_marks
                result.marks_obtained = marks
            else:
                result = ExamResult(
                    examination_id=exam.id,
                    student_id=student.id,
                    subject=subject,
                    total_marks=total_marks,
                    marks_obtained=marks
                )
                db.session.add(result)

        db.session.commit()

        flash('Examination marks saved successfully!', 'success')

        return redirect(url_for(
            'exam_results',
            exam_id=exam.id,
            subject=subject
        ))

    results = []

    if selected_subject:
        results = ExamResult.query.filter_by(
            examination_id=exam.id,
            subject=selected_subject
        ).all()

    result_map = {
        result.student_id: result
        for result in results
    }

    return render_template(
        'exam_results.html',
        exam=exam,
        students=students,
        result_map=result_map,
        selected_subject=selected_subject
    )


@app.route('/exams/delete/<int:exam_id>', methods=['POST'])
@login_required
def delete_exam(exam_id):

    exam = Examination.query.get_or_404(exam_id)

    ExamResult.query.filter_by(
        examination_id=exam.id
    ).delete()

    db.session.delete(exam)
    db.session.commit()

    flash('Examination deleted successfully!', 'success')

    return redirect(url_for('exams'))

# Create database tables
with app.app_context():
    db.create_all()


# Run application
if __name__ == '__main__':
    app.run(debug=True)