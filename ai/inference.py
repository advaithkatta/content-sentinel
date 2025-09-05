# ai/inference.py
"""
Combined inference:
 - Toxicity: unitary/toxic-bert (HF pipeline)
 - Spam: mshenoda/roberta-spam (HF pipeline)
 - Misinformation: retrieve evidence from Wikipedia, verify via an NLI model

Usage:
    python ai/inference.py
"""
import logging
from typing import List, Dict, Optional
import torch
import torch.nn.functional as F

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import wikipedia  # pip install wikipedia

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

### --- Moderation models (pipelines) ---
log.info("Loading toxicity & spam pipelines (may download models)...")
toxic_classifier = pipeline(
    "text-classification",
    model="unitary/toxic-bert",
    tokenizer="unitary/toxic-bert",
    truncation=True
)

spam_classifier = pipeline(
    "text-classification",
    model="mshenoda/roberta-spam",
    tokenizer="mshenoda/roberta-spam",
    truncation=True
)

### --- NLI verifier (FEVER-style) ---
# This is a strong NLI model trained on FEVER / NLI data; used to check evidence vs claim.
NLI_MODEL_NAME = "ynie/roberta-large-snli_mnli_fever_anli_R1_R2_R3-nli"

log.info("Loading NLI model (this is large)...")
nli_tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
nli_model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME)
# Prepare id2label mapping
try:
    _id2label = getattr(nli_model.config, "id2label", None)
    # ensure keys are ints
    if _id2label:
        id2label = {int(k): v.lower() for k, v in _id2label.items()}
    else:
        id2label = {}
except Exception:
    id2label = {}
log.info("NLI label mapping: %s", id2label)


# --------------------
# Helper: spam mapping
# --------------------
def _normalize_spam_prediction(spam_preds: List[Dict]) -> Dict:
    """
    spam_preds: list of {label, score}
    Returns: {"label":"SPAM"/"HAM"/original_label, "score": float}
    Heuristic mapping: prefer explicit 'spam'/'ham' substrings; otherwise map LABEL_1 -> SPAM.
    """
    # try to find explicit label names
    for p in spam_preds:
        lab = p["label"].lower()
        if "spam" in lab:
            return {"label": "SPAM", "score": float(p["score"])}
        if "ham" in lab:
            return {"label": "HAM", "score": float(p["score"])}

    # fallback: pick highest score and heuristically interpret LABEL_1 as SPAM
    best = max(spam_preds, key=lambda x: x["score"])
    best_lab = best["label"]
    best_score = float(best["score"])
    # heuristic: if label contains '1' it's often the positive class (spam). adjust if wrong for your model.
    if "1" in best_lab:
        return {"label": "SPAM", "score": best_score}
    elif "0" in best_lab:
        return {"label": "HAM", "score": best_score}
    else:
        # unknown label naming — return raw label but normalized score
        return {"label": best_lab, "score": best_score}


# --------------------
# Helper: wikipedia retrieval
# --------------------
def fetch_wikipedia_summaries(query: str, top_k: int = 3) -> List[Dict[str, str]]:
    """
    Search Wikipedia for `query` and return up to top_k page summaries.
    Returns a list of {"title": ..., "summary": ...}
    """
    try:
        titles = wikipedia.search(query, results=top_k)
    except Exception as e:
        log.warning("Wikipedia search failed: %s", e)
        return []

    results = []
    for t in titles:
        try:
            # disable auto_suggest for reliability on some queries
            page = wikipedia.page(t, auto_suggest=False)
            summary = page.summary
            results.append({"title": page.title, "summary": summary})
            if len(results) >= top_k:
                break
        except wikipedia.DisambiguationError as de:
            # choose first disambiguation option conservatively
            opt = de.options[0] if de.options else None
            if opt:
                try:
                    page = wikipedia.page(opt, auto_suggest=False)
                    results.append({"title": page.title, "summary": page.summary})
                except Exception:
                    continue
        except Exception:
            continue
    return results


# --------------------
# Helper: NLI check (evidence vs claim)
# --------------------
def nli_evidence_check(evidence: str, claim: str) -> Dict:
    """
    Returns a dictionary with:
      { "label": "entailment"/"contradiction"/"neutral", "score": float }
    Uses the loaded nli_model and tokenizer.
    """
    # tokenize as pair: premise=evidence, hypothesis=claim
    inputs = nli_tokenizer(evidence, claim, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        out = nli_model(**inputs)
        logits = out.logits  # shape (1, n_labels)
        probs = F.softmax(logits, dim=1).cpu().numpy()[0]

    # identify argmax label
    top_idx = int(probs.argmax())
    label = id2label.get(top_idx, None)
    # fallback guesses if id2label wasn't set
    if not label:
        # common ordering in many FEVER NLI models: 0: contradiction, 1: entailment, 2: neutral
        common_map = {0: "contradiction", 1: "entailment", 2: "neutral"}
        label = common_map.get(top_idx, str(top_idx))
    return {"label": label, "score": float(probs[top_idx]), "all_probs": probs.tolist()}


# --------------------
# Misinformation aggregator
# --------------------
def verify_claim_with_wiki(claim: str, top_k: int = 3,
                           entail_threshold: float = 0.80,
                           contradiction_threshold: float = 0.80) -> Dict:
    """
    Retrieve top_k wiki summaries for the claim, run NLI against each,
    and aggregate rules:
      - if any evidence yields entailment >= entail_threshold -> 'supported'
      - elif any evidence yields contradiction >= contradiction_threshold -> 'refuted'
      - else -> 'not_enough_info' with best_score
    """
    evidences = fetch_wikipedia_summaries(claim, top_k=top_k)
    if not evidences:
        return {"label": "undetermined", "score": 0.0, "reason": "no evidence found"}

    best_entail = {"score": 0.0, "evidence_title": None}
    best_contra = {"score": 0.0, "evidence_title": None}
    best_neutral = {"score": 0.0, "evidence_title": None}

    for e in evidences:
        ev_text = e["summary"]
        nli_res = nli_evidence_check(ev_text, claim)
        lab = nli_res["label"]
        sc = nli_res["score"]
        if "entail" in lab:
            if sc > best_entail["score"]:
                best_entail = {"score": sc, "evidence_title": e["title"], "nli": nli_res}
        elif "contradict" in lab or "contradiction" in lab:
            if sc > best_contra["score"]:
                best_contra = {"score": sc, "evidence_title": e["title"], "nli": nli_res}
        else:
            if sc > best_neutral["score"]:
                best_neutral = {"score": sc, "evidence_title": e["title"], "nli": nli_res}

    # Decision rules (conservative)
    if best_entail["score"] >= entail_threshold:
        return {"label": "supported", "score": best_entail["score"], "evidence": best_entail}
    if best_contra["score"] >= contradiction_threshold:
        return {"label": "refuted", "score": best_contra["score"], "evidence": best_contra}

    # otherwise return the strongest signal (could be neutral)
    # choose whichever max score among entail/contra/neutral
    candidates = [
        ("supported", best_entail["score"], best_entail),
        ("refuted", best_contra["score"], best_contra),
        ("not_enough_info", best_neutral["score"], best_neutral),
    ]
    best = max(candidates, key=lambda x: x[1])
    return {"label": best[0], "score": best[1], "evidence": best[2]}


# --------------------
# Public analyze function
# --------------------
def analyze_content(text: str) -> Dict:
    """
    Returns:
      {
        "toxicity": {"label":..., "score":...},
        "spam": {"label":..., "score":...},
        "misinformation": {"label": "supported|refuted|not_enough_info|undetermined", "score":..., "evidence": {...}}
      }
    """
    out = {}

    # 1) toxicity
    try:
        tox = toxic_classifier(text)[0]
        out["toxicity"] = {"label": tox["label"], "score": float(tox["score"])}
    except Exception as e:
        log.exception("Toxic pipeline failed: %s", e)
        out["toxicity"] = {"label": "error", "score": 0.0}

    # 2) spam (get all scores to be robust)
    try:
        spam_preds = spam_classifier(text, return_all_scores=True)[0]
        spam_norm = _normalize_spam_prediction(spam_preds)
        out["spam"] = spam_norm
    except Exception as e:
        log.exception("Spam pipeline failed: %s", e)
        out["spam"] = {"label": "error", "score": 0.0}

    # 3) misinformation: retrieve + NLI verify (conservative thresholds)
    try:
        misinfo_res = verify_claim_with_wiki(text, top_k=3,
                                             entail_threshold=0.85,
                                             contradiction_threshold=0.85)
        out["misinformation"] = misinfo_res
    except Exception as e:
        log.exception("Misinformation check failed: %s", e)
        # fallback: best-effort zero-shot (less reliable)
        try:
            zshot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
            zres = zshot(text, candidate_labels=["supported", "refuted", "not enough info"])
            out["misinformation"] = {"label": zres["labels"][0], "score": float(zres["scores"][0]), "note": "fallback zero-shot"}
        except Exception:
            out["misinformation"] = {"label": "undetermined", "score": 0.0}

    return out


# --------------------
# Quick test
# --------------------
if __name__ == "__main__":
    tests = [
        "The sun orbits the earth, obviously.",
        "Vaccines contain microchips.",
        "Grass is green.",
        "Water boils at 100 degrees Celsius at sea level.",
        "Covid-19 is a virus.",
        "Covid-19 isn't fun to have.",
        "FREE $$$ Click here to win a prize!"
    ]
    for t in tests:
        print("\nClaim/Text:", t)
        res = analyze_content(t)
        print("Result:")
        import json
        print(json.dumps(res, indent=2, ensure_ascii=False))