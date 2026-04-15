

from flask import Flask, render_template, request
import os
from main import read_resumes, evaluate_candidate, evaluate_candidate_fair
import matplotlib.pyplot as plt
import pandas as pd

app = Flask(__name__)
UPLOAD_FOLDER = "resumes"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    #Step 1: Clear old files
    for old_file in os.listdir(app.config["UPLOAD_FOLDER"]):
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], old_file))
    #NEW: Get job input
    skills_input = request.form.get("skills")
    experience_input = int(request.form.get("experience"))

    job_skills = set([s.strip().lower() for s in skills_input.split(",")])

    #Step 2: Save new uploaded files
    files = request.files.getlist("resumes")

    for file in files:
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))

    #Step 3: Read resumes
    resumes = read_resumes("resumes")

    results = []
    selected = []
    rejected = []

    #Step 4: Process candidates
    for candidate in resumes:
        biased = evaluate_candidate(candidate)
        fair = evaluate_candidate_fair(candidate, job_skills, experience_input)

        data = {
            "name": candidate["name"],
            "gender": candidate["gender"],

            "biased_score": biased["score"],
            "fair_score": fair["score"],

            "biased_decision": biased["decision"],
            "fair_decision": fair["decision"],

            "matched_skills": list(fair["matched_skills"]),
            "missing_skills": list(fair["missing_skills"]),

            "email": candidate["email"],
            "phone": candidate["phone"],
            "experience": candidate["experience"],

            # NEW: Bias info
            "bias_changed": biased["score"] != fair["score"],



        }

        #THIS WAS MISSING
        if fair["decision"] == "Selected":
            selected.append(data)
        else:
            rejected.append(data)

        # optional (for chart)
        results.append(data)
    selected = sorted(selected, key=lambda x: x["fair_score"], reverse=True)
    results = sorted(results, key=lambda x: x["fair_score"], reverse=True)
    names = [r["name"] for r in results]
    biased_scores = [r["biased_score"] for r in results]
    fair_scores = [r["fair_score"] for r in results]

    x = range(len(names))

    #CHART 1: Biased Model
    plt.figure(figsize=(8, 5))
    plt.bar(names, biased_scores)
    plt.title("Biased Model Scores")

    plt.xticks(rotation=30, ha='right')  # FIX overlap
    plt.tight_layout()  # auto spacing

    plt.savefig("static/biased.png")
    plt.close()

    #CHART 2: Fair Model
    plt.figure(figsize=(8, 5))
    plt.bar(names, fair_scores)
    plt.title("Fair Model Scores")

    plt.xticks(rotation=30, ha='right')  #  FIX overlap
    plt.tight_layout()

    plt.savefig("static/fair.png")
    plt.close()




    # Step 5: Return result page
    total = len(selected) + len(rejected)
    selected_count = len(selected)
    rejected_count = len(rejected)
    # PIE CHART
    labels = ["Selected", "Rejected"]
    sizes = [selected_count, rejected_count]
    plt.figure()
    plt.pie(sizes, labels=labels, autopct='%1.1f%%')
    plt.title("Selection Distribution")
    plt.savefig("static/pie.png")
    plt.close()
    #  CREATE CSV FOR SELECTED CANDIDATES
    df = pd.DataFrame(selected)
    df.to_csv("static/selected_candidates.csv", index=False)
    return render_template("result.html",
                           selected=selected,
                           rejected=rejected,
                           total=total,
                           selected_count=selected_count,
                           rejected_count=rejected_count)
    # return render_template("result.html", results=results)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
    # app.run(debug=True)
