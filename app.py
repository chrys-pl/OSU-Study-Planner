from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime

# -----------------------------
# Basic configuration
# -----------------------------
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

app = Flask(__name__)
app.secret_key = "local-demo-secret"


# -----------------------------
# Database helpers
# -----------------------------
def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db_connect()
    cur = conn.cursor()

    # Courses table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT
        )
    """)

    # Assignments table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            due_date TEXT,
            course_id INTEGER,
            is_complete INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


with app.app_context():
    init_db()


# -----------------------------
# Welcome / Entry Page
# -----------------------------
@app.route("/", methods=["GET"])
def login():
    return render_template("login.html")


# -----------------------------
# Dashboard
# -----------------------------
@app.route("/dashboard")
def dashboard():
    conn = db_connect()
    cur = conn.cursor()
    courses = cur.execute("SELECT * FROM courses ORDER BY id DESC").fetchall()
    assignments = cur.execute("""
        SELECT a.id, a.title, a.due_date, a.is_complete, c.title AS course_title
        FROM assignments a
        LEFT JOIN courses c ON a.course_id = c.id
        ORDER BY a.id DESC
    """).fetchall()
    conn.close()

    return render_template("dashboard.html", courses=courses, assignments=assignments)


# -----------------------------
# Courses
# -----------------------------
@app.route("/courses/add", methods=["GET", "POST"])
def add_course():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not title:
            flash("Course title is required.", "error")
            return render_template("add_course.html", title=title, description=description)

        conn = db_connect()
        conn.execute("INSERT INTO courses (title, description) VALUES (?, ?)", (title, description))
        conn.commit()
        conn.close()
        flash("Your course has been saved! ✓", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_course.html")


@app.route("/courses/delete/<int:course_id>", methods=["POST"])
def delete_course(course_id):
    conn = db_connect()
    conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.execute("DELETE FROM assignments WHERE course_id = ?", (course_id,))
    conn.commit()
    conn.close()
    flash("Course deleted.", "info")
    return redirect(url_for("dashboard"))


# -----------------------------
# Assignments
# -----------------------------
@app.route("/assignments/add", methods=["GET", "POST"])
def add_assignment():
    conn = db_connect()
    courses = conn.execute("SELECT id, title FROM courses ORDER BY title ASC").fetchall()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        course_id = request.form.get("course_id")
        due_date = request.form.get("due_date", "").strip()

        if not title:
            flash("Assignment title is required.", "error")
            return render_template("add_assignment.html", courses=courses, title=title, due_date=due_date)

        if due_date:
            try:
                parsed = datetime.strptime(due_date, "%Y-%m-%d")
                due_date = parsed.strftime("%Y-%m-%d")
            except ValueError:
                flash("Tip: use YYYY-MM-DD for due date.", "info")

        conn.execute(
            "INSERT INTO assignments (title, due_date, course_id) VALUES (?, ?, ?)",
            (title, due_date, course_id if course_id else None),
        )
        conn.commit()
        conn.close()
        flash("Your assignment has been saved! ✓", "success")
        return redirect(url_for("dashboard"))

    conn.close()
    return render_template("add_assignment.html", courses=courses)


@app.route("/assignments/complete/<int:assignment_id>", methods=["POST"])
def toggle_assignment_complete(assignment_id):
    conn = db_connect()
    cur = conn.cursor()
    row = cur.execute("SELECT is_complete FROM assignments WHERE id = ?", (assignment_id,)).fetchone()
    if row:
        new_val = 0 if row["is_complete"] else 1
        cur.execute("UPDATE assignments SET is_complete = ? WHERE id = ?", (new_val, assignment_id))
        conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))


@app.route("/assignments/delete/<int:assignment_id>", methods=["POST"])
def delete_assignment(assignment_id):
    conn = db_connect()
    conn.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
    conn.commit()
    conn.close()
    flash("Assignment deleted.", "info")
    return redirect(url_for("dashboard"))


# -----------------------------
# Help Page
# -----------------------------
@app.route("/help")
def help_page():
    return render_template("help.html")


# -----------------------------
# Run the App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
