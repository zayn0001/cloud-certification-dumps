"""Check every data/*.json file against the question schema. Exits 1 on any problem.

Usage: python validate.py
"""
import json
import re
import sys
from pathlib import Path

KEYS = {"question_id", "prompt", "answers", "tags", "question_choice_type", "section_name", "bloom_level", "idea_text"}
ANSWER_KEYS = {"text", "isCorrect", "explanation"}


def check_question(q):
    """Return a list of problems with one question dict."""
    if not isinstance(q, dict):
        return ["not an object"]
    errs = []
    if set(q) != KEYS:
        errs.append(f"keys {sorted(set(q) ^ KEYS)} missing or unexpected")
        return errs
    for k in ("question_id", "prompt", "question_choice_type", "section_name", "bloom_level", "idea_text"):
        if not isinstance(q[k], str):
            errs.append(f"{k} must be a string")
    if not isinstance(q["tags"], list) or not all(isinstance(t, str) for t in q["tags"]):
        errs.append("tags must be a list of strings")
    if not str(q["prompt"]).strip():
        errs.append("empty prompt")
    answers = q["answers"]
    if not isinstance(answers, list) or len(answers) < 2:
        return errs + ["needs at least 2 answers"]
    for a in answers:
        if not isinstance(a, dict) or set(a) != ANSWER_KEYS:
            return errs + [f"answer must have exactly {sorted(ANSWER_KEYS)}"]
        if not isinstance(a["text"], str) or not a["text"].strip():
            errs.append("empty answer text")
        if not isinstance(a["isCorrect"], bool):
            errs.append("isCorrect must be true/false")
        if not isinstance(a["explanation"], str):
            errs.append("explanation must be a string")
    texts = [str(a["text"]).strip().lower() for a in answers]
    if len(set(texts)) < len(texts):
        errs.append("duplicate answer text")
    n_correct = sum(a["isCorrect"] is True for a in answers)
    if n_correct == 0:
        errs.append("no correct answer")
    expected = "multiple_select" if n_correct > 1 else "multiple_choice"
    if q["question_choice_type"] != expected:
        errs.append(f"question_choice_type should be {expected} ({n_correct} correct)")
    return errs


def validate(data_dir):
    errors, ids, prompts = [], {}, {}
    files = sorted(Path(data_dir).glob("*.json"))
    if not files:
        return [f"no .json files in {data_dir}"]
    for path in files:
        try:
            questions = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{path.name}: invalid JSON: {e}")
            continue
        if not isinstance(questions, list):
            errors.append(f"{path.name}: top level must be a list")
            continue
        if len({q.get("section_name") for q in questions if isinstance(q, dict)}) > 1:
            errors.append(f"{path.name}: all questions in a file must share one section_name")
        for i, q in enumerate(questions):
            where = f"{path.name}[{i}] {q.get('question_id', '?') if isinstance(q, dict) else ''}"
            errors += [f"{where}: {e}" for e in check_question(q)]
            if not isinstance(q, dict) or not isinstance(q.get("prompt"), str):
                continue
            qid = q.get("question_id")
            if qid in ids:
                errors.append(f"{where}: duplicate question_id (also in {ids[qid]})")
            ids[qid] = path.name
            # same prompt with different options is a legit exam variant; same prompt + same options is a duplicate
            norm = lambda s: re.sub(r"\W+", " ", str(s).lower()).strip()
            key = (norm(q["prompt"]), frozenset(norm(a.get("text")) for a in q.get("answers") or [] if isinstance(a, dict)))
            if key in prompts:
                errors.append(f"{where}: duplicate of {prompts[key]}")
            prompts[key] = qid
    return errors


if __name__ == "__main__":
    good = {"question_id": "x-1", "prompt": "Q?", "tags": [], "question_choice_type": "multiple_choice",
            "section_name": "S", "bloom_level": "", "idea_text": "",
            "answers": [{"text": "a", "isCorrect": True, "explanation": ""},
                        {"text": "b", "isCorrect": False, "explanation": ""}]}
    assert check_question(good) == []
    assert "no correct answer" in check_question({**good, "answers": [{**a, "isCorrect": False} for a in good["answers"]]})
    assert check_question({**good, "question_choice_type": "multiple_select"})

    errors = validate(Path(__file__).parent / "data")
    for e in errors:
        print(e)
    print(f"{len(errors)} problem(s)" if errors else "All question files are valid.")
    sys.exit(1 if errors else 0)
