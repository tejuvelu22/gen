CREATE TABLE IF NOT EXISTS textbooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    textbook_id INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    exercise_label TEXT NOT NULL,
    problem_latex TEXT NOT NULL,
    solution_latex TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (textbook_id) REFERENCES textbooks (id)
);
