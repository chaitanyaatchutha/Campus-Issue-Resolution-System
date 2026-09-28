from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import secrets;
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
# -----------------------------
# LOAD ML MODEL
# -----------------------------
MODEL = None
VECTORIZER = None

try:
    MODEL = joblib.load("model.pkl")
    VECTORIZER = joblib.load("vectorizer.pkl")

    print("✅ ML Model Loaded Successfully")

except Exception as e:
    print("❌ ML Model Not Loaded:", e)
# -----------------------------
# DATABASE CONNECTION
# -----------------------------

EMAIL = "cirscomplaints@gmail.com"
APP_PASSWORD = "abevctsavbwedxcu"

department_emails = {
    "Electrical": "cirselectrical11@gmail.com",
    "Maintenance": "cirsmaintenance1@gmail.com",
    "CSE": "cirscse@gmail.com",
    "ECE": "cirsece@gmail.com",
    "Cleaning": "cirscleaning@gmail.com",
    "Hostel": "cirshostel@gmail.com",
    "Others": "cirsothers@gmail.com",
    "Library": "cirslibrary@gmail.com"
}

departments = [
    ("electrical", "electrical123", "Electrical"),
    ("maintenance","maintenance123","Maintenance"),
    ("cse","cse123","CSE"),
    ("ece","ece123","ECE"),
    ("cleaning","cleaning123","Cleaning"),
    ("hostel", "hostel123", "Hostel"),
    ("library", "library123", "Library"),
    ("others", "others123", "Others")
]


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("TIDB_HOST"),
        port=int(os.getenv("TIDB_PORT", "4000")),
        user=os.getenv("TIDB_USER"),
        password=os.getenv("TIDB_PASSWORD"),
        database=os.getenv("TIDB_DATABASE", "cirs"),
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )

def send_department_email(student, complaint, department):

    receiver = department_emails.get(
        department,
        department_emails["Others"]
    )

    msg = MIMEMultipart()

    msg["From"] = EMAIL
    msg["To"] = receiver
    msg["Subject"] = f"New Complaint - {department}"

    body = f"""
New Complaint Received

Student : {student}

Department : {department}

Complaint :

{complaint}

Please login to the Campus Complaint System.
"""

    msg.attach(MIMEText(body, "plain"))

    try:

        server = smtplib.SMTP("smtp.gmail.com",587)

        server.starttls()

        server.login(EMAIL,APP_PASSWORD)

        server.send_message(msg)

        server.quit()

        print("Email Sent")

    except Exception as e:

        print(e)

def create_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("USE TIDB_DATABASE")

    # Students table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INT AUTO_INCREMENT PRIMARY KEY,
        fullname VARCHAR(100),
        rollno VARCHAR(30) UNIQUE,
        department VARCHAR(100),
        email VARCHAR(100) UNIQUE,
        phone VARCHAR(15),
        password VARCHAR(255)
    )
    """) 

    # Admins table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins(
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE,
        password VARCHAR(255),
        department VARCHAR(100)
    )
    """)

    # Departments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments(
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE,
        password VARCHAR(255),
        department VARCHAR(100)
        )
    """)

    # Complaints table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints(
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT,
        student_name VARCHAR(100),
        subject VARCHAR(200),
        description TEXT,
        category VARCHAR(100),
        status VARCHAR(30) DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    admins=[
        ("admin","admin123","Admin")
    ]
    # Department admins
    departments = [
        ("electrical", "electrical123", "Electrical"),
        ("maintenance","maintenance123","Maintenance"),
        ("cse","cse123","CSE"),
        ("ece","ece123","ECE"),
        ("cleaning","cleaning123","Cleaning"),
        ("hostel", "hostel123", "Hostel"),
        ("library", "library123", "Library"),
        ("others", "others123", "Others")
    ]

    for username, password, department in departments:
        cursor.execute(
            "SELECT id FROM departments WHERE username=%s",
            (username,)
        )

        if cursor.fetchone() is None:
            cursor.execute(
                """
                INSERT INTO departments(username,password,department)
                VALUES(%s,%s,%s)
                """,
                (
                    username,
                    generate_password_hash(password),
                    department
                )
            )

    for username, password, department in admins:
            cursor.execute(
                "SELECT id FROM admins WHERE username=%s",
                (username,)
            )
    
            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO admins(username,password,department)
                    VALUES(%s,%s,%s)
                    """,
                    (
                        username,
                        generate_password_hash(password),
                        department
                    )
                )
    
    conn.commit()
    conn.close()
    


create_database()


def db():
    return mysql.connector.connect(
        host=os.getenv("TIDB_HOST"),
        port=int(os.getenv("TIDB_PORT", "4000")),
        user=os.getenv("TIDB_USER"),
        password=os.getenv("TIDB_PASSWORD"),
        database=os.getenv("TIDB_DATABASE", "cirs"),
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )


# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# STUDENT LOGIN PAGE
# -----------------------------
@app.route("/studentlogin")
def student_login_page():
    return render_template("studentLogin.html")




# -----------------------------
# STUDENT REGISTER PAGE
# -----------------------------
@app.route("/studentregistration")
def student_registration_page():
    return render_template("student_registration.html")


# -----------------------------
# ADMIN LOGIN PAGE
# -----------------------------
@app.route("/adminlogin")
def admin_login_page():
    return render_template("admin_login.html")

#Department Login Page
@app.route("/departmentlogin")
def department_login_page():
    return render_template("department_login.html")
#Contact Page
@app.route("/contact")
def contact_page():
    return render_template("contact.html")

# -----------------------------
# REGISTER
# -----------------------------
@app.route("/register", methods=["POST"])
def register():

    fullname = request.form["fullname"]
    rollno = request.form["rollno"]
    department = request.form["department"]
    email = request.form["email"]
    phone = request.form["phone"]
    password = request.form["password"]
    confirm_password= request.form["confirm_password"]
    
    conn = db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM students WHERE email=%s OR rollno=%s",
        (email, rollno)
    )

    if cursor.fetchone():
        flash("Student already registered.")
        conn.close()
        return redirect(url_for("student_registration_page"))

    if password!=confirm_password:
        flash("The password and confirm password are different.")
        conn.close()
        return redirect(url_for("student_registration_page"))

    hashed = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO students
        (fullname,rollno,department,email,phone,password)
        VALUES(%s,%s,%s,%s,%s,%s)
    """, (fullname, rollno, department, email, phone, hashed))

    conn.commit()
    conn.close()

    flash("Registration Successful. Please login.")
    return redirect(url_for("student_login_page"))


# -----------------------------
# STUDENT LOGIN
# -----------------------------
@app.route("/login", methods=["POST"])
def login():

    email = request.form["studentid"]
    password = request.form["password"]

    conn = db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM students WHERE email=%s",
        (email,)
    )

    student = cursor.fetchone()

    conn.close()

    if student and check_password_hash(student["password"], password):

        session["student_id"] = student["id"]
        session["student_name"] = student["fullname"]

        return redirect(url_for("student_dashboard"))

    flash("Invalid Email or Password")
    return redirect(url_for("student_login_page"))


# -----------------------------
# ADMIN LOGIN
# -----------------------------
@app.route("/admin_login", methods=["POST"])
def admin_login():

    username = request.form["username"]
    password = request.form["password"]

    conn = db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM admins WHERE username=%s",
        (username,)
    )

    admin = cursor.fetchone()

    conn.close()

    if admin and check_password_hash(admin["password"], password):

        session["admin"] = admin["username"]
        session["department"] = admin["department"]

        return redirect(url_for("admin_dashboard"))

    flash("Invalid Admin Login")
    return redirect(url_for("admin_login_page"))

#Department Login
@app.route("/department_login", methods=["POST"])
def department_login():

    username = request.form["username"]
    password = request.form["password"]

    conn = db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM departments WHERE username=%s",
        (username,)
    )

    admin = cursor.fetchone()

    conn.close()

    if admin and check_password_hash(admin["password"], password):

        session["admin"] = admin["username"]
        session["department"] = admin["department"]

        return redirect(url_for("department_dashboard"))

    flash("Invalid Department Login")
    return redirect(url_for("department_login_page"))

# -----------------------------
# STUDENT DASHBOARD
# -----------------------------
@app.route("/student_dashboard")
def student_dashboard():

    if "student_id" not in session:
        return redirect(url_for("student_login_page"))

    return render_template(
        "student_dashboard.html",
        name=session["student_name"]
    )


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
@app.route("/admin_dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect(url_for("admin_login_page"))

    conn = db()
    cursor = conn.cursor(dictionary=True)

    # All complaints
    cursor.execute("""
        SELECT id, student_name, category, status, created_at
        FROM complaints
        ORDER BY created_at DESC
    """)
    complaints = cursor.fetchall()

    # Dashboard statistics
    cursor.execute("SELECT COUNT(*) AS total FROM complaints")
    total = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS pending
        FROM complaints
        WHERE status='Pending'
    """)
    pending = cursor.fetchone()["pending"]

    cursor.execute("""
        SELECT COUNT(*) AS progress
        FROM complaints
        WHERE status='In Progress'
    """)
    progress = cursor.fetchone()["progress"]

    cursor.execute("""
        SELECT COUNT(*) AS resolved
        FROM complaints
        WHERE status='Resolved'
    """)
    resolved = cursor.fetchone()["resolved"]

    cursor.execute("""
        SELECT COUNT(*) AS rejected
        FROM complaints
        WHERE status='Rejected'
    """)
    rejected = cursor.fetchone()["rejected"]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        complaints=complaints,
        total=total,
        department=session["department"],
        pending=pending,
        progress=progress,
        resolved=resolved,
        rejected=rejected
    )

# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
@app.route("/department_dashboard")
def department_dashboard():

    if "admin" not in session:
        return redirect(url_for("department_login_page"))

    conn = db()
    cursor = conn.cursor(dictionary=True)

    # All complaints
    cursor.execute("SELECT * FROM complaints WHERE category=%s ORDER BY created_at DESC",(session["department"],))
    complaints = cursor.fetchall()

    # Dashboard statistics
    cursor.execute("SELECT COUNT(*) AS total FROM complaints WHERE category=%s",(session["department"],))
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS pending FROM complaints WHERE status='Pending' AND category=%s",(session["department"],))
    pending = cursor.fetchone()["pending"]

    cursor.execute("SELECT COUNT(*) AS progress FROM complaints WHERE status='In Progress' AND category=%s",(session["department"],))
    progress = cursor.fetchone()["progress"]

    cursor.execute("SELECT COUNT(*) AS resolved FROM complaints WHERE status='Resolved' AND category=%s",(session["department"],))
    resolved = cursor.fetchone()["resolved"]

    cursor.execute("SELECT COUNT(*) AS rejected FROM complaints WHERE status='Rejected' AND category=%s",(session["department"],))
    rejected = cursor.fetchone()["rejected"]

    conn.close()

    return render_template(
        "department_dashboard.html",
        complaints=complaints,
        total=total,
        department=session["department"],
        pending=pending,
        progress=progress,
        resolved=resolved,
        rejected=rejected
    )

# -----------------------------
# UPDATE COMPLAINT STATUS
# -----------------------------
@app.route("/update_status/<int:id>", methods=["POST"])
def update_status(id):

    if "admin" not in session:
        return redirect(url_for("admin_login_page"))

    status = request.form["status"]

    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE complaints
        SET status=%s
        WHERE id=%s
    """, (status, id))

    conn.commit()
    conn.close()

    flash("Complaint status updated successfully.")

    return redirect(url_for("admin_dashboard"))

# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))

@app.route("/new_complaint")
def new_complaint():

    if "student_id" not in session:
        return redirect(url_for("student_login_page"))

    return render_template("new_complaint.html")

@app.route("/submit_complaint", methods=["POST"])
def submit_complaint():

    if "student_id" not in session:
        return redirect(url_for("student_login_page"))
    
    description = request.form["description"]

    # Default category
    category = "General"

    # Predict category if model exists
    if MODEL and VECTORIZER:
        try:
            x = VECTORIZER.transform([description])
            category = str(MODEL.predict(x)[0]).strip()
        except Exception as e:
            print(e)

    try:
        conn = db()
    except mysql.connector.Error as e:
        print(e)
    cursor = conn.cursor()



    cursor.execute("""
        INSERT INTO complaints
        (student_id,student_name,description,category)
        VALUES(%s,%s,%s,%s)
    """,(
        session["student_id"],
        session["student_name"],
        description,
        category
    ))

    conn.commit()
    send_department_email(
        session["student_name"],
        description,
        category
    )
    conn.close()

    flash("Complaint Submitted Successfully")

    return redirect(url_for("student_dashboard"))

@app.route("/complaint_status")
def complaint_status():

    if "student_id" not in session:
        return redirect(url_for("student_login_page"))

    conn = db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM complaints
        WHERE student_id=%s
        ORDER BY id DESC
    """,(session["student_id"],))

    complaints = cursor.fetchall()

    conn.close()

    return render_template(
        "complaint_status.html",
        complaints=complaints
    )

@app.route("/change_password")
def change_password_page():

    if "student_id" not in session:
        return redirect(url_for("student_login_page"))

    return render_template("student_change_password.html")


@app.route("/change_password", methods=["POST"])
def change_password():

    if "student_id" not in session:
        return redirect(url_for("student_login_page"))

    old_password = request.form["old_password"]
    new_password = request.form["new_password"]
    confirm_password = request.form["confirm_password"]

    if new_password != confirm_password:
        flash("New passwords do not match.")
        return redirect(url_for("change_password_page"))

    conn = db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT password FROM students WHERE id=%s",
        (session["student_id"],)
    )

    student = cursor.fetchone()

    if not check_password_hash(student["password"], old_password):
        conn.close()
        flash("Current password is incorrect.")
        return redirect(url_for("change_password_page"))

    new_hash = generate_password_hash(new_password)

    cursor.execute(
        "UPDATE students SET password=%s WHERE id=%s",
        (new_hash, session["student_id"])
    )

    conn.commit()
    conn.close()

    flash("Password changed successfully.")

    return redirect(url_for("student_dashboard"))

@app.route("/admin_change_password")
def admin_change_password_page():

    if "admin" not in session:
        return redirect(url_for("admin_login_page"))

    return render_template("admin_change_password.html")

@app.route("/admin_change_password", methods=["POST"])
def admin_change_password():

    if "admin" not in session:
        return redirect(url_for("admin_login_page"))

    old_password = request.form["old_password"]
    new_password = request.form["new_password"]
    confirm_password = request.form["confirm_password"]

    if new_password != confirm_password:
        flash("New passwords do not match.")
        return redirect(url_for("admin_change_password_page"))

    conn = db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM admins WHERE username=%s",
        (session["admin"],)
    )

    admin = cursor.fetchone()

    if not check_password_hash(admin["password"], old_password):
        conn.close()
        flash("Current password is incorrect.")
        return redirect(url_for("admin_change_password_page"))

    new_hash = generate_password_hash(new_password)

    cursor.execute(
        "UPDATE admins SET password=%s WHERE username=%s",
        (new_hash, session["admin"])
    )

    conn.commit()
    conn.close()

    flash("Password changed successfully.")

    return redirect(url_for("admin_dashboard"))

@app.route("/department_change_password")
def department_change_password_page():

    if "admin" not in session:
        return redirect(url_for("department_login_page"))

    return render_template("department_change_password.html")

@app.route("/department_change_password", methods=["POST"])
def department_change_password():

    if "admin" not in session:
        return redirect(url_for("department_login_page"))

    old_password = request.form["old_password"]
    new_password = request.form["new_password"]
    confirm_password = request.form["confirm_password"]

    if new_password != confirm_password:
        flash("New passwords do not match.")
        return redirect(url_for("department_change_password_page"))

    conn = db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM departments WHERE username=%s",
        (session["admin"],)
    )

    admin = cursor.fetchone()

    if not check_password_hash(admin["password"], old_password):
        conn.close()
        flash("Current password is incorrect.")
        return redirect(url_for("department_change_password_page"))

    new_hash = generate_password_hash(new_password)

    cursor.execute(
        "UPDATE departments SET password=%s WHERE username=%s",
        (new_hash, session["admin"])
    )

    conn.commit()
    conn.close()

    flash("Password changed successfully.")

    return redirect(url_for("department_dashboard"))

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
