from __future__ import annotations

import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import (
    KFold,
    StratifiedKFold,
    cross_validate,
    train_test_split,
)
from sklearn.pipeline import Pipeline

RANDOM_STATE = 42
TEST_SIZE = 0.20
CV_FOLDS = 5
MIN_SAMPLES_FOR_STRATIFICATION = 2
MAX_ITER = 3000
MAX_FEATURES = 10000
TOP_FEATURES_PER_CLASS = 20
MISCLASSIFIED_EXAMPLE_LIMIT = 10
SENTENCE_COLUMN = "sentence"
LABEL_COLUMN = "label"
OUTPUTS_DIR = Path("outputs")
RESULTS_PATH = OUTPUTS_DIR / "results.txt"
CLASSIFICATION_REPORT_CSV = OUTPUTS_DIR / "classification_report.csv"
CONFUSION_MATRIX_CSV = OUTPUTS_DIR / "confusion_matrix.csv"
CONFUSION_MATRIX_PNG = OUTPUTS_DIR / "confusion_matrix.png"
FEATURE_IMPORTANCE_CSV = OUTPUTS_DIR / "feature_importance.csv"
MODEL_PATH = OUTPUTS_DIR / "model.pkl"
MODEL_METADATA_PATH = OUTPUTS_DIR / "model_metadata.json"
DATASET_PATH = Path("FINAL_ESG_DATASET.csv")


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    sublinear_tf=True,
                    min_df=2,
                    max_df=0.95,
                    strip_accents="unicode",
                    max_features=MAX_FEATURES,
                    stop_words="english",
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=MAX_ITER,
                    random_state=RANDOM_STATE,
                    class_weight="balanced",
                ),
            ),
        ]
    )


def validate_required_columns(df: pd.DataFrame) -> None:
    missing_columns = [
        column for column in [SENTENCE_COLUMN, LABEL_COLUMN] if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Dataset is missing required columns: {missing_columns}. "
            f"Expected columns include '{SENTENCE_COLUMN}' and '{LABEL_COLUMN}'."
        )


def normalize_labels(labels: pd.Series) -> pd.Series:
    return labels.astype(str).str.strip().str.upper()


def ensure_outputs_dir() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def format_fold_scores(metric_name: str, scores: List[float]) -> List[str]:
    lines = [f"{metric_name}:"]
    for index, score in enumerate(scores, start=1):
        lines.append(f"  Fold {index}: {score:.4f}")
    lines.append(f"  Mean: {pd.Series(scores).mean():.4f}")
    lines.append(f"  Std:  {pd.Series(scores).std(ddof=0):.4f}")
    return lines


def print_class_distribution(title: str, labels: pd.Series) -> None:
    print(f"\n{title}")
    print(labels.value_counts().sort_index())


def compute_min_class_count(labels: pd.Series) -> int:
    if labels.empty:
        return 0
    return int(labels.value_counts().min())


def can_use_stratification(labels: pd.Series) -> bool:
    return compute_min_class_count(labels) >= MIN_SAMPLES_FOR_STRATIFICATION


def run_cross_validation(
    pipeline: Pipeline,
    texts: pd.Series,
    labels: pd.Series,
) -> Tuple[List[float], List[float], str]:
    if len(texts) < 2:
        return [], [], "SKIPPED"

    min_class_count = compute_min_class_count(labels)
    if min_class_count >= MIN_SAMPLES_FOR_STRATIFICATION:
        n_splits = min(CV_FOLDS, min_class_count)
        if n_splits >= 2:
            cv = StratifiedKFold(
                n_splits=n_splits,
                shuffle=True,
                random_state=RANDOM_STATE,
            )
            cv_mode = f"StratifiedKFold(n_splits={n_splits})"
        else:
            cv = KFold(n_splits=2, shuffle=True, random_state=RANDOM_STATE)
            cv_mode = "KFold(n_splits=2)"
    else:
        n_splits = min(CV_FOLDS, len(texts))
        if n_splits < 2:
            return [], [], "SKIPPED"
        warnings.warn(
            "At least one class has fewer than 2 samples; using non-stratified KFold for cross-validation."
        )
        cv = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
        cv_mode = f"KFold(n_splits={n_splits})"

    cv_results = cross_validate(
        clone(pipeline),
        texts,
        labels,
        cv=cv,
        scoring={"accuracy": "accuracy", "macro_f1": "f1_macro"},
        n_jobs=None,
        return_train_score=False,
    )
    return list(cv_results["test_accuracy"]), list(cv_results["test_macro_f1"]), cv_mode


def extract_top_features(
    pipeline: Pipeline, top_n: int = TOP_FEATURES_PER_CLASS
) -> pd.DataFrame:
    vectorizer: TfidfVectorizer = pipeline.named_steps["tfidf"]
    classifier: LogisticRegression = pipeline.named_steps["classifier"]
    feature_names = vectorizer.get_feature_names_out()
    classes = list(classifier.classes_)
    coefficients = classifier.coef_

    rows: List[Dict[str, object]] = []

    if len(classes) == 2 and coefficients.shape[0] == 1:
        class_coefficient_map = {
            classes[0]: -coefficients[0],
            classes[1]: coefficients[0],
        }
    else:
        class_coefficient_map = {
            class_name: coefficients[index] for index, class_name in enumerate(classes)
        }

    for class_name, class_coefficients in class_coefficient_map.items():
        top_indices = class_coefficients.argsort()[-top_n:][::-1]
        for feature_index in top_indices:
            rows.append(
                {
                    "Class": class_name,
                    "Feature": feature_names[feature_index],
                    "Coefficient": float(class_coefficients[feature_index]),
                }
            )

    return pd.DataFrame(rows, columns=["Class", "Feature", "Coefficient"])


def save_confusion_matrix_artifacts(
    y_true: pd.Series, y_pred: pd.Series, labels: List[str]
) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    pd.DataFrame(cm, index=labels, columns=labels).to_csv(CONFUSION_MATRIX_CSV)

    fig, ax = plt.subplots(figsize=(8, 6))
    display = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    display.plot(ax=ax, cmap="Blues", values_format="d", colorbar=True)
    ax.set_title("Confusion Matrix")
    fig.tight_layout()
    fig.savefig(CONFUSION_MATRIX_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)


def save_classification_report_csv(
    y_true: pd.Series, y_pred: pd.Series, labels: List[str]
) -> pd.DataFrame:
    report_dict = classification_report(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
        output_dict=True,
    )
    report_df = pd.DataFrame(report_dict).transpose()
    report_df.to_csv(CLASSIFICATION_REPORT_CSV)
    return report_df


def build_metrics_dict(
    y_true: pd.Series,
    y_pred: pd.Series,
    labels: List[str],
) -> Dict[str, object]:
    report_dict = classification_report(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
        output_dict=True,
    )
    per_class_f1 = {
        label: float(report_dict.get(label, {}).get("f1-score", 0.0))
        for label in labels
    }
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "per_class_f1": per_class_f1,
    }


def build_model_metadata(
    classes: List[str], vocabulary_size: int, dataset_size: int
) -> Dict[str, object]:
    return {
        "classes": classes,
        "vectorizer_vocabulary_size": int(vocabulary_size),
        "dataset_size": int(dataset_size),
    }


def build_confidence_summary(probabilities: np.ndarray) -> Dict[str, float]:
    if probabilities.size == 0:
        return {
            "average_prediction_confidence": 0.0,
            "min_prediction_confidence": 0.0,
            "max_prediction_confidence": 0.0,
        }

    confidences = probabilities.max(axis=1)
    return {
        "average_prediction_confidence": float(np.mean(confidences)),
        "min_prediction_confidence": float(np.min(confidences)),
        "max_prediction_confidence": float(np.max(confidences)),
    }


def print_misclassified_examples(
    X_test: pd.Series,
    y_true: pd.Series,
    y_pred: np.ndarray,
    probabilities: np.ndarray,
) -> None:
    misclassified_mask = y_true.to_numpy() != y_pred
    misclassified_indices = np.where(misclassified_mask)[0][
        :MISCLASSIFIED_EXAMPLE_LIMIT
    ]

    print("\n" + "=" * 50)
    print("MISCLASSIFIED EXAMPLES")
    print("=" * 50)

    if len(misclassified_indices) == 0:
        print("No misclassified examples in test set.")
        return

    X_test_list = list(X_test)
    y_true_list = list(y_true)
    for index in misclassified_indices:
        confidence = (
            float(np.max(probabilities[index])) if len(probabilities[index]) else 0.0
        )
        print(f"\nSentence: {X_test_list[index]}")
        print(f"True label: {y_true_list[index]}")
        print(f"Predicted label: {y_pred[index]}")
        print(f"Confidence: {confidence:.4f}")


def main() -> None:
    np.random.seed(RANDOM_STATE)
    ensure_outputs_dir()

    df = pd.read_csv(DATASET_PATH)
    validate_required_columns(df)
    df = df.dropna(subset=[SENTENCE_COLUMN, LABEL_COLUMN])

    print("=" * 50)
    print("DATASET INFORMATION")
    print("=" * 50)
    print(f"Original rows after schema validation: {len(df)}")

    df[SENTENCE_COLUMN] = df[SENTENCE_COLUMN].astype(str)
    df[LABEL_COLUMN] = normalize_labels(df[LABEL_COLUMN])
    df = df.drop_duplicates(subset=[SENTENCE_COLUMN])

    print(f"Rows after deduplication: {len(df)}")
    print_class_distribution("Label Distribution (normalized):", df[LABEL_COLUMN])
    print("\nMissing Values:")
    print(df[[SENTENCE_COLUMN, LABEL_COLUMN]].isnull().sum())

    pipeline = build_pipeline()

    print("\nRunning cross-validation...")
    cv_accuracy_scores, cv_macro_f1_scores, cv_mode = run_cross_validation(
        pipeline,
        df[SENTENCE_COLUMN],
        df[LABEL_COLUMN],
    )

    if cv_accuracy_scores:
        print(f"\nCross-validation mode: {cv_mode}")
        print("\nCross-Validation Accuracy")
        for line in format_fold_scores("Accuracy (CV)", cv_accuracy_scores)[1:]:
            print(line)

        print("\nCross-Validation Macro F1")
        for line in format_fold_scores("Macro F1 (CV)", cv_macro_f1_scores)[1:]:
            print(line)
    else:
        print("\nCross-validation skipped: not enough samples.")

    label_min_count = compute_min_class_count(df[LABEL_COLUMN])
    stratify_labels = (
        df[LABEL_COLUMN] if can_use_stratification(df[LABEL_COLUMN]) else None
    )
    if stratify_labels is None:
        warnings.warn(
            "At least one class has fewer than 2 samples; using random train/test split without stratification."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        df[SENTENCE_COLUMN],
        df[LABEL_COLUMN],
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=stratify_labels,
    )

    print("\nTrain/Test Split")
    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")
    print_class_distribution("Class Distribution Before Split:", df[LABEL_COLUMN])
    print_class_distribution("Class Distribution - Train:", y_train)
    print_class_distribution("Class Distribution - Test:", y_test)
    print(f"\nMinimum class count in full dataset: {label_min_count}")

    print("\nTraining model...")
    pipeline.fit(X_train, y_train)
    print("Training complete.")

    predictions = pipeline.predict(X_test)
    probability_matrix = pipeline.predict_proba(X_test)
    sorted_labels = sorted(list(pipeline.classes_))

    metrics = build_metrics_dict(y_test, predictions, sorted_labels)
    confidence_summary = build_confidence_summary(probability_matrix)
    report = classification_report(
        y_test, predictions, labels=sorted_labels, zero_division=0
    )

    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(json.dumps(metrics, indent=2))
    print("\nConfidence Summary")
    print(json.dumps(confidence_summary, indent=2))
    print(f"\nAccuracy (Test): {metrics['accuracy']:.4f}")
    print(f"Macro F1 (Test): {metrics['macro_f1']:.4f}")
    print("\nClassification Report:\n")
    print(report)

    print_misclassified_examples(X_test, y_test, predictions, probability_matrix)

    save_classification_report_csv(y_test, predictions, sorted_labels)
    save_confusion_matrix_artifacts(y_test, predictions, sorted_labels)
    extract_top_features(pipeline).to_csv(FEATURE_IMPORTANCE_CSV, index=False)

    vectorizer: TfidfVectorizer = pipeline.named_steps["tfidf"]
    classifier: LogisticRegression = pipeline.named_steps["classifier"]
    training_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    results_lines = [
        "ESG GREENWASHING CLASSIFIER RESULTS",
        "=" * 40,
        "",
        f"Dataset Size: {len(df)}",
        f"Train Size: {len(X_train)}",
        f"Test Size: {len(X_test)}",
        f"Vocabulary Size: {len(vectorizer.vocabulary_)}",
        f"Number of Labels: {len(sorted_labels)}",
        f"Training Date/Time: {training_timestamp}",
        f"Model Parameters: {classifier.get_params()}",
        f"Cross-Validation Mode: {cv_mode}",
        "",
        "Structured Metrics",
        "------------------",
        json.dumps(metrics, indent=2),
        "",
        "Confidence Summary",
        "------------------",
        json.dumps(confidence_summary, indent=2),
        "",
        "Cross-Validation Scores",
        "-----------------------",
    ]

    if cv_accuracy_scores:
        results_lines.extend(format_fold_scores("Accuracy (CV)", cv_accuracy_scores))
        results_lines.append("")
        results_lines.extend(format_fold_scores("Macro F1 (CV)", cv_macro_f1_scores))
        results_lines.extend(
            [
                "",
                f"Mean Accuracy (CV): {pd.Series(cv_accuracy_scores).mean():.4f}",
                f"Mean Macro F1 (CV): {pd.Series(cv_macro_f1_scores).mean():.4f}",
            ]
        )
    else:
        results_lines.extend(
            [
                "Cross-validation skipped.",
                "",
                "Mean Accuracy (CV): 0.0000",
                "Mean Macro F1 (CV): 0.0000",
            ]
        )

    results_lines.extend(
        [
            f"Accuracy (Test): {metrics['accuracy']:.4f}",
            f"Macro F1 (Test): {metrics['macro_f1']:.4f}",
            f"Average Prediction Confidence (Test): {confidence_summary['average_prediction_confidence']:.4f}",
            f"Min Prediction Confidence (Test): {confidence_summary['min_prediction_confidence']:.4f}",
            f"Max Prediction Confidence (Test): {confidence_summary['max_prediction_confidence']:.4f}",
            "",
            "Classification Report",
            "---------------------",
            report,
        ]
    )
    RESULTS_PATH.write_text("\n".join(results_lines))

    joblib.dump(pipeline, MODEL_PATH)
    MODEL_METADATA_PATH.write_text(
        json.dumps(
            build_model_metadata(
                classes=sorted_labels,
                vocabulary_size=len(vectorizer.vocabulary_),
                dataset_size=len(df),
            ),
            indent=2,
        )
    )

    print(f"\nSaved evaluation results to {RESULTS_PATH}")
    print(f"Saved classification report to {CLASSIFICATION_REPORT_CSV}")
    print(f"Saved confusion matrix CSV to {CONFUSION_MATRIX_CSV}")
    print(f"Saved confusion matrix image to {CONFUSION_MATRIX_PNG}")
    print(f"Saved feature importance to {FEATURE_IMPORTANCE_CSV}")
    print(f"Model saved as {MODEL_PATH}")
    print(f"Model metadata saved as {MODEL_METADATA_PATH}")

    examples = [
        "We aim to achieve net zero emissions by 2040.",
        "Scope 1 emissions decreased by 18% during FY2024.",
        "This report follows the GRI Standards.",
        "The company operates manufacturing facilities in 12 countries.",
        "We are committed to building a more sustainable future.",
    ]

    print("\n" + "=" * 50)
    print("EXAMPLE PREDICTIONS")
    print("=" * 50)

    for sentence in examples:
        probabilities = pipeline.predict_proba([sentence])[0]
        probability_distribution = {
            label: float(probability)
            for label, probability in zip(pipeline.classes_, probabilities)
        }
        prediction_index = int(probabilities.argmax())
        prediction = pipeline.classes_[prediction_index]
        confidence = float(probabilities[prediction_index])

        print(f"\nSentence: {sentence}")
        print(f"Predicted label: {prediction}")
        print(f"Prediction confidence: {confidence:.4f}")
        print(f"Probability distribution: {probability_distribution}")


if __name__ == "__main__":
    main()
