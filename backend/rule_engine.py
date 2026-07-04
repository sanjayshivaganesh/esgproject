import math
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    import joblib
except Exception:
    joblib = None
import numpy as np
from sklearn.cluster import KMeans

DEBUG = True
CONFIG = {
    "MAX_HITS_PER_CATEGORY": 3,
    "RANDOM_STATE": 42,
    "MIN_VALID_SENTENCE_LENGTH": 10,
    "LONG_SENTENCE_SPLIT_THRESHOLD": 200,
    "SENTENCE_OBJECT_DEDUPLICATION_THRESHOLD": 0.90,
    "DUPLICATE_THRESHOLD": 0.92,
    "SIMILARITY_THRESHOLD": 0.55,
    "OVERALL_MATCH_THRESHOLD": 0.45,
    "TOPIC_REJECT_CROSS_TOPIC": True,
    "OUTCOME_ENTITY_MATCH_WEIGHT": 0.30,
    "OUTCOME_SUBENTITY_MATCH_WEIGHT": 0.20,
    "MIN_TARGETS_FOR_KMEANS": 5,
    "MAX_TARGET_CLUSTERS": 5,
    "KMEANS_N_INIT": 10,
    "EMBEDDING_DIM": 384,
    "OUTCOME_NUMERIC_SCORE_PER_VALUE": 8,
    "OUTCOME_ENTITY_SCORE_PER_ENTITY": 10,
    "OUTCOME_SCOPE_SCORE": 15,
    "OUTCOME_METRIC_PRESENT_SCORE": 10,
    "OUTCOME_COMPARISON_YEAR_SCORE": 6,
    "OUTCOME_BASELINE_YEAR_SCORE": 6,
    "OUTCOME_MULTIPLE_NUMERIC_BONUS": 8,
    "OUTCOME_MULTIPLE_KPI_BONUS": 5,
    "OUTCOME_MULTIPLE_ENTITY_BONUS": 5,
    "OUTCOME_TRIAD_CONFIDENCE_BONUS": 10,
    "OUTCOME_MAX_SCORE": 100.0,
    "CLAIM_PROMOTIONAL_WEIGHT": 3.0,
    "CLAIM_VAGUE_WEIGHT": 1.5,
    "TARGET_PRESSURE_WEIGHT": 10,
    "TARGET_DENSITY_LOG_BASE": 10,
    "SUPPORT_RATIO_MAX": 2.0,
    "SUPPORT_RATIO_STRENGTH_DIVISOR": 50,
    "TRANSPARENCY_FRAMEWORK_DIVISOR": 3,
    "TRANSPARENCY_ASSURANCE_DIVISOR": 2,
    "TRANSPARENCY_SCOPE_DIVISOR": 3,
    "TRANSPARENCY_METHODOLOGY_DIVISOR": 3,
    "TRANSPARENCY_FRAMEWORK_WEIGHT": 0.35,
    "TRANSPARENCY_ASSURANCE_WEIGHT": 0.35,
    "TRANSPARENCY_SCOPE_WEIGHT": 0.2,
    "TRANSPARENCY_METHODOLOGY_WEIGHT": 0.1,
    "CONFIDENCE_BASE_SCORE": 35,
    "CONFIDENCE_RULE_SIGNAL_CAP": 35,
    "CONFIDENCE_RULE_SIGNAL_MULTIPLIER": 3,
    "CONFIDENCE_QUANTIFIED_CAP": 30,
    "CONFIDENCE_QUANTIFIED_MULTIPLIER": 8,
    "SUPPORT_RATIO_STRONG_THRESHOLD": 1.0,
    "SUPPORT_RATIO_PARTIAL_THRESHOLD": 0.5,
}

MAX_HITS_PER_CATEGORY = CONFIG["MAX_HITS_PER_CATEGORY"]
RANDOM_STATE = CONFIG["RANDOM_STATE"]
MIN_VALID_SENTENCE_LENGTH = CONFIG["MIN_VALID_SENTENCE_LENGTH"]
LONG_SENTENCE_SPLIT_THRESHOLD = CONFIG["LONG_SENTENCE_SPLIT_THRESHOLD"]
DEFAULT_NEUTRAL_LABEL = "NEUTRAL"
VALID_LABELS = ["CLAIM", "OUTCOME", "TARGET", "TRANSPARENCY", "NEUTRAL"]

BASE_DIR = Path(__file__).resolve().parent
MODEL_FILENAME = "model_copy.pkl"
MODEL_CANDIDATE_PATHS = [
    BASE_DIR / "outputs" / MODEL_FILENAME,
    BASE_DIR / MODEL_FILENAME,
    BASE_DIR.parent / "greenwashing_ml" / "outputs" / MODEL_FILENAME,
    BASE_DIR.parent / "greenwashing_ml" / MODEL_FILENAME,
]
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
SENTENCE_OBJECT_DEDUPLICATION_THRESHOLD = CONFIG[
    "SENTENCE_OBJECT_DEDUPLICATION_THRESHOLD"
]
EMBEDDING_DUPLICATE_THRESHOLD = CONFIG["DUPLICATE_THRESHOLD"]
TARGET_OUTCOME_SIMILARITY_THRESHOLD = CONFIG["SIMILARITY_THRESHOLD"]
OUTCOME_ENTITY_WEIGHT = CONFIG["OUTCOME_ENTITY_MATCH_WEIGHT"]
OUTCOME_SUBENTITY_WEIGHT = CONFIG["OUTCOME_SUBENTITY_MATCH_WEIGHT"]
MIN_TARGETS_FOR_KMEANS = CONFIG["MIN_TARGETS_FOR_KMEANS"]
MAX_TARGET_CLUSTERS = CONFIG["MAX_TARGET_CLUSTERS"]
KMEANS_N_INIT = CONFIG["KMEANS_N_INIT"]

OUTCOME_NUMERIC_SCORE_PER_VALUE = CONFIG["OUTCOME_NUMERIC_SCORE_PER_VALUE"]
OUTCOME_ENTITY_SCORE_PER_ENTITY = CONFIG["OUTCOME_ENTITY_SCORE_PER_ENTITY"]
OUTCOME_SCOPE_SCORE = CONFIG["OUTCOME_SCOPE_SCORE"]
OUTCOME_METRIC_PRESENT_SCORE = CONFIG["OUTCOME_METRIC_PRESENT_SCORE"]
OUTCOME_COMPARISON_YEAR_SCORE = CONFIG["OUTCOME_COMPARISON_YEAR_SCORE"]
OUTCOME_BASELINE_YEAR_SCORE = CONFIG["OUTCOME_BASELINE_YEAR_SCORE"]
OUTCOME_MULTIPLE_NUMERIC_BONUS = CONFIG["OUTCOME_MULTIPLE_NUMERIC_BONUS"]
OUTCOME_MULTIPLE_KPI_BONUS = CONFIG["OUTCOME_MULTIPLE_KPI_BONUS"]
OUTCOME_MULTIPLE_ENTITY_BONUS = CONFIG["OUTCOME_MULTIPLE_ENTITY_BONUS"]
OUTCOME_MAX_SCORE = CONFIG["OUTCOME_MAX_SCORE"]

CONFIDENCE_BUCKETS = [
    (0.0, 0.50, "<0.50"),
    (0.50, 0.70, "0.50–0.70"),
    (0.70, 0.85, "0.70–0.85"),
    (0.85, 0.95, "0.85–0.95"),
    (0.95, float("inf"), ">0.95"),
]

UNIT_PATTERN = (
    r"%|percent|tons?|tonnes?|metric\s*tons?|tco2e|mtco2e|kg|g|mt|mwh|gwh|kwh|"
    r"million|billion|liters?|litres?|gallons?|m3|cubic\s*met(?:er|re)s?|"
    r"hectares?|acres?"
)
APPROXIMATE_QUALIFIER_PATTERN = (
    r"~|approximately|approx\.?|about|around|more than|less than"
)
NUMERIC_VALUE_PATTERN = re.compile(r"\d+(?:\.\d+)?")
YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
HORIZON_PATTERN = re.compile(r"\bby\s+(20\d{2})\b")
MEASUREMENT_UNIT_PATTERN = re.compile(
    rf"\d+(?:\.\d+)?\s?(?:{UNIT_PATTERN})",
    flags=re.IGNORECASE,
)
KPI_RANGE_PATTERN = re.compile(
    rf"\bbetween\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)\s*({UNIT_PATTERN})\b",
    flags=re.IGNORECASE,
)
KPI_SINGLE_PATTERN = re.compile(
    rf"(?:(?P<qualifier>{APPROXIMATE_QUALIFIER_PATTERN})\s*)?"
    rf"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>{UNIT_PATTERN})\b",
    flags=re.IGNORECASE,
)
COMPARISON_YEAR_PATTERNS = [
    re.compile(
        r"\b(?:compared to|versus|vs\.?|against|from)\s+(20\d{2}|19\d{2})\b",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:year-on-year|yoy)\b.*?\b(20\d{2}|19\d{2})\b", flags=re.IGNORECASE
    ),
]
BASELINE_YEAR_PATTERNS = [
    re.compile(
        r"\bbaseline\s+year\s+(?:of\s+)?(20\d{2}|19\d{2})\b", flags=re.IGNORECASE
    ),
    re.compile(
        r"\b(?:from|vs\.?|versus)\s+(20\d{2}|19\d{2})\s+baseline\b", flags=re.IGNORECASE
    ),
    re.compile(r"\bbaseline\s+(20\d{2}|19\d{2})\b", flags=re.IGNORECASE),
]

ENTITY_PATTERNS = {
    "emissions": r"\b(emissions?|ghg|greenhouse\s*gas|carbon|co2|co2e|tco2e|mtco2e)\b",
    "scope_1": r"\bscope\s*1\b",
    "scope_2": r"\bscope\s*2\b",
    "scope_3": r"\bscope\s*3\b",
    "energy": r"\b(energy|electricity|power)\b",
    "renewable_energy": r"\b(renewable\s*(energy|electricity|power)|renewables|solar|wind|hydro)\b",
    "water": r"\bwater\b",
    "water_stewardship": r"\bwater\s+stewardship\b",
    "waste": r"\b(waste|landfill)\b",
    "recycling": r"\b(recycling|recycled)\b",
    "biodiversity": r"\b(biodiversity|ecosystem|habitat)\b",
    "forestry": r"\b(forestry|forest|deforestation|reforestation)\b",
    "nature": r"\b(nature|nature-positive|nature positive)\b",
    "supply_chain_emissions": r"\bsupply\s*chain\s*emissions?\b",
    "supply_chain": r"\bsupply\s*chain\b",
    "fleet_emissions": r"\bfleet\s*emissions?\b",
    "methane": r"\bmethane\b",
    "plastic_waste": r"\b(plastic\s*waste|packaging\s*waste)\b",
    "materials": r"\bmaterials?\b",
    "packaging": r"\bpackaging\b",
    "plastics": r"\bplastics?\b",
    "hydrogen": r"\bhydrogen\b",
    "battery": r"\bbatter(?:y|ies)\b",
    "critical_minerals": r"\bcritical\s+minerals?\b",
    "circular_economy": r"\bcircular\s+economy\b",
    "manufacturing": r"\bmanufacturing\b",
    "energy_efficiency": r"\benergy\s+efficiency\b",
}
COMPILED_ENTITY_PATTERNS = {
    name: re.compile(pattern, flags=re.IGNORECASE)
    for name, pattern in ENTITY_PATTERNS.items()
}

METRIC_PATTERNS = [
    (
        "reduction",
        re.compile(r"reduc|decreas|lower|cut|avoid|eliminate", flags=re.IGNORECASE),
    ),
    ("improvement", re.compile(r"improv|increas|boost|grow", flags=re.IGNORECASE)),
    ("recycling", re.compile(r"recycl", flags=re.IGNORECASE)),
    ("restoration", re.compile(r"restor|conserv|protect", flags=re.IGNORECASE)),
    ("achievement", re.compile(r"achiev|reach", flags=re.IGNORECASE)),
]

_embedding_model: Optional[Any] = None
_embedding_model_failed = False


# ------------------------------
# Shared safety helpers
# ------------------------------
def debug_log(message: str) -> None:
    if DEBUG:
        print(f"[DEBUG] {message}")


def normalize_embedding(embedding: Optional[np.ndarray]) -> Optional[np.ndarray]:
    if embedding is None:
        return None
    try:
        array = np.asarray(embedding, dtype=np.float32)
        if array.ndim != 1:
            array = array.reshape(-1)
        norm = np.linalg.norm(array)
        if not np.isfinite(norm):
            return np.zeros(CONFIG["EMBEDDING_DIM"], dtype=np.float32)
        if norm == 0.0:
            return np.zeros_like(array, dtype=np.float32)
        return (array / norm).astype(np.float32)
    except Exception:
        return np.zeros(CONFIG["EMBEDDING_DIM"], dtype=np.float32)


def cosine_similarity(a: Optional[np.ndarray], b: Optional[np.ndarray]) -> float:
    normalized_a = normalize_embedding(a)
    normalized_b = normalize_embedding(b)
    if normalized_a is None or normalized_b is None:
        return 0.0
    if np.linalg.norm(normalized_a) == 0.0 or np.linalg.norm(normalized_b) == 0.0:
        return 0.0
    return float(np.dot(normalized_a, normalized_b))


def zero_embedding_matrix(size: int) -> np.ndarray:
    return np.zeros((size, CONFIG["EMBEDDING_DIM"]), dtype=np.float32)


def load_ml_model() -> Tuple[Optional[Any], List[str]]:
    for model_path in MODEL_CANDIDATE_PATHS:
        if not model_path.exists():
            continue
        try:
            model = joblib.load(model_path)
            classes = list(getattr(model, "classes_", []))
            print(f"ML model loaded successfully from {model_path}!")
            print(f"Model classes: {classes}")
            return model, classes
        except Exception as error:
            print(f"Error loading ML model from {model_path}: {error}")
    print(
        "ML model not found. ML inference disabled; continuing with rule engine only."
    )
    return None, []


ml_model, model_classes = load_ml_model()


# ------------------------------
# Phase 1: Classification
# ------------------------------
def _default_probabilities() -> Dict[str, float]:
    probabilities = {label: 0.0 for label in VALID_LABELS}
    probabilities[DEFAULT_NEUTRAL_LABEL] = 1.0
    return probabilities


def get_embedding_model():
    """Lazy-load the embedding model so import-time startup stays lightweight."""
    global _embedding_model, _embedding_model_failed
    if _embedding_model_failed:
        return None
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        except Exception as error:
            print(f"Error loading embedding model: {error}")
            _embedding_model_failed = True
            return None
    return _embedding_model


def predict_sentence(sentence: str) -> Dict[str, Any]:
    """
    Predict sentence label using ML model as primary source.
    Returns {"label": str, "confidence": float, "probabilities": dict}
    Labels: CLAIM, OUTCOME, TARGET, TRANSPARENCY, NEUTRAL
    """
    if ml_model is None:
        return {
            "label": DEFAULT_NEUTRAL_LABEL,
            "confidence": 0.0,
            "probabilities": _default_probabilities(),
        }

    probabilities = {label: 0.0 for label in VALID_LABELS}

    try:
        available_classes = list(getattr(ml_model, "classes_", []))
        if not available_classes:
            return {
                "label": DEFAULT_NEUTRAL_LABEL,
                "confidence": 0.0,
                "probabilities": _default_probabilities(),
            }

        predicted_label = str(ml_model.predict([sentence])[0]).strip().upper()
        proba = ml_model.predict_proba([sentence])[0]
        predicted_index = int(np.argmax(proba))
        confidence = float(proba[predicted_index]) if len(proba) else 0.0

        for index, model_class in enumerate(available_classes):
            standardized_class = str(model_class).strip().upper()
            if standardized_class in probabilities:
                probabilities[standardized_class] = float(proba[index])

        label = (
            predicted_label
            if predicted_label in VALID_LABELS
            else DEFAULT_NEUTRAL_LABEL
        )

        return {
            "label": label,
            "confidence": confidence,
            "probabilities": probabilities,
        }
    except Exception as error:
        print(f"ML inference error: {error}")
        return {
            "label": DEFAULT_NEUTRAL_LABEL,
            "confidence": 0.0,
            "probabilities": _default_probabilities(),
        }


def compute_validation_flags(sentence: str) -> Dict[str, Any]:
    """
    Pure structural validation (no label knowledge).
    Returns only whether sentence is well-formed and structural flags.
    """
    normalized_sentence = normalize(sentence)
    is_valid = len(normalized_sentence) > MIN_VALID_SENTENCE_LENGTH

    return {
        "is_valid": is_valid,
        "flags": {
            "has_numbers": bool(NUMERIC_VALUE_PATTERN.search(normalized_sentence)),
            "has_year": bool(YEAR_PATTERN.search(normalized_sentence)),
            "has_measurement_unit": bool(
                MEASUREMENT_UNIT_PATTERN.search(normalized_sentence)
            ),
        },
    }


def resolve_label(ml_prediction: Dict[str, Any], validation: Dict[str, Any]) -> str:
    """
    Strict ML-first architecture: ML is the sole classifier.
    Structural validation may downgrade invalid text to NEUTRAL,
    but rules never replace the ML label with another class.
    """
    ml_label = ml_prediction["label"]
    is_valid = validation.get("is_valid", True)

    if not is_valid:
        return DEFAULT_NEUTRAL_LABEL

    return ml_label


def determine_label(
    sentence: str,
    ml_label: Optional[str] = None,
    confidence: Optional[float] = None,
    prediction: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Determine final label with ML-first structural validation.
    Kept backward compatible with the original signature.
    """
    if prediction is None:
        if ml_label is not None:
            sanitized_label = str(ml_label).strip().upper()
            prediction = {
                "label": sanitized_label
                if sanitized_label in VALID_LABELS
                else DEFAULT_NEUTRAL_LABEL,
                "confidence": float(confidence or 0.0),
                "probabilities": {label: 0.0 for label in VALID_LABELS},
            }
        else:
            prediction = predict_sentence(sentence)
    validation = compute_validation_flags(sentence)
    return resolve_label(prediction, validation)


def build_sentence_objects(text: str) -> List[Dict[str, Any]]:
    """Build standardized sentence objects from document text.

    Uses existing helpers: `split_sentences`, `deduplicate_sentences_with_embeddings`,
    `predict_sentence`, `determine_label`, `extract_kpi_grounding`, and
    `score_outcome_strength` to populate each sentence dict with the fields
    expected by downstream code.
    """
    try:
        raw_sentences = split_sentences(text)
        sentences, embeddings = deduplicate_sentences_with_embeddings(
            raw_sentences,
            threshold=SENTENCE_OBJECT_DEDUPLICATION_THRESHOLD,
        )
        if not sentences:
            return []

        if len(embeddings) != len(sentences):
            embeddings = zero_embedding_matrix(len(sentences))

        sentence_objects: List[Dict[str, Any]] = []
        total_entities_extracted = 0
        for index, sentence in enumerate(sentences):
            embedding = (
                embeddings[index]
                if len(embeddings) > index
                else np.zeros(CONFIG["EMBEDDING_DIM"], dtype=float)
            )
            prediction = predict_sentence(sentence)
            final_label = determine_label(sentence, prediction=prediction)
            grounding = extract_kpi_grounding(sentence)
            total_entities_extracted += int(grounding.get("entity_count", 0) or 0)
            sentence_obj = {
                "text": sentence,
                "label": final_label,
                "confidence": float(prediction.get("confidence", 0.0) or 0.0),
                "probabilities": prediction.get(
                    "probabilities", _default_probabilities()
                ),
                "prediction": prediction,
                "embedding": embedding,
                "grounding": grounding,
                "linked_targets": [],
                "linked_outcomes": [],
                "best_link_similarity": 0.0,
                "best_semantic_similarity": 0.0,
                "best_overall_match": 0.0,
                "index": index,
            }
            sentence_obj["outcome_strength"] = score_outcome_strength(sentence_obj)
            sentence_objects.append(sentence_obj)

        debug_log(f"Entities extracted across sentences: {total_entities_extracted}")
        return sentence_objects
    except Exception as error:
        print(f"Error building sentence objects: {error}")
        return []


def extract_entities(text: str) -> List[str]:
    entities: List[str] = []
    for entity_name, pattern in COMPILED_ENTITY_PATTERNS.items():
        if pattern.search(text):
            entities.append(entity_name)
    return entities


def _resolve_primary_entity(
    entities: Sequence[str],
) -> Tuple[Optional[str], Optional[str]]:
    # Handle common scope combinations first
    if "scope_1" in entities and "scope_2" in entities:
        return "emissions", "scope_1_2"
    if "scope_1" in entities:
        return "emissions", "scope_1"
    if "scope_2" in entities:
        return "emissions", "scope_2"
    if "scope_3" in entities:
        return "emissions", "scope_3"

    entity_priority = [
        "emissions",
        "energy",
        "renewable_energy",
        "water",
        "water_stewardship",
        "waste",
        "recycling",
        "biodiversity",
        "forestry",
        "nature",
        "materials",
        "packaging",
        "plastics",
        "hydrogen",
        "battery",
        "critical_minerals",
        "circular_economy",
        "supply_chain_emissions",
        "supply_chain",
        "manufacturing",
        "energy_efficiency",
        "methane",
        "fleet_emissions",
    ]
    for candidate in entity_priority:
        if candidate in entities:
            return candidate, None
    return None, None


def _extract_first_year(patterns: Sequence[re.Pattern], text: str) -> Optional[int]:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return int(match.group(1))
    return None


def _spans_overlap(span_a: Tuple[int, int], span_b: Tuple[int, int]) -> bool:
    return span_a[0] < span_b[1] and span_b[0] < span_a[1]


def extract_kpi_matches(sentence: str) -> List[Dict[str, Any]]:
    normalized_sentence = normalize(sentence)
    matches: List[Dict[str, Any]] = []
    occupied_spans: List[Tuple[int, int]] = []

    for match in KPI_RANGE_PATTERN.finditer(normalized_sentence):
        span = match.span()
        occupied_spans.append(span)
        matches.append(
            {
                "value": float(match.group(1)),
                "value_max": float(match.group(2)),
                "unit": match.group(3).strip().lower(),
                "qualifier": "between",
                "text": match.group(0),
            }
        )

    for match in KPI_SINGLE_PATTERN.finditer(normalized_sentence):
        span = match.span()
        if any(_spans_overlap(span, occupied_span) for occupied_span in occupied_spans):
            continue
        qualifier = match.group("qualifier")
        matches.append(
            {
                "value": float(match.group("value")),
                "value_max": None,
                "unit": match.group("unit").strip().lower(),
                "qualifier": qualifier.lower() if qualifier else None,
                "text": match.group(0),
            }
        )
        occupied_spans.append(span)

    return matches


def extract_kpi_grounding(sentence: str) -> Dict[str, Any]:
    try:
        normalized_sentence = normalize(sentence)
        horizon_match = HORIZON_PATTERN.search(normalized_sentence)
        horizon = int(horizon_match.group(1)) if horizon_match else None

        entities = extract_entities(normalized_sentence)
        entity, subentity = _resolve_primary_entity(entities)

        metric = None
        for metric_name, pattern in METRIC_PATTERNS:
            if pattern.search(normalized_sentence):
                metric = metric_name
                break

        kpi_matches = extract_kpi_matches(normalized_sentence)
        primary_kpi = kpi_matches[0] if kpi_matches else {}
        unit = primary_kpi.get("unit")
        metric_present = bool(kpi_matches)
        numeric_count = len(NUMERIC_VALUE_PATTERN.findall(normalized_sentence))
        comparison_year = _extract_first_year(
            COMPARISON_YEAR_PATTERNS, normalized_sentence
        )
        baseline_year = _extract_first_year(BASELINE_YEAR_PATTERNS, normalized_sentence)

        return {
            "entities": entities,
            "horizon": horizon,
            "entity_count": len(entities),
            "entity": entity,
            "subentity": subentity,
            "metric": metric,
            "value": primary_kpi.get("value"),
            "value_max": primary_kpi.get("value_max"),
            "qualifier": primary_kpi.get("qualifier"),
            "unit": unit,
            "metric_present": metric_present,
            "metric_type": "percentage"
            if unit in {"%", "percent"}
            else "absolute"
            if unit
            else "none",
            "kpi_count": len(kpi_matches),
            "kpi_matches": kpi_matches,
            "numeric_count": numeric_count,
            "comparison_year": comparison_year,
            "baseline_year": baseline_year,
            "multiple_kpis": len(kpi_matches) > 1,
            "has_scope_terms": any(
                scope in normalized_sentence
                for scope in ["scope 1", "scope 2", "scope 3"]
            ),
        }
    except Exception as error:
        print(f"Error extracting KPI grounding: {error}")
        return {
            "entities": [],
            "horizon": None,
            "entity_count": 0,
            "entity": None,
            "subentity": None,
            "metric": None,
            "value": None,
            "value_max": None,
            "qualifier": None,
            "unit": None,
            "metric_present": False,
            "metric_type": "none",
            "kpi_count": 0,
            "kpi_matches": [],
            "numeric_count": 0,
            "comparison_year": None,
            "baseline_year": None,
            "multiple_kpis": False,
            "has_scope_terms": False,
        }


# ------------------------------
# Phase 4: Outcome Strength Scoring
# ------------------------------
def score_outcome_strength(sentence_obj: Dict[str, Any]) -> float:
    """
    Score outcome strength (0–100) from structural evidence.
    Note: this is a diagnostic score — it helps with reporting but does not
    change the sentence label assigned by the classifier.
    """
    try:
        if sentence_obj.get("label") != "OUTCOME":
            return 0.0

        grounding = sentence_obj.get("grounding", {})
        numeric_count = int(grounding.get("numeric_count", 0) or 0)
        entity_count = int(grounding.get("entity_count", 0) or 0)
        numeric_count = min(numeric_count, 3)
        entity_count = min(entity_count, 3)

        score = 0.0
        score += numeric_count * OUTCOME_NUMERIC_SCORE_PER_VALUE
        score += entity_count * OUTCOME_ENTITY_SCORE_PER_ENTITY

        if grounding.get("has_scope_terms"):
            score += OUTCOME_SCOPE_SCORE
        if grounding.get("metric_present"):
            score += OUTCOME_METRIC_PRESENT_SCORE
        if grounding.get("comparison_year") is not None:
            score += OUTCOME_COMPARISON_YEAR_SCORE
        if grounding.get("baseline_year") is not None:
            score += OUTCOME_BASELINE_YEAR_SCORE
        if numeric_count >= 2:
            score += OUTCOME_MULTIPLE_NUMERIC_BONUS
        if grounding.get("kpi_count", 0) >= 2:
            score += OUTCOME_MULTIPLE_KPI_BONUS
        if entity_count >= 2:
            score += OUTCOME_MULTIPLE_ENTITY_BONUS

        return clamp(score, 0.0, OUTCOME_MAX_SCORE)
    except Exception as error:
        print(f"Error scoring outcome strength: {error}")
        return 0.0


# ------------------------------
# Phase 5: Cross-Sentence Linking
# ------------------------------
def link_targets_to_outcomes(
    sentence_objects: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    try:
        TOPIC_MAP = {
            "emissions": "carbon",
            "scope_1": "carbon",
            "scope_2": "carbon",
            "scope_3": "carbon",
            "energy": "energy",
            "renewable_energy": "energy",
            "energy_efficiency": "energy",
            "water": "water",
            "water_stewardship": "water",
            "waste": "waste",
            "recycling": "waste",
            "plastic_waste": "waste",
            "biodiversity": "biodiversity",
            "forestry": "biodiversity",
            "nature": "biodiversity",
            "packaging": "packaging",
            "plastics": "packaging",
            "supply_chain": "supply_chain",
            "supply_chain_emissions": "supply_chain",
            "circular_economy": "circular",
            "materials": "circular",
            "hydrogen": "energy",
            "battery": "energy",
            "manufacturing": "supply_chain",
            "methane": "carbon",
            "fleet_emissions": "carbon",
            "critical_minerals": "circular",
        }

        STOPWORDS = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "of",
            "in",
            "to",
            "for",
            "is",
            "are",
            "we",
            "our",
            "its",
            "that",
            "this",
            "with",
            "as",
            "by",
            "on",
            "at",
            "be",
            "have",
            "has",
            "been",
            "will",
            "can",
            "from",
            "it",
            "not",
            "they",
            "their",
        }

        def _lexical_overlap(text_a: str, text_b: str) -> float:
            tokens_a = {
                token
                for token in re.split(r"[^0-9a-zA-Z]+", text_a.lower())
                if token and token not in STOPWORDS
            }
            tokens_b = {
                token
                for token in re.split(r"[^0-9a-zA-Z]+", text_b.lower())
                if token and token not in STOPWORDS
            }
            union = tokens_a.union(tokens_b)
            intersection = tokens_a.intersection(tokens_b)
            return len(intersection) / max(1, len(union))

        def _metric_overlap(
            grounding_a: Dict[str, Any], grounding_b: Dict[str, Any]
        ) -> float:
            metric_a = grounding_a.get("metric")
            metric_b = grounding_b.get("metric")
            has_a = metric_a is not None
            has_b = metric_b is not None
            if has_a and has_b:
                return 1.0 if metric_a == metric_b else 0.5
            if has_a != has_b:
                return 0.3
            return 0.2

        for sentence_obj in sentence_objects:
            sentence_obj["linked_targets"] = []
            sentence_obj["linked_outcomes"] = []
            sentence_obj["best_link_similarity"] = 0.0
            sentence_obj["best_semantic_similarity"] = 0.0
            sentence_obj["best_overall_match"] = 0.0

        targets = [
            s for s in sentence_objects if s.get("label") == "TARGET"
        ]
        outcomes = [
            s for s in sentence_objects if s.get("label") == "OUTCOME"
        ]

        for target in targets:
            target_embedding = normalize_embedding(target.get("embedding"))
            if target_embedding is None:
                debug_log("[MATCH SKIP] No embedding for target")
                continue

            target_grounding = target.get("grounding", {})
            target_entity = target_grounding.get("entity")
            target_topic = TOPIC_MAP.get(target_entity, "unknown")
            target_text = target.get("text", "")

            candidates = []
            for outcome in outcomes:
                outcome_embedding = normalize_embedding(outcome.get("embedding"))
                if outcome_embedding is None:
                    continue

                semantic_sim = cosine_similarity(target_embedding, outcome_embedding)
                if semantic_sim < 0.55:
                    debug_log(
                        f"[MATCH REJECT] semantic_sim={semantic_sim:.3f} < 0.55 | target: {target_text[:80]} | outcome: {outcome.get('text','')[:80]}"
                    )
                    continue

                outcome_grounding = outcome.get("grounding", {})
                outcome_entity = outcome_grounding.get("entity")
                outcome_topic = TOPIC_MAP.get(outcome_entity, "unknown")

                if target_topic == "unknown" and outcome_topic == "unknown":
                    # Neither sentence has a resolvable ESG entity.
                    # Require stronger semantic similarity to compensate.
                    topic_score = 0.3
                    if semantic_sim < 0.68:
                        debug_log(
                            f"[MATCH REJECT] both unknown topic, semantic_sim={semantic_sim:.3f} < 0.68 | target: {target_text[:80]} | outcome: {outcome.get('text','')[:80]}"
                        )
                        continue
                elif target_topic == outcome_topic:
                    topic_score = 1.0
                else:
                    topic_score = 0.0
                    debug_log(
                        f"[MATCH REJECT] topic mismatch: {target_topic} vs {outcome_topic} | target: {target_text[:80]} | outcome: {outcome.get('text','')[:80]}"
                    )
                    continue

                lexical_score = _lexical_overlap(target_text, outcome.get("text", ""))
                metric_score = _metric_overlap(target_grounding, outcome_grounding)
                overall_match = (
                    0.45 * semantic_sim
                    + 0.25 * topic_score
                    + 0.20 * lexical_score
                    + 0.10 * metric_score
                )

                if overall_match < 0.45:
                    debug_log(
                        f"[MATCH REJECT] overall_match={overall_match:.3f} < 0.45 | target: {target_text[:80]} | outcome: {outcome.get('text','')[:80]}"
                    )
                    continue

                candidates.append(
                    {
                        "outcome": outcome,
                        "semantic_sim": semantic_sim,
                        "topic_score": topic_score,
                        "lexical_score": lexical_score,
                        "metric_score": metric_score,
                        "overall_match": overall_match,
                    }
                )

            if not candidates:
                target["best_link_similarity"] = 0.0
                target["best_semantic_similarity"] = 0.0
                target["best_overall_match"] = 0.0
                debug_log(
                    f"[MATCH UNSUPPORTED] No candidates passed threshold | target: {target_text[:80]}"
                )
                continue

            candidates.sort(key=lambda item: item["overall_match"], reverse=True)
            top_candidates = candidates[:3]
            for candidate in top_candidates:
                outcome_obj = candidate["outcome"]
                debug_log(
                    f"[MATCH ACCEPT] overall={candidate['overall_match']:.3f} sem={candidate['semantic_sim']:.3f} topic={candidate['topic_score']:.2f} lex={candidate['lexical_score']:.2f} met={candidate['metric_score']:.2f} | target: {target_text[:80]} | outcome: {outcome_obj.get('text','')[:80]}"
                )
                target["linked_outcomes"].append(outcome_obj)
                outcome_obj["linked_targets"].append(target)
                outcome_obj["best_link_similarity"] = max(
                    float(outcome_obj.get("best_link_similarity", 0.0) or 0.0),
                    candidate["overall_match"],
                )
                outcome_obj["best_semantic_similarity"] = max(
                    float(outcome_obj.get("best_semantic_similarity", 0.0) or 0.0),
                    candidate["semantic_sim"],
                )
                outcome_obj["best_overall_match"] = max(
                    float(outcome_obj.get("best_overall_match", 0.0) or 0.0),
                    candidate["overall_match"],
                )

            target["best_link_similarity"] = top_candidates[0]["overall_match"]
            target["best_semantic_similarity"] = top_candidates[0]["semantic_sim"]
            target["best_overall_match"] = top_candidates[0]["overall_match"]

        return sentence_objects
    except Exception as error:
        print(f"Error linking targets to outcomes: {error}")
        return sentence_objects


# ------------------------------
# Phase 7: Target Clustering
# ------------------------------
def cluster_targets(sentence_objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    try:
        targets = [
            sentence
            for sentence in sentence_objects
            if sentence.get("label") == "TARGET"
        ]
        if not targets:
            return []
        if len(targets) < MIN_TARGETS_FOR_KMEANS:
            return [{"targets": [target.get("text", "") for target in targets]}]

        valid_targets = [
            target
            for target in targets
            if normalize_embedding(target.get("embedding")) is not None
        ]
        if len(valid_targets) < MIN_TARGETS_FOR_KMEANS:
            return [{"targets": [target.get("text", "") for target in targets]}]

        target_embeddings = np.array(
            [normalize_embedding(target.get("embedding")) for target in valid_targets]
        )
        n_clusters = min(MAX_TARGET_CLUSTERS, len(valid_targets))
        kmeans = KMeans(
            n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=KMEANS_N_INIT
        )
        cluster_labels = kmeans.fit_predict(target_embeddings)

        clusters: Dict[int, List[str]] = {}
        for index, cluster_id in enumerate(cluster_labels):
            clusters.setdefault(int(cluster_id), []).append(
                valid_targets[index].get("text", "")
            )

        return [{"targets": texts} for texts in clusters.values()]
    except Exception as error:
        print(f"Error clustering targets: {error}")
        return (
            [
                {
                    "targets": [
                        target.get("text", "")
                        for target in sentence_objects
                        if target.get("label") == "TARGET"
                    ]
                }
            ]
            if sentence_objects
            else []
        )


# ------------------------------
# Existing utility functions (kept for backward compatibility)
# ------------------------------
def embed_sentences(sentences: Sequence[str]) -> np.ndarray:
    if not sentences:
        return np.empty((0, CONFIG["EMBEDDING_DIM"]), dtype=np.float32)

    embedding_model = get_embedding_model()
    if embedding_model is None:
        debug_log("Embedding model unavailable; using zero-vector fallback embeddings.")
        return zero_embedding_matrix(len(sentences))

    try:
        raw_embeddings = embedding_model.encode(
            list(sentences), normalize_embeddings=True, convert_to_numpy=True
        )
        embeddings = np.asarray(raw_embeddings, dtype=np.float32)
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)
        return embeddings
    except TypeError:
        try:
            raw_embeddings = embedding_model.encode(
                list(sentences), normalize_embeddings=True
            )
            embeddings = np.asarray(raw_embeddings, dtype=np.float32)
            if embeddings.ndim == 1:
                embeddings = embeddings.reshape(1, -1)
            return embeddings
        except Exception as error:
            print(f"Error generating embeddings: {error}")
            return zero_embedding_matrix(len(sentences))
    except Exception as error:
        print(f"Error generating embeddings: {error}")
        return zero_embedding_matrix(len(sentences))


def normalize(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def clamp(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    return max(min_val, min(max_val, value))


def word_count(text: Optional[str]) -> int:
    return max(1, len(re.findall(r"\b\w+\b", text or "")))


def split_sentences(text: Optional[str]) -> List[str]:
    """
    Split text into sentences with special handling for KPI lines.
    Preserves original casing so ML inference sees the original sentence text.
    """
    try:
        text = text or ""
        sentences: List[str] = []

        for line in text.split("\n"):
            stripped_line = line.strip()
            if not stripped_line:
                continue

            is_bullet = stripped_line.startswith(("-", "*", "•", "+"))
            is_kpi = ":" in stripped_line and bool(
                re.search(r"\d+", stripped_line.split(":", 1)[1])
            )

            if (
                len(stripped_line) <= LONG_SENTENCE_SPLIT_THRESHOLD
                or is_bullet
                or is_kpi
            ):
                sentences.append(stripped_line)
                continue

            protected = re.sub(r"(\d)\.(\d)", r"\1<DEC>\2", stripped_line)
            for sub_sentence in re.split(r"[.!?]+", protected):
                cleaned_sentence = sub_sentence.replace("<DEC>", ".").strip()
                if cleaned_sentence:
                    sentences.append(cleaned_sentence)

        return list(dict.fromkeys(sentences))
    except Exception as error:
        print(f"Error splitting sentences: {error}")
        return []


def deduplicate_sentences_with_embeddings(
    sentences: Sequence[str],
    threshold: float = EMBEDDING_DUPLICATE_THRESHOLD,
) -> Tuple[List[str], np.ndarray]:
    if not sentences:
        return [], np.empty((0, CONFIG["EMBEDDING_DIM"]), dtype=np.float32)

    try:
        sentences_list = list(sentences)
        if len(sentences_list) != len(set(sentences_list)):
            seen: Dict[str, bool] = {}
            unique_sentences: List[str] = []
            for sentence in sentences_list:
                if sentence not in seen:
                    seen[sentence] = True
                    unique_sentences.append(sentence)
            sentences_list = unique_sentences

        embeddings = embed_sentences(sentences_list)
        if embeddings.size == 0:
            return sentences_list, zero_embedding_matrix(len(sentences_list))

        norms = np.linalg.norm(embeddings, axis=1)
        if np.all(norms == 0.0):
            return sentences_list, embeddings

        keep_indices: List[int] = []
        for index in range(len(embeddings)):
            embedding = embeddings[index]
            if keep_indices:
                kept_embeddings = embeddings[np.array(keep_indices, dtype=np.int64)]
                similarities = np.dot(kept_embeddings, embedding)
                if np.any(similarities > threshold):
                    continue
            keep_indices.append(index)

        kept_sentences = [sentences_list[index] for index in keep_indices]
        kept_embeddings = embeddings[np.array(keep_indices, dtype=np.int64)]
        return kept_sentences, kept_embeddings
    except Exception as error:
        print(f"Error deduplicating sentences with embeddings: {error}")
        return list(sentences), zero_embedding_matrix(len(sentences))


def deduplicate_sentences(
    sentences: Sequence[str], threshold: float = EMBEDDING_DUPLICATE_THRESHOLD
) -> List[str]:
    deduplicated_sentences, _ = deduplicate_sentences_with_embeddings(
        sentences, threshold=threshold
    )
    return deduplicated_sentences


def count_capped_sentence_hits(sentences, keywords, cap=MAX_HITS_PER_CATEGORY):
    hits = 0
    for sentence in sentences:
        if hits >= cap:
            break
        normalized_sentence = normalize(sentence)
        if any(
            re.search(r"\b" + re.escape(keyword) + r"\b", normalized_sentence)
            for keyword in keywords
        ):
            hits += 1
    return hits


def keyword_frequencies(text, keywords, limit=15):
    normalized = normalize(text)
    counts = {}
    for keyword in keywords:
        count = len(re.findall(r"\b" + re.escape(keyword.lower()) + r"\b", normalized))
        if count > 0:
            counts[keyword] = min(count, MAX_HITS_PER_CATEGORY)
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit])


def count_regex(text, pattern):
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def bucket_confidence(confidence: float) -> str:
    for lower, upper, label in CONFIDENCE_BUCKETS:
        if lower <= confidence < upper:
            return label
    return CONFIDENCE_BUCKETS[-1][2]


def average(values: Sequence[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def count_keyword_sentences(sentences: List[str], keywords: Sequence[str]) -> int:
    """
    Count the number of distinct sentences that contain at least one of the given
    keywords, using whole-word boundary matching.

    This is the canonical count function for claim/outcome/transparency density.
    It avoids both the artificial cap-at-3 problem (which made long documents look
    clean) and the substring false-positive problem (e.g. "air" in "repair").
    Max return value = len(sentences), so it is naturally normalised by document.
    """
    count = 0
    for sentence in sentences:
        normalized_s = normalize(sentence)
        if any(
            re.search(r"\b" + re.escape(kw) + r"\b", normalized_s) for kw in keywords
        ):
            count += 1
    return count


# ------------------------------
# Keyword lists
# ------------------------------
POSITIVE_TERMS = ["reduced", "decreased", "lowered", "improved", "avoided"]
NEGATIVE_TERMS = ["increased", "rose", "higher", "growth in emissions", "worsened"]

VAGUE_KEYWORDS = [
    "sustainable",
    "sustainability",
    "eco-friendly",
    "green",
    "responsible",
    "net zero",
    "carbon neutral",
    "climate positive",
    "low carbon",
    "climate action",
    "clean",
    "cleaner",
    "clean energy",
    "clean technology",
    "zero emissions",
    "zero-emission",
    "decarbonization",
    "environmentally friendly",
    "responsible sourcing",
    "environmental stewardship",
    "climate-smart",
    "nature positive",
    "green transition",
    "energy transition",
    "sustainable future",
    "sustainable growth",
    "circular economy",
    "carbon free",
    "carbon-free",
    "eco conscious",
    "environmentally responsible",
    "planet positive",
    "greener future",
    "sustainably sourced",
    "environmental leadership",
    "climate leadership",
    "future-ready",
    "purpose-driven",
    "positive impact",
    "driving sustainability",
    "accelerating sustainability",
    "sustainable development",
    "environmental responsibility",
    "better future",
    "climate resilience",
]

PROMOTIONAL_KEYWORDS = [
    "world-class",
    "leading",
    "best-in-class",
    "innovative",
    "cutting-edge",
    "revolutionary",
    "transformational",
    "game-changing",
    "industry-leading",
    "market-leading",
    "pioneering",
    "breakthrough",
    "state-of-the-art",
    "next-generation",
    "flagship",
    "unmatched",
    "premier",
    "leader in sustainability",
    "setting the standard",
    "driving change",
    "driving impact",
    "empowering a sustainable future",
]

TARGET_KEYWORDS = [
    "aim to",
    "target",
    "goal",
    "commit to",
    "plan to",
    "intend to",
    "roadmap",
    "working toward",
    "working towards",
    "aspire to",
    "will reduce",
    "will achieve",
    "by 2030",
    "by 2040",
    "by 2050",
    "pledge to",
    "will eliminate",
    "will transition",
    "long-term target",
    "future target",
    "ambition",
    "our pathway",
    "we aim to",
    "we strive to",
    "we seek to",
    "we are committed to",
    "our mission is",
    "our goal is",
    "we expect",
    "we anticipate",
    "we aspire",
    "we endeavor",
]

MARKETING_PHRASES = [
    "our commitment",
    "our approach",
    "learn more",
    "sustainability page",
    "what we do",
    "we believe",
    "join us",
    "making a difference",
    "we aspire",
]

ENVIRONMENTAL_KEYWORDS = [
    "emissions",
    "ghg",
    "greenhouse gas",
    "carbon",
    "co2",
    "co2e",
    "tco2e",
    "renewable",
    "renewables",
    "energy",
    "electricity",
    "waste",
    "water",
    "recycling",
    "pollution",
    "climate",
    "biodiversity",
    "environment",
    "decarbonization",
    "landfill",
    "methane",
    "solar",
    "wind",
    "efficiency",
    "energy efficiency",
    "conservation",
    "ecosystem",
    "ecosystems",
    "deforestation",
    "reforestation",
    "circularity",
    "water intensity",
    "energy intensity",
    "waste intensity",
    "renewable electricity",
    "renewable power",
    "clean power",
    "carbon footprint",
    "emissions intensity",
    "resource efficiency",
    "material recovery",
    "plastic waste",
    "packaging waste",
    "air quality",
    "water stewardship",
    "habitat restoration",
    "nature restoration",
    "forest conservation",
    "supply chain emissions",
]

TRANSPARENCY_FRAMEWORK_KEYWORDS = ["ghg protocol", "tcfd", "sasb", "cdp", "gri", "issb"]

TRANSPARENCY_ASSURANCE_KEYWORDS = [
    "audited",
    "verified",
    "assurance",
    "third-party assurance",
    "third-party",
    "independent verification",
]

TRANSPARENCY_SCOPE_TERMS = ["scope 1", "scope 2", "scope 3"]

OUTCOME_VERBS = [
    "reduced",
    "decreased",
    "lowered",
    "cut",
    "improved",
    "achieved",
    "completed",
    "delivered",
    "recycled",
    "recycling",
    "reused",
    "recovered",
    "diverted",
    "avoided",
    "eliminated",
    "saved",
    "conserved",
    "restored",
    "protected",
    "offset",
    "generated",
    "installed",
    "commissioned",
    "electrified",
    "converted",
    "retrofitted",
    "certified",
    "verified",
    "implemented",
    "replaced",
    "reached",
    "accounted for",
    "captured",
    "mitigated",
    "decarbonized",
    "removed",
    "abated",
]

OUTCOME_NOUNS = [
    "reduction",
    "decrease",
    "improvement",
    "energy savings",
    "water savings",
    "emissions reduction",
    "carbon reduction",
    "waste diversion",
    "recycling rate",
    "renewable electricity",
    "renewable energy generated",
    "renewable energy generation",
    "renewable capacity",
    "renewable sourcing",
    "forest restoration",
    "biodiversity protection",
    "habitat restoration",
    "water reuse",
    "water replenishment",
    "land restored",
    "increase in renewable energy",
    "elimination",
    "diversion",
    "replenishment",
    "restoration",
    "removal",
    "abatement",
    "conservation",
    "protection",
]

OUTCOME_ENVIRONMENTAL_CONTEXT_KEYWORDS = [
    "emissions",
    "carbon",
    "co2",
    "ghg",
    "scope 1",
    "scope 2",
    "scope 3",
    "energy",
    "renewable",
    "electricity",
    "fuel",
    "water",
    "waste",
    "plastic",
    "recycling",
    "forest",
    "trees",
    "biodiversity",
    "habitat",
    "land",
    "air",
    "methane",
    "pollution",
    "conservation",
    "ecosystem",
] + ENVIRONMENTAL_KEYWORDS

OUTCOME_FUTURE_TARGET_TERMS = [
    "will",
    "aim",
    "plan",
    "intend",
    "target",
    "goal",
    "commit",
    "expect",
    "aspire",
    "by 2030",
    "by 2040",
    "by 2050",
]

OUTCOME_TRANSPARENCY_TERMS = [
    "gri",
    "sasb",
    "tcfd",
    "issb",
    "assurance",
    "verified report",
    "reporting boundary",
]

OUTCOME_NUMERIC_METRIC_PATTERN = re.compile(
    r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:%|percent|mw|mwh|gwh|kwh|kg\s*co2e|tco2e|mtco2e|co2e|tons?|tonnes?|liters?|litres?|m3|cubic\s*meters?|cubic\s*metres?)\b",
    flags=re.IGNORECASE,
)

STRONG_ACHIEVEMENT_TERMS = [
    "achieved zero waste certification",
    "achieved zero waste",
    "zero waste certification",
    "certified zero waste",
    "landfill free",
    "eliminated single-use plastic",
    "completed remediation",
    "restored habitat",
    "restored wetlands",
    "protected habitat",
]

REPORT_TERMS = [
    "annual report",
    "esg report",
    "sustainability report",
    "reporting period",
    "materiality",
    "material topics",
    "performance data",
    "kpi",
    "key performance indicator",
]

PRESS_RELEASE_TERMS = [
    "press release",
    "announced today",
    "news release",
    "media contact",
    "investor relations",
    "forward-looking statements",
]

CONTROVERSY_PATTERNS = [
    r"environmental fine",
    r"regulatory fine",
    r"pollution incident",
    r"pollution violation",
    r"environmental violation",
    r"greenwashing lawsuit",
    r"environmental lawsuit",
    r"environmental investigation",
    r"regulatory breach",
    r"oil spill",
    r"chemical spill",
    r"consent decree",
    r"environmental settlement",
    r"toxic release",
    r"hazardous waste violation",
    r"clean air act violation",
    r"clean water act violation",
]


OUTCOME_KEYWORD_PRIORITY = sorted(
    list(dict.fromkeys(OUTCOME_VERBS + OUTCOME_NOUNS)),
    key=len,
    reverse=True,
)
OUTCOME_ENVIRONMENTAL_KEYWORD_PRIORITY = sorted(
    list(dict.fromkeys(OUTCOME_ENVIRONMENTAL_CONTEXT_KEYWORDS)),
    key=len,
    reverse=True,
)
OUTCOME_FUTURE_TARGET_PRIORITY = sorted(
    list(dict.fromkeys(OUTCOME_FUTURE_TARGET_TERMS)),
    key=len,
    reverse=True,
)
OUTCOME_TRANSPARENCY_PRIORITY = sorted(
    list(dict.fromkeys(OUTCOME_TRANSPARENCY_TERMS)),
    key=len,
    reverse=True,
)
OUTCOME_PAST_ACHIEVEMENT_PATTERN = re.compile(
    r"\b(reduced|decreased|lowered|cut|improved|achieved|completed|delivered|recycled|reused|recovered|diverted|avoided|eliminated|saved|conserved|restored|protected|offset|generated|installed|commissioned|electrified|converted|retrofitted|certified|verified|implemented|replaced|reached|accounted\s+for)\b",
    flags=re.IGNORECASE,
)


# ------------------------------
# Outcome detection helpers
# ------------------------------
def first_keyword_match(
    normalized_sentence: str, keywords: Sequence[str]
) -> Optional[str]:
    """
    Return the first keyword found in the sentence using whole-word boundary matching.
    Uses regex to prevent "air" matching inside "repair", "land" inside "island", etc.
    """
    for keyword in keywords:
        if re.search(r"\b" + re.escape(keyword) + r"\b", normalized_sentence):
            return keyword
    return None


def analyze_outcome_sentence(sentence_obj: Dict[str, Any]) -> Dict[str, Any]:
    sentence_text = sentence_obj.get("text", "")
    normalized_sentence = normalize(sentence_text)
    grounding = sentence_obj.get("grounding", {})

    matched_outcome_keyword = first_keyword_match(
        normalized_sentence,
        OUTCOME_KEYWORD_PRIORITY,
    )
    matched_environmental_keyword = first_keyword_match(
        normalized_sentence,
        OUTCOME_ENVIRONMENTAL_KEYWORD_PRIORITY,
    ) or grounding.get("entity")
    numeric_match = OUTCOME_NUMERIC_METRIC_PATTERN.search(sentence_text)
    matched_numeric_metric = numeric_match.group(0) if numeric_match else None
    matched_future_term = first_keyword_match(
        normalized_sentence,
        OUTCOME_FUTURE_TARGET_PRIORITY,
    )
    matched_transparency_term = first_keyword_match(
        normalized_sentence,
        OUTCOME_TRANSPARENCY_PRIORITY,
    )

    has_outcome_keyword = matched_outcome_keyword is not None
    has_environmental_context = bool(
        matched_environmental_keyword or grounding.get("entities")
    )
    has_numeric_metric = bool(matched_numeric_metric or grounding.get("metric_present"))
    has_completed_achievement = bool(
        OUTCOME_PAST_ACHIEVEMENT_PATTERN.search(normalized_sentence)
    )

    is_candidate = bool(
        has_outcome_keyword
        or has_numeric_metric
        or sentence_obj.get("label") == "OUTCOME"
    )

    rejection_reasons: List[str] = []
    if not is_candidate:
        return {
            "is_candidate": False,
            "qualified": False,
            "matched_outcome_keyword": None,
            "matched_environmental_keyword": None,
            "matched_numeric_metric": None,
            "reason": "no outcome signal",
            "confidence_bonus": 0.0,
        }

    if not has_environmental_context:
        rejection_reasons.append("missing environmental context")

    if matched_transparency_term and not has_outcome_keyword:
        rejection_reasons.append("transparency disclosure without outcome achievement")

    if matched_future_term and not has_completed_achievement:
        rejection_reasons.append(f"future-target dominated by '{matched_future_term}'")

    if not has_outcome_keyword and not has_numeric_metric:
        rejection_reasons.append(
            "missing outcome keyword and numeric performance signal"
        )

    qualified = (
        len(rejection_reasons) == 0
        and has_environmental_context
        and (has_outcome_keyword or has_numeric_metric)
    )
    confidence_bonus = (
        float(CONFIG["OUTCOME_TRIAD_CONFIDENCE_BONUS"])
        if has_outcome_keyword and has_environmental_context and has_numeric_metric
        else 0.0
    )

    if qualified:
        if has_outcome_keyword and has_numeric_metric:
            reason = "past achievement keyword + environmental context + numeric metric"
        elif has_outcome_keyword:
            reason = "outcome keyword + environmental context"
        else:
            reason = "quantitative environmental performance"
        debug_log(
            "Outcome detected | "
            f"sentence='{sentence_text}' | "
            f"matched outcome keyword='{matched_outcome_keyword}' | "
            f"matched environmental keyword='{matched_environmental_keyword}' | "
            f"matched numeric metric='{matched_numeric_metric}' | "
            f"reason='{reason}'"
        )
    else:
        reason = "; ".join(rejection_reasons) if rejection_reasons else "rejected"
        debug_log(
            "Outcome rejected | "
            f"sentence='{sentence_text}' | "
            f"matched outcome keyword='{matched_outcome_keyword}' | "
            f"matched environmental keyword='{matched_environmental_keyword}' | "
            f"matched numeric metric='{matched_numeric_metric}' | "
            f"reason='{reason}'"
        )

    return {
        "is_candidate": is_candidate,
        "qualified": qualified,
        "matched_outcome_keyword": matched_outcome_keyword,
        "matched_environmental_keyword": matched_environmental_keyword,
        "matched_numeric_metric": matched_numeric_metric,
        "reason": reason,
        "confidence_bonus": confidence_bonus,
    }


# ------------------------------
# Backward-compatible functions
# ------------------------------
def classify_sentence(sentence):
    """Backward compatible: uses predict_sentence and returns label"""
    return predict_sentence(sentence)["label"]


def classify_sentences(text):
    """Backward compatible: returns list of {'sentence': str, 'label': str}"""
    sentence_objs = build_sentence_objects(text)
    return [{"sentence": obj["text"], "label": obj["label"]} for obj in sentence_objs]


def sentence_classes_from_objects(sentence_objects):
    return [
        {"sentence": obj["text"], "label": obj["label"]} for obj in sentence_objects
    ]


# ------------------------------
# Compute functions (updated)
# ------------------------------
def compute_claim_pressure(text, sentence_classes=None, sentence_objects=None):
    """
    Compute claim pressure as a density score (0-100).

    Formula:
        claim_pressure = clamp(
            promo_rate * CLAIM_PROMOTIONAL_WEIGHT * 100
            + vague_rate * CLAIM_VAGUE_WEIGHT * 100
        )

    Rates are computed against the total number of sentences so the score
    reflects concentration of promotional or vague language. This function
    only reports a metric for diagnostics and does not change classifications.

    Deduplication: A single sentence containing both promotional and vague keywords
    is counted only once per category to avoid inflation. The counts represent
    distinct sentences with each signal type, not total keyword occurrences.
    """
    sentences = split_sentences(text)
    if sentence_classes is None:
        sentence_classes = sentence_classes_from_objects(sentence_objects or [])

    total_sentences = max(1, len(sentences))
    target_sentences = sum(1 for item in sentence_classes if item["label"] == "TARGET")

    # Count distinct sentences containing promotional/vague keywords (uncapped).
    # Using whole-word matching to avoid false positives.
    # count_keyword_sentences already handles this correctly - it counts distinct
    # sentences containing at least one keyword from the list.
    promotional_hits = count_keyword_sentences(sentences, PROMOTIONAL_KEYWORDS)
    vague_hits = count_keyword_sentences(sentences, VAGUE_KEYWORDS)

    # Calculate overlap between promotional and vague sentences to detect double-counting
    # A sentence containing both types would be counted in both promotional_hits and vague_hits
    # This is intentional for the claim pressure formula as they represent different signal types
    # However, we track the overlap for transparency
    promotional_sentences = set()
    vague_sentences = set()
    for i, sentence in enumerate(sentences):
        normalized_s = normalize(sentence)
        if any(re.search(r"\b" + re.escape(kw) + r"\b", normalized_s) for kw in PROMOTIONAL_KEYWORDS):
            promotional_sentences.add(i)
        if any(re.search(r"\b" + re.escape(kw) + r"\b", normalized_s) for kw in VAGUE_KEYWORDS):
            vague_sentences.add(i)
    
    overlap_count = len(promotional_sentences & vague_sentences)
    unique_claim_sentences = len(promotional_sentences | vague_sentences)

    # Convert to rates and apply calibrated weights.
    # CLAIM_PROMOTIONAL_WEIGHT=3.0: 33% promo rate → 100 (extreme)
    # CLAIM_VAGUE_WEIGHT=1.5:       67% vague rate → 100 (extreme)
    promotional_rate = promotional_hits / total_sentences
    vague_rate = vague_hits / total_sentences
    raw = (
        promotional_rate * CONFIG["CLAIM_PROMOTIONAL_WEIGHT"] * 100
        + vague_rate * CONFIG["CLAIM_VAGUE_WEIGHT"] * 100
    )
    claim_pressure_raw = raw
    claim_pressure = round(clamp(raw, 0, OUTCOME_MAX_SCORE), 2)

    # target_pressure: informational only — not added to claim_pressure to avoid
    # double-counting with future_target_density in the risk formula.
    target_pressure = (
        min(MAX_HITS_PER_CATEGORY, target_sentences) * CONFIG["TARGET_PRESSURE_WEIGHT"]
    )

    return {
        "claim_pressure": claim_pressure,
        "claim_pressure_raw": claim_pressure_raw,
        "promotional_hits": promotional_hits,  # distinct sentence count (uncapped)
        "vague_hits": vague_hits,  # distinct sentence count (uncapped)
        "target_sentence_count": target_sentences,
        "word_count": word_count(text),
        "target_pressure": target_pressure,  # informational only
        "claim_sentence_overlap": overlap_count,  # sentences with both promo + vague
        "unique_claim_sentences": unique_claim_sentences,  # deduplicated claim signal count
    }


def compute_future_target_density(
    sentence_classes=None, consistency_score=100.0, sentence_objects=None
):
    if sentence_classes is None:
        sentence_classes = sentence_classes_from_objects(sentence_objects or [])
    targets = [s["sentence"] for s in sentence_classes if s["label"] == "TARGET"]

    if not targets:
        return 0.0, 0.0

    total_sentence_count = max(1, len(sentence_objects or []))
    target_sentence_count = len(targets)
    future_target_density = round(
        min(100.0, (target_sentence_count / total_sentence_count) * 100 * 3.0),
        2,
    )
    effective_target_pressure = future_target_density * (1 - (consistency_score / 100))
    effective_target_pressure = round(effective_target_pressure, 2)

    return future_target_density, effective_target_pressure


def compute_outcome_evidence(text, sentence_classes=None, sentence_objects=None):
    """Compute outcome evidence metrics for reporting.

    This is observational: it collects and scores outcome-related signals
    for diagnostics and the dashboard. It does not change sentence labels.
    """
    sentence_classes = sentence_classes or sentence_classes_from_objects(
        sentence_objects or []
    )
    sentence_objs = sentence_objects or []

    real_outcomes = []
    grounded_kpis = []
    quantified_outcomes = 0
    grounded_real_outcomes = 0
    total_outcome_strength = 0.0

    for obj in sentence_objs:
        grounding = obj.get("grounding", {})
        outcome_analysis = analyze_outcome_sentence(obj)
        if not outcome_analysis.get("qualified"):
            continue

        if obj.get("label") != "OUTCOME":
            continue
        base_strength = float(obj.get("outcome_strength", 0.0) or 0.0)

        effective_strength = clamp(
            base_strength + float(outcome_analysis.get("confidence_bonus", 0.0) or 0.0),
            0.0,
            OUTCOME_MAX_SCORE,
        )

        real_outcomes.append(obj.get("text", ""))
        total_outcome_strength += effective_strength

        if grounding.get("metric_present") or outcome_analysis.get(
            "matched_numeric_metric"
        ):
            quantified_outcomes += 1

        if grounding.get("entity") is not None and (
            grounding.get("metric") is not None
            or outcome_analysis.get("matched_numeric_metric")
        ):
            grounded_real_outcomes += 1
            grounded_kpis.append(
                {
                    "sentence": obj.get("text", ""),
                    "entity": grounding.get("entity"),
                    "scope": grounding.get("subentity"),
                    "metric": grounding.get("metric")
                    or outcome_analysis.get("matched_outcome_keyword"),
                    "value": grounding.get("value"),
                    "value_max": grounding.get("value_max"),
                    "qualifier": grounding.get("qualifier"),
                    "unit": grounding.get("unit"),
                    "strength": effective_strength,
                }
            )

    STRONG_ACHIEVEMENT_EXTENDED = list(STRONG_ACHIEVEMENT_TERMS) + [
        "ahead of schedule",
        "exceeded",
        "surpassed",
        "certified",
        "independently verified",
        "externally assured",
        "third-party verified",
        "validated",
        "confirmed",
        "on track",
        "milestone",
        "accomplished",
    ]
    strong_achievements = sum(
        1
        for s in real_outcomes
        if any(
            re.search(r"\b" + re.escape(term) + r"\b", normalize(s))
            for term in STRONG_ACHIEVEMENT_EXTENDED
        )
    )

    outcome_sentence_count = max(1, len(real_outcomes))
    average_strength = total_outcome_strength / outcome_sentence_count
    total_sentences_in_doc = max(1, len(sentence_objs))
    evidence_density = grounded_real_outcomes / total_sentences_in_doc
    raw_score = (
        (average_strength * 0.6)
        + (evidence_density * 100 * 0.3)
        + (strong_achievements * 0.1 * 10)
    )
    outcome_evidence_score = round(clamp(raw_score, 0.0, 100.0), 2)

    return {
        "outcome_evidence_score": outcome_evidence_score,
        "real_outcome_count": len(real_outcomes),
        "quantified_outcomes_count": quantified_outcomes,
        "strong_achievements": strong_achievements,
        "grounded_real_outcomes": grounded_real_outcomes,
        "grounded_kpis": grounded_kpis,
        "outcome_sentences": real_outcomes[:8],
        "raw_outcome_score": round(raw_score, 2),
        "total_outcome_strength": total_outcome_strength,
        "average_outcome_strength": round(
            total_outcome_strength / len(real_outcomes), 2
        )
        if real_outcomes
        else 0.0,
    }


def compute_transparency_signals(text):
    """Extract transparency-related signals for reporting.

    Observational: used for metrics and display; does not alter labels.
    sentences.
    """
    sentences = split_sentences(text)

    normalized_text = normalize(text)
    framework_present = {
        kw: 1 for kw in TRANSPARENCY_FRAMEWORK_KEYWORDS
        if re.search(r'\b' + re.escape(kw.lower()) + r'\b', normalized_text)
    }
    assurance_present = {
        kw: 1 for kw in TRANSPARENCY_ASSURANCE_KEYWORDS
        if re.search(r'\b' + re.escape(kw.lower()) + r'\b', normalized_text)
    }
    framework_count = len(framework_present)
    assurance_count = len(assurance_present)
    framework_hits = framework_present
    assurance_hits = assurance_present
    scope_hits = count_capped_sentence_hits(sentences, TRANSPARENCY_SCOPE_TERMS, cap=3)

    framework_coverage = (
        min(framework_count / max(1, len(TRANSPARENCY_FRAMEWORK_KEYWORDS)), 1.0)
        * OUTCOME_MAX_SCORE
    )
    assurance_coverage = (
        min(assurance_count / max(1, len(TRANSPARENCY_ASSURANCE_KEYWORDS)), 1.0)
        * OUTCOME_MAX_SCORE
    )
    scope_coverage = (
        min(scope_hits / CONFIG["TRANSPARENCY_SCOPE_DIVISOR"], 1.0) * OUTCOME_MAX_SCORE
    )
    methodology_depth = (
        min(
            count_capped_sentence_hits(
                sentences,
                ["methodology", "reporting boundary", "materiality"],
                cap=CONFIG["TRANSPARENCY_METHODOLOGY_DIVISOR"],
            )
            / CONFIG["TRANSPARENCY_METHODOLOGY_DIVISOR"],
            1.0,
        )
        * OUTCOME_MAX_SCORE
    )

    transparency_score = round(
        clamp(
            framework_coverage * CONFIG["TRANSPARENCY_FRAMEWORK_WEIGHT"]
            + assurance_coverage * CONFIG["TRANSPARENCY_ASSURANCE_WEIGHT"]
            + scope_coverage * CONFIG["TRANSPARENCY_SCOPE_WEIGHT"]
            + methodology_depth * CONFIG["TRANSPARENCY_METHODOLOGY_WEIGHT"]
        ),
        2,
    )

    return {
        "score": transparency_score,
        "framework_count": framework_count,
        "assurance_count": assurance_count,
        "scope_count": scope_hits,
        "framework_coverage": round(framework_coverage, 2),
        "assurance_coverage": round(assurance_coverage, 2),
        "scope_coverage": round(scope_coverage, 2),
        "methodology_depth": round(methodology_depth, 2),
        "framework_hits": framework_hits,
        "assurance_hits": assurance_hits,
    }


def classify_document_type(text, outcome, transparency, claim_pressure):
    normalized = normalize(text)
    sentences = split_sentences(text)

    metric_density = outcome.get("quantified_outcomes_count", 0) + min(
        count_regex(text, r"\d+(?:\.\d+)?\s?(%|tons?|tco2e|mwh|gwh)"),
        MAX_HITS_PER_CATEGORY * 2,
    )

    marketing_hits = count_capped_sentence_hits(
        sentences, MARKETING_PHRASES + PROMOTIONAL_KEYWORDS
    )

    press_hits = count_capped_sentence_hits(sentences, PRESS_RELEASE_TERMS)

    report_hits = count_capped_sentence_hits(sentences, REPORT_TERMS)

    has_report_title = (
        "sustainability report" in normalized
        or "esg report" in normalized
        or "impact report" in normalized
    )

    outcome_count = outcome.get("real_outcome_count", 0)

    table_or_metrics = (
        metric_density >= 2
        or outcome_count >= 3
    )

    if metric_density >= 2 and claim_pressure >= 70:
        return {
            "document_type": "IMPACT_MARKETING_REPORT",
            "signals": {
                "metric_density": metric_density,
                "marketing_hits": marketing_hits,
                "press_hits": press_hits,
                "report_hits": report_hits,
                "framework_references": transparency.get("framework_count", 0),
                "assurance_references": transparency.get("assurance_count", 0),
                "scope_references": transparency.get("scope_count", 0),
                "outcome_count": outcome_count,
            },
        }

    if press_hits >= 1 and not table_or_metrics:
        doc_type = "PRESS_RELEASE"
    elif (
        marketing_hits >= 2
        and outcome_count <= 1
        and not table_or_metrics
    ):
        doc_type = "MARKETING_PAGE"
    elif (
        has_report_title
        or (report_hits >= 1 and table_or_metrics)
        or (table_or_metrics and transparency.get("framework_count", 0) >= 1)
    ):
        doc_type = "ESG_REPORT"
    else:
        doc_type = "UNKNOWN"

    return {
        "document_type": doc_type,
        "signals": {
            "metric_density": metric_density,
            "marketing_hits": marketing_hits,
            "press_hits": press_hits,
            "report_hits": report_hits,
            "framework_references": transparency.get("framework_count", 0),
            "assurance_references": transparency.get("assurance_count", 0),
            "scope_references": transparency.get("scope_count", 0),
            "outcome_count": outcome_count,
        },
    }


def support_ratio_category(ratio: float, has_targets: bool = True) -> str:
    """
    Return a human-readable category for the support ratio.

    When a document has no target sentences at all, the concept of support is
    not applicable (there is nothing to support or not-support), so we return
    "N/A" rather than the misleading "unsupported".
    """
    if not has_targets:
        return "N/A"
    if ratio > 2.0:
        return "exceptionally supported"
    if ratio >= 1.2:
        return "well supported"
    if ratio >= 0.8:
        return "balanced"
    if ratio >= 0.4:
        return "weak"
    return "unsupported"


def compute_support_ratio(outcome_dict, claim_dict, consistency_dict):
    """
    Support ratio: proportion of identified target sentences that have at least
    one semantically linked outcome sentence.

    This is a raw count ratio (supported_targets / total_targets), NOT a ratio
    of normalized scores (outcome_evidence_score / claim_pressure). The two
    metrics serve different purposes:
    - Support ratio measures evidence linkage completeness (0-2.0x)
    - Score ratio would measure relative strength (outcome/claim)

    Interpretation:
      0.0          → no targets exist (N/A) or none are supported
      0.0 - 0.4    → unsupported
      0.4 - 0.8    → weak
      0.8 - 1.2    → balanced
      1.2+         → well / exceptionally supported
    """
    target_count = int(consistency_dict.get("targets", 0) or 0)
    supported_targets = int(consistency_dict.get("supported_targets", 0) or 0)
    if target_count == 0:
        # No targets: ratio is undefined; return 0 with N/A category.
        return (0.0, support_ratio_category(0.0, has_targets=False))
    ratio = round(min(CONFIG["SUPPORT_RATIO_MAX"], supported_targets / target_count), 2)
    return (ratio, support_ratio_category(ratio, has_targets=True))


def compute_greenwashing_gap(claim_pressure, outcome_evidence_score):
    """
    Compute greenwashing gap (claim pressure - outcome evidence, floored at 0).
    Also compute outcome_coverage_margin (outcome - claim, floored at 0).

    The gap captures unsupported claim excess.k
    The margin captures outcome surplus — evidence that substantially outpaces claims.
    Both are returned; callers use whichever is relevant.
    """
    gap = round(max(0.0, claim_pressure - outcome_evidence_score), 2)
    coverage_margin = round(max(0.0, outcome_evidence_score - claim_pressure), 2)
    return gap, coverage_margin


def compute_greenwashing_risk(
    greenwashing_gap,
    claim_pressure,
    future_target_density,
    outcome_evidence_score,
    transparency_score,
    consistency_score,
):
    """
    Compute greenwashing risk (0-100) for dashboard reporting.

    The risk calculation combines the gap between claims and outcome evidence
    with supporting factors for future targets and unsupported targets.
    """
    # Unsupported targets: proportion of consistency_score below 100 drives a penalty.
    # When all targets are linked to outcomes (consistency=100), penalty=0.
    # When no targets are linked (consistency=0), penalty=15.
    unsupported_ratio = 1.0 - (consistency_score / 100.0)
    unsupported_penalty = unsupported_ratio * 15.0

    # Transparency is informational only and does not reduce the computed risk.
    # It is informational only: high transparency does not reduce risk unless
    # it is accompanied by high outcome evidence (which lowers the gap naturally).
    risk_raw = (
        greenwashing_gap * 0.75
        + claim_pressure * 0.15
        + future_target_density * 0.15
        + unsupported_penalty
    )

    risk = round(clamp(risk_raw, 0, 100), 2)

    return {
        "risk": risk,
        "risk_raw": round(risk_raw, 2),
        "greenwashing_gap": round(greenwashing_gap, 2),
        "claim_pressure": round(claim_pressure, 2),
        "future_target_density": round(future_target_density, 2),
        "outcome_evidence_score": round(outcome_evidence_score, 2),
        "unsupported_penalty": round(unsupported_penalty, 2),
        "transparency_score": round(transparency_score, 2),  # informational only
    }


def contextual_controversies(text):
    normalized = normalize(text)
    hits = {}
    for pattern in CONTROVERSY_PATTERNS:
        count = len(re.findall(pattern, normalized))
        if count:
            hits[pattern] = count
    return hits


def outcome_supports_target(target_grounding, outcome_grounding):
    if target_grounding["entity"] != outcome_grounding["entity"]:
        return False

    if (
        target_grounding["subentity"]
        and outcome_grounding["subentity"]
        and target_grounding["subentity"] != outcome_grounding["subentity"]
    ):
        return False

    if (
        target_grounding["metric"]
        and outcome_grounding["metric"]
        and target_grounding["metric"] != outcome_grounding["metric"]
    ):
        return False

    return True


def compute_cross_sentence_consistency(sentence_classes=None, sentence_objects=None):
    _ = sentence_classes
    if sentence_objects is None:
        return {
            "targets": 0,
            "supported_targets": 0,
            "unsupported_targets": 0,
            "consistency_score": 50.0,
            "average_match_score": 0.0,
            "average_support_confidence": 0.0,
            "supported_target_examples": [],
            "unsupported_target_examples": [],
        }

    try:
        targets = [s for s in sentence_objects if s.get("label") == "TARGET"]
        supported_targets = sum(
            1 for t in targets if len(t.get("linked_outcomes", [])) > 0
        )
        supported_target_examples = []
        unsupported_target_examples = []

        for target in targets:
            linked_outcomes = target.get("linked_outcomes", [])
            if linked_outcomes:
                supported_target_examples.append(
                    {
                        "target": target.get("text", ""),
                        "outcome": linked_outcomes[0].get("text", ""),
                    }
                )
            else:
                unsupported_target_examples.append({"target": target.get("text", "")})

        unsupported_targets = len(targets) - supported_targets
        consistency_score = (
            50.0
            if len(targets) == 0
            else round((supported_targets / len(targets)) * 100, 2)
        )

        match_scores = [
            float(t.get("best_overall_match", 0.0) or 0.0)
            for t in targets
            if t.get("linked_outcomes")
        ]
        average_match_score = (
            round(sum(match_scores) / max(1, len(match_scores)), 4)
            if match_scores
            else 0.0
        )
        average_support_confidence = average_match_score

        return {
            "targets": len(targets),
            "supported_targets": supported_targets,
            "unsupported_targets": unsupported_targets,
            "consistency_score": consistency_score,
            "average_match_score": average_match_score,
            "average_support_confidence": average_support_confidence,
            "supported_target_examples": supported_target_examples[:5],
            "unsupported_target_examples": unsupported_target_examples[:5],
        }
    except Exception as error:
        print(f"Error computing cross-sentence consistency: {error}")
        return {
            "targets": 0,
            "supported_targets": 0,
            "unsupported_targets": 0,
            "consistency_score": 50.0,
            "average_match_score": 0.0,
            "average_support_confidence": 0.0,
            "supported_target_examples": [],
            "unsupported_target_examples": [],
        }


def normalize_lemma(keyword):
    """
    Simple lemmatization for grouping related outcome indicators.
    
    Maps related word forms to a canonical lemma:
    - Verbs ending in -ed, -ing → base form
    - Nouns ending in -s, -es → singular form
    - Specific mappings for common ESG terms
    """
    keyword_lower = keyword.lower().strip()
    
    # Specific mappings for irregular forms
    LEMMA_MAP = {
        "reduced": "reduction",
        "decreased": "reduction",
        "lowered": "reduction",
        "cut": "reduction",
        "reducing": "reduction",
        "decreasing": "reduction",
        "lowering": "reduction",
        "cutting": "reduction",
        "improved": "improvement",
        "improving": "improvement",
        "increased": "improvement",
        "increasing": "improvement",
        "boosted": "improvement",
        "boosting": "improvement",
        "grew": "improvement",
        "growing": "improvement",
        "recycled": "recycling",
        "recycling": "recycling",
        "reused": "restoration",
        "reusing": "restoration",
        "recovered": "restoration",
        "recovering": "restoration",
        "restored": "restoration",
        "restoring": "restoration",
        "conserved": "conservation",
        "conserving": "conservation",
        "protected": "protection",
        "protecting": "protection",
        "saved": "conservation",
        "saving": "conservation",
        "diverted": "diversion",
        "diverting": "diversion",
        "eliminated": "elimination",
        "eliminating": "elimination",
        "avoided": "avoidance",
        "avoiding": "avoidance",
        "offset": "offset",
        "offsetting": "offset",
        "generated": "generation",
        "generating": "generation",
        "installed": "installation",
        "installing": "installation",
        "commissioned": "commission",
        "commissioning": "commission",
        "electrified": "electrification",
        "electrifying": "electrification",
        "converted": "conversion",
        "converting": "conversion",
        "retrofitted": "retrofit",
        "retrofitting": "retrofit",
        "certified": "certification",
        "certifying": "certification",
        "verified": "verification",
        "verifying": "verification",
        "implemented": "implementation",
        "implementing": "implementation",
        "replaced": "replacement",
        "replacing": "replacement",
        "reached": "achievement",
        "reaching": "achievement",
        "achieved": "achievement",
        "achieving": "achievement",
        "completed": "completion",
        "completing": "completion",
        "delivered": "delivery",
        "delivering": "delivery",
        "captured": "capture",
        "capturing": "capture",
        "mitigated": "mitigation",
        "mitigating": "mitigation",
        "decarbonized": "decarbonization",
        "decarbonizing": "decarbonization",
        "removed": "removal",
        "removing": "removal",
        "abated": "abatement",
        "abating": "abatement",
    }
    
    if keyword_lower in LEMMA_MAP:
        return LEMMA_MAP[keyword_lower]
    
    # Fallback: simple suffix stripping
    if keyword_lower.endswith("ed"):
        return keyword_lower[:-2]
    elif keyword_lower.endswith("ing"):
        if keyword_lower.endswith("ting"):
            return keyword_lower[:-4] + "e"
        return keyword_lower[:-3]
    elif keyword_lower.endswith("s") and not keyword_lower.endswith("ss"):
        return keyword_lower[:-1]
    
    return keyword_lower


def extract_context_signals(text):
    """
    Extract keyword signals for the dashboard using weighted scoring.

    Frequencies are reported as DISTINCT SENTENCE COUNTS, not raw token occurrences.
    This means: "reduced: 12" = 12 distinct sentences that contain the word "reduced",
    NOT "the word appeared 12 times total in the document".

    Weighting approach:
    - Multi-word phrases receive higher base weights (length multiplier)
    - Generic filler words are penalized (lower weight)
    - TF-IDF-like scoring: frequency * phrase_weight * inverse_commonality
    - Results are sorted by weighted score, not raw frequency

    Outcome indicators are lemmatized to group related forms (e.g., "reduced" + "reduction" → "Reduction").

    Rationale: raw token frequency is misleading ("sustainability: 564" in a large GRI
    report tells the user nothing useful). Weighted scoring surfaces meaningful concepts
    while naturally bounded by document length.
    """
    sentences = split_sentences(text)
    controversy_counts = contextual_controversies(text)

    # Generic filler words to down-weight
    GENERIC_FILLER = {
        "sustainable", "sustainability", "green", "clean", "eco-friendly",
        "responsible", "environmental", "climate", "future", "impact"
    }

    def compute_weighted_score(keyword, sentence_count, total_sentences):
        """Compute a TF-IDF-like weighted score for a keyword."""
        if sentence_count == 0:
            return 0.0
        
        # Base score: sentence frequency
        tf = sentence_count / max(1, total_sentences)
        
        # Phrase length bonus: multi-word phrases get higher weight
        word_count = len(keyword.split())
        length_weight = 1.0 + (word_count - 1) * 0.5
        
        # Filler penalty: generic words get lower weight
        filler_penalty = 0.5 if keyword.lower() in GENERIC_FILLER else 1.0
        
        # Inverse commonality: penalize very common terms across all keywords
        # (simplified IDF - assumes uniform distribution for this context)
        idf_weight = 1.0
        
        weighted_score = tf * length_weight * filler_penalty * idf_weight * 100
        return round(weighted_score, 2)

    total_sentences = max(1, len(sentences))

    # Distinct sentence counts per keyword (word-boundary matched).
    transparency_keywords_all = (
        TRANSPARENCY_FRAMEWORK_KEYWORDS + TRANSPARENCY_ASSURANCE_KEYWORDS
    )
    transparency_counts = {
        kw: count_keyword_sentences(sentences, [kw]) for kw in transparency_keywords_all
    }
    transparency_counts = {
        kw: (count, compute_weighted_score(kw, count, total_sentences))
        for kw, count in transparency_counts.items()
        if count > 0
    }
    transparency_counts = dict(
        sorted(transparency_counts.items(), key=lambda x: x[1][1], reverse=True)[:15]
    )
    # Return just counts for backward compatibility
    transparency_counts_simple = {kw: count for kw, (count, _) in transparency_counts.items()}

    outcome_keywords_all = OUTCOME_VERBS + OUTCOME_NOUNS
    outcome_counts_raw = {
        kw: count_keyword_sentences(sentences, [kw]) for kw in outcome_keywords_all
    }
    
    # Group outcome indicators by lemma
    outcome_lemma_groups = {}
    for kw, count in outcome_counts_raw.items():
        if count > 0:
            lemma = normalize_lemma(kw)
            if lemma not in outcome_lemma_groups:
                outcome_lemma_groups[lemma] = 0
            outcome_lemma_groups[lemma] += count
    
    # Compute weighted scores for grouped lemmas
    outcome_counts = {
        lemma: (count, compute_weighted_score(lemma, count, total_sentences))
        for lemma, count in outcome_lemma_groups.items()
    }
    outcome_counts = dict(
        sorted(outcome_counts.items(), key=lambda x: x[1][1], reverse=True)[:15]
    )
    outcome_counts_simple = {kw: count for kw, (count, _) in outcome_counts.items()}

    claim_keywords_all = VAGUE_KEYWORDS + PROMOTIONAL_KEYWORDS
    claim_counts = {
        kw: count_keyword_sentences(sentences, [kw]) for kw in claim_keywords_all
    }
    claim_counts = {
        kw: (count, compute_weighted_score(kw, count, total_sentences))
        for kw, count in claim_counts.items()
        if count > 0
    }
    claim_counts = dict(
        sorted(claim_counts.items(), key=lambda x: x[1][1], reverse=True)[:15]
    )
    claim_counts_simple = {kw: count for kw, (count, _) in claim_counts.items()}

    return {
        "controversy": {
            "count": sum(controversy_counts.values()),
            "hits": list(controversy_counts.keys()),
            "frequencies": controversy_counts,
        },
        "indicators": {
            "claim_language": list(claim_counts_simple.keys()),
            "claim_language_frequencies": claim_counts_simple,
            "transparency": list(transparency_counts_simple.keys()),
            "transparency_frequencies": transparency_counts_simple,
            "outcome": list(outcome_counts_simple.keys()),
            "outcome_frequencies": outcome_counts_simple,
        },
    }


def confidence_score(claim, outcome, transparency, document, consistency=None, sentence_objects=None):
    """
    Compute confidence score measuring analysis quality, NOT company performance.
    
    Confidence depends on:
    - Document length (sufficient data for analysis)
    - Signal coverage (adequate signals detected)
    - Sentence classification confidence (ML model certainty)
    - Quantity of linked evidence (target-outcome linkage quality)
    - Document completeness (report structure, methodology)
    - Consistency of extracted signals (low contradiction)
    
    Confidence decreases when:
    - Evidence is sparse (short documents, few signals)
    - Evidence is contradictory (low linkage quality)
    - Evidence is poorly linked (low semantic similarity)
    - Document lacks structure (no methodology, no reporting framework)
    
    Confidence does NOT increase simply because a company performs well environmentally.
    """
    # Base score: neutral starting point
    score = CONFIG["CONFIDENCE_BASE_SCORE"]
    
    # Document length factor: longer documents generally provide more complete analysis
    word_count = int(claim.get("word_count", 0) or 0)
    if word_count < 100:
        score -= 15.0  # Very short documents have limited analysis value
    elif word_count < 300:
        score -= 8.0   # Short documents may miss context
    elif word_count >= 1000:
        score += 5.0   # Longer documents provide more complete picture
    
    # Signal coverage: adequate signals detected for meaningful analysis
    total_signals = (
        int(claim.get("promotional_hits", 0) or 0)
        + int(claim.get("vague_hits", 0) or 0)
        + int(claim.get("target_sentence_count", 0) or 0)
        + int(outcome.get("real_outcome_count", 0) or 0)
        + int(transparency.get("framework_count", 0) or 0)
        + int(transparency.get("assurance_count", 0) or 0)
    )
    if total_signals < 3:
        score -= 10.0  # Too few signals for reliable analysis
    elif total_signals >= 10:
        score += 5.0   # Good signal coverage
    
    # Sentence classification confidence: average ML model certainty
    if sentence_objects:
        avg_prediction_confidence = average(
            [float(obj.get("confidence", 0.0) or 0.0) for obj in sentence_objects]
        )
        if avg_prediction_confidence < 0.60:
            score -= 10.0  # Low classifier confidence
        elif avg_prediction_confidence < 0.75:
            score -= 5.0   # Moderate classifier confidence
        elif avg_prediction_confidence >= 0.85:
            score += 5.0   # High classifier confidence
    
    # Linkage quality: quantity and quality of target-outcome links
    if consistency is not None:
        avg_match = float(consistency.get("average_match_score", 0.0) or 0.0)
        targets = int(consistency.get("targets", 0) or 0)
        supported = int(consistency.get("supported_targets", 0) or 0)
        
        # Penalize poor linkage quality
        if avg_match < 0.55:
            score -= 12.0  # Very weak semantic matches
        elif avg_match < 0.65:
            score -= 6.0   # Weak semantic matches
        elif avg_match >= 0.75:
            score += 5.0   # Strong semantic matches
        
        # Penalize unsupported targets (evidence gaps)
        if targets > 0:
            unsupported_ratio = (targets - supported) / targets
            if unsupported_ratio > 0.5:
                score -= 10.0  # Most targets lack evidence
            elif unsupported_ratio > 0.25:
                score -= 5.0   # Many targets lack evidence
            elif unsupported_ratio == 0.0 and targets >= 3:
                score += 5.0   # All targets well-supported
    
    # Document completeness: structure and methodology
    framework_count = int(transparency.get("framework_count", 0) or 0)
    assurance_count = int(transparency.get("assurance_count", 0) or 0)
    scope_count = int(transparency.get("scope_count", 0) or 0)
    
    if framework_count == 0 and assurance_count == 0:
        score -= 8.0  # No reporting framework or assurance
    elif framework_count >= 2:
        score += 3.0   # Multiple frameworks referenced
    if assurance_count >= 1:
        score += 3.0   # External verification present
    if scope_count >= 2:
        score += 2.0   # Comprehensive scope coverage
    
    # Document type bonus: structured reports are more reliable
    doc_type = document.get("document_type", "")
    if doc_type == "ESG_REPORT":
        score += 5.0
    elif doc_type == "MARKETING_PAGE" or doc_type == "PRESS_RELEASE":
        score -= 5.0  # Marketing content less reliable
    
    # Quantified outcomes: signal data quality (not company performance)
    # This measures whether outcomes have numeric data, not whether they're "good"
    quantified = int(outcome.get("quantified_outcomes_count", 0) or 0)
    total_outcomes = int(outcome.get("real_outcome_count", 0) or 0)
    if total_outcomes > 0:
        quantification_rate = quantified / total_outcomes
        if quantification_rate < 0.3:
            score -= 5.0   # Most outcomes lack quantitative data
        elif quantification_rate >= 0.7:
            score += 5.0   # Most outcomes have quantitative data
    
    # Baseline epistemic deduction for real-world noise
    score -= 2.0
    
    # Hard cap: never output 100% for real documents
    score = min(score, 95.0)
    
    return round(clamp(score, 10.0, 95.0), 2)


def generate_drivers(claim, outcome, transparency, metrics):
    """
    Generate dynamic driver explanations based on actual scoring inputs.
    
    Drivers describe how the score was derived, not just what was detected.
    Explanations are contextual and reference the specific metrics that contribute
    to each score component.
    """
    claim_drivers = []
    outcome_drivers = []
    transparency_drivers = []
    risk_drivers = []

    vague = int(claim.get("vague_hits", 0) or 0)
    promo = int(claim.get("promotional_hits", 0) or 0)
    target_count = int(claim.get("target_sentence_count", 0) or 0)
    quantified = int(outcome.get("quantified_outcomes_count", 0) or 0)
    real_outcomes = int(outcome.get("real_outcome_count", 0) or 0)
    strong = int(outcome.get("strong_achievements", 0) or 0)
    grounded = int(outcome.get("grounded_real_outcomes", 0) or 0)
    fw_count = int(transparency.get("framework_count", 0) or 0)
    assurance = int(transparency.get("assurance_count", 0) or 0)
    scope = int(transparency.get("scope_count", 0) or 0)
    gap = float(metrics.get("greenwashing_gap", 0) or 0)
    claim_pressure = float(metrics.get("claim_pressure", 0) or 0)
    support_ratio = float(metrics.get("support_ratio", 0) or 0)
    future_density = float(metrics.get("future_target_density", 0) or 0)
    unsupported = int(metrics.get("unsupported_targets", 0) or 0)
    supported = int(metrics.get("supported_targets", 0) or 0)
    total_targets = int(claim.get("target_sentence_count", 0) or 0)

    # Claim drivers: explain what drives claim pressure
    if vague >= 2:
        claim_drivers.append(
            f"{vague} sentences with broad sustainability terms contribute to claim pressure"
        )
    if promo >= 1:
        claim_drivers.append(
            f"{promo} promotional positioning sentences elevate claim pressure"
        )
    if target_count >= 2:
        claim_drivers.append(
            f"{target_count} forward-looking target sentences increase claim pressure"
        )
    if target_count > 0 and quantified > 0:
        pct = round((quantified / max(1, real_outcomes)) * 100)
        claim_drivers.append(
            f"{pct}% of outcomes have quantitative data, partially offsetting claim pressure"
        )

    # Outcome drivers: explain how outcomes affect the greenwashing gap
    if quantified >= 2:
        outcome_drivers.append(
            f"{quantified} quantified outcomes partially offset claim pressure"
        )
    if real_outcomes >= 3:
        outcome_drivers.append(
            f"{real_outcomes} measured outcomes reduce the greenwashing gap"
        )
    if strong >= 1:
        outcome_drivers.append(
            f"{strong} verified past-performance statements strengthen outcome evidence"
        )
    if grounded >= 1:
        outcome_drivers.append(
            f"{grounded} entity-metric-value grounded outcomes increase outcome evidence score"
        )

    # Transparency drivers: explain disclosure quality
    if fw_count >= 1:
        fw_keywords = list(transparency.get("framework_hits", {}).keys())
        fw_label = ", ".join(fw_keywords[:4]) if fw_keywords else f"{fw_count} frameworks"
        transparency_drivers.append(
            f"Disclosure frameworks referenced: {fw_label} (improves transparency score)"
        )
    if assurance >= 1:
        transparency_drivers.append(
            f"{assurance} verification/assurance keyword types detected (strengthens transparency)"
        )
    if scope >= 2:
        transparency_drivers.append(
            f"Scope 1/2/3 boundary references across {scope} sentences (comprehensive scope coverage)"
        )

    # Risk drivers: explain what drives greenwashing risk
    if gap >= 25:
        outcome_evidence = float(metrics.get("outcome_evidence_score", 0) or 0)
        risk_drivers.append(
            f"Greenwashing gap of {gap:.0f} points: claim pressure ({claim_pressure:.0f}) exceeds outcome evidence ({outcome_evidence:.0f})"
        )
    if claim_pressure >= 40 and support_ratio < 0.8:
        risk_drivers.append(
            f"High claim pressure ({claim_pressure:.0f}) with weak target-outcome linkage ({support_ratio:.2f}x support ratio)"
        )
    if future_density >= 30 and support_ratio < 0.8:
        risk_drivers.append(
            f"Future target density {future_density:.0f}% with insufficient outcome backing (support ratio: {support_ratio:.2f}x)"
        )
    if support_ratio < 0.4:
        risk_drivers.append(
            f"Support ratio {support_ratio:.2f}x: most targets ({unsupported} of {total_targets}) lack linked outcome evidence"
        )
    if unsupported > 0 and total_targets > 0:
        pct_unsupported = round((unsupported / total_targets) * 100)
        risk_drivers.append(
            f"{unsupported} of {total_targets} targets ({pct_unsupported}%) have no linked outcome evidence (evidence gap)"
        )
    controversy_count = int(metrics.get("controversy_count", 0) or 0)
    if controversy_count > 0:
        risk_drivers.append(
            f"{controversy_count} potential controversy indicators detected (elevates risk)"
        )

    return {
        "claim": claim_drivers,
        "outcome": outcome_drivers,
        "transparency": transparency_drivers,
        "risk": risk_drivers,
    }


def deduplicate_grounded_kpis(grounded_kpis):
    unique_kpis = []
    seen = set()
    for kpi in grounded_kpis:
        key = (kpi.get("entity"), kpi.get("scope"), kpi.get("value"), kpi.get("unit"))
        if key not in seen:
            seen.add(key)
            unique_kpis.append(kpi)
    return unique_kpis


def default_analysis_output():
    default_consistency = {
        "targets": 0,
        "supported_targets": 0,
        "unsupported_targets": 0,
        "consistency_score": 50.0,  # neutral default — 50 means no information, not perfect
        "supported_target_examples": [],
        "unsupported_target_examples": [],
    }
    default_claim = {
        "claim_pressure": 0.0,
        "claim_pressure_raw": 0.0,
        "promotional_hits": 0,
        "vague_hits": 0,
        "target_sentence_count": 0,
        "word_count": 0,
        "target_pressure": 0,
    }
    default_outcome = {
        "outcome_evidence_score": 0.0,
        "real_outcome_count": 0,
        "quantified_outcomes_count": 0,
        "strong_achievements": 0,
        "grounded_real_outcomes": 0,
        "grounded_kpis": [],
        "outcome_sentences": [],
        "raw_outcome_score": 0.0,
        "total_outcome_strength": 0.0,
        "average_outcome_strength": 0.0,
    }
    default_transparency = {
        "score": 0.0,
        "framework_count": 0,
        "assurance_count": 0,
        "scope_count": 0,
        "framework_coverage": 0.0,
        "assurance_coverage": 0.0,
        "scope_coverage": 0.0,
        "methodology_depth": 0.0,
        "framework_hits": {},
        "assurance_hits": {},
    }
    default_document = {"document_type": "UNKNOWN", "signals": {}}
    default_risk = {
        "risk": 0.0,
        "risk_raw": 0.0,
        "greenwashing_gap": 0.0,
        "claim_pressure": 0.0,
        "future_target_density": 0.0,
        "outcome_evidence_score": 0.0,
        "unsupported_penalty": 0.0,
        "transparency_score": 0.0,
    }
    default_context = {
        "controversy": {"count": 0, "hits": [], "frequencies": {}},
        "indicators": {
            "claim_language": [],
            "claim_language_frequencies": {},
            "transparency": [],
            "transparency_frequencies": {},
            "outcome": [],
            "outcome_frequencies": {},
        },
    }

    return {
        "claim_pressure": 0.0,
        "cross_sentence_consistency": default_consistency,
        "claim": default_claim,
        "outcome_evidence": default_outcome,
        "transparency_score": 0.0,
        "transparency_detail": default_transparency,
        "greenwashing_gap": 0.0,
        "outcome_coverage_margin": 0.0,
        "support_ratio": 0.0,
        "support_ratio_category": support_ratio_category(0.0, has_targets=False),
        "support_ratio_explanation": {
            "number_of_targets": 0,
            "number_of_linked_outcomes": 0,
            "average_outcome_strength": 0.0,
            "support_category": support_ratio_category(0.0, has_targets=False),
            "supported_targets": 0,
            "unsupported_targets": 0,
            "percentage_supported": 0.0,
            "average_match_score": 0.0,
        },
        "future_target_density": 0.0,
        "effective_target_pressure": 0.0,
        "confidence_score": 0.0,
        "risk": 0.0,
        "risk_raw": 0.0,
        "document_type": default_document["document_type"],
        "document_classification": default_document,
        "sentence_classification": {
            "classification_breakdown": {
                "claim_count": 0,
                "outcome_count": 0,
                "target_count": 0,
                "transparency_count": 0,
                "neutral_count": 0,
            },
            "samples": [],
        },
        "grounded_kpis": [],
        "deduplicated_kpis": [],
        "supported_target_examples": [],
        "unsupported_target_examples": [],
        "support_ratio_components": {
            "grounded_supported_outcomes": 0,
            "total_outcome_strength": 0.0,
            "claim_count": 0,
        },
        "diagnostics": {
            "classification_breakdown": {
                "claim_count": 0,
                "outcome_count": 0,
                "target_count": 0,
                "transparency_count": 0,
                "neutral_count": 0,
            },
            "confidence_distribution": {},
            "grounding_coverage": {
                "entities_with_scope": 0,
                "entities_with_value": 0,
                "total_grounded": 0,
                "grounding_coverage_percentage": 0.0,
            },
            "outcome_strength_distribution": {},
            "target_clusters": [],
            "linked_targets": [],
            "average_prediction_confidence": 0.0,
            "average_outcome_strength": 0.0,
            "average_semantic_similarity": 0.0,
            "average_match_score": 0.0,
            "average_support_confidence": 0.0,
            "number_of_linked_targets": 0,
            "number_of_supported_targets": 0,
            "risk_components": default_risk,
        },
        "controversy": default_context["controversy"],
        "indicators": default_context["indicators"],
        "drivers": {"claim": [], "outcome": [], "transparency": [], "risk": []},
        "signals": {
            "cross_sentence_consistency": default_consistency,
            "claim_pressure": 0.0,
            "outcome_evidence_score": 0.0,
            "transparency_score": 0.0,
            "greenwashing_gap": 0.0,
            "outcome_coverage_margin": 0.0,
            "support_ratio": 0.0,
            "support_ratio_category": support_ratio_category(0.0, has_targets=False),
            "future_target_density": 0.0,
            "risk_raw": 0.0,
            "risk_components": default_risk,
            "document_type": default_document["document_type"],
            "confidence_score": 0.0,
            "claim_keywords": {},
            "transparency_keywords": {},
            "outcome_keywords": {},
            "controversy_keywords": {},
        },
    }


# ------------------------------
# Main function (backward compatible)
# ------------------------------
def analyze_text(text: str, ml_predictions: Optional[dict] = None):
    _ = ml_predictions

    default_output = default_analysis_output()
    stage_timings: Dict[str, float] = {}

    try:
        stage_start = time.perf_counter()
        sentence_objs = build_sentence_objects(text)
        stage_timings["build_sentence_objects"] = round(
            time.perf_counter() - stage_start, 4
        )

        stage_start = time.perf_counter()
        sentence_objs = link_targets_to_outcomes(sentence_objs)
        stage_timings["link_targets_to_outcomes"] = round(
            time.perf_counter() - stage_start, 4
        )

        sentence_classes = sentence_classes_from_objects(sentence_objs)

        stage_start = time.perf_counter()
        consistency = compute_cross_sentence_consistency(sentence_objects=sentence_objs)
        stage_timings["compute_cross_sentence_consistency"] = round(
            time.perf_counter() - stage_start, 4
        )

        stage_start = time.perf_counter()
        claim = (
            compute_claim_pressure(
                text, sentence_classes, sentence_objects=sentence_objs
            )
            or default_output["claim"]
        )
        stage_timings["compute_claim_pressure"] = round(
            time.perf_counter() - stage_start, 4
        )

        stage_start = time.perf_counter()
        outcome = (
            compute_outcome_evidence(
                text, sentence_classes, sentence_objects=sentence_objs
            )
            or default_output["outcome_evidence"]
        )
        stage_timings["compute_outcome_evidence"] = round(
            time.perf_counter() - stage_start, 4
        )

        stage_start = time.perf_counter()
        transparency = (
            compute_transparency_signals(text) or default_output["transparency_detail"]
        )
        stage_timings["compute_transparency_signals"] = round(
            time.perf_counter() - stage_start, 4
        )

        stage_start = time.perf_counter()
        context = extract_context_signals(text) or {
            "controversy": default_output["controversy"],
            "indicators": default_output["indicators"],
        }
        stage_timings["extract_context_signals"] = round(
            time.perf_counter() - stage_start, 4
        )

        deduplicated_kpis = deduplicate_grounded_kpis(outcome.get("grounded_kpis", []))

        claim_pressure = float(claim.get("claim_pressure", 0.0) or 0.0)
        document = (
            classify_document_type(text, outcome, transparency, claim_pressure)
            or default_output["document_classification"]
        )
        outcome_evidence_score = float(
            outcome.get("outcome_evidence_score", 0.0) or 0.0
        )
        transparency_score = float(transparency.get("score", 0.0) or 0.0)
        future_target_density, effective_target_pressure = (
            compute_future_target_density(
                sentence_classes,
                float(consistency.get("consistency_score", 50.0) or 50.0),
                sentence_objects=sentence_objs,
            )
        )
        # Calculate gap using raw values for accuracy, then round for display
        greenwashing_gap, outcome_coverage_margin = compute_greenwashing_gap(
            float(claim_pressure), float(outcome_evidence_score)
        )
        displayed_claim_pressure = round(claim_pressure)
        displayed_outcome_evidence = round(outcome_evidence_score)
        support_ratio, support_category = compute_support_ratio(
            outcome, claim, consistency
        )

        # support_category already set by compute_support_ratio; re-derive only to pass
        # has_targets so the N/A label is correct when there are no target sentences.
        has_targets = int(consistency.get("targets", 0) or 0) > 0
        support_category = support_ratio_category(
            support_ratio, has_targets=has_targets
        )
        confidence = float(
            confidence_score(
                claim,
                outcome,
                transparency,
                document,
                consistency=consistency,
                sentence_objects=sentence_objs,
            )
            or 0.0
        )

        risk_result = compute_greenwashing_risk(
            greenwashing_gap,
            claim_pressure,
            future_target_density,
            outcome_evidence_score,
            transparency_score,
            float(consistency.get("consistency_score", 50.0) or 50.0),
        )

        claim_count = sum(1 for item in sentence_classes if item["label"] == "CLAIM")
        real_outcome_count = sum(
            1 for item in sentence_classes if item["label"] == "OUTCOME"
        )
        target_count = sum(1 for item in sentence_classes if item["label"] == "TARGET")
        transparency_count = sum(
            1 for item in sentence_classes if item["label"] == "TRANSPARENCY"
        )
        neutral_count = sum(
            1 for item in sentence_classes if item["label"] == "NEUTRAL"
        )

        confidence_distribution = {}
        for obj in sentence_objs:
            confidence_bucket = bucket_confidence(
                float(obj.get("confidence", 0.0) or 0.0)
            )
            confidence_distribution[confidence_bucket] = (
                confidence_distribution.get(confidence_bucket, 0) + 1
            )

        outcome_strength_distribution = {}
        for obj in sentence_objs:
            if obj.get("label") == "OUTCOME":
                strength_value = float(obj.get("outcome_strength", 0.0) or 0.0)
                bucket_floor = min(int(strength_value // 10) * 10, 90)
                strength_bucket = f"{bucket_floor}-{bucket_floor + 9}"
                outcome_strength_distribution[strength_bucket] = (
                    outcome_strength_distribution.get(strength_bucket, 0) + 1
                )

        target_clusters = cluster_targets(sentence_objs)

        total_grounded = sum(
            1 for obj in sentence_objs if obj.get("grounding", {}).get("entity")
        )
        grounding_coverage = {
            "entities_with_scope": sum(
                1 for obj in sentence_objs if obj.get("grounding", {}).get("subentity")
            ),
            "entities_with_value": sum(
                1
                for obj in sentence_objs
                if obj.get("grounding", {}).get("value") is not None
            ),
            "total_grounded": total_grounded,
            "grounding_coverage_percentage": round(
                (total_grounded / len(sentence_objs)) * 100, 2
            )
            if sentence_objs
            else 0.0,
        }

        target_objects = [obj for obj in sentence_objs if obj.get("label") == "TARGET"]
        linked_target_count = sum(
            1 for obj in target_objects if obj.get("linked_outcomes")
        )
        linked_outcome_count = sum(
            len(obj.get("linked_outcomes", [])) for obj in target_objects
        )
        linked_similarities = [
            float(obj.get("best_semantic_similarity", 0.0) or 0.0)
            for obj in target_objects
            if obj.get("linked_outcomes")
        ]
        outcome_strength_values = [
            float(obj.get("outcome_strength", 0.0) or 0.0)
            for obj in sentence_objs
            if obj.get("label") == "OUTCOME"
        ]
        average_outcome_strength = (
            round(sum(outcome_strength_values) / len(outcome_strength_values), 2)
            if outcome_strength_values
            else 0.0
        )

        support_ratio_explanation = {
            "number_of_targets": int(consistency.get("targets", 0) or 0),
            "number_of_linked_outcomes": linked_outcome_count,
            "average_outcome_strength": average_outcome_strength,
            "support_category": support_category,
            "supported_targets": int(consistency.get("supported_targets", 0) or 0),
            "unsupported_targets": int(consistency.get("unsupported_targets", 0) or 0),
            "percentage_supported": round(
                (int(consistency.get("supported_targets", 0) or 0) / max(1, int(consistency.get("targets", 0) or 0))) * 100, 1
            ) if int(consistency.get("targets", 0) or 0) > 0 else 0.0,
            "average_match_score": float(consistency.get("average_match_score", 0.0) or 0.0),
        }

        if DEBUG:
            debug_log(
                f"Grounding coverage %: {grounding_coverage['grounding_coverage_percentage']:.2f}"
            )
            debug_log(f"Stage timings (s): {stage_timings}")

        metrics = {
            **risk_result,
            "support_ratio": support_ratio,
            "future_target_density": future_target_density,
            "effective_target_pressure": effective_target_pressure,
            "controversy_count": int(
                context.get("controversy", {}).get("count", 0) or 0
            ),
            "unsupported_targets": int(consistency.get("unsupported_targets", 0) or 0),
            "supported_targets": int(consistency.get("supported_targets", 0) or 0),
            "outcome_evidence_score": outcome_evidence_score,
            "claim_pressure": claim_pressure,
        }
        drivers = generate_drivers(claim, outcome, transparency, metrics)

        return {
            "claim_pressure": claim_pressure,
            "cross_sentence_consistency": consistency,
            "claim": claim,
            "outcome_evidence": outcome,
            "transparency_score": transparency_score,
            "transparency_detail": transparency,
            "greenwashing_gap": greenwashing_gap,
            # Surplus: outcome evidence exceeds claim pressure. Positive signal.
            # 0.0 when gap > 0 (claims dominate). Positive when outcomes dominate.
            "outcome_coverage_margin": outcome_coverage_margin,
            "support_ratio": support_ratio,
            "support_ratio_category": support_category,
            "support_ratio_explanation": support_ratio_explanation,
            "unsupported_targets": int(consistency.get("unsupported_targets", 0) or 0),
            "supported_targets": int(consistency.get("supported_targets", 0) or 0),
            "average_match_score": float(consistency.get("average_match_score", 0.0) or 0.0),
            "future_target_density": future_target_density,
            "effective_target_pressure": effective_target_pressure,
            "confidence_score": confidence,
            "risk": float(risk_result.get("risk", 0.0) or 0.0),
            "risk_raw": float(risk_result.get("risk_raw", 0.0) or 0.0),
            "document_type": document.get("document_type", "UNKNOWN") or "UNKNOWN",
            "document_classification": document,
            "sentence_classification": {
                "classification_breakdown": {
                    "claim_count": claim_count,
                    "outcome_count": real_outcome_count,
                    "target_count": target_count,
                    "transparency_count": transparency_count,
                    "neutral_count": neutral_count,
                },
                "samples": sentence_classes[:12],
            },
            "grounded_kpis": outcome.get("grounded_kpis", []),
            "deduplicated_kpis": deduplicated_kpis,
            "supported_target_examples": consistency.get(
                "supported_target_examples", []
            ),
            "unsupported_target_examples": consistency.get(
                "unsupported_target_examples", []
            ),
            "support_ratio_components": {
                "grounded_supported_outcomes": int(
                    outcome.get("grounded_real_outcomes", 0) or 0
                ),
                "total_outcome_strength": float(
                    outcome.get("total_outcome_strength", 0.0) or 0.0
                ),
                "claim_count": (
                    int(claim.get("target_sentence_count", 0) or 0)
                    + int(claim.get("promotional_hits", 0) or 0)
                    + int(claim.get("vague_hits", 0) or 0)
                ),
            },
            "diagnostics": {
                "classification_breakdown": {
                    "claim_count": claim_count,
                    "outcome_count": real_outcome_count,
                    "target_count": target_count,
                    "transparency_count": transparency_count,
                    "neutral_count": neutral_count,
                },
                "confidence_distribution": confidence_distribution,
                "grounding_coverage": grounding_coverage,
                "outcome_strength_distribution": outcome_strength_distribution,
                "target_clusters": target_clusters,
                "linked_targets": [
                    {
                        "target": t.get("text", ""),
                        "linked_outcomes": [
                            o.get("text", "") for o in t.get("linked_outcomes", [])
                        ],
                    }
                    for t in sentence_objs
                    if t.get("label") == "TARGET"
                ],
                "average_prediction_confidence": average(
                    [float(obj.get("confidence", 0.0) or 0.0) for obj in sentence_objs]
                ),
                "average_outcome_strength": average_outcome_strength,
                "average_semantic_similarity": average(linked_similarities),
                "average_match_score": float(
                    consistency.get("average_match_score", 0.0) or 0.0
                ),
                "average_support_confidence": float(
                    consistency.get("average_support_confidence", 0.0) or 0.0
                ),
                "number_of_linked_targets": linked_target_count,
                "number_of_supported_targets": int(
                    consistency.get("supported_targets", 0) or 0
                ),
                "risk_components": risk_result,
            },
            "controversy": context.get("controversy", default_output["controversy"]),
            "indicators": context.get("indicators", default_output["indicators"]),
            "drivers": drivers,
            "signals": {
                "cross_sentence_consistency": consistency,
                "claim_pressure": claim_pressure,
                "outcome_evidence_score": outcome_evidence_score,
                "transparency_score": transparency_score,
                "greenwashing_gap": greenwashing_gap,
                "outcome_coverage_margin": outcome_coverage_margin,
                "support_ratio": support_ratio,
                "support_ratio_category": support_category,
                "future_target_density": future_target_density,
                "risk_raw": float(risk_result.get("risk_raw", 0.0) or 0.0),
                "risk_components": risk_result,
                "document_type": document.get("document_type", "UNKNOWN") or "UNKNOWN",
                "confidence_score": confidence,
                "claim_keywords": context.get("indicators", {}).get(
                    "claim_language_frequencies", {}
                ),
                "transparency_keywords": context.get("indicators", {}).get(
                    "transparency_frequencies", {}
                ),
                "outcome_keywords": context.get("indicators", {}).get(
                    "outcome_frequencies", {}
                ),
                "controversy_keywords": context.get("controversy", {}).get(
                    "frequencies", {}
                ),
            },
        }
    except Exception as error:
        print(f"Error analyzing text: {error}")
        return default_output
