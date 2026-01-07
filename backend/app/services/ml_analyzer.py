"""
ML-Based SMS Scam Analyzer

Uses pretrained HuggingFace models to detect phishing/scam SMS messages.
Implements ensemble scoring with multiple models for high accuracy.
"""
import re
import logging
import time
from typing import List, Dict, Tuple, Optional
from transformers import pipeline, Pipeline
import torch

from ..config.ml_config import (
    MODELS,
    ENSEMBLE_WEIGHTS,
    RISK_LEVEL_THRESHOLDS,
    SCAM_INDICATORS,
    LABEL_MAPPINGS,
    MAX_MESSAGE_LENGTH,
)
from ..utils.url_extractor import extract_urls, is_shortened_url

logger = logging.getLogger(__name__)


class MLAnalyzer:
    """
    ML-based analyzer for SMS scam detection.

    Uses an ensemble of pretrained HuggingFace models:
    - BERT phishing detector
    - DistilBERT SMS spam detector
    - URL phishing classifier
    - Rules-based scam indicator detector
    """

    def __init__(self):
        """Initialize ML models (cached globally)."""
        self.models: Dict[str, Optional[Pipeline]] = {
            "phishing_text": None,
            "sms_spam": None,
            "url_phishing": None,
        }
        self._models_loaded = False
        self.device = 0 if torch.cuda.is_available() else -1
        logger.info(f"MLAnalyzer initialized with device: {'GPU' if self.device == 0 else 'CPU'}")

    def load_models(self) -> None:
        """
        Load all HuggingFace models into memory.

        Called once at startup to avoid per-request loading.
        Models are cached globally.
        """
        if self._models_loaded:
            logger.info("Models already loaded, skipping")
            return

        logger.info("Loading HuggingFace models...")
        start_time = time.time()

        try:
            # Load phishing text model
            logger.info(f"Loading phishing text model: {MODELS['phishing_text']}")
            self.models["phishing_text"] = pipeline(
                "text-classification",
                model=MODELS["phishing_text"],
                device=self.device,
                top_k=None,
            )

            # Load SMS spam model
            logger.info(f"Loading SMS spam model: {MODELS['sms_spam']}")
            self.models["sms_spam"] = pipeline(
                "text-classification",
                model=MODELS["sms_spam"],
                device=self.device,
                top_k=None,
            )

            # Load URL phishing model
            logger.info(f"Loading URL phishing model: {MODELS['url_phishing']}")
            self.models["url_phishing"] = pipeline(
                "text-classification",
                model=MODELS["url_phishing"],
                device=self.device,
                top_k=None,
            )

            self._models_loaded = True
            elapsed = time.time() - start_time
            logger.info(f"All models loaded successfully in {elapsed:.2f}s")

        except Exception as e:
            logger.error(f"Failed to load models: {e}", exc_info=True)
            raise

    def _extract_scam_score(
        self,
        predictions: List[Dict[str, any]],
        model_type: str
    ) -> float:
        """
        Extract scam probability from model predictions.

        Handles different label formats across models.

        Args:
            predictions: Model output (list of label/score dicts)
            model_type: Type of model (phishing_text, sms_spam, url_phishing)

        Returns:
            Probability of scam/phishing (0.0 to 1.0)
        """
        if not predictions:
            return 0.0

        label_mapping = LABEL_MAPPINGS.get(model_type, {})

        # Find the scam-related score
        scam_score = 0.0
        for pred in predictions:
            label = pred.get("label", "").lower()
            score = pred.get("score", 0.0)

            # Map label to internal representation
            mapped_label = label_mapping.get(label, label_mapping.get(label.upper(), label))

            if mapped_label == "SCAM" or "scam" in mapped_label.lower():
                scam_score = max(scam_score, score)
            elif "phishing" in label or "spam" in label or "malicious" in label:
                scam_score = max(scam_score, score)
            elif label in ["LABEL_1", "label_1"]:  # Common positive class
                scam_score = max(scam_score, score)

        return scam_score

    def _analyze_text_with_models(self, text: str) -> Tuple[float, float]:
        """
        Run text through both text classification models.

        Args:
            text: SMS message text

        Returns:
            Tuple of (phishing_score, spam_score)
        """
        phishing_score = 0.0
        spam_score = 0.0

        # Run phishing text model
        if self.models["phishing_text"]:
            try:
                start = time.time()
                predictions = self.models["phishing_text"](text[:512])  # Truncate for BERT
                phishing_score = self._extract_scam_score(predictions[0], "phishing_text")
                logger.debug(f"Phishing model score: {phishing_score:.3f} ({time.time()-start:.3f}s)")
            except Exception as e:
                logger.error(f"Phishing model failed: {e}")

        # Run SMS spam model
        if self.models["sms_spam"]:
            try:
                start = time.time()
                predictions = self.models["sms_spam"](text[:512])
                spam_score = self._extract_scam_score(predictions[0], "sms_spam")
                logger.debug(f"Spam model score: {spam_score:.3f} ({time.time()-start:.3f}s)")
            except Exception as e:
                logger.error(f"Spam model failed: {e}")

        return phishing_score, spam_score

    def _analyze_urls(self, urls: List[str]) -> float:
        """
        Analyze URLs for phishing using URL classifier model.

        Args:
            urls: List of URLs extracted from message

        Returns:
            Maximum phishing score across all URLs (0.0 if no URLs)
        """
        if not urls or not self.models["url_phishing"]:
            return 0.0

        max_url_score = 0.0

        for url in urls:
            try:
                start = time.time()
                # URL models typically work better with just the URL string
                predictions = self.models["url_phishing"](url)
                url_score = self._extract_scam_score(predictions[0], "url_phishing")
                max_url_score = max(max_url_score, url_score)
                logger.debug(f"URL '{url[:50]}...' score: {url_score:.3f} ({time.time()-start:.3f}s)")
            except Exception as e:
                logger.error(f"URL model failed for '{url}': {e}")

        return max_url_score

    def _analyze_rules(self, text: str) -> Tuple[float, List[str]]:
        """
        Analyze text for rule-based scam indicators.

        Args:
            text: SMS message text

        Returns:
            Tuple of (rules_score_boost, triggered_reasons)
        """
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
                    # Only count each indicator once
                    break

        return total_boost, triggered_reasons

    def _calculate_ensemble_score(
        self,
        phishing_score: float,
        spam_score: float,
        url_score: float,
        rules_boost: float,
    ) -> float:
        """
        Calculate final ensemble risk score.

        Formula: 0.55*phishing + 0.25*spam + 0.35*url + rules_boost
        Clamped to [0.0, 1.0]

        Args:
            phishing_score: Phishing text model score
            spam_score: SMS spam model score
            url_score: URL phishing model score
            rules_boost: Rules-based score boost

        Returns:
            Final risk score (0.0 to 1.0)
        """
        weighted_score = (
            ENSEMBLE_WEIGHTS["phishing_text"] * phishing_score
            + ENSEMBLE_WEIGHTS["sms_spam"] * spam_score
            + ENSEMBLE_WEIGHTS["url_phishing"] * url_score
            + rules_boost
        )

        # Clamp to valid range
        final_score = max(0.0, min(1.0, weighted_score))

        logger.debug(
            f"Ensemble: phishing={phishing_score:.3f}, spam={spam_score:.3f}, "
            f"url={url_score:.3f}, rules={rules_boost:.3f} -> final={final_score:.3f}"
        )

        return final_score

    def _determine_risk_level(self, risk_score: float) -> str:
        """
        Map risk score to risk level category.

        Args:
            risk_score: Final ensemble risk score

        Returns:
            Risk level: "low", "medium", or "high"
        """
        if risk_score > RISK_LEVEL_THRESHOLDS["medium"]:
            return "high"
        elif risk_score > RISK_LEVEL_THRESHOLDS["low"]:
            return "medium"
        else:
            return "low"

    def _generate_reasons(
        self,
        urls: List[str],
        url_score: float,
        rules_reasons: List[str],
        phishing_score: float,
    ) -> List[str]:
        """
        Generate human-friendly reasons for the risk assessment.

        Args:
            urls: List of URLs found in message
            url_score: URL phishing score
            rules_reasons: Reasons from rules-based analysis
            phishing_score: Phishing text model score

        Returns:
            List of human-readable reason strings
        """
        reasons = []

        # URL-related reasons
        if urls:
            reasons.append("Contains a link")
            if url_score > 0.6:
                reasons.append("Link looks suspicious")
            if any(is_shortened_url(url) for url in urls):
                reasons.append("Uses shortened URL (hard to verify)")

        # Add top 3 rules-based reasons
        reasons.extend(rules_reasons[:3])

        # ML-based reason
        if phishing_score > 0.7:
            reasons.append("Message resembles phishing/scam language")
        elif phishing_score > 0.5:
            reasons.append("Message contains suspicious patterns")

        # Deduplicate while preserving order
        seen = set()
        unique_reasons = []
        for reason in reasons:
            if reason not in seen:
                seen.add(reason)
                unique_reasons.append(reason)

        return unique_reasons

    async def analyze_sms(
        self,
        message_id: str,
        text: str,
        sender: Optional[str] = None,
        received_ts: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Analyze an SMS message for scam indicators.

        Main entry point for SMS analysis.

        Args:
            message_id: Unique identifier for the message
            text: SMS message text
            sender: Phone number of sender (optional)
            received_ts: Timestamp when message was received (optional)

        Returns:
            Analysis result dictionary with risk score, level, reasons, etc.

        Raises:
            ValueError: If text is empty or exceeds max length
        """
        # Validate input
        if not text or not text.strip():
            raise ValueError("Message text cannot be empty")

        if len(text) > MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters"
            )

        logger.info(f"Analyzing message_id={message_id}, length={len(text)}")
        overall_start = time.time()

        # Ensure models are loaded
        if not self._models_loaded:
            self.load_models()

        # Extract URLs
        urls = extract_urls(text)
        logger.debug(f"Extracted {len(urls)} URLs: {urls}")

        # Run text models
        phishing_score, spam_score = self._analyze_text_with_models(text)

        # Run URL analysis
        url_score = self._analyze_urls(urls)

        # Run rules-based analysis
        rules_boost, rules_reasons = self._analyze_rules(text)

        # Calculate final ensemble score
        risk_score = self._calculate_ensemble_score(
            phishing_score, spam_score, url_score, rules_boost
        )

        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)

        # Generate human-friendly reasons
        reasons = self._generate_reasons(urls, url_score, rules_reasons, phishing_score)

        # Calculate total inference time
        total_time = time.time() - overall_start

        logger.info(
            f"Analysis complete for message_id={message_id}: "
            f"risk_score={risk_score:.3f}, risk_level={risk_level}, "
            f"time={total_time:.3f}s"
        )

        return {
            "message_id": message_id,
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "reasons": reasons,
            "model_scores": {
                "phishing_text": round(phishing_score, 3),
                "sms_spam": round(spam_score, 3),
                "url_phishing": round(url_score, 3),
                "rules": round(rules_boost, 3),
            },
            "urls": urls,
            "version": "1.0.0",
            "inference_time_seconds": round(total_time, 3),
        }


# Global instance (singleton pattern)
_ml_analyzer_instance: Optional[MLAnalyzer] = None


def get_ml_analyzer() -> MLAnalyzer:
    """
    Get or create the global ML analyzer instance.

    Returns:
        MLAnalyzer instance (singleton)
    """
    global _ml_analyzer_instance
    if _ml_analyzer_instance is None:
        _ml_analyzer_instance = MLAnalyzer()
    return _ml_analyzer_instance
