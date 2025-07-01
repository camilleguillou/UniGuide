import os

from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from collections import Counter

# Configure application
app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Define the apology function
def apology(message, code=400):
    return render_template("apology.html", top=code, bottom=message), code

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    return render_template("intro.html")

@app.route("/major")
def major():
    major_name = session.get("major", "Unknown")
    return render_template("major.html", major=major_name)

@app.route("/faculty", methods=["GET", "POST"])
def faculty():
    if request.method == "POST":
        # Process answers and determine the faculty result
        answers = request.form.getlist("answer")
        faculty_result = determine_faculty(answers)
        return jsonify({"faculty_result": faculty_result})
    return render_template("faculty.html")

@app.route("/country")
def country():
    return render_template("country.html")

@app.route("/quiz1", methods=["GET", "POST"])
def quiz1():
    if request.method == "POST":
        session["quiz1"] = request.form.to_dict()
        session.modified = True
        return redirect(url_for("quiz2"))
    return render_template("quiz1.html")

@app.route("/quiz2", methods=["GET", "POST"])
def quiz2():
    if "quiz1" not in session:
        return apology("Missing quiz1 data, please restart the quiz.", 400)
    if request.method == "POST":
        session["quiz2"] = request.form.to_dict()
        total_score = compute_faculty_score(session["quiz1"], session["quiz2"])
        session["faculty"] = determine_faculty(total_score)
        session.modified = True
        return render_template("faculty_results.html", faculty=session["faculty"])
    return render_template("quiz2.html")

@app.route("/quiz3", methods=["GET", "POST"])
def quiz3():
    faculty = session.get("faculty")
    if faculty is None:
        return apology("Faculty not found. Please restart the quiz.", 400)
    if request.method == "POST":
        quiz3_answers = request.form.to_dict()
        major = determine_major(quiz3_answers, faculty)
        country = session.get("country", "Unknown")
        session["results"] = {
            "faculty": faculty,
            "major": major,
            "country": country
        }
        session.modified = True
        return redirect("/major_results")
    return render_template("quiz3.html", faculty=faculty)

@app.route("/quiz4", methods=["GET", "POST"])
def quiz4():
    if request.method == "POST":
        answers = request.form.to_dict()
        counts, recommended_country = determine_country(answers)
        session["country"] = recommended_country
        if "results" not in session:
            session["results"] = {}
        session["results"]["country"] = recommended_country
        session.modified = True
        return redirect(url_for("country_result"))
    return render_template("quiz4.html")

@app.route("/major_results")
def results():
    result = session.get("results", {})
    faculty = result.get("faculty", "Unknown")
    major = result.get("major", "Unknown")
    return render_template("major_results.html", faculty=faculty, major=major)

@app.route("/country_result")
def country_result():
    country_name = session.get("country", "Unknown")
    return render_template("country_results.html", country=country_name)

@app.route("/results")
def view_results():
    result = session.get("results", {})
    faculty = result.get("faculty", "Unknown")
    major = result.get("major", "Unknown")
    country = result.get("country", "Unknown")
    return render_template("results.html", faculty=faculty, major=major, country=country)

# ---- Logic Functions ----

def compute_faculty_score(quiz1, quiz2):
    score = 0
    for answer in quiz1.values():
        score += {"A": 1, "B": 2, "C": 3}.get(answer, 0)
    for answer in quiz2.values():
        score += {"A": 1, "B": 2, "C": 3}.get(answer, 0)
    return score

def determine_faculty(score):
    if score == 0:
        return "Unknown"
    elif score <= 21:
        return "Arts"
    elif score <= 41:
        return "Social Sciences"
    else:
        return "STEM"

def determine_major(quiz3_answers, faculty):
    if faculty == "Arts":
        prefix = "Artsq"
        majors = {"A": "Fine Arts", "B": "Philosophy", "C": "Literature"}
    elif faculty == "Social Sciences":
        prefix = "SociSq"
        majors = {"A": "Anthropology", "B": "Political Science", "C": "Economics"}
    elif faculty == "STEM":
        prefix = "STEMq"
        majors = {"A": "Computer Science", "B": "Engineering", "C": "Biology"}
    else:
        return "Unknown"

    answers = [quiz3_answers.get(f"{prefix}{i}", "").strip().upper() for i in range(1, 16)]
    answers = [ans for ans in answers if ans in majors]
    if not answers:
        return "Unknown"

    counts = Counter(answers)
    most_frequent = max(counts, key=counts.get, default="Unknown")
    return majors.get(most_frequent, "Unknown")

def determine_country(answers):
    counts = Counter(answers.values())
    most_common = counts.most_common()
    if most_common:
        most_common_answer = most_common[0][0]
        return counts, {
            "A": "Canada",
            "B": "Australia",
            "C": "Japan",
            "D": "Spain"
        }.get(most_common_answer, "Unknown")
    return counts, "Unknown"

# Only for local testing, not used on Render
if __name__ == "__main__":
    app.run(debug=True)
