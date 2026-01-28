"""
ML Model Configuration

Configuration for ML-based SMS scam detection models,
including model IDs, ensemble weights, thresholds, and scam indicators.
"""

# HuggingFace Model IDs
MODELS = {
    "phishing_text": "ealvaradob/bert-finetuned-phishing",  # BERT-based phishing detector
    "sms_spam": "mrm8488/bert-small-finetuned-sms-spam-detection",  # SMS spam classifier
    "url_phishing": "elftsdmr/malware-url-detect",  # URL phishing detector
}

# Ensemble weights for final risk score calculation
# Formula: weighted_sum(model_scores) + rules_boost
ENSEMBLE_WEIGHTS = {
    "phishing_text": 0.55,  # Primary signal - phishing language detection
    "sms_spam": 0.25,       # Secondary signal - spam patterns
    "url_phishing": 0.35,   # High weight if URLs present
}

# Risk level thresholds
RISK_LEVEL_THRESHOLDS = {
    "low": 0.3,      # Below this is low risk
    "medium": 0.6,   # Between 0.3-0.6 is medium risk
    # Above 0.6 is high risk
}

# Maximum message length for analysis
MAX_MESSAGE_LENGTH = 2000

# Rule-based scam indicators
# Each indicator provides a score boost and a human-readable reason
SCAM_INDICATORS = {
    "urgency": {
        "patterns": [
            r"\burgent\b",
            r"\basap\b",
            r"\bimmediately\b",
            r"\bact now\b",
            r"\bhurry\b",
            r"\blimited time\b",
            r"\bexpires soon\b",
            r"\bwithin \d+ hours?\b",
        ],
        "score_boost": 0.15,
        "reason": "Creates false sense of urgency",
    },
    "money": {
        "patterns": [
            r"\$\d+",
            r"\bmoney\b",
            r"\bcash\b",
            r"\bprize\b",
            r"\bwin\b",
            r"\bwinner\b",
            r"\breward\b",
            r"\bclaim\b",
            r"\brefund\b",
            r"\bfree\s+money\b",
        ],
        "score_boost": 0.12,
        "reason": "Mentions money or prizes",
    },
    "credentials": {
        "patterns": [
            r"\bpassword\b",
            r"\bpin\b",
            r"\bssn\b",
            r"\bsocial security\b",
            r"\bcredit card\b",
            r"\bbank account\b",
            r"\blogin\b",
            r"\bverify\s+account\b",
            r"\bconfirm\s+identity\b",
        ],
        "score_boost": 0.2,
        "reason": "Requests sensitive information",
    },
    "authority_impersonation": {
        "patterns": [
            r"\birs\b",
            r"\bbank\s+of\b",
            r"\bfedex\b",
            r"\bups\b",
            r"\busps\b",
            r"\bamazon\b",
            r"\bpaypal\b",
            r"\bapple\b",
            r"\bgoogle\b",
            r"\bmicrosoft\b",
            r"\bpolice\b",
            r"\bfbi\b",
        ],
        "score_boost": 0.18,
        "reason": "Impersonates known authority/brand",
    },
    "action_required": {
        "patterns": [
            r"\bclick here\b",
            r"\bverify now\b",
            r"\bconfirm now\b",
            r"\bupdate now\b",
            r"\bactivate\b",
            r"\breply\s+with\b",
            r"\bcall\s+\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            r"\btext\s+back\b",
        ],
        "score_boost": 0.1,
        "reason": "Pressures for immediate action",
    },
    "threats": {
        "patterns": [
            r"\baccount\s+suspended\b",
            r"\baccount\s+locked\b",
            r"\baccount\s+closed\b",
            r"\bwill be\s+charged\b",
            r"\blegal\s+action\b",
            r"\barrest\b",
            r"\bwarrant\b",
            r"\bpenalty\b",
            r"\bfine\b",
        ],
        "score_boost": 0.15,
        "reason": "Uses threats or fear tactics",
    },
}

# Label mappings for different models
# Maps model output labels to internal standardized labels
LABEL_MAPPINGS = {
    "phishing_text": {
        "LABEL_0": "SAFE",
        "LABEL_1": "SCAM",
        "label_0": "SAFE",
        "label_1": "SCAM",
    },
    "sms_spam": {
        "LABEL_0": "SAFE",
        "LABEL_1": "SCAM",
        "label_0": "SAFE",
        "label_1": "SCAM",
        "ham": "SAFE",
        "spam": "SCAM",
    },
    "url_phishing": {
        "LABEL_0": "SAFE",
        "LABEL_1": "SCAM",
        "label_0": "SAFE",
        "label_1": "SCAM",
        "benign": "SAFE",
        "malware": "SCAM",
        "phishing": "SCAM",
    },
}
