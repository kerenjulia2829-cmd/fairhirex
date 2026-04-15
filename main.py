# import pandas as pd
#
# # Sample job requirement
# job_skills = {"python", "machine learning", "sql"}
#
# # Sample resumes (we will later replace with real parsing)
# resumes = [
#     {"name": "Alice", "skills": {"python", "sql"}, "experience": 2},
#     {"name": "Bob", "skills": {"java", "c++"}, "experience": 3},
#     {"name": "Charlie", "skills": {"python", "machine learning", "sql"}, "experience": 1}
# ]
#
# def calculate_score(candidate):
#     skill_match = len(candidate["skills"].intersection(job_skills))
#     experience_score = candidate["experience"]
#
#     total_score = skill_match * 2 + experience_score
#     return total_score
#
# # Evaluate candidates
# for candidate in resumes:
#     score = calculate_score(candidate)
#     decision = "Selected" if score >= 5 else "Rejected"
#
#     print(f"Name: {candidate['name']}")
#     print(f"Score: {score}")
#     print(f"Decision: {decision}")
#     print("-" * 30)

import os
import re
import pytesseract
import pytesseract

try:
    pytesseract.get_tesseract_version()
except:
    pass
from docx import Document
from PIL import Image
import pytesseract
def read_docx(file_path):
    doc = Document(file_path)
    text = ""

    for para in doc.paragraphs:
        text += para.text + "\n"

    return text
def read_image(file_path):
    img = Image.open(file_path)
    text = pytesseract.image_to_string(img)
    return text
from PyPDF2 import PdfReader
def read_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        text += page.extract_text()

    return text

# Job requirement
job_skills = {"python", "machine learning", "sql"}
SKILL_KEYWORDS = [
    "python", "machine learning", "sql",
    "java", "c++", "data analysis", "deep learning"
]
def extract_skills(text):
    text = text.lower()
    found_skills = set()

    for skill in SKILL_KEYWORDS:
        if skill in text:
            found_skills.add(skill)

    return found_skills
def extract_email(text):
    match = re.search(r"\S+@\S+", text)
    return match.group() if match else "Not found"


def extract_phone(text):
    match = re.search(r"\d{10}", text)
    return match.group() if match else "Not found"


def extract_experience(text):
    match = re.search(r"(\d+)\s+years", text.lower())
    return int(match.group(1)) if match else 0

def read_resumes(folder_path):
    resumes = []

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)

        # TXT
        if file.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

        # PDF
        elif file.endswith(".pdf"):
            text = read_pdf(file_path)

        # DOCX
        elif file.endswith(".docx"):
            text = read_docx(file_path)

        # IMAGE (JPG / PNG)
        elif file.endswith((".jpg", ".png", ".jpeg")):
            text = read_image(file_path)


        elif file.endswith(".csv"):

            import pandas as pd

            df = pd.read_csv(file_path)

            for _, row in df.iterrows():
                resumes.append({

                    "name": str(row.get("name", "Unknown")),

                    "gender": "Unknown",

                    "skills": set(str(row.get("skills", "")).lower().split(",")),

                    "experience": int(row.get("experience", 0)),

                    "email": row.get("email", "Not found"),

                    "phone": str(row.get("phone", "Not found"))

                })

            continue  # ✅ VERY IMPORTANT (skip rest of loop)

        skills = extract_skills(text)

        resumes.append({
            "name": file.split(".")[0],
            "gender": "Unknown",
            "skills": skills,
            "experience": extract_experience(text),
            "email": extract_email(text),
            "phone": extract_phone(text)

        })

    return resumes
# Scoring function
def evaluate_candidate(candidate):
    matched_skills = candidate["skills"].intersection(job_skills)
    missing_skills = job_skills - candidate["skills"]

    skill_score = len(matched_skills) * 2
    experience_score = candidate["experience"]

    total_score = skill_score + experience_score

    # Bias (intentional for demo)
    if candidate["gender"].lower() == "male":
        total_score += 1

    decision = "Selected" if total_score >= 5 else "Rejected"

    return {
        "score": total_score,
        "decision": decision,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "experience": candidate["experience"],
        "gender": candidate["gender"]
    }

#new function-no bias
def evaluate_candidate_fair(candidate, job_skills, min_exp):
    matched_skills = candidate["skills"].intersection(job_skills)
    missing_skills = job_skills - candidate["skills"]

    skill_score = len(matched_skills) * 2
    experience_score = candidate["experience"]

    total_score = skill_score + experience_score

    # NEW: Experience condition
    # NEW LOGIC
    if min_exp != 0:  # only apply experience filter if user gives value
        if experience_score < min_exp:
            total_score -= 2

    if len(matched_skills) >= 2:
        decision = "Selected"
    else:
        decision = "Rejected"

    return {
        "score": total_score,
        "decision": decision,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "experience": candidate["experience"],
        "gender": candidate["gender"]
    }

# MAIN
resumes = read_resumes("resumes")
if __name__ == "__main__":
    resumes = read_resumes("resumes")

    selected = []
    rejected = []

    for candidate in resumes:
        biased = evaluate_candidate(candidate)
        fair = evaluate_candidate_fair(candidate, job_skills, 0)

        data = {
            "name": candidate["name"],
            "gender": candidate["gender"],
            "biased_score": biased["score"],
            "fair_score": fair["score"],
            "biased_decision": biased["decision"],
            "fair_decision": fair["decision"],
            "matched_skills": list(fair["matched_skills"]),
            "missing_skills": list(fair["missing_skills"])
        }

        if fair["decision"] == "Selected":
            selected.append(data)
        else:
            rejected.append(data)

    selected = sorted(selected, key=lambda x: x["fair_score"], reverse=True)

    print("\n===== FINAL RANKING (FAIR MODEL) =====\n")

    rank = 1
    for r in selected:
        print(f"Rank {rank}: {r['name']} ({r['gender']})")
        print(f"Score: {r['fair_score']}")
        print(f"Decision: {r['fair_decision']}")
        print("-" * 40)
        rank += 1
