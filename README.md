# Textbook Problem Paper Builder

A Flask website where teachers/students can:

1. Upload large textbook PDFs.
2. Store textbook metadata in SQL (SQLite).
3. Create a paper by choosing textbook + page + exercise label.
4. Paste a LaTeX problem statement.
5. Generate and store a LaTeX step-by-step solution paper.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:5000>.

## Notes

- PDFs are saved in `uploads/`; SQL metadata is stored in `app.db`.
- Generated papers are stored in the `papers` SQL table.
- The current `solve_problem` function is a scaffold that can be swapped with a real solver/LLM pipeline.
