import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from collections import Counter

# Configure application
app = Flask(__name__)


# Define the apology function
def apology(message, code=400):
    return render_template("apology.html", top=code, bottom=message), code


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///quiz.db")


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


@app.route("/faculty")
def faculty():
    if request.method == "POST":
        # Process answers and determine the faculty result
        answers = request.form.getlist("answer")
        faculty_result = determine_faculty(answers)

        # Store result in session or client-side storage via JavaScript
        return jsonify({"faculty_result": faculty_result})

    return render_template("faculty.html")


@app.route("/country")
def country():
    return render_template("country.html")


# Route for Quiz 1
@app.route("/quiz1", methods=["GET", "POST"])
def quiz1():

    if request.method == "POST":
        # Store quiz 1 answers in session
        session["quiz1"] = request.form.to_dict()
        session.modified = True
        # Debugging print
        print("Session after quiz1:", session)
        # Redirect to quiz2
        return redirect(url_for("quiz2"))
    return render_template("quiz1.html")


# Route for Quiz 2
@app.route("/quiz2", methods=["GET", "POST"])
def quiz2():

    if "quiz1" not in session:
        return apology("Missing quiz1 data, please restart the quiz.", 400)

    if request.method == "POST":
        # Store quiz 2 answers
        session["quiz2"] = request.form.to_dict()

        # Compute faculty result
        total_score = compute_faculty_score(session["quiz1"], session["quiz2"])
        session["faculty"] = determine_faculty(total_score)
        session.modified = True

        return render_template("faculty_results.html", faculty=session["faculty"])

    return render_template("quiz2.html")


# Route for Quiz 3
@app.route("/quiz3", methods=["GET", "POST"])
def quiz3():
    faculty = session.get("faculty")

    if faculty is None:
        return apology("Faculty not found. Please restart the quiz.", 400)

    if request.method == "POST":
        quiz3_answers = request.form.to_dict()
        major = determine_major(quiz3_answers, faculty)
        country = session.get("country", "Unknown")

        # New result entry
        new_result = {"faculty": faculty, "major": major, "country":country}

        # Store results in session
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

        # Store the recommended country in the session
        session["country"] = recommended_country
        session.modified = True

        # Store the result in session
        if "results" not in session:
            session["results"] = {}

        session["results"] ["country"] = recommended_country
        session.modified = True

        return redirect(url_for("country_result"))

    return render_template("quiz4.html")


# Route for Results
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


# Function to compute faculty score
def compute_faculty_score(quiz1, quiz2):
    score = 0
    for answer in quiz1.values():
        score += {"A": 1, "B": 2, "C": 3}.get(answer, 0)
    for answer in quiz2.values():
        score += {"A": 1, "B": 2, "C": 3}.get(answer, 0)
    return score


# Function to determine faculty
def determine_faculty(score):
    if score == 0:
        return "Unknown"
    elif score <= 21:
        return "Arts"
    elif score <= 41:
        return "Social Sciences"
    else:
        return "STEM"


# Function to determine major
def determine_major(quiz3_answers, faculty):
    # Identify the correct question prefix
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

    # Collect all 15 answers
    answers = [quiz3_answers.get(f"{prefix}{i}", "").strip().upper() for i in range(1, 16)]
    answers = [ans for ans in answers if ans in majors]

    if not answers:
        return "Unknown"

    # Count occurrences of A, B, and C
    counts = Counter(answers)

    # Find the most frequent answer
    most_frequent = max(counts, key=counts.get, default="Unknown")

    # Return the corresponding major
    return majors.get(most_frequent, "Unknown")


def determine_country(answers):
    """Determines the recommended country based on quiz answers."""
    counts = Counter(answers.values())

    # Determine most frequent answers
    most_common = counts.most_common()

    # Determine country based on most common answers
    if most_common:
        most_common_answer = most_common[0][0]
        if most_common_answer == "A":
            country = "Canada"
        elif most_common_answer == "B":
            country = "Australia"
        elif most_common_answer == "C":
            country = "Japan"
        elif most_common_answer == "D":
            country = "Spain"
        else:
            country = "Unknown"
    else:
        country = "Unknown"

    return counts, country


@app.route("/results")
def view_results():
    result = session.get("results", {})

    faculty = result.get("faculty", "Unknown")
    major = result.get("major", "Unknown")
    country = result.get("country", "Unknown")

    return render_template("results.html", faculty=faculty, major=major, country=country)

if __name__ == "__main__":
    app.run(debug=True)
