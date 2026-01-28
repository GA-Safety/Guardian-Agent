"""
Unit tests for ML analyzer logic (without loading actual models)

Tests scoring logic, rules detection, and ensemble calculations.
"""
import pytest
import re
from app.config.ml_config import (
    ENSEMBLE_WEIGHTS,
    RISK_LEVEL_THRESHOLDS,
    SCAM_INDICATORS,
)


class TestEnsembleScoring:
    """Test ensemble score calculation logic"""

    def _calculate_ensemble(
        self,
        phishing: float,
        spam: float,
        url: float,
        rules: float,
    ) -> float:
        """Mirror the ensemble calculation from MLAnalyzer"""
        weighted = (
            ENSEMBLE_WEIGHTS["phishing_text"] * phishing
            + ENSEMBLE_WEIGHTS["sms_spam"] * spam
            + ENSEMBLE_WEIGHTS["url_phishing"] * url
            + rules
        )
        return max(0.0, min(1.0, weighted))

    def test_high_phishing_score(self):
        """Test high phishing score dominates"""
        score = self._calculate_ensemble(0.9, 0.1, 0.0, 0.0)
        assert score > 0.4  # Should be weighted heavily

    def test_ensemble_with_rules_boost(self):
        """Test rules boost increases final score"""
        base_score = self._calculate_ensemble(0.5, 0.3, 0.2, 0.0)
        boosted_score = self._calculate_ensemble(0.5, 0.3, 0.2, 0.2)
        assert boosted_score > base_score

    def test_clamping_max(self):
        """Test that scores are clamped to 1.0"""
        score = self._calculate_ensemble(1.0, 1.0, 1.0, 1.0)
        assert score == 1.0

    def test_clamping_min(self):
        """Test that scores are clamped to 0.0"""
        score = self._calculate_ensemble(0.0, 0.0, 0.0, 0.0)
        assert score == 0.0

    def test_realistic_scam_scenario(self):
        """Test realistic scam detection scenario"""
        # High phishing + high URL + rules boost
        score = self._calculate_ensemble(0.85, 0.7, 0.9, 0.25)
        assert score > 0.7  # Should be high risk


class TestRiskLevelDetermination:
    """Test risk level categorization"""

    def _determine_risk_level(self, risk_score: float) -> str:
        """Mirror risk level logic from MLAnalyzer"""
        if risk_score > RISK_LEVEL_THRESHOLDS["medium"]:
            return "high"
        elif risk_score > RISK_LEVEL_THRESHOLDS["low"]:
            return "medium"
        else:
            return "low"

    def test_low_risk(self):
        """Test low risk threshold"""
        assert self._determine_risk_level(0.0) == "low"
        assert self._determine_risk_level(0.3) == "low"

    def test_medium_risk(self):
        """Test medium risk threshold"""
        assert self._determine_risk_level(0.5) == "medium"
        assert self._determine_risk_level(0.59) == "medium"

    def test_high_risk(self):
        """Test high risk threshold"""
        assert self._determine_risk_level(0.75) == "high"
        assert self._determine_risk_level(1.0) == "high"

    def test_boundary_conditions(self):
        """Test exact threshold boundaries"""
        low_threshold = RISK_LEVEL_THRESHOLDS["low"]
        medium_threshold = RISK_LEVEL_THRESHOLDS["medium"]

        assert self._determine_risk_level(low_threshold - 0.01) == "low"
        assert self._determine_risk_level(low_threshold + 0.01) == "medium"
        assert self._determine_risk_level(medium_threshold + 0.01) == "high"


class TestRulesDetection:
    """Test rules-based scam indicator detection"""

    def _check_rules(self, text: str) -> tuple[float, list[str]]:
        """Mirror rules detection logic from MLAnalyzer"""
        text_lower = text.lower()
        total_boost = 0.0
        triggered_reasons = []

        for indicator_name, indicator_config in SCAM_INDICATORS.items():
            for pattern in indicator_config["patterns"]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    total_boost += indicator_config["score_boost"]
                    reason = indicator_config["reason"]
                    if reason not in triggered_reasons:
                        triggered_reasons.append(reason)
                    break

        return total_boost, triggered_reasons

    def test_urgency_detection(self):
        """Test urgency pattern detection"""
        text = "URGENT: Your account will expire today!"
        boost, reasons = self._check_rules(text)
        assert boost > 0
        assert "Creates false sense of urgency" in reasons

    def test_account_lock_detection(self):
        """Test account lock pattern detection"""
        text = "Your account locked due to unusual activity"
        boost, reasons = self._check_rules(text)
        assert boost > 0
        assert "Uses threats or fear tactics" in reasons

    def test_credential_request_detection(self):
        """Test credential request detection"""
        text = "Please verify your account password"
        boost, reasons = self._check_rules(text)
        assert boost > 0
        assert "Requests sensitive information" in reasons

    def test_money_transfer_detection(self):
        """Test money transfer pattern detection"""
        text = "You won $5000 cash prize immediately"
        boost, reasons = self._check_rules(text)
        assert boost > 0
        assert "Mentions money or prizes" in reasons or "Creates false sense of urgency" in reasons

    def test_impersonation_detection(self):
        """Test impersonation pattern detection"""
        text = "This is the IRS. You owe back taxes."
        boost, reasons = self._check_rules(text)
        assert boost > 0
        assert "Impersonates known authority/brand" in reasons

    def test_link_shortener_detection(self):
        """Test link shortener detection"""
        text = "Click here now: http://example.com"
        boost, reasons = self._check_rules(text)
        assert boost > 0
        assert "Pressures for immediate action" in reasons

    def test_multiple_indicators(self):
        """Test multiple scam indicators in one message"""
        text = (
            "URGENT: Your bank account has been locked. "
            "Verify your password at bit.ly/verify immediately!"
        )
        boost, reasons = self._check_rules(text)
        # Should detect urgency, threats, credential request, and action
        assert boost >= 0.35  # Multiple boosts
        assert len(reasons) >= 2

    def test_safe_message(self):
        """Test that safe messages trigger no rules"""
        text = "Hi mom, can you pick up milk on your way home? Thanks!"
        boost, reasons = self._check_rules(text)
        assert boost == 0.0
        assert len(reasons) == 0


class TestScamSampleScoring:
    """Test scoring with realistic scam samples"""

    def _calculate_ensemble(
        self, phishing: float, spam: float, url: float, rules: float
    ) -> float:
        """Mirror ensemble calculation"""
        weighted = (
            ENSEMBLE_WEIGHTS["phishing_text"] * phishing
            + ENSEMBLE_WEIGHTS["sms_spam"] * spam
            + ENSEMBLE_WEIGHTS["url_phishing"] * url
            + rules
        )
        return max(0.0, min(1.0, weighted))

    def _check_rules(self, text: str) -> float:
        """Get rules boost for text"""
        text_lower = text.lower()
        total_boost = 0.0
        for indicator_config in SCAM_INDICATORS.values():
            for pattern in indicator_config["patterns"]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    total_boost += indicator_config["score_boost"]
                    break
        return total_boost

    def test_bank_phishing_sample(self):
        """Test realistic bank phishing message"""
        text = (
            "ALERT: Your Bank of America account has been locked due to "
            "suspicious activity. Verify immediately at bit.ly/verify123"
        )
        rules_boost = self._check_rules(text)

        # Simulate high model scores
        final_score = self._calculate_ensemble(0.85, 0.75, 0.9, rules_boost)
        assert final_score > 0.7  # Should be high risk

    def test_prize_scam_sample(self):
        """Test prize/lottery scam message"""
        text = (
            "Congratulations! You've won $5000. "
            "Claim your prize now at www.prize-winner.tk"
        )
        rules_boost = self._check_rules(text)

        # Would have moderate model scores
        final_score = self._calculate_ensemble(0.6, 0.5, 0.7, rules_boost)
        assert final_score > 0.4  # Should be at least medium risk

    def test_safe_message_sample(self):
        """Test legitimate message"""
        text = "Your package from Amazon will arrive tomorrow between 2-4pm"
        rules_boost = self._check_rules(text)

        # Low model scores
        final_score = self._calculate_ensemble(0.1, 0.1, 0.0, rules_boost)
        assert final_score < 0.35  # Should be low risk
