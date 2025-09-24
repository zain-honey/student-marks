import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import io

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_secret")
# SQLite for local/dev. For production set DATABASE_URL env var to Postgres.
db_uri = os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(BASE_DIR, 'students.db')}"
app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2MB limit

db = SQLAlchemy(app)

# -----------------
# Models
# -----------------
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    father_name = db.Column(db.String(120))
    dob = db.Column(db.String(20))
    class_name = db.Column(db.String(50))
    image = db.Column(db.String(200), default="")
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    marks = db.Column(db.Float, nullable=False)

    student = db.relationship('Student', backref=db.backref('marks', lazy=True))
    subject = db.relationship('Subject')

# -----------------
# DB init
# -----------------
def init_db():
    with app.app_context():
        db.create_all()
        # default admin
        admin_user = os.environ.get("ADMIN_USER", "admin")
        admin_pass = os.environ.get("ADMIN_PASS", "admin123")
        if not Admin.query.filter_by(username=admin_user).first():
            a = Admin(username=admin_user)
            a.set_password(admin_pass)
            db.session.add(a)
            db.session.commit()
            print(f"✅ Created default admin -> {admin_user} / {admin_pass}")

# -----------------
# Helpers
# -----------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"png","jpg","jpeg","gif"}

def login_required(role=None):
    def wrapper():
        if 'role' not in session:
            return False
        if role and session.get('role') != role:
            return False
        return True
    return wrapper

# -----------------
# Routes
# -----------------
@app.route('/')
def index():
    return render_template('index.html')

# login route handles both admin and student by role param
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        if role == 'admin':
            username = request.form.get('username')
            password = request.form.get('password')
            admin = Admin.query.filter_by(username=username).first()
            if admin and admin.check_password(password):
                session['role'] = 'admin'
                session['user'] = username
                session['admin_id'] = admin.id
                return redirect(url_for('admin_dashboard'))
            flash("Invalid admin credentials", "danger")
            return redirect(url_for('login'))
        else:
            roll = request.form.get('roll_no')
            password = request.form.get('password')
            student = Student.query.filter_by(roll_no=roll).first()
            if student and student.check_password(password):
                session['role'] = 'student'
                session['student_id'] = student.id
                return redirect(url_for('student_dashboard'))
            flash("Invalid student credentials", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# -----------------
# Admin
# -----------------
@app.route('/admin')
def admin_dashboard():
    if not login_required('admin')():
        return redirect(url_for('login'))
    students = Student.query.order_by(Student.roll_no).all()
    subjects = Subject.query.order_by(Subject.name).all()
    marks = Mark.query.all()
    return render_template('admin.html', students=students, subjects=subjects, marks=marks)

@app.route('/admin/add_student', methods=['POST'])
def admin_add_student():
    if not login_required('admin')():
        return redirect(url_for('login'))
    roll = request.form.get('roll_no')
    name = request.form.get('name')
    father = request.form.get('father_name')
    dob = request.form.get('dob')
    class_name = request.form.get('class_name')
    password = request.form.get('password') or "password123"

    if Student.query.filter_by(roll_no=roll).first():
        flash("Roll number already exists", "danger")
        return redirect(url_for('admin_dashboard'))

    image_filename = ""
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{roll}_{int(datetime.utcnow().timestamp())}_{file.filename}")
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            image_filename = filename

    s = Student(roll_no=roll, name=name, father_name=father, dob=dob, class_name=class_name, image=image_filename)
    s.set_password(password)
    db.session.add(s)
    db.session.commit()
    flash("Student added", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_student/<int:sid>', methods=['POST'])
def admin_delete_student(sid):
    if not login_required('admin')():
        return redirect(url_for('login'))
    s = Student.query.get_or_404(sid)
    # remove marks too
    Mark.query.filter_by(student_id=s.id).delete()
    # optionally delete image file
    if s.image:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], s.image))
        except:
            pass
    db.session.delete(s)
    db.session.commit()
    flash("Student removed", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_subject', methods=['POST'])
def admin_add_subject():
    if not login_required('admin')():
        return redirect(url_for('login'))
    name = request.form.get('subject_name')
    if not name:
        flash("Subject name required", "danger")
        return redirect(url_for('admin_dashboard'))
    if Subject.query.filter_by(name=name).first():
        flash("Subject already exists", "danger")
    else:
        sub = Subject(name=name)
        db.session.add(sub)
        db.session.commit()
        flash("Subject added", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_subject/<int:sub_id>', methods=['POST'])
def admin_delete_subject(sub_id):
    if not login_required('admin')():
        return redirect(url_for('login'))
    # delete related marks first
    Mark.query.filter_by(subject_id=sub_id).delete()
    Subject.query.filter_by(id=sub_id).delete()
    db.session.commit()
    flash("Subject removed", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/save_mark', methods=['POST'])
def admin_save_mark():
    if not login_required('admin')():
        return redirect(url_for('login'))
    student_id = request.form.get('student_id')
    subject_id = request.form.get('subject_id')
    marks = request.form.get('marks')
    try:
        marks_v = float(marks)
    except:
        flash("Invalid marks", "danger")
        return redirect(url_for('admin_dashboard'))
    existing = Mark.query.filter_by(student_id=student_id, subject_id=subject_id).first()
    if existing:
        existing.marks = marks_v
    else:
        m = Mark(student_id=student_id, subject_id=subject_id, marks=marks_v)
        db.session.add(m)
    db.session.commit()
    flash("Marks saved", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/export_csv')
def admin_export_csv():
    if not login_required('admin')():
        return redirect(url_for('login'))
    students = Student.query.all()
    subjects = Subject.query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    header = ["Roll No", "Student Name"] + [sub.name for sub in subjects]
    writer.writerow(header)

    for s in students:
        row = [s.roll_no, s.name]
        for sub in subjects:
            mark = Mark.query.filter_by(student_id=s.id, subject_id=sub.id).first()
            row.append(mark.marks if mark else "")
        writer.writerow(row)

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, attachment_filename='marks_export.csv')

# -----------------
# Student Routes
# -----------------
@app.route('/student')
def student_dashboard():
    if not login_required('student')():
        return redirect(url_for('login'))
    student = Student.query.get(session.get('student_id'))
    marks = student.marks if student else []
    # compute percentage (assume 100 per subject)
    total = sum(m.marks for m in marks) if marks else 0
    count = len(marks) if marks else 0
    percentage = (total / (count * 100) * 100) if count else None
    return render_template('student.html', student=student, marks=marks, percentage=percentage)

@app.route('/student/change_password', methods=['POST'])
def student_change_password():
    if not login_required('student')():
        return redirect(url_for('login'))
    student = Student.query.get(session.get('student_id'))
    old = request.form.get('old_password')
    new = request.form.get('new_password')
    if not student.check_password(old):
        flash("Old password incorrect", "danger")
    else:
        student.set_password(new)
        db.session.commit()
        flash("Password changed", "success")
    return redirect(url_for('student_dashboard'))

# -----------------
# Run
# -----------------
if __name__ == "__main__":
    init_db()
    # Use reloader False to avoid Windows watchdog issues seen earlier
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False, use_reloader=False)
