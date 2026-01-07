"""
Mock Data for ML Analyzer Testing

Provides realistic SMS message samples covering various scam types and safe messages.
Used for testing the ML analyzer and ensuring comprehensive test coverage.
"""

# Scam Message Samples
SCAM_MESSAGES = {
    "bank_phishing": {
        "text": (
            "URGENT: Your Bank of America account has been suspended due to suspicious activity. "
            "Verify your identity immediately at bit.ly/verify-account or your account will be closed."
        ),
        "sender": "+15555551234",
        "expected_risk": "high",
        "expected_indicators": ["urgency", "impersonation", "shortened_url", "threats"],
        "description": "Classic bank impersonation phishing with urgency and threats",
    },
    "irs_scam": {
        "text": (
            "FINAL NOTICE: This is the IRS. You owe $4,532 in back taxes. "
            "Call 1-800-555-0199 immediately to avoid legal action and arrest warrant."
        ),
        "sender": "+15555559999",
        "expected_risk": "high",
        "expected_indicators": ["impersonation", "threats", "money", "urgency"],
        "description": "IRS impersonation scam with threats and urgency",
    },
    "package_delivery_scam": {
        "text": (
            "FedEx: Your package is on hold. Update shipping address at "
            "fedex-delivery.tk/track?id=ABC123 within 24 hours or it will be returned."
        ),
        "sender": "+15555552222",
        "expected_risk": "high",
        "expected_indicators": ["impersonation", "urgency", "action_required"],
        "description": "Fake package delivery notification",
    },
    "prize_winner_scam": {
        "text": (
            "Congratulations! You've won $10,000 in our sweepstakes! "
            "Claim your prize NOW at www.prize-claim.tk before it expires in 2 hours!"
        ),
        "sender": "+15555553333",
        "expected_risk": "medium",
        "expected_indicators": ["money", "urgency"],
        "description": "Fake prize/lottery scam",
    },
    "crypto_scam": {
        "text": (
            "Your Coinbase account requires verification. Click here to verify: "
            "t.co/xYz123 or your crypto wallet will be locked permanently."
        ),
        "sender": "+15555554444",
        "expected_risk": "high",
        "expected_indicators": ["impersonation", "shortened_url", "threats", "action_required"],
        "description": "Cryptocurrency platform phishing",
    },
    "paypal_phishing": {
        "text": (
            "PayPal Security Alert: Unusual activity detected. "
            "Verify your password and credit card details at paypal-security.com/verify"
        ),
        "sender": "+15555555555",
        "expected_risk": "high",
        "expected_indicators": ["impersonation", "credentials", "action_required"],
        "description": "PayPal credential phishing",
    },
    "western_union_scam": {
        "text": (
            "You must wire $500 via Western Union to claim your inheritance of $50,000. "
            "This is urgent and must be done today."
        ),
        "sender": "+15555556666",
        "expected_risk": "high",
        "expected_indicators": ["money", "urgency"],
        "description": "Wire transfer / advance fee scam",
    },
    "job_scam": {
        "text": (
            "You've been selected for a $25/hr work-from-home job! "
            "Reply with your SSN and bank account for direct deposit setup."
        ),
        "sender": "+15555557777",
        "expected_risk": "high",
        "expected_indicators": ["money", "credentials"],
        "description": "Fake job offer requesting sensitive info",
    },
    "microsoft_tech_support": {
        "text": (
            "Microsoft Security: Your computer has been infected with malware. "
            "Call our tech support at 1-888-555-TECH immediately to avoid data loss."
        ),
        "sender": "+15555558888",
        "expected_risk": "high",
        "expected_indicators": ["impersonation", "threats", "urgency"],
        "description": "Tech support scam",
    },
    "refund_scam": {
        "text": (
            "You are eligible for a tax refund of $1,247. "
            "Click here to claim: irs-refund.tk/claim Expires in 48 hours."
        ),
        "sender": "+15555550000",
        "expected_risk": "high",
        "expected_indicators": ["money", "urgency", "impersonation"],
        "description": "Fake tax refund scam",
    },
}

# Safe/Legitimate Message Samples
SAFE_MESSAGES = {
    "personal_message": {
        "text": "Hey! Are we still on for dinner tonight at 7pm? Let me know!",
        "sender": "+15551234567",
        "expected_risk": "low",
        "expected_indicators": [],
        "description": "Personal message from friend",
    },
    "delivery_confirmation": {
        "text": (
            "Your Amazon package has been delivered to your front door. "
            "Tracking number: 1Z999AA10123456784"
        ),
        "sender": "+15551112222",
        "expected_risk": "low",
        "expected_indicators": [],
        "description": "Legitimate delivery confirmation",
    },
    "appointment_reminder": {
        "text": (
            "Reminder: Your dentist appointment is tomorrow at 2:00 PM. "
            "Reply CONFIRM to confirm or CANCEL to reschedule."
        ),
        "sender": "+15559876543",
        "expected_risk": "low",
        "expected_indicators": [],
        "description": "Appointment reminder",
    },
    "two_factor_auth": {
        "text": "Your verification code is: 847392. This code expires in 5 minutes.",
        "sender": "+15550001111",
        "expected_risk": "low",
        "expected_indicators": [],
        "description": "Legitimate 2FA code",
    },
    "subscription_renewal": {
        "text": (
            "Your Netflix subscription will renew on Jan 15 for $15.99. "
            "Manage your subscription at netflix.com/account"
        ),
        "sender": "+15552223333",
        "expected_risk": "low",
        "expected_indicators": [],
        "description": "Subscription renewal notice",
    },
    "weather_alert": {
        "text": (
            "Weather Alert: Heavy rain expected in your area from 3-6 PM today. "
            "Drive safely!"
        ),
        "sender": "+15554445555",
        "expected_risk": "low",
        "expected_indicators": [],
        "description": "Weather notification",
    },
    "family_message": {
        "text": "Happy birthday! Hope you have an amazing day. Love, Mom",
        "sender": "+15556667777",
        "expected_risk": "low",
        "expected_indicators": [],
        "description": "Family birthday message",
    },
}

# Edge Cases
EDGE_CASE_MESSAGES = {
    "empty_message": {
        "text": "",
        "sender": "+15555550001",
        "expected_error": "Message text cannot be empty",
        "description": "Empty message should raise validation error",
    },
    "very_long_message": {
        "text": "A" * 3000,  # Exceeds MAX_MESSAGE_LENGTH (2000)
        "sender": "+15555550002",
        "expected_error": "exceeds maximum length",
        "description": "Message exceeding max length should raise error",
    },
    "whitespace_only": {
        "text": "   \n\t  ",
        "sender": "+15555550003",
        "expected_error": "Message text cannot be empty",
        "description": "Whitespace-only message should be treated as empty",
    },
    "special_characters": {
        "text": "Test message with émojis 🎉🔥 and spëcial çharacters!",
        "sender": "+15555550004",
        "expected_risk": "low",
        "description": "Message with unicode and emojis",
    },
    "multiple_urls": {
        "text": (
            "Check out these sites: https://example.com, www.test.org, "
            "and bit.ly/short for more info"
        ),
        "sender": "+15555550005",
        "expected_risk": "low",
        "description": "Message with multiple URLs",
    },
}

# Mock Model Predictions
MOCK_MODEL_PREDICTIONS = {
    "high_scam": {
        "phishing_text": [{"label": "LABEL_1", "score": 0.92}],
        "sms_spam": [{"label": "spam", "score": 0.85}],
        "url_phishing": [{"label": "phishing", "score": 0.88}],
    },
    "medium_scam": {
        "phishing_text": [{"label": "LABEL_1", "score": 0.65}],
        "sms_spam": [{"label": "spam", "score": 0.55}],
        "url_phishing": [{"label": "LABEL_1", "score": 0.60}],
    },
    "low_scam": {
        "phishing_text": [{"label": "LABEL_0", "score": 0.15}],
        "sms_spam": [{"label": "ham", "score": 0.10}],
        "url_phishing": [{"label": "benign", "score": 0.05}],
    },
    "safe": {
        "phishing_text": [{"label": "LABEL_0", "score": 0.05}],
        "sms_spam": [{"label": "ham", "score": 0.02}],
        "url_phishing": [{"label": "benign", "score": 0.01}],
    },
}

# Test URLs
TEST_URLS = {
    "shortened": [
        "http://bit.ly/abc123",
        "http://t.co/xyz789",
        "http://tinyurl.com/test",
        "http://goo.gl/short",
    ],
    "legitimate": [
        "https://www.google.com",
        "https://amazon.com/product/123",
        "https://github.com/user/repo",
    ],
    "suspicious": [
        "http://paypal-verify.tk",
        "http://bank-secure.ml",
        "http://irs-refund.ga",
    ],
}


def get_all_scam_messages():
    """Get all scam message samples"""
    return SCAM_MESSAGES


def get_all_safe_messages():
    """Get all safe message samples"""
    return SAFE_MESSAGES


def get_all_edge_cases():
    """Get all edge case samples"""
    return EDGE_CASE_MESSAGES


def get_message_by_key(key: str):
    """Get a specific message sample by key"""
    if key in SCAM_MESSAGES:
        return SCAM_MESSAGES[key]
    elif key in SAFE_MESSAGES:
        return SAFE_MESSAGES[key]
    elif key in EDGE_CASE_MESSAGES:
        return EDGE_CASE_MESSAGES[key]
    else:
        raise KeyError(f"Message key '{key}' not found")


def get_mock_predictions(risk_level: str):
    """Get mock model predictions for a given risk level"""
    return MOCK_MODEL_PREDICTIONS.get(risk_level, MOCK_MODEL_PREDICTIONS["safe"])
