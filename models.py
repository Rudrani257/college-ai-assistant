# models.py - MongoDB Schema Design and Helper Functions
# Collections: students, admins, chatbot_qa, courses, notifications, timetable, events, placements, faculty, alumni

from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from bson import ObjectId
from datetime import datetime

mongo = PyMongo()
bcrypt = Bcrypt()


# ─────────────────────────────────────────────
# SCHEMA DEFINITIONS (for reference/seeding)
# ─────────────────────────────────────────────

STUDENT_SCHEMA = {
    "student_id": "STU001",             # Unique login ID
    "password": "hashed_password",
    "name": "John Doe",
    "roll_number": "20BCE001",
    "branch": "Computer Engineering",
    "year": 3,
    "semester": 5,
    "email": "john@college.edu",
    "phone": "9876543210",
    "profile_pic": "",
    "father_name": "Richard Doe",
    "address": "Nagpur, MH",
    "dob": "2002-05-10",
    "cgpa": 8.5,
    "attendance": {                     # Subject-wise attendance %
        "Data Structures": 85,
        "DBMS": 90,
        "OS": 78
    },
    "results": [                        # Year-wise results
        {
            "year": 1, "semester": 1,
            "subjects": [
                {"name": "Engineering Maths", "credits": 4, "marks": 78, "grade": "B+"},
                {"name": "Physics", "credits": 3, "marks": 85, "grade": "A"}
            ],
            "sgpa": 8.2
        }
    ],
    "internal_marks": {                 # Current semester internal marks
        "Data Structures": {"IA1": 18, "IA2": 19, "assignment": 10},
    },
    "timetable_class": "CE-B",          # Links to timetable collection
    "exam_schedule": [
        {"subject": "DBMS", "date": "2024-11-20", "time": "10:00 AM", "room": "A101"}
    ],
    "projects": [
        {"title": "College AI Assistant", "year": 3, "tech": "Python, Flask, MongoDB", "guide": "Dr. Smith"}
    ],
    "internships": [
        {"company": "TCS", "role": "ML Intern", "duration": "2 months", "year": 2023}
    ],
    "activities": [
        {"name": "Hackathon 2023", "position": "Winner", "level": "National"}
    ],
    "fee_status": [
        {"semester": 5, "amount": 45000, "paid": True, "date": "2023-07-15"}
    ],
    "notifications": []                 # Notification IDs
}

ADMIN_SCHEMA = {
    "admin_id": "ADMIN001",
    "password": "hashed",
    "name": "Dr. Principal",
    "role": "super_admin",             # super_admin / dept_admin
    "department": "All"
}

CHATBOT_QA_SCHEMA = {
    "category": "admissions",
    "keywords": ["admission", "apply", "how to join", "enrollment"],
    "question": "How to apply for admission?",
    "answer": "Visit our website and fill the online application form...",
    "priority": 1,
    "active": True
}

COURSE_SCHEMA = {
    "name": "B.Tech Computer Engineering",
    "code": "BCE",
    "duration": "4 Years",
    "intake": 60,
    "fee_per_year": 85000,
    "eligibility": "12th PCM with 60% marks",
    "description": "..."
}

NOTIFICATION_SCHEMA = {
    "title": "Fee Payment Deadline",
    "message": "Last date for fee payment is 31st July",
    "target": "all",                   # all / branch / individual student_id
    "target_value": "",
    "created_at": "datetime",
    "important": True
}

TIMETABLE_SCHEMA = {
    "class": "CE-B",
    "semester": 5,
    "schedule": {
        "Monday": [
            {"time": "9:00-10:00", "subject": "Data Structures", "faculty": "Dr. Sharma", "room": "A101"},
        ],
        "Tuesday": []
    }
}

EVENT_SCHEMA = {
    "title": "Tech Fest 2024",
    "description": "Annual technical festival",
    "date": "2024-02-15",
    "time": "9:00 AM",
    "venue": "Main Auditorium",
    "category": "technical",          # technical / cultural / sports / academic
    "registration_link": ""
}

PLACEMENT_SCHEMA = {
    "branch": "Computer Engineering",
    "year": 2023,
    "total_placed": 55,
    "total_students": 60,
    "highest_package": "44 LPA",
    "average_package": "8.5 LPA",
    "top_recruiters": ["TCS", "Infosys", "Google", "Microsoft"],
    "company_wise": [
        {"company": "Google", "package": "44 LPA", "students": 2}
    ]
}

FACULTY_SCHEMA = {
    "name": "Dr. Ramesh Sharma",
    "department": "Computer Engineering",
    "designation": "Professor & HOD",
    "qualification": "Ph.D. Computer Science",
    "experience": "20 years",
    "email": "sharma@college.edu",
    "specialization": "Machine Learning, AI",
    "publications": 25
}

ALUMNI_SCHEMA = {
    "name": "Rahul Gupta",
    "batch": "2018-2022",
    "branch": "Computer Engineering",
    "company": "Google",
    "role": "Senior Software Engineer",
    "location": "Bangalore",
    "linkedin": ""
}


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def get_student_by_id(student_id):
    """Fetch student by their login ID"""
    return mongo.db.students.find_one({"student_id": student_id})

def get_admin_by_id(admin_id):
    """Fetch admin by their login ID"""
    return mongo.db.admins.find_one({"admin_id": admin_id})

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password(hashed, plain):
    """Verify password against hash"""
    return bcrypt.check_password_hash(hashed, plain)

def get_all_chatbot_qa():
    """Fetch all active chatbot Q&A entries"""
    return list(mongo.db.chatbot_qa.find({"active": True}))

def get_notifications_for_student(student):
    """Get notifications for a specific student (global + branch-specific + personal)"""
    return list(mongo.db.notifications.find({
        "$or": [
            {"target": "all"},
            {"target": "branch", "target_value": student.get("branch", "")},
            {"target": "individual", "target_value": student.get("student_id", "")}
        ]
    }).sort("created_at", -1).limit(20))

def calculate_cgpa(results):
    """Calculate CGPA from results array"""
    if not results:
        return 0.0
    total_sgpa = sum(r.get("sgpa", 0) for r in results)
    return round(total_sgpa / len(results), 2)


# ─────────────────────────────────────────────
# DATABASE SEED FUNCTION (run once to populate)
# ─────────────────────────────────────────────

def seed_database(app):
    """Seed initial data into MongoDB - run once"""
    with app.app_context():
        # Seed Admin
        if not mongo.db.admins.find_one({"admin_id": "ADMIN001"}):
            mongo.db.admins.insert_one({
                "admin_id": "ADMIN001",
                "password": hash_password("admin123"),
                "name": "Dr. R.K. Sharma",
                "role": "super_admin",
                "department": "All"
            })
            print("✅ Admin seeded")

        # Seed Sample Student
        if not mongo.db.students.find_one({"student_id": "STU001"}):
            mongo.db.students.insert_one({
                "student_id": "STU001",
                "password": hash_password("student123"),
                "name": "Arjun Mehta",
                "roll_number": "21BCE001",
                "branch": "Computer Engineering",
                "year": 3,
                "semester": 5,
                "email": "arjun@college.edu",
                "phone": "9876543210",
                "father_name": "Vikram Mehta",
                "address": "Nagpur, MH",
                "dob": "2003-04-15",
                "cgpa": 8.7,
                "timetable_class": "CE-A",
                "attendance": {
                    "Data Structures": 88,
                    "Database Management": 92,
                    "Operating Systems": 80,
                    "Computer Networks": 85,
                    "Software Engineering": 90
                },
                "results": [
                    {
                        "year": 1, "semester": 1,
                        "subjects": [
                            {"name": "Engineering Mathematics I", "credits": 4, "marks": 78, "grade": "B+"},
                            {"name": "Engineering Physics", "credits": 3, "marks": 82, "grade": "A"},
                            {"name": "Basic Electronics", "credits": 3, "marks": 75, "grade": "B+"},
                            {"name": "Programming in C", "credits": 4, "marks": 90, "grade": "O"}
                        ],
                        "sgpa": 8.4
                    },
                    {
                        "year": 1, "semester": 2,
                        "subjects": [
                            {"name": "Engineering Mathematics II", "credits": 4, "marks": 80, "grade": "A"},
                            {"name": "Data Structures", "credits": 4, "marks": 88, "grade": "A+"},
                            {"name": "Digital Electronics", "credits": 3, "marks": 76, "grade": "B+"},
                            {"name": "OOP with Java", "credits": 4, "marks": 85, "grade": "A"}
                        ],
                        "sgpa": 8.6
                    }
                ],
                "internal_marks": {
                    "Data Structures": {"IA1": 19, "IA2": 20, "assignment": 10},
                    "Database Management": {"IA1": 18, "IA2": 19, "assignment": 9},
                    "Operating Systems": {"IA1": 17, "IA2": 18, "assignment": 10},
                    "Computer Networks": {"IA1": 16, "IA2": 18, "assignment": 8},
                    "Software Engineering": {"IA1": 18, "IA2": 17, "assignment": 9}
                },
                "exam_schedule": [
                    {"subject": "Data Structures", "date": "2024-11-18", "time": "10:00 AM", "room": "A101"},
                    {"subject": "Database Management", "date": "2024-11-20", "time": "10:00 AM", "room": "B202"},
                    {"subject": "Operating Systems", "date": "2024-11-22", "time": "2:00 PM", "room": "A101"}
                ],
                "projects": [
                    {"title": "College AI Assistant", "year": 3, "tech": "Python, Flask, MongoDB", "guide": "Dr. Sharma", "status": "Ongoing"}
                ],
                "internships": [
                    {"company": "Infosys", "role": "Python Developer Intern", "duration": "2 months", "year": 2023, "certificate": ""}
                ],
                "activities": [
                    {"name": "Smart India Hackathon 2023", "position": "Finalist", "level": "National"},
                    {"name": "College Cricket Team", "position": "Captain", "level": "Inter-College"}
                ],
                "fee_status": [
                    {"semester": 5, "amount": 85000, "paid": True, "date": "2023-07-10"},
                    {"semester": 4, "amount": 85000, "paid": True, "date": "2023-01-08"}
                ]
            })
            print("✅ Sample student seeded")

        # Seed Chatbot Q&A
        if mongo.db.chatbot_qa.count_documents({}) == 0:
            chatbot_data = [
                {
                    "category": "courses",
                    "keywords": ["courses", "programs", "branches", "departments", "what courses", "available courses"],
                    "question": "What courses are offered?",
                    "answer": "🎓 <b>Courses Offered at BCOE:</b><br><br><b>B.Tech Programs (4 Years):</b><br>• Computer Engineering (CE) - 60 seats<br>• Information Technology (IT) - 60 seats<br>• Electronics & Communication (ECE) - 60 seats<br>• Mechanical Engineering (ME) - 60 seats<br>• Civil Engineering (Civil) - 60 seats<br>• Electrical Engineering (EE) - 60 seats<br><br><b>M.Tech Programs (2 Years):</b><br>• Computer Science & Engineering<br>• VLSI Design<br>• Structural Engineering<br><br><b>MBA Program (2 Years)</b><br><br>All programs are AICTE approved and NBA accredited.",
                    "priority": 1, "active": True
                },
                {
                    "category": "fees",
                    "keywords": ["fee", "fees", "cost", "tuition", "fee structure", "how much", "charges"],
                    "question": "What is the fee structure?",
                    "answer": "💰 <b>Fee Structure (Per Year):</b><br><br><b>B.Tech Programs:</b><br>• Computer Engineering: ₹85,000/year<br>• Information Technology: ₹85,000/year<br>• Electronics & Communication: ₹80,000/year<br>• Mechanical Engineering: ₹75,000/year<br>• Civil Engineering: ₹75,000/year<br>• Electrical Engineering: ₹78,000/year<br><br><b>M.Tech Programs:</b><br>• All branches: ₹65,000/year<br><br><b>Additional Fees:</b><br>• Development Fund: ₹10,000/year<br>• Examination Fee: ₹3,500/semester<br>• Library Fee: ₹2,000/year<br><br>📌 Fees subject to revision. Scholarships available for eligible students.",
                    "priority": 1, "active": True
                },
                {
                    "category": "admissions",
                    "keywords": ["admission", "apply", "how to join", "enrollment", "application", "join", "get admission"],
                    "question": "What is the admission procedure?",
                    "answer": "📋 <b>Admission Procedure:</b><br><br><b>For B.Tech:</b><br>1️⃣ Appear in MHT-CET or JEE Main exam<br>2️⃣ Register on Maharashtra CET Cell website<br>3️⃣ Participate in CAP (Centralized Admission Process)<br>4️⃣ Fill college preference during CAP rounds<br>5️⃣ Report to college after allotment with original documents<br><br><b>Required Documents:</b><br>• 12th Marksheet & Certificate<br>• CET/JEE Scorecard<br>• Caste Certificate (if applicable)<br>• Domicile Certificate<br>• Aadhar Card, Passport Photos<br><br><b>For Direct Second Year (DSE):</b><br>Diploma holders can apply directly to 2nd year via MHCET DSE counseling.",
                    "priority": 1, "active": True
                },
                {
                    "category": "eligibility",
                    "keywords": ["eligibility", "qualification", "marks required", "cutoff", "minimum marks", "criteria", "who can apply"],
                    "question": "What is the eligibility criteria?",
                    "answer": "✅ <b>Eligibility Criteria:</b><br><br><b>B.Tech Programs:</b><br>• 12th (HSC) with Physics, Chemistry, Mathematics<br>• Minimum 45% aggregate (40% for reserved categories)<br>• Valid MHT-CET / JEE Main score<br>• No age restriction<br><br><b>M.Tech Programs:</b><br>• B.Tech/B.E. in relevant branch<br>• Minimum 55% aggregate<br>• Valid GATE score preferred<br><br><b>MBA Program:</b><br>• Any Bachelor's degree (min. 50%)<br>• Valid MAH-MBA-CET / CAT / MAT score",
                    "priority": 1, "active": True
                },
                {
                    "category": "placements",
                    "keywords": ["placement", "placements", "salary", "package", "job", "campus placement", "companies", "lpa", "highest package"],
                    "question": "What are the placement statistics?",
                    "answer": "🏆 <b>Placement Statistics 2023:</b><br><br><b>Overall:</b><br>• Total Students Placed: 89%<br>• Highest Package: 44 LPA (Google)<br>• Average Package: 8.2 LPA<br><br><b>Branch-wise (Highest / Average):</b><br>• Computer Engineering: 44 LPA / 10.5 LPA<br>• IT: 36 LPA / 9.8 LPA<br>• ECE: 28 LPA / 7.2 LPA<br>• Mechanical: 18 LPA / 5.5 LPA<br>• Civil: 12 LPA / 4.8 LPA<br><br><b>Top Recruiters:</b><br>Google, Microsoft, Amazon, TCS, Infosys, Wipro, Accenture, L&T, Capgemini, IBM<br><br>📈 Placement Cell: placement@rknec.edu",
                    "priority": 1, "active": True
                },
                {
                    "category": "faculty",
                    "keywords": ["faculty", "professor", "teacher", "staff", "hod", "department head", "teaching"],
                    "question": "Tell me about faculty information",
                    "answer": "👨‍🏫 <b>Faculty Information:</b><br><br><b>Department of Computer Engineering:</b><br>• Dr. R.K. Sharma – HOD, PhD (AI/ML), 20 yrs exp<br>• Dr. Priya Desai – Professor, PhD (Networks)<br>• Prof. Ankit Jain – Asst. Professor, M.Tech<br><br><b>Department of IT:</b><br>• Dr. Suresh Patil – HOD, PhD (Data Science)<br>• Prof. Neha Singh – Asst. Professor, M.Tech<br><br><b>Total Faculty:</b> 180+ qualified faculty members<br>• PhD Holders: 45%<br>• Industry Experience: 30+ faculty members<br><br>📧 Contact respective department for specific faculty details.",
                    "priority": 1, "active": True
                },
                {
                    "category": "events",
                    "keywords": ["events", "fest", "festival", "upcoming", "cultural", "technical", "activities", "college events"],
                    "question": "What are the upcoming events?",
                    "answer": "🎉 <b>Upcoming Events:</b><br><br>📅 <b>TechNova 2026</b> (Tech Fest) – Feb 15-17, 2026<br>• Hackathon, Coding Contest, Robotics<br>• Prize Pool: ₹5 Lakhs<br><br>🎭 <b>Resonance 2026</b> (Cultural Fest) – Feb 22-24, 2026<br>• Dance, Music, Drama, Fashion Show<br><br>🏏 <b>Interbranch Sports Tournament</b> – March 5-10, 2026<br>• Cricket, Football, Basketball, Table Tennis<br><br>🎓 <b>Annual Convocation</b> – April 20, 2026<br><br>📌 Register on college ERP portal or contact Student Council.",
                    "priority": 1, "active": True
                },
                {
                    "category": "calendar",
                    "keywords": ["academic calendar", "calendar", "schedule", "academic year", "holidays", "exam dates", "semester dates"],
                    "question": "What is the academic calendar?",
                    "answer": "📅 <b>Academic Calendar 2025-26:</b><br><br><b>Odd Semester (June – November):</b><br>• Classes Begin: June 12, 2025<br>• Internal Assessment I: August 14-18, 2025<br>• Internal Assessment II: September 18-22, 2025<br>• Diwali Break: November 10-17, 2026<br>• End Semester Exam: November 20 – December 10, 2023<br><br><b>Even Semester (January – May):</b><br>• Classes Begin: January 8, 2026<br>• Internal Assessment I: February 19-23, 2026<br>• Internal Assessment II: March 25-29, 202<br>• End Semester Exam: April 22 – May 12, 2026<br>• Summer Vacation: May 13 – June 10, 2026",
                    "priority": 1, "active": True
                },
                {
                    "category": "hostel",
                    "keywords": ["hostel", "accommodation", "stay", "dormitory", "pg", "residence", "room", "boarding"],
                    "question": "What are the hostel facilities?",
                    "answer": "🏠 <b>Hostel Facilities:</b><br><br><b>Boys Hostel:</b><br>• Capacity: 400 students<br>• Rooms: Single, Double, Triple sharing<br>• Fee: ₹50,000 – ₹80,000/year (room + food)<br><br><b>Girls Hostel:</b><br>• Capacity: 200 students<br>• 24/7 security with CCTV<br>• Fee: ₹55,000 – ₹85,000/year<br><br><b>Amenities:</b><br>✅ 24/7 Wi-Fi Internet<br>✅ Mess with nutritious food (3 meals/day)<br>✅ RO Water, Laundry<br>✅ Indoor Games Room<br>✅ Medical First Aid<br>✅ Warden & Security 24/7<br><br>📞 Hostel Office: +91-712-2806401",
                    "priority": 1, "active": True
                },
                {
                    "category": "scholarships",
                    "keywords": ["scholarship", "financial aid", "fee waiver", "free", "scholarship details", "merit scholarship"],
                    "question": "What scholarships are available?",
                    "answer": "🎓 <b>Scholarships Available:</b><br><br><b>Government Scholarships:</b><br>• EBC Scholarship (income < 8L): Full tuition waiver<br>• OBC/SC/ST Scholarship: Government schemes<br>• Dr. Panjabrao Deshmukh Scholarship (Agri background)<br><br><b>College Merit Scholarships:</b><br>• MHT-CET Top 10 Rank: 50% fee waiver<br>• 1st year topper: ₹10,000 cash prize<br>• Sports Excellence Scholarship: ₹15,000/year<br><br><b>External Scholarships:</b><br>• Wipro, TCS, Infosys CSR Scholarships<br>• Inspire Scholarship (MHRD)<br><br>📋 Apply at scholarship.maharashtra.gov.in<br>📧 scholarship@bcoe.edu",
                    "priority": 1, "active": True
                },
                {
                    "category": "sports",
                    "keywords": ["sports", "gym", "ground", "cricket", "football", "basketball", "facilities", "playground"],
                    "question": "What are the sports facilities?",
                    "answer": "⚽ <b>Sports Facilities:</b><br><br><b>Outdoor:</b><br>🏏 Cricket Ground (full-size)<br>⚽ Football Ground<br>🏐 Volleyball Court (2)<br>🎾 Tennis Court (2)<br>🏀 Basketball Court (2)<br>🏃 400m Athletics Track<br><br><b>Indoor:</b><br>🏸 Badminton Courts (4)<br>🏓 Table Tennis (6 tables)<br>♟️ Chess & Carrom room<br>🥊 Boxing & Wrestling area<br><br><b>Gymnasium:</b><br>• Fully equipped with modern machines<br>• Separate for Boys & Girls<br>• Timing: 6 AM – 9 PM<br><br>🏅 College teams regularly participate in University & National level competitions.",
                    "priority": 1, "active": True
                },
                {
                    "category": "campus",
                    "keywords": ["campus", "library", "lab", "canteen", "infrastructure", "facilities", "amenities", "wifi"],
                    "question": "What are the campus facilities?",
                    "answer": "🏛️ <b>Campus Facilities:</b><br><br>📚 <b>Central Library:</b> 50,000+ books, e-journal access, 24/7 digital library<br><br>💻 <b>Laboratories:</b><br>• 20+ state-of-art computer labs<br>• Advanced research labs (AI/ML, IoT, Robotics, VLSI)<br><br>🌐 <b>Internet:</b> 1 Gbps campus-wide Wi-Fi<br><br>🍽️ <b>Canteen:</b> Multiple food outlets, hygienic food<br><br>🏥 <b>Medical:</b> Full-time doctor, dispensary on campus<br><br>🚌 <b>Transport:</b> College bus service covering 15+ routes<br><br>🏦 <b>Bank & ATM:</b> On-campus bank branch<br><br>💡 <b>Power:</b> 24/7 power backup (100 KVA generator)",
                    "priority": 1, "active": True
                },
                {
                    "category": "contact",
                    "keywords": ["contact", "phone", "email", "address", "location", "how to reach", "call"],
                    "question": "What are the contact details?",
                    "answer": "📞 <b>Contact Details:</b><br><br>🏛️ <b>Bharat College of Engg </b><br>Badlapur,<br>Mumbai – 440013, Maharashtra<br><br>📞 Phone: +91-712-2806400 / 2806401<br>📧 Email: info@bcoe.edu<br>🌐 Website: www.bcoe.edu<br><br><b>Department Contacts:</b><br>• Admission: admission@bcoe.edu<br>• Examination: exam@bcoe.edu<br>• Placement: placement@bcoe.edu<br>• Hostel: hostel@bcoe.edu<br><br>⏰ Office Hours: Mon-Sat, 9 AM – 5 PM<br><br>📍 <a href='https://maps.google.com' target='_blank'>View on Google Maps</a>",
                    "priority": 1, "active": True
                },
                {
                    "category": "anti_ragging",
                    "keywords": ["ragging", "anti ragging", "bullying", "harassment", "complaint", "iqac", "grievance"],
                    "question": "What is the anti-ragging policy?",
                    "answer": "🛡️ <b>Anti-Ragging Policy:</b><br><br>BCOE has ZERO TOLERANCE for ragging as per UGC Regulations 2009 and Supreme Court directives.<br><br><b>Prohibited Activities:</b><br>• Physical/mental harassment of freshers<br>• Eve teasing, verbal abuse, forced activities<br>• Online bullying or intimidation<br><br><b>Punishment:</b><br>• Immediate suspension/expulsion<br>• FIR under IPC sections<br>• Fine up to ₹25,000<br><br><b>Report Ragging:</b><br>📞 National Helpline: 1800-180-5522 (24/7 Free)<br>📞 College Anti-Ragging: +91-712-2806405<br>📧 antiragging@bcoe.edu<br>🌐 www.antiragging.in<br><br>All complaints are kept CONFIDENTIAL.",
                    "priority": 1, "active": True
                },
                {
                    "category": "ranking",
                    "keywords": ["naac", "nirf", "ranking", "accreditation", "rating", "nba", "grade", "rank"],
                    "question": "What are the NAAC/NIRF rankings?",
                    "answer": "🏆 <b>Rankings & Accreditations:</b><br><br><b>NAAC Accreditation:</b><br>• Grade: A+ (CGPA: 3.52/4.0)<br>• Valid: 2023–2028<br><br><b>NIRF Ranking 2023:</b><br>• Engineering Category: Rank 151-200<br>• Overall Category: Rank 201-250<br><br><b>NBA Accreditation:</b><br>• Accredited Programs: CE, IT, ECE, ME, Civil, EE<br><br><b>Other Recognitions:</b><br>• ISO 9001:2015 Certified<br>• Autonomous Status by UGC<br>• Affiliated to Mumbai University<br>• AICTE Approved<br><br>🥇 Consistently ranked among Top 5 Engineering colleges in Maharashtra region.",
                    "priority": 1, "active": True
                },
                {
                    "category": "alumni",
                    "keywords": ["alumni", "alumnus", "pass out", "graduates", "old students", "notable alumni"],
                    "question": "Tell me about notable alumni",
                    "answer": "🌟 <b>Notable Alumni:</b><br><br>• <b>Rahul Gupta (2018)</b> – Senior SWE at Google, Mountain View<br>• <b>Priya Sharma (2019)</b> – ML Engineer at Microsoft<br>• <b>Amit Deshmukh (2015)</b> – Co-founder at TechStartup (₹50Cr valuation)<br>• <b>Sneha Patil (2017)</b> – IAS Officer (AIR 45)<br>• <b>Rohan Joshi (2016)</b> – PhD from IIT Bombay, Now Professor<br><br><b>Alumni Association:</b><br>📧 alumni@rknec.edu<br>🌐 alumni.rknec.edu<br><br>Annual Alumni Meet: Every January<br>Alumni have donated ₹2 Crore+ to college infrastructure.<br><br>Join our Alumni Network on LinkedIn: BCOE Alumni Network",
                    "priority": 1, "active": True
                },
                {
                    "category": "greeting",
                    "keywords": ["hello", "hi", "hey", "good morning", "good evening", "start", "help", "what can you do"],
                    "question": "Hello / Help",
                    "answer": "👋 <b>Hello! Welcome to BCOE Assistant!</b><br><br>I can help you with information about:<br><br>🎓 Courses & Programs<br>💰 Fee Structure<br>📋 Admission Procedure<br>✅ Eligibility Criteria<br>🏆 Placement Statistics<br>👨‍🏫 Faculty Information<br>🎉 Upcoming Events<br>📅 Academic Calendar<br>🏠 Hostel Facilities<br>🎓 Scholarships<br>⚽ Sports Facilities<br>🏛️ Campus Facilities<br>🛡️ Anti-Ragging Policy<br>🏅 NAAC/NIRF Rankings<br>📞 Contact Details<br><br>Just type your question and I'll help you! 😊",
                    "priority": 0, "active": True
                }
            ]
            mongo.db.chatbot_qa.insert_many(chatbot_data)
            print("✅ Chatbot Q&A seeded")

        # Seed Timetable
        if mongo.db.timetable.count_documents({}) == 0:
            mongo.db.timetable.insert_one({
                "class": "CE-A",
                "semester": 5,
                "schedule": {
                    "Monday": [
                        {"time": "9:00-10:00", "subject": "Data Structures", "faculty": "Dr. Sharma", "room": "A101"},
                        {"time": "10:00-11:00", "subject": "Database Management", "faculty": "Dr. Desai", "room": "A101"},
                        {"time": "11:00-11:15", "subject": "Break", "faculty": "", "room": ""},
                        {"time": "11:15-12:15", "subject": "Operating Systems", "faculty": "Prof. Jain", "room": "A101"},
                        {"time": "12:15-1:15", "subject": "Computer Networks", "faculty": "Dr. Patil", "room": "A101"},
                        {"time": "1:15-2:00", "subject": "Lunch Break", "faculty": "", "room": ""},
                        {"time": "2:00-4:00", "subject": "DS Lab", "faculty": "Prof. Singh", "room": "Lab 1"}
                    ],
                    "Tuesday": [
                        {"time": "9:00-10:00", "subject": "Software Engineering", "faculty": "Dr. Mehta", "room": "A101"},
                        {"time": "10:00-11:00", "subject": "Data Structures", "faculty": "Dr. Sharma", "room": "A101"},
                        {"time": "11:15-12:15", "subject": "Database Management", "faculty": "Dr. Desai", "room": "A101"},
                        {"time": "12:15-1:15", "subject": "Operating Systems", "faculty": "Prof. Jain", "room": "A101"},
                        {"time": "2:00-4:00", "subject": "Networks Lab", "faculty": "Dr. Patil", "room": "Lab 2"}
                    ],
                    "Wednesday": [
                        {"time": "9:00-10:00", "subject": "Computer Networks", "faculty": "Dr. Patil", "room": "A101"},
                        {"time": "10:00-11:00", "subject": "Software Engineering", "faculty": "Dr. Mehta", "room": "A101"},
                        {"time": "11:15-12:15", "subject": "Data Structures", "faculty": "Dr. Sharma", "room": "A101"},
                        {"time": "12:15-1:15", "subject": "Database Management", "faculty": "Dr. Desai", "room": "A101"},
                        {"time": "2:00-4:00", "subject": "DBMS Lab", "faculty": "Dr. Desai", "room": "Lab 3"}
                    ],
                    "Thursday": [
                        {"time": "9:00-10:00", "subject": "Operating Systems", "faculty": "Prof. Jain", "room": "A101"},
                        {"time": "10:00-11:00", "subject": "Computer Networks", "faculty": "Dr. Patil", "room": "A101"},
                        {"time": "11:15-12:15", "subject": "Software Engineering", "faculty": "Dr. Mehta", "room": "A101"},
                        {"time": "12:15-1:15", "subject": "Data Structures", "faculty": "Dr. Sharma", "room": "A101"},
                        {"time": "2:00-5:00", "subject": "Mini Project", "faculty": "Guide", "room": "Lab 4"}
                    ],
                    "Friday": [
                        {"time": "9:00-10:00", "subject": "Database Management", "faculty": "Dr. Desai", "room": "A101"},
                        {"time": "10:00-11:00", "subject": "Operating Systems", "faculty": "Prof. Jain", "room": "A101"},
                        {"time": "11:15-12:15", "subject": "Computer Networks", "faculty": "Dr. Patil", "room": "A101"},
                        {"time": "12:15-1:15", "subject": "Software Engineering", "faculty": "Dr. Mehta", "room": "A101"},
                        {"time": "2:00-4:00", "subject": "SE Lab", "faculty": "Dr. Mehta", "room": "Lab 5"}
                    ],
                    "Saturday": [
                        {"time": "9:00-11:00", "subject": "Tutorial / Extra Class", "faculty": "As assigned", "room": "A101"},
                        {"time": "11:15-1:15", "subject": "Library / Sports Hour", "faculty": "", "room": "Library/Ground"}
                    ]
                }
            })
            print("✅ Timetable seeded")

        # Seed Events
        if mongo.db.events.count_documents({}) == 0:
            mongo.db.events.insert_many([
                {
                    "title": "TechNova 2026 – Annual Tech Fest",
                    "description": "Biggest tech fest of the year featuring Hackathon, Coding Contest, Robotics Challenge and more!",
                    "date": "2026-02-15", "time": "9:00 AM",
                    "venue": "Main Campus", "category": "technical",
                    "registration_link": "https://technova.bcoe.edu"
                },
                {
                    "title": "Campus Placement Drive – TCS",
                    "description": "TCS Nextstep recruitment drive for final year students.",
                    "date": "2026-01-25", "time": "8:00 AM",
                    "venue": "Placement Hall", "category": "placement",
                    "registration_link": ""
                },
                {
                    "title": "Resonance 2026 – Cultural Festival",
                    "description": "Annual cultural fest with dance, music, drama and much more!",
                    "date": "2026-02-22", "time": "9:00 AM",
                    "venue": "Amphitheatre", "category": "cultural",
                    "registration_link": ""
                }
            ])
            print("✅ Events seeded")

        # Seed Notifications
        if mongo.db.notifications.count_documents({}) == 0:
            mongo.db.notifications.insert_many([
                {
                    "title": "Fee Payment Deadline",
                    "message": "Last date for Semester 5 fee payment is 31st January 2024. Late fee of ₹100/day will be charged after this date.",
                    "target": "all", "target_value": "",
                    "created_at": datetime.now(), "important": True
                },
                {
                    "title": "Internal Assessment II Schedule",
                    "message": "Internal Assessment II will be conducted from March 18-22, 2024. Timetable uploaded on ERP portal.",
                    "target": "all", "target_value": "",
                    "created_at": datetime.now(), "important": True
                },
                {
                    "title": "Project Submission Deadline",
                    "message": "Final year project report submission deadline: April 5, 2026. Submit to respective project guides.",
                    "target": "branch", "target_value": "Computer Engineering",
                    "created_at": datetime.now(), "important": False
                }
            ])
            print("✅ Notifications seeded")

        print("🎉 Database seeding complete!")