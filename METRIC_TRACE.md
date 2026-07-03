# ESG Greenwashing Analyzer - End-to-End Metric Trace

This document traces each key metric from calculation to display to ensure single source of truth.

## 1. Claim Pressure

**Calculation:**
- Function: `compute_claim_pressure(text, sentence_classes, sentence_objects)`
- Location: rule_engine.py lines 1708-1784
- Formula: `clamp(promo_rate * CLAIM_PROMOTIONAL_WEIGHT * 100 + vague_rate * CLAIM_VAGUE_WEIGHT * 100, 0, 100)`
- Returns: dict with `claim_pressure`, `claim_pressure_raw`, `promotional_hits`, `vague_hits`, `target_sentence_count`, `word_count`, `target_pressure`, `claim_sentence_overlap`, `unique_claim_sentences`

**Storage:**
- Variable: `claim` in `analyze_text()`
- Location: rule_engine.py line 2973

**Serialization:**
- API Response: `rule.claim_pressure` (top-level)
- Location: rule_engine.py line 3208
- Also in: `rule.claim.claim_pressure`
- Also in: `rule.signals.claim_pressure`

**Frontend Reception:**
- Component: ResultsPage.jsx
- Function: `normalizeResult(result)`
- Location: line 38
- Access: `rule.claim_pressure`

**Display:**
- ScoreCard: "Claim Pressure"
- Location: line 219
- Value: `data.claimPressure`
- Assessment list: line 274

---

## 2. Outcome Evidence Score

**Calculation:**
- Function: `compute_outcome_evidence(text, sentence_classes, sentence_objects)`
- Location: rule_engine.py lines 1809-1920
- Formula: `clamp((average_strength * 0.6) + (evidence_density * 100 * 0.3) + (strong_achievements * 0.1 * 10), 0, 100)`
- Returns: dict with `outcome_evidence_score`, `real_outcome_count`, `quantified_outcomes_count`, etc.

**Storage:**
- Variable: `outcome` in `analyze_text()`
- Location: rule_engine.py line 2980

**Serialization:**
- API Response: `rule.outcome_evidence.outcome_evidence_score`
- Location: rule_engine.py line 3211
- Also in: `rule.signals.outcome_evidence_score`

**Frontend Reception:**
- Component: ResultsPage.jsx
- Function: `normalizeResult(result)`
- Location: line 39
- Access: `rule.outcome_evidence.outcome_evidence_score`

**Display:**
- ScoreCard: "Outcome Evidence"
- Location: line 225
- Value: `data.outcomeEvidence`
- Assessment list: line 275

---

## 3. Transparency Score

**Calculation:**
- Function: `compute_transparency_signals(text)`
- Location: rule_engine.py lines 1923-1991
- Formula: Weighted sum of framework_coverage, assurance_coverage, scope_coverage, methodology_depth
- Returns: dict with `score`, `framework_count`, `assurance_count`, etc.

**Storage:**
- Variable: `transparency` in `analyze_text()`
- Location: rule_engine.py line 2991

**Serialization:**
- API Response: `rule.transparency_score` (top-level)
- Location: rule_engine.py line 3212
- Also in: `rule.transparency_detail.score`
- Also in: `rule.signals.transparency_score`

**Frontend Reception:**
- Component: ResultsPage.jsx
- Function: `normalizeResult(result)`
- Location: line 40
- Access: `rule.transparency_score`

**Display:**
- ScoreCard: "Transparency"
- Location: line 238
- Value: `data.transparencyScore`
- Assessment list: line 276

---

## 4. Greenwashing Gap

**Calculation:**
- Function: `compute_greenwashing_gap(claim_pressure, outcome_evidence_score)`
- Location: rule_engine.py lines 2135-2146
- Formula: `max(0.0, claim_pressure - outcome_evidence_score)`
- Returns: tuple `(gap, coverage_margin)`

**Storage:**
- Variable: `greenwashing_gap` in `analyze_text()`
- Location: rule_engine.py line 3063

**Serialization:**
- API Response: `rule.greenwashing_gap` (top-level)
- Location: rule_engine.py line 3214
- Also in: `rule.signals.greenwashing_gap`

**Frontend Reception:**
- Component: ResultsPage.jsx
- Function: `normalizeResult(result)`
- Location: line 45
- Access: `rule.greenwashing_gap`

**Display:**
- ScoreCard: "Greenwashing Gap"
- Location: line 244
- Value: `data.greenwashingGap`
- Assessment list: line 279

---

## 5. Support Ratio

**Calculation:**
- Function: `compute_support_ratio(outcome_dict, claim_dict, consistency_dict)`
- Location: rule_engine.py lines 2108-2132
- Formula: `supported_targets / total_targets` (raw count ratio, NOT score ratio)
- Returns: tuple `(ratio, category)`

**Storage:**
- Variable: `support_ratio` in `analyze_text()`
- Location: rule_engine.py line 3029

**Serialization:**
- API Response: `rule.support_ratio` (top-level)
- Location: rule_engine.py line 3218
- Also in: `rule.signals.support_ratio`

**Frontend Reception:**
- Component: ResultsPage.jsx
- Function: `normalizeResult(result)`
- Location: line 42
- Access: `rule.support_ratio`

**Display:**
- ScoreCard: "Support Ratio"
- Location: line 231
- Value: `data.supportRatio.toFixed(2) + 'x'`
- Assessment list: line 278
- SmallMetric: line 324

---

## 6. Risk Score

**Calculation:**
- Function: `compute_greenwashing_risk(gap, claim_pressure, future_density, outcome_evidence, transparency, consistency)`
- Location: rule_engine.py lines 2149-2200
- Formula: `gap * 0.75 + claim_pressure * 0.15 + future_target_density * 0.15 + unsupported_penalty`
- Returns: dict with `risk`, `risk_raw`, etc.

**Storage:**
- Variable: `risk_result` in `analyze_text()`
- Location: rule_engine.py line 3088

**Serialization:**
- API Response: `rule.risk` (top-level)
- Location: rule_engine.py line 3243
- Also in: `rule.signals.risk_components`

**Frontend Reception:**
- Component: ResultsPage.jsx
- Function: `normalizeResult(result)`
- Location: line 29
- Access: `rule.risk`

**Display:**
- ScoreCard: "Risk Score"
- Location: line 250
- Value: `data.greenwashingRisk`
- Assessment: line 271

---

## 7. Confidence Score

**Calculation:**
- Function: `confidence_score(claim, outcome, transparency, document, consistency, sentence_objects)`
- Location: rule_engine.py lines 2546-2666
- Formula: Multi-factor analysis quality score (document length, signal coverage, classification confidence, linkage quality, document completeness)
- Returns: float (10-95)

**Storage:**
- Variable: `confidence` in `analyze_text()`
- Location: rule_engine.py line 3040

**Serialization:**
- API Response: `rule.confidence_score` (top-level)
- Location: rule_engine.py line 3242
- Also in: `rule.signals.confidence_score`

**Frontend Reception:**
- Component: ResultsPage.jsx
- Function: `normalizeResult(result)`
- Location: line 41
- Access: `rule.confidence_score`

**Display:**
- SmallMetric: "Confidence Score"
- Location: line 336
- Value: `data.confidenceScore`

---

## 8. Future Target Density

**Calculation:**
- Function: `compute_future_target_density(sentence_classes, consistency_score, sentence_objects)`
- Location: rule_engine.py lines 1787-1806
- Formula: `min(100.0, (target_sentence_count / total_sentence_count) * 100 * 3.0)`
- Returns: tuple `(future_target_density, effective_target_pressure)`

**Storage:**
- Variable: `future_target_density` in `analyze_text()`
- Location: line 3018

**Serialization:**
- API Response: `rule.future_target_density` (top-level)
- Location: rule_engine.py line 3224
- Also in: `rule.signals.future_target_density`

**Frontend Reception:**
- Component: ResultsPage.jsx
- Function: `normalizeResult(result)`
- Location: line 46
- Access: `rule.future_target_density`

**Display:**
- Assessment list: line 280

---

## 9. Document Type

**Calculation:**
- Function: `classify_document_type(text, outcome, transparency, claim_pressure)`
- Location: rule_engine.py lines 1994-2083
- Logic: Heuristic classification based on marketing hits, press hits, report hits, metric density
- Returns: dict with `document_type` and `signals`

**Storage:**
- Variable: `document` in `analyze_text()`
- Location: rule_engine.py line 3047

**Serialization:**
- API Response: `rule.document_type` (top-level)
- Location: rule_engine.py line 3245
- Also in: `rule.document_classification.document_type`
- Also in: `rule.signals.document_type`

**Frontend Reception:**
- Component: ResultsPage.jsx
- Function: `normalizeResult(result)`
- Location: line 41
- Access: `rule.document_type`

**Display:**
- SmallMetric: "Document Type"
- Location: line 299
- Assessment list: line 277

---

## 10. Support Ratio Details (New)

**Calculation:**
- Function: `compute_cross_sentence_consistency(sentence_classes, sentence_objects)`
- Location: rule_engine.py lines 2236-2443
- Logic: Counts targets, supported targets, unsupported targets, calculates average match score

**Storage:**
- Variable: `consistency` in `analyze_text()`
- Location: line 2963

**Serialization:**
- API Response: `rule.support_ratio_explanation` (top-level)
- Location: rule_engine.py line 3220
- Fields: `number_of_targets`, `supported_targets`, `unsupported_targets`, `percentage_supported`, `average_match_score`

**Frontend Reception:**
- Component: ResultsPage.jsx
- Function: `normalizeResult(result)`
- Location: lines 24, 91-96
- Access: `rule.support_ratio_explanation`

**Display:**
- Target-Outcome Linkage Details section
- Location: lines 357-381
- Displays: Total Targets, Supported Targets, Unsupported Targets, Percentage Supported, Avg Match Score

---

## 11. Claim Themes / Indicators

**Calculation:**
- Function: `extract_context_signals(text)`
- Location: rule_engine.py lines 2440-2520
- Logic: Weighted TF-IDF-like scoring with phrase length weighting and filler word penalties
- Returns: dict with `controversy`, `indicators` (claim_language, transparency, outcome frequencies)

**Storage:**
- Variable: `context` in `analyze_text()`
- Location: line 2998

**Serialization:**
- API Response: `rule.indicators.claim_language_frequencies`
- Location: rule_engine.py line 3318
- Also in: `rule.signals.claim_keywords`

**Frontend Reception:**
- Component: ResultsPage.jsx
- Function: `normalizeResult(result)`
- Location: line 53
- Access: `rule.signals.claim_keywords ?? rule.indicators.claim_language_frequencies`

**Display:**
- ListCard: "Claim Themes"
- Location: line 384

---

## 12. Outcome Indicators

**Calculation:**
- Function: `extract_context_signals(text)` with lemmatization
- Location: rule_engine.py lines 2440-2520
- Logic: Weighted scoring with `normalize_lemma()` for grouping related word forms
- Returns: dict with `indicators.outcome_frequencies`

**Storage:**
- Variable: `context` in `analyze_text()`
- Location: line 2998

**Serialization:**
- API Response: `rule.indicators.outcome_frequencies`
- Location: rule_engine.py line 3340
- Also in: `rule.signals.outcome_keywords`

**Frontend Reception:**
- Component: ResultsPage.jsx
- Function: `normalizeResult(result)`
- Location: line 55
- Access: `rule.signals.outcome_keywords ?? rule.indicators.outcome_frequencies`

**Display:**
- ListCard: "Outcome Indicators"
- Location: line 390

---

## 13. Drivers

**Calculation:**
- Function: `generate_drivers(claim, outcome, transparency, metrics)`
- Location: rule_engine.py lines 2669-2789
- Logic: Dynamic explanations based on actual scoring inputs
- Returns: dict with `claim`, `outcome`, `transparency`, `risk` driver arrays

**Storage:**
- Variable: `drivers` in `analyze_text()`
- Location: line 3205

**Serialization:**
- API Response: `rule.drivers` (top-level)
- Location: rule_engine.py line 3319

**Frontend Reception:**
- Component: ResultsPage.jsx
- Function: `normalizeResult(result)`
- Location: lines 58-62
- Access: `rule.drivers.claim`, `rule.drivers.outcome`, etc.

**Display:**
- ListCard: "Claim Drivers", "Outcome Drivers", "Transparency Drivers", "Risk Drivers"
- Location: lines 377-399

---

## Summary of Single Source of Truth

All metrics originate from backend calculations in `rule_engine.py`:
- No frontend recalculations
- No duplicate field names in backend output
- Canonical field names used throughout
- Frontend purely presents backend values via `normalizeResult()`

**Canonical Field Names:**
- `claim_pressure` (not `claimPressure` in backend)
- `outcome_evidence.outcome_evidence_score` (not `evidence.evidence_score`)
- `greenwashing_gap` (not `gap`)
- `transparency_score` (not `transparency`)
- `support_ratio` (with `support_ratio_explanation` for details)
- `risk` (not `greenwashingRisk` in backend)
- `confidence_score`
- `future_target_density`
- `document_type`
- `indicators` (for themes)
- `drivers` (for explanations)
