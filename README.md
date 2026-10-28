# Cert Flashcards

An interactive [Streamlit](https://streamlit.io) flashcard app for practising cloud certification exam questions.

| Exam | File | Questions |
| --- | --- | ---: |
| Azure Administrator (AZ-104) | `data/az-104.json` | 267 |
| Google Cloud Associate Cloud Engineer | `data/gcp-ace.json` | 183 |
| Google Cloud Professional Cloud Architect | `data/gcp-pca.json` | 701 |
| Google Cloud Professional ML Engineer | `data/gcp-pmle.json` | 790 |

## Features

- Filter by exam (section), shuffle with an optional seed for a repeatable order
- Single-answer and multi-select questions, with answers shuffled per card
- Explanations for correct and incorrect choices (where the dataset has them)
- Overall and last-10 accuracy, a progress bar, and jump-to-question

## Quick start

Requires Python 3.9+.

```bash
git clone https://github.com/zayn0001/cloud-certification-dumps.git
cd cloud-certification-dumps
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run main.py
```

The app opens at http://localhost:8501.

You can also open the repo in GitHub Codespaces or a VS Code Dev Container: the app starts on its own (see `.devcontainer/`).

## Question format

Each file in `data/` is a JSON array of questions for **one** exam. Every question has exactly these fields:

```json
{
  "question_id": "gcp-ace-0001",
  "prompt": "Which storage class should you use for backups accessed less than once a year?",
  "answers": [
    { "text": "Standard", "isCorrect": false, "explanation": "" },
    { "text": "Archive", "isCorrect": true, "explanation": "Archive is the cheapest class for data accessed less than once a year." }
  ],
  "tags": [],
  "question_choice_type": "multiple_choice",
  "section_name": "Google Cloud Associate Cloud Engineer",
  "bloom_level": "",
  "idea_text": ""
}
```

| Field | Rules |
| --- | --- |
| `question_id` | Unique across all files: `<file prefix>-<4-digit number>` |
| `prompt` | Self-contained: don't refer to exhibits, tables or case studies that aren't included in the text |
| `answers` | At least 2, no duplicate `text`, at least one with `isCorrect: true` |
| `question_choice_type` | `multiple_choice` if exactly one answer is correct, `multiple_select` if more than one |
| `section_name` | The same for every question in a file. It appears in the app's section filter |
| `tags`, `bloom_level`, `idea_text`, `explanation` | Optional content; leave as `[]` or `""` if unused |

## Adding or editing questions

1. Edit an existing file in `data/`, or add a new `data/<exam>.json` for a new exam.
2. Run the validator:

   ```bash
   python validate.py
   ```

   It checks the schema, answer keys, choice types, unique IDs and duplicates.

## Disclaimer

This is an unofficial study aid, not affiliated with or endorsed by Microsoft or Google. Answers may be wrong or out of date, so always check them against the official documentation.
