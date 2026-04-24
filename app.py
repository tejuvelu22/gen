from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "app.db"
UPLOAD_DIR = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"pdf"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-change-me"
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB textbooks

UPLOAD_DIR.mkdir(exist_ok=True)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_: Any) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    schema_path = BASE_DIR / "schema.sql"
    db.executescript(schema_path.read_text())
    db.commit()
    db.close()


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def solve_problem(problem_latex: str) -> str:
    """
    Generates a step-by-step LaTeX-friendly explanation.
    In production, replace this with an LLM/math CAS pipeline.
    """
    cleaned = " ".join(problem_latex.split())
    return "\n".join(
        [
            r"\\textbf{Step 1: Understand the problem}",
            rf"\\text{{Given problem: }} {cleaned}",
            r"",
            r"\\textbf{Step 2: Choose a strategy}",
            r"\\text{Identify known quantities, unknowns, and the formula or theorem that applies.}",
            r"",
            r"\\textbf{Step 3: Show the algebra clearly}",
            r"\\text{Write each transformation on its own line and use exponent notation like }x^2\\text{.}",
            r"",
            r"\\textbf{Step 4: Verify}",
            r"\\text{Substitute back or check units/signs.}",
            r"",
            r"\\boxed{\\text{Final answer goes here after completing the symbolic steps.}}",
        ]
    )


@app.route("/")
def index() -> str:
    db = get_db()
    textbooks = db.execute(
        "SELECT id, title, original_filename, created_at FROM textbooks ORDER BY created_at DESC"
    ).fetchall()
    papers = db.execute(
        """
        SELECT p.id, p.page_number, p.exercise_label, p.created_at, t.title AS textbook_title
        FROM papers p
        JOIN textbooks t ON t.id = p.textbook_id
        ORDER BY p.created_at DESC
        """
    ).fetchall()
    return render_template("index.html", textbooks=textbooks, papers=papers)


@app.route("/upload", methods=["POST"])
def upload_textbook() -> str:
    title = request.form.get("title", "").strip()
    file = request.files.get("pdf")

    if not title:
        flash("Please provide a textbook title.")
        return redirect(url_for("index"))

    if file is None or file.filename == "":
        flash("Please choose a PDF file.")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Only PDF uploads are supported.")
        return redirect(url_for("index"))

    original_name = secure_filename(file.filename)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    stored_name = f"{timestamp}_{original_name}"
    file_path = UPLOAD_DIR / stored_name
    file.save(file_path)

    db = get_db()
    db.execute(
        """
        INSERT INTO textbooks (title, original_filename, stored_filename, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (title, original_name, stored_name, datetime.utcnow().isoformat()),
    )
    db.commit()

    flash("Textbook uploaded successfully.")
    return redirect(url_for("index"))


@app.route("/textbooks/<int:textbook_id>")
def view_textbook(textbook_id: int) -> str:
    db = get_db()
    textbook = db.execute("SELECT * FROM textbooks WHERE id = ?", (textbook_id,)).fetchone()
    if textbook is None:
        flash("Textbook not found.")
        return redirect(url_for("index"))
    return render_template("textbook.html", textbook=textbook)


@app.route("/files/<path:filename>")
def uploaded_file(filename: str):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/papers/new", methods=["GET", "POST"])
def create_paper() -> str:
    db = get_db()
    textbooks = db.execute("SELECT id, title FROM textbooks ORDER BY title").fetchall()

    if request.method == "GET":
        return render_template("new_paper.html", textbooks=textbooks)

    textbook_id = request.form.get("textbook_id", type=int)
    page_number = request.form.get("page_number", type=int)
    exercise_label = request.form.get("exercise_label", "").strip()
    problem_latex = request.form.get("problem_latex", "").strip()

    if not textbook_id or page_number is None or not exercise_label or not problem_latex:
        flash("Please fill in all fields.")
        return render_template("new_paper.html", textbooks=textbooks)

    solution_latex = solve_problem(problem_latex)

    db.execute(
        """
        INSERT INTO papers (
            textbook_id,
            page_number,
            exercise_label,
            problem_latex,
            solution_latex,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            textbook_id,
            page_number,
            exercise_label,
            problem_latex,
            solution_latex,
            datetime.utcnow().isoformat(),
        ),
    )
    db.commit()

    paper_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    flash("Paper created and stored in SQL successfully.")
    return redirect(url_for("view_paper", paper_id=paper_id))


@app.route("/papers/<int:paper_id>")
def view_paper(paper_id: int) -> str:
    db = get_db()
    paper = db.execute(
        """
        SELECT p.*, t.title AS textbook_title
        FROM papers p
        JOIN textbooks t ON t.id = p.textbook_id
        WHERE p.id = ?
        """,
        (paper_id,),
    ).fetchone()

    if paper is None:
        flash("Paper not found.")
        return redirect(url_for("index"))

    return render_template("paper.html", paper=paper)


if __name__ == "__main__":
    if not DB_PATH.exists():
        init_db()
    app.run(debug=True)
