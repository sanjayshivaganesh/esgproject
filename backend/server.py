from fastapi import FastAPI
import json
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from rule_engine import analyze_text

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://esgproject.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputText(BaseModel):
    text: str

@app.post("/analyze")
def analyze(data: InputText):
    text = (data.text or "").strip()

    rule_output = analyze_text(text)

    print("\n===== ESG ANALYSIS DEBUG =====")
    print(json.dumps(rule_output, indent=2))
    print("=============================\n")

    rule_risk = rule_output.get("risk", 0)
    rule_risk_norm = round(max(0.0, min(rule_risk / 100.0, 1.0)), 4)

    if rule_risk_norm > 0.7:
        verdict = "high risk greenwashing"
    elif rule_risk_norm > 0.4:
        verdict = "moderate risk greenwashing"
    else:
        verdict = "low risk greenwashing"

    return {
        "rule": rule_output,
        "debug": {
            "claim": rule_output.get("claim", {}),
            "outcome_evidence": rule_output.get("outcome_evidence", {}),
            "controversy": rule_output.get("controversy", {}),
            "document_type": rule_output.get("document_type"),
            "support_ratio_category": rule_output.get("support_ratio_category"),
        },
        "fusion": {
            "score": rule_risk_norm,
            "verdict": verdict
        }
    }
