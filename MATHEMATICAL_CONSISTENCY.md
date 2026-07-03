# Mathematical Consistency Validation

## Verified Formulas

### 1. Greenwashing Gap
**Formula:** `gap = max(0.0, claim_pressure - outcome_evidence_score)`
**Location:** rule_engine.py line 2144
**Status:** ✅ VERIFIED

**Example:**
- Claim Pressure = 71
- Outcome Evidence = 45
- Greenwashing Gap = 71 - 45 = 26
- Displayed: 26

**Consistency Check:** The gap is always the difference between claim pressure and outcome evidence. This is mathematically consistent.

---

### 2. Support Ratio
**Formula:** `support_ratio = supported_targets / total_targets`
**Location:** rule_engine.py line 2131
**Status:** ✅ VERIFIED

**Important:** This is a raw count ratio, NOT a score ratio.
- Support ratio measures evidence linkage completeness (0-2.0x)
- It does NOT equal outcome_evidence_score / claim_pressure

**Example:**
- Total Targets = 5
- Supported Targets = 3
- Support Ratio = 3 / 5 = 0.6x
- Displayed: 0.60x

**Consistency Check:** The support ratio is correctly calculated as a proportion of targets with linked outcomes. This is intentionally different from the score ratio (outcome/claim). The frontend explanation has been updated to reflect this.

---

### 3. Risk Score
**Formula:** `risk = clamp(gap * 0.75 + claim_pressure * 0.15 + future_target_density * 0.15 + unsupported_penalty, 0, 100)`
**Location:** rule_engine.py lines 2178-2185
**Status:** ✅ VERIFIED

**Components:**
- Greenwashing Gap: 75% weight
- Claim Pressure: 15% weight
- Future Target Density: 15% weight
- Unsupported Penalty: variable (0-15 points based on consistency_score)

**Example:**
- Gap = 26
- Claim Pressure = 71
- Future Target Density = 30
- Unsupported Penalty = 5 (assuming consistency_score = 67)
- Risk = 26 * 0.75 + 71 * 0.15 + 30 * 0.15 + 5 = 19.5 + 10.65 + 4.5 + 5 = 39.65
- Displayed: 40 (rounded)

**Consistency Check:** The risk formula is correctly implemented and documented. Transparency score is intentionally excluded from the risk calculation (informational only).

---

### 4. Outcome Evidence Score
**Formula:** `outcome_evidence_score = clamp((average_strength * 0.6) + (evidence_density * 100 * 0.3) + (strong_achievements * 0.1 * 10), 0, 100)`
**Location:** rule_engine.py lines 1897-1902
**Status:** ✅ VERIFIED

**Components:**
- Average Outcome Strength: 60% weight
- Evidence Density: 30% weight
- Strong Achievements: 10% weight (multiplied by 10)

**Consistency Check:** The formula correctly weights different evidence factors. Transparency and frameworks are intentionally excluded (they are separate metrics).

---

### 5. Claim Pressure
**Formula:** `claim_pressure = clamp(promo_rate * CLAIM_PROMOTIONAL_WEIGHT * 100 + vague_rate * CLAIM_VAGUE_WEIGHT * 100, 0, 100)`
**Location:** rule_engine.py lines 1761-1766
**Status:** ✅ VERIFIED

**Constants:**
- CLAIM_PROMOTIONAL_WEIGHT = 3.0
- CLAIM_VAGUE_WEIGHT = 1.5

**Consistency Check:** The formula correctly weights promotional and vague language. Target sentences are tracked separately (target_pressure) but not added to claim_pressure to avoid double-counting with future_target_density.

---

### 6. Transparency Score
**Formula:** `transparency_score = clamp(framework_coverage * TRANSPARENCY_FRAMEWORK_WEIGHT + assurance_coverage * TRANSPARENCY_ASSURANCE_WEIGHT + scope_coverage * TRANSPARENCY_SCOPE_WEIGHT + methodology_depth * TRANSPARENCY_METHODOLOGY_WEIGHT, 0, 100)`
**Location:** rule_engine.py lines 1970-1978
**Status:** ✅ VERIFIED

**Consistency Check:** Transparency is correctly separated from environmental evidence. It does not reduce risk (informational only).

---

### 7. Future Target Density
**Formula:** `future_target_density = min(100.0, (target_sentence_count / total_sentence_count) * 100 * 3.0)`
**Location:** rule_engine.py lines 1799-1802
**Status:** ✅ VERIFIED

**Consistency Check:** The multiplier of 3.0 gives higher weight to target density. Effective target pressure is adjusted by consistency score.

---

### 8. Confidence Score
**Formula:** Multi-factor analysis quality score
**Location:** rule_engine.py lines 2546-2666
**Status:** ✅ VERIFIED

**Factors:**
- Document length (penalty for short documents)
- Signal coverage (adequate signals detected)
- Sentence classification confidence (ML model certainty)
- Linkage quality (target-outcome semantic similarity)
- Document completeness (frameworks, assurance, scope)
- Document type (ESG reports > marketing pages)
- Quantification rate (data quality, not performance)

**Consistency Check:** Confidence measures analysis quality, NOT company performance. This is correctly implemented.

---

## Summary of Mathematical Consistency

✅ All formulas are correctly implemented
✅ All formulas are documented in code
✅ No contradictions between displayed values
✅ Support ratio correctly documented as raw count ratio (not score ratio)
✅ Greenwashing gap correctly calculated as claim - outcome
✅ Risk score correctly weighted by gap, claim pressure, and future density
✅ Transparency correctly separated from environmental evidence
✅ Confidence score correctly measures analysis quality

## Potential User Confusion Points

### Support Ratio vs Score Ratio
- **Support Ratio:** supported_targets / total_targets (measures linkage completeness)
- **Score Ratio:** outcome_evidence_score / claim_pressure (would measure relative strength)

The dashboard displays Support Ratio, which is intentionally different from the score ratio. This is correct but could be confusing without proper explanation. The frontend has been updated with the correct explanation.

### Transparency vs Outcome Evidence
- **Transparency:** Frameworks, assurance, scope (informational only)
- **Outcome Evidence:** Past environmental performance (affects risk)

These are separate metrics. Transparency does not reduce risk unless accompanied by high outcome evidence (which naturally lowers the gap). This is correctly implemented.
