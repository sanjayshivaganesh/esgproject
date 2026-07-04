# ESG Greenwashing Analyzer - Deployment Memory Audit

## Constraint
**Maximum deployment size: 512 MB** (including models, tokenizers, weights, and runtime assets)

---

## Current Component Size Audit

### 1. Embedding Model: all-MiniLM-L6-v2
**Model Files:**
- model.safetensors: 87 MB
- tokenizer.json: 455 KB
- vocab.txt: 226 KB
- Config files: ~2 KB

**Total: ~87.7 MB**

**Runtime RAM (estimated):**
- Model loaded in memory: ~90 MB
- Tokenizer overhead: ~5 MB
- Embedding cache (per document): ~1-5 MB (depends on document length)

**Total runtime RAM: ~95-100 MB**

---

### 2. ML Classifier: model.pkl
**Model File:**
- model.pkl: 406 KB

**Total: 406 KB**

**Runtime RAM (estimated):**
- Model loaded in memory: ~1 MB
- Scikit-learn overhead: ~2 MB

**Total runtime RAM: ~3 MB**

---

### 3. Python Dependencies
**Key Dependencies:**
- sentence-transformers: ~50 MB (includes PyTorch)
- scikit-learn: ~30 MB
- numpy: ~20 MB
- joblib: ~5 MB
- Other dependencies: ~20 MB

**Total dependency size: ~125 MB** (installed, not all loaded at runtime)

**Runtime RAM (estimated):**
- PyTorch runtime: ~40-60 MB
- NumPy arrays: ~10-20 MB
- Other runtime: ~10 MB

**Total runtime RAM: ~60-90 MB**

---

### 4. Hidden Memory Overheads

#### Embedding Cache
- **Current:** No persistent cache
- **Runtime:** Embeddings stored in memory per document
- **Size:** 384 dimensions × 4 bytes × N sentences ≈ 1.5 KB per sentence
- **Example:** 1000 sentences ≈ 1.5 MB

#### Sentence Objects
- **Current:** Full sentence objects stored in memory
- **Size per object:** ~2-3 KB (text, label, confidence, embedding, grounding, links)
- **Example:** 1000 sentences ≈ 2-3 MB

#### KMeans Clustering
- **Current:** Uses sklearn KMeans for target clustering
- **Runtime RAM:** Minimal for small datasets (< 1 MB)

#### Duplicate Detection
- **Current:** Computes cosine similarity matrix for deduplication
- **Runtime RAM:** O(N²) for N sentences
- **Example:** 1000 sentences ≈ 8 MB (1000 × 1000 × 8 bytes)

---

## Current Total Deployment Size

### Disk Space
- Embedding model: 87.7 MB
- ML classifier: 0.4 MB
- Python code: ~1 MB
- **Total: ~89 MB**

### Runtime RAM
- Embedding model: ~95 MB
- ML classifier: ~3 MB
- PyTorch runtime: ~60 MB
- NumPy/runtime: ~30 MB
- Document processing: ~5-15 MB
- **Total: ~190-210 MB**

**Status: ✅ WELL UNDER 512 MB LIMIT**

---

## Previous Recommendations Audit

### Phase 1 Improvements (Implemented)
1. **Dynamic thresholding** - ✅ Fits (no additional memory)
2. **Lower unknown topic threshold** - ✅ Fits (no additional memory)
3. **Generic phrase filtering** - ✅ Fits (regex compiled once, negligible memory)
4. **Confidence-weighted matching** - ✅ Fits (no additional memory)

### Phase 2 Recommendations (Not Yet Implemented)
5. **Improve entity extraction** - ✅ Fits (regex patterns, negligible memory)
6. **Add temporal ordering penalty** - ✅ Fits (sentence indices, negligible memory)
7. **Ensure consistent embedding normalization** - ✅ Fits (no additional memory)
8. **Hierarchical topic mapping** - ✅ Fits (dictionary, negligible memory)

### Phase 3 Recommendations (Not Yet Implemented)
9. **ANN for candidate retrieval (FAISS)** - ⚠️ REQUIRES EVALUATION
   - **Memory impact:** FAISS index adds ~10-50 MB depending on size
   - **Still fits:** Yes (89 MB + 50 MB = 139 MB << 512 MB)
   - **Recommendation:** IMPLEMENT (significant performance gain)

10. **Caching for repeated computations** - ⚠️ REQUIRES EVALUATION
    - **Memory impact:** Depends on cache size (10-100 MB)
    - **Still fits:** Yes (89 MB + 100 MB = 189 MB << 512 MB)
    - **Recommendation:** IMPLEMENT with size limits

---

## Optimization Opportunities

### 1. Quantization

#### Embedding Model Quantization
**Current:** all-MiniLM-L6-v2 (FP32, 87 MB)

**Options:**
- **INT8 quantization:** ~22 MB (4x reduction)
- **Accuracy impact:** <1% degradation
- **Runtime RAM:** ~25 MB (vs 95 MB)
- **Deployment size:** ~24 MB (vs 89 MB)

**Recommendation:** IMPLEMENT INT8 QUANTIZATION
- **Pareto-optimal:** Significant memory reduction with minimal accuracy loss
- **Implementation:** Use `torch.quantization` or export to ONNX with quantization

#### ML Classifier Quantization
**Current:** 406 KB (already small)

**Recommendation:** SKIP (diminishing returns)

---

### 2. ONNX Conversion

#### Embedding Model to ONNX
**Current:** PyTorch/safetensors format

**Options:**
- **ONNX FP32:** ~87 MB (no size reduction)
- **ONNX INT8:** ~22 MB (4x reduction)
- **Accuracy impact:** <1% degradation
- **Runtime RAM:** ~20-30 MB (vs 95 MB)
- **Inference speed:** 1.5-2x faster

**Recommendation:** IMPLEMENT ONNX INT8
- **Pareto-optimal:** Memory reduction + speed improvement
- **Implementation:** Use `torch.onnx.export` with quantization

#### ML Classifier to ONNX
**Current:** scikit-learn pickle

**Options:**
- **ONNX:** ~300-400 KB (similar size)
- **Accuracy impact:** None
- **Runtime RAM:** ~1 MB (vs 3 MB)
- **Inference speed:** Minimal improvement

**Recommendation:** OPTIONAL (minor benefit)

---

### 3. Distilled Model Alternatives

#### Smaller Embedding Models
**Current:** all-MiniLM-L6-v2 (87 MB, 384 dim)

**Alternatives:**
1. **all-MiniLM-L4-v2** (23 MB, 256 dim)
   - **Size:** 23 MB (4x smaller)
   - **Accuracy impact:** 2-5% degradation
   - **Runtime RAM:** ~25 MB
   - **Recommendation:** CONSIDER if memory critical

2. **paraphrase-multilingual-MiniLM-L12-v2** (471 MB, 384 dim)
   - **Size:** 471 MB (EXCEEDS LIMIT)
   - **Recommendation:** REJECT

3. **e5-small-v2** (33 MB, 384 dim)
   - **Size:** 33 MB
   - **Accuracy impact:** 1-3% degradation
   - **Runtime RAM:** ~35 MB
   - **Recommendation:** STRONG ALTERNATIVE

**Recommendation:** STAY WITH all-MiniLM-L6-v2 + QUANTIZATION
- **Rationale:** Current model fits well with quantization
- **Pareto-optimal:** Quantization achieves similar size reduction with less accuracy loss than model downgrade

---

### 4. Unnecessary Computations

#### Current Inefficiencies

1. **Brute-force O(n*m) matching**
   - **Current:** Every target compared to every outcome
   - **Impact:** Slow for large documents
   - **Optimization:** ANN (FAISS) - already recommended

2. **Duplicate detection O(n²) similarity matrix**
   - **Current:** Computes full similarity matrix
   - **Impact:** Memory and time
   - **Optimization:** Use incremental comparison or ANN

3. **Repeated embedding normalization**
   - **Current:** May normalize same embeddings multiple times
   - **Impact:** Minor CPU overhead
   - **Optimization:** Cache normalized embeddings

4. **Regex compilation on every call**
   - **Current:** Some regex patterns compiled in functions
   - **Impact:** Minor CPU overhead
   - **Optimization:** Compile at module load (already done for GENERIC_PHRASES)

---

## Recommended Deployment Configuration

### Option 1: Conservative (Current + Minor Optimizations)
**Deployment Size:** ~89 MB
**Runtime RAM:** ~200 MB
**Inference Latency:** ~500-1000ms per page
**Accuracy:** Baseline (100%)

**Changes:**
- Implement ANN (FAISS) for candidate retrieval
- Add caching with size limits
- Optimize duplicate detection

---

### Option 2: Balanced (Quantization)
**Deployment Size:** ~25 MB
**Runtime RAM:** ~80 MB
**Inference Latency:** ~400-800ms per page
**Accuracy:** 99% (1% degradation)

**Changes:**
- Convert embedding model to ONNX INT8
- Implement ANN (FAISS)
- Add caching with size limits
- Optimize duplicate detection

---

### Option 3: Aggressive (Model Swap + Quantization)
**Deployment Size:** ~12 MB
**Runtime RAM:** ~40 MB
**Inference Latency:** ~300-600ms per page
**Accuracy:** 96-98% (2-4% degradation)

**Changes:**
- Switch to e5-small-v2 (33 MB → 12 MB with INT8)
- Convert to ONNX INT8
- Implement ANN (FAISS)
- Add caching with size limits

---

## Pareto-Optimal Recommendation

### Selected: Option 2 (Balanced - Quantization)

**Rationale:**
1. **Memory:** 25 MB << 512 MB (plenty of headroom)
2. **Accuracy:** 99% (minimal degradation)
3. **Speed:** ONNX provides 1.5-2x speedup
4. **Complexity:** Moderate (requires ONNX conversion)
5. **Risk:** Low (quantization is well-established)

**Trade-off Analysis:**
- **Memory vs Accuracy:** 4x memory reduction for 1% accuracy loss → EXCELLENT
- **Memory vs Speed:** 4x memory reduction + 1.5x speedup → EXCELLENT
- **Complexity vs Benefit:** Moderate complexity for significant benefits → GOOD

---

## Implementation Plan

### Phase 1: ONNX Conversion (Priority: HIGH)
1. Export all-MiniLM-L6-v2 to ONNX format
2. Apply INT8 quantization
3. Replace sentence-transformers with ONNX Runtime
4. Test accuracy degradation
5. Benchmark inference speed

**Expected Outcome:**
- Size: 87 MB → 22 MB
- RAM: 95 MB → 25 MB
- Speed: 1.5-2x faster
- Accuracy: 99%

---

### Phase 2: ANN Implementation (Priority: HIGH)
1. Integrate FAISS for candidate retrieval
2. Build embedding index for outcomes
3. Replace brute-force matching with ANN search
4. Tune top-k parameters

**Expected Outcome:**
- Speed: 10-20x faster for large documents
- Memory: +10-20 MB for FAISS index
- Accuracy: No change (same similarity metric)

---

### Phase 3: Caching (Priority: MEDIUM)
1. Implement LRU cache for embeddings
2. Cache normalized embeddings
3. Set size limits (max 50 MB)
4. Add cache hit metrics

**Expected Outcome:**
- Speed: 2-3x faster for repeated documents
- Memory: +10-50 MB (configurable)
- Accuracy: No change

---

## Deployment Summary (Recommended Configuration)

### Total Estimated Model Size
- **Embedding model (ONNX INT8):** 22 MB
- **ML classifier (pickle):** 0.4 MB
- **FAISS index:** 10-20 MB
- **Python code:** 1 MB
- **Total:** ~33-43 MB

### Estimated Runtime RAM
- **Embedding model:** 25 MB
- **ML classifier:** 3 MB
- **ONNX Runtime:** 10 MB
- **FAISS index:** 15 MB
- **NumPy/runtime:** 20 MB
- **Document processing:** 5-15 MB
- **Cache (optional):** 0-50 MB
- **Total:** ~78-138 MB (without cache)

### Estimated Inference Latency
- **Small document (< 50 sentences):** ~200-400ms
- **Medium document (50-200 sentences):** ~400-800ms
- **Large document (200-500 sentences):** ~800-1500ms

### Expected Annotation Accuracy
- **Compared to current:** 99% (1% degradation from quantization)
- **Absolute accuracy:** Maintained from Phase 1 improvements

### Remaining Optimization Opportunities
1. **Further quantization (INT4):** Additional 2x reduction, 2-3% accuracy loss
2. **Model distillation:** Custom distilled model for specific domain
3. **Pruning:** Remove unused layers from embedding model
4. **Knowledge distillation:** Train smaller model on current model outputs

---

## Conclusion

**Current Status:** ✅ WELL UNDER 512 MB LIMIT (89 MB disk, 200 MB RAM)

**Recommended Action:** IMPLEMENT ONNX INT8 QUANTIZATION
- **Pareto-optimal:** Significant memory/speed improvement with minimal accuracy loss
- **Risk:** Low (well-established technique)
- **Complexity:** Moderate (requires ONNX conversion)

**Alternative:** If quantization is too complex, current implementation is acceptable and well within limits.

**Previous Recommendations:** All fit within 512 MB limit. No rejections needed.
