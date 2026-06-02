from flask import Flask, render_template, request
import os
import re
import csv
import pdfplumber

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

# Create uploads folder automatically
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Skills List
skills_list = [
    "python", "java", "sql",
    "machine learning", "deep learning",
    "data science", "html", "css",
    "javascript", "excel",
    "power bi", "statistics",
    "network security", "cryptography",
    "linux", "aws", "azure",
    "cloud computing", "spring",
    "mysql", "database"
]

# Job Roles
job_roles = {

    "Data Scientist": [
        "python", "sql",
        "machine learning",
        "data science", "excel"
    ],

    "Data Analyst": [
        "python", "sql",
        "excel", "power bi",
        "statistics"
    ],

    "Software Developer": [
        "python", "java",
        "sql", "javascript"
    ],

    "Web Developer": [
        "html", "css",
        "javascript"
    ],

    "AI Engineer": [
        "python",
        "machine learning",
        "deep learning",
        "sql"
    ],

    "Cyber Security": [
        "python",
        "network security",
        "cryptography",
        "linux"
    ],

    "Cloud Engineer": [
        "aws", "azure",
        "cloud computing",
        "linux", "python"
    ],

    "Full Stack Developer": [
        "html", "css",
        "javascript",
        "python", "sql"
    ],

    "Java Developer": [
        "java", "sql",
        "spring", "javascript"
    ],

    "Database Administrator": [
        "sql", "mysql",
        "database", "excel"
    ]
}

# Extract text from PDF
def extract_text_from_pdf(pdf_path):

    text = ""

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text.lower() + "\n"

    return text


# Find skills
def find_skills(text):

    found_skills = []

    for skill in skills_list:

        if skill in text:
            found_skills.append(skill)

    return found_skills


# Extract email
def extract_email(text):

    email = re.findall(
        r"[\w\.-]+@[\w\.-]+",
        text
    )

    return email[0] if email else "Not Found"


# Extract phone number
def extract_phone(text):

    phone = re.findall(
        r"\d{10}",
        text
    )

    return phone[0] if phone else "Not Found"


# Extract candidate name
def extract_name(text):

    lines = text.split("\n")

    for line in lines:

        line = line.strip()

        if line:
            return line.title()

    return "Not Found"


# Calculate score
def calculate_score(found_skills, role):

    required_skills = job_roles.get(role, [])

    matched = len(
        set(found_skills) &
        set(required_skills)
    )

    total = len(required_skills)

    if total == 0:
        return 0

    return int((matched / total) * 100)


# Save candidate history
def save_candidate_history(
    name,
    email,
    phone,
    role,
    score,
    status,
    filename
):

    file_exists = os.path.exists(
        "candidate_history.csv"
    )

    with open(
        "candidate_history.csv",
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if not file_exists:

            writer.writerow([
                "Name",
                "Email",
                "Phone",
                "Role",
                "Score",
                "Status",
                "Resume File"
            ])

        writer.writerow([
            name,
            email,
            phone,
            role,
            score,
            status,
            filename
        ])


@app.route("/", methods=["GET", "POST"])
def index():

    missing_skills = []
    score = None
    status = ""

    candidate_name = ""
    candidate_email = ""
    candidate_phone = ""
    resume_filename = ""

    if request.method == "POST":

        role = request.form["role"]

        file = request.files["resume"]

        if file and file.filename:

            resume_filename = file.filename

            filepath = os.path.abspath(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    resume_filename
                )
            )

            file.save(filepath)

            resume_text = extract_text_from_pdf(
                filepath
            )

            candidate_name = extract_name(
                resume_text
            )

            candidate_email = extract_email(
                resume_text
            )

            candidate_phone = extract_phone(
                resume_text
            )

            detected_skills = find_skills(
                resume_text
            )

            required_skills = job_roles.get(
                role,
                []
            )

            missing_skills = list(
                set(required_skills) -
                set(detected_skills)
            )

            score = calculate_score(
                detected_skills,
                role
            )

            if score >= 80:
                status = "Highly Recommended"

            elif score >= 60:
                status = "Selected"

            else:
                status = "Rejected"

            save_candidate_history(
                candidate_name,
                candidate_email,
                candidate_phone,
                role,
                score,
                status,
                resume_filename
            )

    return render_template(
        "index.html",
        missing_skills=missing_skills,
        score=score,
        status=status,
        name=candidate_name,
        email=candidate_email,
        phone=candidate_phone,
        filename=resume_filename
    )


@app.route("/history")
def history():

    candidates = []

    if os.path.exists(
        "candidate_history.csv"
    ):

        with open(
            "candidate_history.csv",
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:
                candidates.append(row)

    return render_template(
        "history.html",
        candidates=candidates
    )


if __name__ == "__main__":
    app.run(debug=True)


def clear_history():

   if os.path.exists("candidate_history.csv"):
       os.remove("candidate_history.csv")

   return render_template(
       "history.html",
       candidates=[]
   )
   app.run(debug=True)