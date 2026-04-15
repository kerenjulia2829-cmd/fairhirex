import os
import re
import pandas as pd
import pytesseract
from docx import Document
from PIL import Image
from PyPDF2 import PdfReader

# Safe OCR (won't crash if tesseract missing)
try:
    pytesseract.get_tesseract_version()
except:
    pass


# =========================
# FILE READ FUNCTIONS
# =========================

def read_docx(file_path):
    doc = Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text


def read_image(file_path):
    try:
        img = Image.open(file_path)
        return pytesseract.image_to_string(img)
    except:
        return ""


def read_pdf(file_path):
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() or ""
    except:
        pass
    return text


# =========================
# DATASET SUPPORT
# =========================

def read_dataset(file_path):
    data = []

    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path)
        else:
            return data

        for _, row in df.iterrows():
            skills = set(str(row.get("Skills", "")).lower().split(","))

            data.append({
                "name": str(row.get("Name", "Unknown")),
                "gender": "Unknown",
                "skills": skills,
                "experience": int(row.get("Experience", 0)),
                "email": row.get("Email", "Not found"),
                "phone": str(row.get("Phone", "Not found"))
            })

    except Exception as e:
        print("Dataset error:", e)

    return data


# =========================
# SKILL EXTRACTION
# =========================

job_skills = {"python", "machine learning", "sql"}

SKILL_KEYWORDS = [
    "python", "machine learning", "sql",
    "java", "c++", "data analysis", "deep learning"
]


def extract_skills(text):
    text = text.lower()
    found = set()

    for skill in SKILL_KEYWORDS:
        if skill in text:
            found.add(skill)

    return found


def extract_email(text):
    match = re.search(r"\S+@\S+", text)
    return match.group() if match else "Not found"


def extract_phone(text):
    match = re.search(r"\d{10}", text)
    return match.group() if match else "Not found"


def extract_experience(text):
    match = re.search(r"(\d+)\s+years", text.lower())
    return int(match.group(1)) if match else 0


# =========================
# MAIN RESUME READER
# =========================

def read_resumes(folder_path):
    resumes = []

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)

        # DATASET FILES
        if file.endswith((".csv", ".xlsx")):
            resumes.extend(read_dataset(file_path))
            continue

        text = ""

        try:
            if file.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()

            elif file.endswith(".pdf"):
                text = read_pdf(file_path)

            elif file.endswith(".docx"):
                text = read_docx(file_path)

            elif file.endswith((".jpg", ".png", ".jpeg")):
                text = read_image(file_path)

            else:
                continue

        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue

        if not text:
            continue

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


# =========================
# SCORING FUNCTIONS
# =========================

def evaluate_candidate(candidate):
    matched = candidate["skills"].intersection(job_skills)

    score = len(matched) * 2 + candidate["experience"]

    # Bias (intentional)
    if candidate["gender"].lower() == "male":
        score += 1

    decision = "Selected" if score >= 5 else "Rejected"

    return {
        "score": score,
        "decision": decision,
        "matched_skills": matched,
        "missing_skills": job_skills - candidate["skills"],
        "experience": candidate["experience"],
        "gender": candidate["gender"]
    }


def evaluate_candidate_fair(candidate, job_skills, min_exp):
    matched = candidate["skills"].intersection(job_skills)

    score = len(matched) * 2 + candidate["experience"]

    # Apply experience filter only if given
    if min_exp != 0 and candidate["experience"] < min_exp:
        score -= 2

    decision = "Selected" if len(matched) >= 2 else "Rejected"

    return {
        "score": score,
        "decision": decision,
        "matched_skills": matched,
        "missing_skills": job_skills - candidate["skills"],
        "experience": candidate["experience"],
        "gender": candidate["gender"]
    }


# =========================
# TEST RUN (LOCAL)
# =========================

if __name__ == "__main__":
    resumes = read_resumes("resumes")

    selected = []

    for c in resumes:
        fair = evaluate_candidate_fair(c, job_skills, 0)

        if fair["decision"] == "Selected":
            selected.append({
                "name": c["name"],
                "score": fair["score"]
            })

    print("\n===== FINAL RANKING =====\n")
    for i, r in enumerate(sorted(selected, key=lambda x: x["score"], reverse=True), 1):
        print(f"{i}. {r['name']} - {r['score']}")
