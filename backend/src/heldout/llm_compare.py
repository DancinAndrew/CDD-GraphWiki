"""
Run an LLM extractor on the same held-out paragraphs as the rules and score it the same way.

    ollama pull qwen3.5:9b
    PYTHONPATH=backend python -m src.heldout.llm_compare run --set uk_mlr_2017   # calls the model
    PYTHONPATH=backend python -m src.heldout.llm_compare score                   # offline: scores every cached run

`run` sends one held-out paragraph per request, with the task definition taken from
data/heldout/ANNOTATION_GUIDELINE.md, and stores every raw answer in data/heldout/llm_runs/<set>/<model>.jsonl.
The default model is the open-weight qwen3.5:9b served locally by Ollama (temperature 0, fixed seed), so the
run needs no API key. Any OpenAI-compatible endpoint works through --base-url and --model; a remote endpoint
reads its key from NVIDIA_API_KEY. There is no mock fallback: a failed request is recorded as a failure and
counted as "no types". `score` needs no model, so anyone can recompute the numbers from the cached answers.
"""
import os
import re
import sys
import json
import time
import hashlib
import argparse
from typing import Any, Dict, List, Optional, Set

import httpx

from src.paths import find_data_dir
from src.heldout.evaluate import (
    HELDOUT_SETS, HeldOutCorpus, load_corpus, score, corpus_stats, error_rows, format_report, results_dir,
)

DEFAULT_MODEL = "qwen3.5:9b"
DEFAULT_BASE_URL = "http://localhost:11434/v1"  # Ollama's OpenAI-compatible endpoint
SEED = 7
PROMPT_VERSION = "heldout-v1"

SYSTEM_PROMPT = """You annotate clauses of {title} ({description}) with obligation types.

{guideline}

Answer with JSON only, in this form:
{{"labels": [{{"clause_id": "<an id from the input>", "types": ["<type>", ...]}}]}}
List only clauses that have at least one type. Use only the eight type names above. If no clause has a type, answer {{"labels": []}}."""

USER_PROMPT = """Paragraph {paragraph} of {title}. Each line is one clause: its id in square brackets, then its text.

{clauses}"""


def guideline_text(data_dir: str) -> str:
    """The parts of the annotation guideline that define the task (everything from 'Unit of annotation' on)."""
    with open(os.path.join(data_dir, "heldout", "ANNOTATION_GUIDELINE.md"), encoding="utf-8") as f:
        text = f.read()
    start = text.index("## Unit of annotation")
    end = text.index("## Paragraph-level view")
    return text[start:end].strip()


def paragraph_units(corpus: HeldOutCorpus) -> List[Dict[str, Any]]:
    units: Dict[str, List] = {}
    for clause in corpus.held_out:
        units.setdefault(corpus.paragraph_of[clause.clause_id], []).append(clause)
    out = []
    for paragraph, clauses in units.items():
        lines = []
        for c in clauses:
            text = re.sub(r"^#+\s*\S+\s*", "", c.raw_text).strip()  # drop the "### 6.14A" heading marker
            lines.append(f"[{c.clause_id}] {text}")
        out.append({"paragraph": paragraph, "clause_ids": [c.clause_id for c in clauses], "text": "\n".join(lines)})
    return out


def _load_env_key(repo_root: str, name: str) -> Optional[str]:
    if os.getenv(name):
        return os.getenv(name)
    env_path = os.path.join(repo_root, ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"{name}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None


def parse_answer(content: str) -> Dict[str, Any]:
    """Pull the JSON object out of a model answer (models sometimes wrap it in prose or code fences)."""
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.S)
    match = re.search(r"\{.*\}", content, flags=re.S)
    if not match:
        raise ValueError("no JSON object in the answer")
    return json.loads(match.group(0))


def run_model(data_dir: str, set_name: str, model: str, base_url: str, out_path: str,
              limit: Optional[int] = None) -> None:
    repo_root = os.path.dirname(os.path.abspath(data_dir))
    local = any(host in base_url for host in ("localhost", "127.0.0.1"))
    api_key = "ollama" if local else _load_env_key(repo_root, "NVIDIA_API_KEY")
    if not api_key:
        sys.exit("NVIDIA_API_KEY is not set for a remote endpoint; `score` works without it on the cached answers.")
    corpus = load_corpus(data_dir, set_name)
    system = SYSTEM_PROMPT.format(title=corpus.spec.title, description=corpus.spec.description,
                                  guideline=guideline_text(data_dir))
    units = paragraph_units(corpus)[:limit] if limit else paragraph_units(corpus)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as out, httpx.Client(timeout=600) as client:
        for i, unit in enumerate(units, 1):
            user = USER_PROMPT.format(paragraph=unit["paragraph"], title=corpus.spec.title, clauses=unit["text"])
            record: Dict[str, Any] = {
                "paragraph": unit["paragraph"], "model": model, "prompt_version": PROMPT_VERSION,
                "prompt_sha256": hashlib.sha256((system + "\n" + user).encode("utf-8")).hexdigest(),
                "temperature": 0.0, "seed": SEED, "base_url": base_url,
            }
            messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
            if local:
                record["thinking"] = False
            for attempt in range(3):
                try:
                    if local:
                        # Ollama's native API, so the model's reasoning mode can be switched off and JSON enforced.
                        response = client.post(
                            base_url.replace("/v1", "") + "/api/chat",
                            json={"model": model, "stream": False, "think": False, "format": "json",
                                  "options": {"temperature": 0, "seed": SEED, "num_ctx": 8192},
                                  "messages": messages},
                        )
                        response.raise_for_status()
                        record["response"] = response.json()["message"]["content"]
                    else:
                        response = client.post(
                            f"{base_url}/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
                            json={"model": model, "temperature": 0.0, "seed": SEED, "max_tokens": 4096,
                                  "messages": messages},
                        )
                        response.raise_for_status()
                        record["response"] = response.json()["choices"][0]["message"]["content"]
                    record.pop("error", None)
                    break
                except Exception as e:  # recorded, never replaced by a mock answer
                    record["error"] = f"{type(e).__name__}: {str(e)[:200]}"
                    time.sleep(2 * (attempt + 1))
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            print(f"[{i}/{len(units)}] {unit['paragraph']}: {'error' if 'error' in record else 'ok'}")


def load_answers(path: str, corpus: HeldOutCorpus) -> Dict[str, Any]:
    """Turn cached answers into predictions, counting failures and citations of clause IDs that were not given."""
    units = {u["paragraph"]: set(u["clause_ids"]) for u in paragraph_units(corpus)}
    types = set(corpus.types)
    predictions: Dict[str, Set[str]] = {c.clause_id: set() for c in corpus.held_out}
    stats = {"paragraphs_sent": 0, "failed_requests": 0, "unparseable_answers": 0,
             "cited_clause_ids": 0, "invalid_clause_ids": [], "invalid_type_names": []}
    with open(path, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            stats["paragraphs_sent"] += 1
            if "error" in record:
                stats["failed_requests"] += 1
                continue
            try:
                labels = parse_answer(record["response"]).get("labels", [])
            except (ValueError, json.JSONDecodeError):
                stats["unparseable_answers"] += 1
                continue
            given = units.get(record["paragraph"], set())
            for label in labels if isinstance(labels, list) else []:
                clause_id = str(label.get("clause_id", ""))
                stats["cited_clause_ids"] += 1
                if clause_id not in given:
                    stats["invalid_clause_ids"].append(f"{record['paragraph']}: {clause_id}")
                    continue
                for t in label.get("types", []) or []:
                    if t in types:
                        predictions[clause_id].add(t)
                    else:
                        stats["invalid_type_names"].append(f"{record['paragraph']}: {t}")
    missing = set(units) - {json.loads(l)["paragraph"] for l in open(path, encoding="utf-8")}
    stats["paragraphs_missing_from_run"] = sorted(missing)
    return {"predictions": predictions, "stats": stats}


def score_cached(data_dir: str, set_name: str, path: str, out_dir: str) -> Dict[str, Any]:
    corpus = load_corpus(data_dir, set_name)
    loaded = load_answers(path, corpus)
    predictions, stats = loaded["predictions"], loaded["stats"]
    first = json.loads(open(path, encoding="utf-8").readline())
    model, prompt_version = first["model"], first.get("prompt_version", PROMPT_VERSION)
    scores = score(corpus, predictions)
    invalid = len(stats["invalid_clause_ids"])
    notes = [
        f"Model: {model} (temperature 0, seed {SEED}, reasoning mode off, prompt {prompt_version}), one request per held-out paragraph, "
        f"given the task definition from ANNOTATION_GUIDELINE.md.",
        f"Requests: {stats['paragraphs_sent']} sent, {stats['failed_requests']} failed, "
        f"{stats['unparseable_answers']} answers not valid JSON.",
        f"Citations: {stats['cited_clause_ids']} clause IDs returned, {invalid} not among the clauses sent "
        f"({(invalid / stats['cited_clause_ids'] * 100) if stats['cited_clause_ids'] else 0:.1f}%).",
    ]
    if stats["invalid_clause_ids"]:
        notes.append("Invalid clause IDs: " + "; ".join(stats["invalid_clause_ids"][:20]))
    slug = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"llm_{slug}_report.txt"), "w", encoding="utf-8") as f:
        f.write(format_report(f"LLM extractor ({model}) on held-out {corpus.spec.title} paragraphs",
                              corpus_stats(corpus), scores, error_rows(corpus, predictions), notes))
    summary = {"model": model, "prompt_version": prompt_version, "requests": {k: v for k, v in stats.items()},
               "scores": scores}
    with open(os.path.join(out_dir, f"llm_{slug}_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return summary


def model_slug(model: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", model.lower()).strip("_")


def runs_path(data_dir: str, set_name: str, model: str) -> str:
    return os.path.join(data_dir, "heldout", "llm_runs", set_name, f"{model_slug(model)}.jsonl")


def score_all(data_dir: str) -> Dict[str, Dict[str, Any]]:
    """Score every cached run of every held-out set; needs no model."""
    summaries: Dict[str, Dict[str, Any]] = {}
    for set_name in HELDOUT_SETS:
        folder = os.path.join(data_dir, "heldout", "llm_runs", set_name)
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if name.endswith(".jsonl"):
                summaries[f"{set_name}/{name[:-6]}"] = score_cached(
                    data_dir, set_name, os.path.join(folder, name), results_dir(data_dir, set_name))
    return summaries


def main() -> None:
    data_dir = find_data_dir()
    parser = argparse.ArgumentParser(description="LLM comparison on held-out regulatory paragraphs")
    parser.add_argument("command", choices=["run", "score"])
    parser.add_argument("--set", default=None, choices=sorted(HELDOUT_SETS), help="held-out set to run (required for run)")
    parser.add_argument("--model", default=os.getenv("HELDOUT_LLM_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.getenv("HELDOUT_LLM_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--limit", type=int, default=None, help="only the first N paragraphs (smoke test)")
    args = parser.parse_args()
    if args.command == "run":
        if not args.set:
            parser.error("run needs --set")
        run_model(data_dir, args.set, args.model, args.base_url, runs_path(data_dir, args.set, args.model), args.limit)
    for key, summary in score_all(data_dir).items():
        o = summary["scores"]["paragraph"]["overall"]
        r = summary["requests"]
        print(f"{key:<32} paragraph: found {o['tp']}/{o['tp'] + o['fn']}, precision {o['precision']:.2f} | "
              f"invalid clause IDs {len(r['invalid_clause_ids'])}/{r['cited_clause_ids']}, failed {r['failed_requests']}")


if __name__ == "__main__":
    main()
