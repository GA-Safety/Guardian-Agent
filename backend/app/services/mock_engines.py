"""
Mock implementations for rule engine and ML scorer

TODO: Replace with actual implementations when ML model is trained and rule engine is complete
"""
import re
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class MockRuleEngine:
    """
    Mock rule engine for detecting scam patterns in SMS messages.
    
    TODO: Replace with actual rule engine implementation
    """
    
    def __init__(self):
        """Initialize rule patterns"""
        self.rules = {
            "urgency": {
                "patterns": [
                    r"\burgent\b",
                    r"\bact now\b",
                    r"\bexpires today\b",
                    r"\bimmediate action required\b",
                    r"\bexpires in\b",
                    r"\blimited time\b",
                    r"\bmust act\b",
                ],
                "description": "Creates false urgency",
            },
            "financial": {
                "patterns": [
                    r"\bverify account\b",
                    r"\bsuspended\b",
                    r"\bupdate payment\b",
                    r"\bconfirm your card\b",
                    r"\baccount locked\b",
                    r"\bpayment failed\b",
                    r"\bverify identity\b",
                ],
                "description": "Financial account manipulation attempt",
            },
            "suspicious_link": {
                "patterns": [
                    r"bit\.ly/\w+",
                    r"tinyurl\.com/\w+",
                    r"t\.co/\w+",
                    r"goo\.gl/\w+",
                    r"short\.link/\w+",
                    r"http[s]?://[a-z0-9-]+\.(tk|ml|ga|cf|gq)",
                ],
                "description": "Contains suspicious shortened link",
            },
            "impersonation": {
                "patterns": [
                    r"\bIRS\b",
                    r"\bSocial Security\b",
                    r"\bMedicare\b",
                    r"\byour bank\b",
                    r"\bgovernment\b",
                    r"\bfederal\b",
                    r"\btax department\b",
                ],
                "description": "Impersonates official organization",
            },
            "prizes_money": {
                "patterns": [
                    r"\bwinner\b",
                    r"\bcongratulations\b",
                    r"\bclaim your\b",
                    r"\bfree money\b",
                    r"\bprize\b",
                    r"\byou've won\b",
                    r"\bclaim now\b",
                ],
                "description": "Promises prizes or free money",
            },
        }
    
    async def analyze(self, message_content: str) -> List[Dict[str, any]]:
        """
        Analyze message content for rule matches.
        
        Args:
            message_content: The SMS message text to analyze
            
        Returns:
            List of rule match dictionaries with rule_name, confidence, and description
        """
        matches = []
        content_lower = message_content.lower()
        
        for rule_name, rule_config in self.rules.items():
            for pattern in rule_config["patterns"]:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    # Calculate confidence based on pattern match strength
                    confidence = 0.7 if rule_name in ["urgency", "financial"] else 0.6
                    
                    matches.append({
                        "rule_name": rule_name,
                        "confidence": confidence,
                        "description": rule_config["description"],
                    })
                    # Only count each rule once per message
                    break
        
        logger.debug(f"Rule engine found {len(matches)} matches")
        return matches


class MockMLScorer:
    """
    Mock ML scorer that returns scores based on keyword density.
    
    TODO: Replace with actual BERT model implementation
    """
    
    def __init__(self):
        """Initialize scam keywords for scoring"""
        self.scam_keywords = {
            "high_risk": [
                "urgent", "suspended", "verify", "click", "link", "expires",
                "immediate", "action required", "account locked", "verify identity",
            ],
            "medium_risk": [
                "update", "confirm", "verify", "security", "alert", "warning",
            ],
        }
    
    async def score(self, message_content: str) -> float:
        """
        Score message content for scam likelihood.
        
        Args:
            message_content: The SMS message text to score
            
        Returns:
            Score between 0.0 (safe) and 1.0 (high risk)
        """
        content_lower = message_content.lower()
        
        # Count high-risk keywords
        high_risk_count = sum(
            1 for keyword in self.scam_keywords["high_risk"]
            if keyword in content_lower
        )
        
        # Count medium-risk keywords
        medium_risk_count = sum(
            1 for keyword in self.scam_keywords["medium_risk"]
            if keyword in content_lower
        )
        
        # Calculate base score from keyword density
        base_score = min(0.3 + (high_risk_count * 0.15) + (medium_risk_count * 0.1), 0.9)
        
        # Boost score for suspicious patterns
        if re.search(r"bit\.ly|tinyurl|t\.co", content_lower):
            base_score = min(base_score + 0.2, 1.0)
        
        if re.search(r"\b(IRS|Social Security|Medicare)\b", content_lower, re.IGNORECASE):
            base_score = min(base_score + 0.15, 1.0)
        
        # Add some randomness to simulate ML uncertainty (0.05 variance)
        import random
        score = max(0.0, min(1.0, base_score + random.uniform(-0.05, 0.05)))
        
        logger.debug(f"ML scorer returned score: {score:.3f}")
        return round(score, 3)

