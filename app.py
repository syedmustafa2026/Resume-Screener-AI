import os
import re
import csv
import pdfplumber
from flask import Flask, render_template, request, redirect, session, send_file

app = Flask(__name__)
app.secret_key = "super_secret_key"

UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# SAARE PROFESSIONAL OPTIONS WAPAS LAGA DIYE HAIN
JOB_ROLES = {
    "Data Scientist": ["python", "machine learning", "data science", "pandas", "numpy", "sql", "scikit-learn"],
    "Machine Learning Engineer": ["python", "deep learning", "tensorflow", "pytorch", "keras", "computer vision", "nlp"],
    "Data Analyst": ["python", "excel", "sql", "tableau", "power bi", "pandas", "statistics", "data cleaning"],
    "Python Developer": ["python", "flask", "django", "api", "sql", "git", "rest framework", "fastapi"],
    "Web Developer": ["html", "css", "javascript", "react", "node.js", "bootstrap", "mongodb"],
    "Full Stack Developer": ["html", "css", "javascript", "react", "node.js", "express", "sql", "mongodb", "git"],
    "Software Engineer": ["java", "python", "c++", "data structures", "algorithms", "git", "sql", "oops"]
}

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            parsed_text = page.extract_text()
            if parsed_text:
                text += parsed_text + "\n"
    return text

def parse_contact_info(text):
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_regex = r'\b\d{10}\b|\+?\d{1,3}[-.\s]?\d{10}\b'
    
    email_match = re.search(email_regex, text)
    phone_match = re.search(phone_regex, text)
    
    email = email_match.group(0) if email_match else "Not Found"
    phone = phone_match.group(0) if phone_match else "Not Found"
    
    name = "Unknown"
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        name = lines[0]
        
    return name, email, phone

def calculate_score_and_skills(resume_text, job_role):
    required_skills = JOB_ROLES.get(job_role, [])
    if not required_skills:
        return 0, []
        
    resume_text_lower = resume_text.lower()
    matched_skills = [skill for skill in required_skills if skill in resume_text_lower]
    missing_skills = [skill for skill in required_skills if skill not in resume_text_lower]
    
    score = int((len(matched_skills) / len(required_skills)) * 100)
    return score, missing_skills

def save_candidate_history(name, email, phone, role, score, status, filename):
    csv_file = "candidate_history.csv"
    with open(csv_file, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([name, email, phone, role, score, status, filename])

# ROUTES
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        job_role = request.form.get("job_role")
        file = request.files.get("resume")
        
        if file and file.filename.endswith('.pdf'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            
            resume_text = extract_text_from_pdf(file_path)
            name, email, phone = parse_contact_info(resume_text)
            score, missing_skills = calculate_score_and_skills(resume_text, job_role)
            
            status = "Highly Recommended" if score >= 80 else "Pending"
            
            save_candidate_history(name, email, phone, job_role, f"{score}%", status, file.filename)
            
            candidate_details = {
                "name": name, "email": email, "phone": phone, "role": job_role,
                "score": score, "status": status, "missing_skills": missing_skills,
                "filename": file.filename
            }
            return render_template("index.html", job_roles=JOB_ROLES.keys(), candidate=candidate_details)
            
    return render_template("index.html", job_roles=JOB_ROLES.keys(), candidate=None)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect("/history")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")

@app.route("/history")
def history():
    if not session.get("admin"):
        return redirect("/login")
        
    candidates = []
    total = 0
    selected = 0
    rejected = 0
    highly_rec = 0
    
    csv_file = "candidate_history.csv"
    if os.path.exists(csv_file):
        with open(csv_file, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 7:
                    candidates.append({
                        "name": row[0], "email": row[1], "phone": row[2],
                        "role": row[3], "score": row[4], "status": row[5], "filename": row[6]
                    })
                    total += 1
                    if row[5] == "Selected": selected += 1
                    elif row[5] == "Rejected": rejected += 1
                    elif row[5] == "Highly Recommended": highly_rec += 1
                    
    return render_template("history.html", candidates=candidates, total=total, selected=selected, rejected=rejected, highly_rec=highly_rec)

@app.route("/update_status", methods=["POST"])
def update_status():
    if not session.get("admin"):
        return redirect("/login")

    target_email = request.form.get("email")
    new_status = request.form.get("status")
    
    csv_file = "candidate_history.csv"
    updated_rows = []

    if os.path.exists(csv_file):
        with open(csv_file, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 7:
                    if row[1] == target_email:
                        row[5] = new_status
                updated_rows.append(row)

        with open(csv_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(updated_rows)
            
    return redirect("/history")

@app.route("/clear-history", methods=["POST"])
def clear_history():
    if not session.get("admin"):
        return redirect("/login")
    csv_file = "candidate_history.csv"
    if os.path.exists(csv_file):
        os.remove(csv_file)
    return redirect("/history")

# DIRECT EXCEL DOWNLOAD COMPATIBLE ROUTE
@app.route("/export")
def export_excel():
    if not session.get("admin"):
        return redirect("/login")
    csv_file = "candidate_history.csv"
    if os.path.exists(csv_file):
        return send_file(csv_file, as_attachment=True, download_name="candidate_data.csv", mimetype="text/csv")
    else:
        return "No history found to export!", 404

if __name__ == "__main__":
    app.run(debug=True)