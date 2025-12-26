"""
Risk assessment configuration and thresholds
"""
import os
from typing import Dict, List

# Risk thresholds - configurable via environment variables
RISK_THRESHOLDS = {
    "ml_high": float(os.getenv("ML_HIGH_THRESHOLD", "0.8")),
    "ml_medium": float(os.getenv("ML_MEDIUM_THRESHOLD", "0.5")),
    "rule_high": int(os.getenv("RULE_HIGH_THRESHOLD", "3")),
    "rule_medium": int(os.getenv("RULE_MEDIUM_THRESHOLD", "1")),
}

# Safe next steps templates by risk level
SAFE_NEXT_STEPS: Dict[str, List[str]] = {
    "HIGH_RISK": [
        "Do not click any links in this message",
        "Do not reply or call any numbers provided",
        "Delete this message immediately",
        "If concerned, contact the organization directly using official contact information",
    ],
    "MEDIUM_RISK": [
        "Be cautious with this message",
        "Verify the sender independently before responding",
        "Do not provide any personal information",
        "Check with family if unsure",
    ],
    "SAFE": [
        "This message appears legitimate",
        "Always remain cautious with unexpected requests",
    ],
}

