# routes.py - All application routes organized by blueprint

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, Response
from models import mongo, bcrypt, get_student_by_id, get_admin_by_id, check_password, hash_password, \
    get_all_chatbot_qa, get_notifications_for_student
from bson import ObjectId
from datetime import datetime
from fuzzywuzzy import fuzz
import json, re

# ─────────────────────────────────────────────
# BLUEPRINTS
# ─────────────────────────────────────────────
main_bp = Blueprint('main', __name__)
student_bp = Blueprint('student', __name__, url_prefix='/student')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ─────────────────────────────────────────────
# UTILITY: SMART CHATBOT MATCHING
# ─────────────────────────────────────────────
def find_best_answer(user_query):
    """
    Intelligent keyword + fuzzy matching to find best chatbot answer.
    Uses both exact keyword matching and fuzzy string similarity.
    """
    user_query_lower = user_query.lower().strip()
    qa_list = get_all_chatbot_qa()
    
    best_match = None
    best_score = 0

    for qa in qa_list:
        keywords = qa.get('keywords', [])
        
        # 1. Direct keyword matching (highest priority)
        for keyword in keywords:
            if keyword.lower() in user_query_lower:
                score = 100  # Direct match = perfect score
                if score > best_score:
                    best_score = score
                    best_match = qa
                break
        
        # 2. Fuzzy matching on the question text
        if best_score < 80:
            question_score = fuzz.partial_ratio(user_query_lower, qa['question'].lower())
            if question_score > best_score and question_score >= 60:
                best_score = question_score
                best_match = qa

        # 3. Word-by-word matching on keywords
        if best_score < 80:
            user_words = set(user_query_lower.split())
            for keyword in keywords:
                kw_words = set(keyword.lower().split())
                overlap = user_words & kw_words
                if overlap:
                    word_score = (len(overlap) / max(len(kw_words), 1)) * 90
                    if word_score > best_score:
                        best_score = word_score
                        best_match = qa

    return best_match, best_score


# ─────────────────────────────────────────────
# MAIN / PUBLIC ROUTES
# ─────────────────────────────────────────────

@main_bp.route('/')
def index():
    """Homepage with chatbot"""
    # Fetch upcoming events for homepage
    events = list(mongo.db.events.find().sort("date", 1).limit(3))
    notifications = list(mongo.db.notifications.find({"target": "all", "important": True}).limit(3))
    return render_template('index.html', events=events, notifications=notifications)


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Unified login for students and admins"""
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        password = request.form.get('password', '').strip()
        user_type = request.form.get('user_type', 'student')

        if user_type == 'admin':
            admin = get_admin_by_id(user_id)
            if admin and check_password(admin['password'], password):
                session['admin_id'] = str(admin['_id'])
                session['admin_login_id'] = admin['admin_id']
                session['admin_name'] = admin['name']
                session['role'] = 'admin'
                flash('Welcome back, ' + admin['name'] + '!', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                flash('Invalid Admin ID or Password', 'danger')
        else:
            student = get_student_by_id(user_id)
            if student and check_password(student['password'], password):
                session['student_id'] = str(student['_id'])
                session['student_login_id'] = student['student_id']
                session['student_name'] = student['name']
                session['role'] = 'student'
                flash('Welcome, ' + student['name'] + '!', 'success')
                return redirect(url_for('student.dashboard'))
            else:
                flash('Invalid Student ID or Password', 'danger')

    return render_template('login.html')


@main_bp.route('/logout')
def logout():
    """Clear session and logout"""
    name = session.get('student_name') or session.get('admin_name', 'User')
    session.clear()
    flash(f'Goodbye, {name}! You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@main_bp.route('/chatbot', methods=['POST'])
def chatbot():
    """API endpoint for chatbot queries - no login required"""
    data = request.get_json()
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({"response": "Please type a question.", "matched": False})

    best_match, score = find_best_answer(user_message)

    if best_match and score >= 55:
        return jsonify({
            "response": best_match['answer'],
            "category": best_match.get('category', ''),
            "matched": True,
            "score": score
        })
    else:
        # Fallback response
        suggestions = [
            "courses offered", "fee structure", "admission procedure",
            "placement statistics", "hostel facilities", "contact details"
        ]
        fallback = (
            "🤔 I couldn't find an exact answer for that.<br><br>"
            "You can try asking about:<br>"
            + "".join(f"• {s}<br>" for s in suggestions)
            + "<br>Or contact us at <b>info@rknec.edu</b>"
        )
        return jsonify({"response": fallback, "matched": False, "score": score})


# ─────────────────────────────────────────────
# STUDENT ROUTES
# ─────────────────────────────────────────────

def student_required(f):
    """Decorator to protect student routes"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'student':
            flash('Please login as a student to access this page.', 'warning')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated


@student_bp.route('/dashboard')
@student_required
def dashboard():
    """Student dashboard - overview"""
    student = mongo.db.students.find_one({"student_id": session['student_login_id']})
    notifications = get_notifications_for_student(student)
    events = list(mongo.db.events.find().sort("date", 1).limit(5))
    return render_template('student/dashboard.html', student=student,
                           notifications=notifications, events=events)


@student_bp.route('/profile')
@student_required
def profile():
    """Student profile page"""
    student = mongo.db.students.find_one({"student_id": session['student_login_id']})
    return render_template('student/profile.html', student=student)


@student_bp.route('/results')
@student_required
def results():
    """Student results - semester-wise marks"""
    student = mongo.db.students.find_one({"student_id": session['student_login_id']})
    return render_template('student/results.html', student=student)


@student_bp.route('/timetable')
@student_required
def timetable():
    """Student timetable"""
    student = mongo.db.students.find_one({"student_id": session['student_login_id']})
    tt = mongo.db.timetable.find_one({"class": student.get('timetable_class', '')})
    return render_template('student/timetable.html', student=student, timetable=tt)


@student_bp.route('/attendance')
@student_required
def attendance():
    """Student attendance details"""
    student = mongo.db.students.find_one({"student_id": session['student_login_id']})
    return render_template('student/attendance.html', student=student)


@student_bp.route('/result/pdf')
@student_required
def result_pdf():
    """Generate downloadable PDF of results"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    import io

    student = mongo.db.students.find_one({"student_id": session['student_login_id']})
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("RCOEM - Academic Result Card", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Name: {student['name']} | Roll No: {student['roll_number']}", styles['Normal']))
    elements.append(Paragraph(f"Branch: {student['branch']} | CGPA: {student['cgpa']}", styles['Normal']))
    elements.append(Spacer(1, 20))

    for result in student.get('results', []):
        elements.append(Paragraph(f"Semester {result['semester']} (Year {result['year']}) - SGPA: {result['sgpa']}", styles['Heading2']))
        data = [['Subject', 'Credits', 'Marks', 'Grade']]
        for sub in result['subjects']:
            data.append([sub['name'], sub['credits'], sub['marks'], sub['grade']])
        t = Table(data, colWidths=[200, 60, 60, 60])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#eff6ff')]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

    doc.build(elements)
    buffer.seek(0)
    return Response(buffer.getvalue(), mimetype='application/pdf',
                    headers={"Content-Disposition": f"attachment;filename={student['roll_number']}_results.pdf"})


# ─────────────────────────────────────────────
# ADMIN ROUTES
# ─────────────────────────────────────────────

def admin_required(f):
    """Decorator to protect admin routes"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with stats"""
    total_students = mongo.db.students.count_documents({})
    total_events = mongo.db.events.count_documents({})
    total_qa = mongo.db.chatbot_qa.count_documents({})
    total_notifications = mongo.db.notifications.count_documents({})
    recent_students = list(mongo.db.students.find().sort("_id", -1).limit(5))
    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           total_events=total_events,
                           total_qa=total_qa,
                           total_notifications=total_notifications,
                           recent_students=recent_students)


@admin_bp.route('/students')
@admin_required
def students():
    """List all students"""
    branch_filter = request.args.get('branch', '')
    query = {"branch": branch_filter} if branch_filter else {}
    all_students = list(mongo.db.students.find(query, {"password": 0}))
    branches = mongo.db.students.distinct("branch")
    return render_template('admin/students.html', students=all_students, branches=branches,
                           selected_branch=branch_filter)


@admin_bp.route('/students/add', methods=['GET', 'POST'])
@admin_required
def add_student():
    """Add a new student"""
    if request.method == 'POST':
        import random, string
        student_id = request.form.get('student_id')
        # Check duplicate
        if mongo.db.students.find_one({"student_id": student_id}):
            flash('Student ID already exists!', 'danger')
            return redirect(url_for('admin.add_student'))

        # Auto-generate password
        auto_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        student_data = {
            "student_id": student_id,
            "password": hash_password(auto_password),
            "name": request.form.get('name'),
            "roll_number": request.form.get('roll_number'),
            "branch": request.form.get('branch'),
            "year": int(request.form.get('year', 1)),
            "semester": int(request.form.get('semester', 1)),
            "email": request.form.get('email'),
            "phone": request.form.get('phone'),
            "father_name": request.form.get('father_name', ''),
            "address": request.form.get('address', ''),
            "dob": request.form.get('dob', ''),
            "cgpa": 0.0,
            "timetable_class": request.form.get('timetable_class', ''),
            "attendance": {}, "results": [], "internal_marks": {},
            "exam_schedule": [], "projects": [], "internships": [],
            "activities": [], "fee_status": [], "notifications": []
        }
        mongo.db.students.insert_one(student_data)
        flash(f'Student added successfully! Auto-generated Password: <strong>{auto_password}</strong> — Please note it down.', 'success')
        return redirect(url_for('admin.students'))

    return render_template('admin/add_student.html')


@admin_bp.route('/students/edit/<student_id>', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    """Edit student data"""
    student = mongo.db.students.find_one({"student_id": student_id})
    if not student:
        flash('Student not found!', 'danger')
        return redirect(url_for('admin.students'))

    if request.method == 'POST':
        update_data = {
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "phone": request.form.get('phone'),
            "year": int(request.form.get('year', 1)),
            "semester": int(request.form.get('semester', 1)),
            "cgpa": float(request.form.get('cgpa', 0)),
            "timetable_class": request.form.get('timetable_class', '')
        }
        mongo.db.students.update_one({"student_id": student_id}, {"$set": update_data})
        flash('Student updated successfully!', 'success')
        return redirect(url_for('admin.students'))

    return render_template('admin/edit_student.html', student=student)


@admin_bp.route('/students/delete/<student_id>', methods=['POST'])
@admin_required
def delete_student(student_id):
    """Delete a student"""
    mongo.db.students.delete_one({"student_id": student_id})
    flash('Student deleted.', 'info')
    return redirect(url_for('admin.students'))


@admin_bp.route('/chatbot-qa')
@admin_required
def chatbot_qa():
    """Manage chatbot Q&A"""
    qa_list = list(mongo.db.chatbot_qa.find())
    categories = mongo.db.chatbot_qa.distinct("category")
    return render_template('admin/chatbot_qa.html', qa_list=qa_list, categories=categories)


@admin_bp.route('/chatbot-qa/add', methods=['POST'])
@admin_required
def add_qa():
    """Add new Q&A entry"""
    keywords_raw = request.form.get('keywords', '')
    keywords = [k.strip() for k in keywords_raw.split(',') if k.strip()]
    mongo.db.chatbot_qa.insert_one({
        "category": request.form.get('category'),
        "keywords": keywords,
        "question": request.form.get('question'),
        "answer": request.form.get('answer'),
        "priority": int(request.form.get('priority', 1)),
        "active": True
    })
    flash('Q&A entry added!', 'success')
    return redirect(url_for('admin.chatbot_qa'))


@admin_bp.route('/chatbot-qa/toggle/<qa_id>', methods=['POST'])
@admin_required
def toggle_qa(qa_id):
    """Toggle Q&A active/inactive"""
    qa = mongo.db.chatbot_qa.find_one({"_id": ObjectId(qa_id)})
    if qa:
        mongo.db.chatbot_qa.update_one({"_id": ObjectId(qa_id)},
                                        {"$set": {"active": not qa.get('active', True)}})
    return redirect(url_for('admin.chatbot_qa'))


@admin_bp.route('/chatbot-qa/delete/<qa_id>', methods=['POST'])
@admin_required
def delete_qa(qa_id):
    """Delete a Q&A entry"""
    mongo.db.chatbot_qa.delete_one({"_id": ObjectId(qa_id)})
    flash('Q&A entry deleted.', 'info')
    return redirect(url_for('admin.chatbot_qa'))


@admin_bp.route('/notifications')
@admin_required
def notifications():
    """Manage notifications"""
    notifs = list(mongo.db.notifications.find().sort("created_at", -1))
    return render_template('admin/notifications.html', notifications=notifs)


@admin_bp.route('/notifications/send', methods=['POST'])
@admin_required
def send_notification():
    """Send a notification"""
    mongo.db.notifications.insert_one({
        "title": request.form.get('title'),
        "message": request.form.get('message'),
        "target": request.form.get('target', 'all'),
        "target_value": request.form.get('target_value', ''),
        "created_at": datetime.now(),
        "important": request.form.get('important') == 'on'
    })
    flash('Notification sent!', 'success')
    return redirect(url_for('admin.notifications'))


@admin_bp.route('/notifications/delete/<notif_id>', methods=['POST'])
@admin_required
def delete_notification(notif_id):
    mongo.db.notifications.delete_one({"_id": ObjectId(notif_id)})
    flash('Notification deleted.', 'info')
    return redirect(url_for('admin.notifications'))


@admin_bp.route('/events')
@admin_required
def events():
    """Manage events"""
    all_events = list(mongo.db.events.find().sort("date", -1))
    return render_template('admin/events.html', events=all_events)


@admin_bp.route('/events/add', methods=['POST'])
@admin_required
def add_event():
    mongo.db.events.insert_one({
        "title": request.form.get('title'),
        "description": request.form.get('description'),
        "date": request.form.get('date'),
        "time": request.form.get('time'),
        "venue": request.form.get('venue'),
        "category": request.form.get('category', 'general'),
        "registration_link": request.form.get('registration_link', '')
    })
    flash('Event added!', 'success')
    return redirect(url_for('admin.events'))


@admin_bp.route('/events/delete/<event_id>', methods=['POST'])
@admin_required
def delete_event(event_id):
    mongo.db.events.delete_one({"_id": ObjectId(event_id)})
    flash('Event deleted.', 'info')
    return redirect(url_for('admin.events'))


@admin_bp.route('/timetable')
@admin_required
def timetable():
    """Manage timetables"""
    timetables = list(mongo.db.timetable.find())
    return render_template('admin/timetable.html', timetables=timetables)


@admin_bp.route('/timetable/update/<class_name>', methods=['POST'])
@admin_required
def update_timetable(class_name):
    """Update timetable for a class - updates all students in that class"""
    # This updates the timetable collection and all students in that class see it
    day = request.form.get('day')
    schedule_json = request.form.get('schedule_json', '[]')
    try:
        schedule_data = json.loads(schedule_json)
        mongo.db.timetable.update_one(
            {"class": class_name},
            {"$set": {f"schedule.{day}": schedule_data}},
            upsert=True
        )
        flash(f'Timetable updated for {class_name} - {day}!', 'success')
    except:
        flash('Invalid data format.', 'danger')
    return redirect(url_for('admin.timetable'))


@admin_bp.route('/student/<student_id>/results/add', methods=['POST'])
@admin_required
def add_result(student_id):
    """Add result for a student"""
    subjects_json = request.form.get('subjects_json', '[]')
    try:
        subjects = json.loads(subjects_json)
        result_entry = {
            "year": int(request.form.get('year', 1)),
            "semester": int(request.form.get('semester', 1)),
            "subjects": subjects,
            "sgpa": float(request.form.get('sgpa', 0))
        }
        mongo.db.students.update_one(
            {"student_id": student_id},
            {"$push": {"results": result_entry}}
        )
        # Recalculate CGPA
        student = mongo.db.students.find_one({"student_id": student_id})
        from models import calculate_cgpa
        new_cgpa = calculate_cgpa(student.get('results', []))
        mongo.db.students.update_one({"student_id": student_id}, {"$set": {"cgpa": new_cgpa}})
        flash('Result added and CGPA updated!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.edit_student', student_id=student_id))



   # ─────────────────────────────────────────────
# EDIT CHATBOT Q&A
# ─────────────────────────────────────────────

@admin_bp.route('/edit_chatbot/<id>', methods=['GET', 'POST'])
@admin_required
def edit_chatbot(id):
    qa = mongo.db.chatbot_qa.find_one({"_id": ObjectId(id)})

    if request.method == 'POST':
        mongo.db.chatbot_qa.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "category": request.form['category'],
                    "question": request.form['question'],
                    "answer": request.form['answer'],
                    "keywords": [k.strip() for k in request.form['keywords'].split(',')],
                    "priority": int(request.form['priority'])
                }
            }
        )
        flash('Q&A updated successfully!', 'success')
        return redirect(url_for('admin.chatbot_qa'))

    return render_template('admin/edit_chatbot.html', qa=qa)

    # ─────────────────────────────────────────────
# FACULTY MANAGEMENT
# ─────────────────────────────────────────────

@admin_bp.route('/faculty')
@admin_required
def faculty():
    faculty_list = list(mongo.db.faculty.find())
    return render_template('admin/faculty.html', faculty_list=faculty_list)


@admin_bp.route('/faculty/add', methods=['POST'])
@admin_required
def add_faculty():
    mongo.db.faculty.insert_one({
        "name": request.form.get('name'),
        "department": request.form.get('department'),
        "designation": request.form.get('designation'),
        "email": request.form.get('email'),
        "phone": request.form.get('phone')
    })
    flash("Faculty added successfully!", "success")
    return redirect(url_for('admin.faculty'))


@admin_bp.route('/faculty/edit/<id>', methods=['GET', 'POST'])
@admin_required
def edit_faculty(id):
    faculty = mongo.db.faculty.find_one({"_id": ObjectId(id)})

    if request.method == 'POST':
        mongo.db.faculty.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "name": request.form.get('name'),
                    "department": request.form.get('department'),
                    "designation": request.form.get('designation'),
                    "email": request.form.get('email'),
                    "phone": request.form.get('phone')
                }
            }
        )
        flash("Faculty updated!", "success")
        return redirect(url_for('admin.faculty'))

    return render_template('admin/edit_faculty.html', faculty=faculty)


@admin_bp.route('/faculty/delete/<id>', methods=['POST'])
@admin_required
def delete_faculty(id):
    mongo.db.faculty.delete_one({"_id": ObjectId(id)})
    flash("Faculty deleted!", "info")
    return redirect(url_for('admin.faculty'))

@admin_bp.route('/attendance/<student_id>', methods=['GET', 'POST'])
@admin_required
def edit_attendance(student_id):

    student = mongo.db.students.find_one({"student_id": student_id})

    if request.method == 'POST':
        mongo.db.students.update_one(
            {"student_id": student_id},
            {
                "$set": {
                    "attendance": {
                        "total_classes": int(request.form.get('total_classes', 0)),
                        "attended": int(request.form.get('attended', 0))
                    }
                }
            }
        )
        flash("Attendance updated!", "success")
        return redirect(url_for('admin.students'))

    return render_template('admin/edit_attendance.html', student=student)