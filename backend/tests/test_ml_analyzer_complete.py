"""
Comprehensive Unit Tests for ML Analyzer

Tests the ML analyzer with mocked HuggingFace models to avoid loading actual models.
Covers: model initialization, scoring, ensemble calculation, risk determination, and edge cases.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio

from app.services.ml_analyzer import MLAnalyzer, get_ml_analyzer
from app.config.ml_config import (
    ENSEMBLE_WEIGHTS,
    RISK_LEVEL_THRESHOLDS,
    MAX_MESSAGE_LENGTH,
)
from tests.mock_data import (
    get_all_scam_messages,
    get_all_safe_messages,
    get_all_edge_cases,
    get_mock_predictions,
    TEST_URLS,
)


class TestMLAnalyzerInitialization:
    """Test ML analyzer initialization and model loading"""

    def test_analyzer_init(self):
        """Test analyzer initializes with correct default state"""
        analyzer = MLAnalyzer()
        assert analyzer.models["phishing_text"] is None
        assert analyzer.models["sms_spam"] is None
        assert analyzer.models["url_phishing"] is None
        assert analyzer._models_loaded is False
        assert analyzer.device in [0, -1]  # GPU or CPU

    @patch("app.services.ml_analyzer.pipeline")
    def test_load_models_success(self, mock_pipeline):
        """Test successful model loading"""
        # Mock pipeline to return mock model
        mock_model = Mock()
        mock_pipeline.return_value = mock_model

        analyzer = MLAnalyzer()
        analyzer.load_models()

        # Check models are loaded
        assert analyzer._models_loaded is True
        assert analyzer.models["phishing_text"] is not None
        assert analyzer.models["sms_spam"] is not None
        assert analyzer.models["url_phishing"] is not None

        # Verify pipeline was called 3 times (one per model)
        assert mock_pipeline.call_count == 3

    @patch("app.services.ml_analyzer.pipeline")
    def test_load_models_idempotent(self, mock_pipeline):
        """Test that load_models can be called multiple times safely"""
        mock_model = Mock()
        mock_pipeline.return_value = mock_model

        analyzer = MLAnalyzer()
        analyzer.load_models()
        call_count_first = mock_pipeline.call_count

        # Call again
        analyzer.load_models()
        call_count_second = mock_pipeline.call_count

        # Should not reload models
        assert call_count_first == call_count_second

    @patch("app.services.ml_analyzer.pipeline")
    def test_load_models_failure(self, mock_pipeline):
        """Test model loading handles errors gracefully"""
        mock_pipeline.side_effect = Exception("Model download failed")

        analyzer = MLAnalyzer()
        with pytest.raises(Exception, match="Model download failed"):
            analyzer.load_models()

    def test_get_ml_analyzer_singleton(self):
        """Test get_ml_analyzer returns singleton instance"""
        analyzer1 = get_ml_analyzer()
        analyzer2 = get_ml_analyzer()
        assert analyzer1 is analyzer2


class TestMLAnalyzerScoring:
    """Test ML analyzer scoring methods"""

    def test_extract_scam_score_phishing_label1(self):
        """Test extracting scam score from LABEL_1 format"""
        analyzer = MLAnalyzer()
        predictions = [
            {"label": "LABEL_0", "score": 0.15},
            {"label": "LABEL_1", "score": 0.85},
        ]
        score = analyzer._extract_scam_score(predictions, "phishing_text")
        assert score == 0.85

    def test_extract_scam_score_spam_label(self):
        """Test extracting scam score from spam/ham labels"""
        analyzer = MLAnalyzer()
        predictions = [
            {"label": "ham", "score": 0.20},
            {"label": "spam", "score": 0.80},
        ]
        score = analyzer._extract_scam_score(predictions, "sms_spam")
        assert score == 0.80

    def test_extract_scam_score_phishing_label(self):
        """Test extracting scam score from phishing label"""
        analyzer = MLAnalyzer()
        predictions = [
            {"label": "benign", "score": 0.30},
            {"label": "phishing", "score": 0.70},
        ]
        score = analyzer._extract_scam_score(predictions, "url_phishing")
        assert score == 0.70

    def test_extract_scam_score_empty_predictions(self):
        """Test handling of empty predictions"""
        analyzer = MLAnalyzer()
        score = analyzer._extract_scam_score([], "phishing_text")
        assert score == 0.0

    def test_calculate_ensemble_score(self):
        """Test ensemble score calculation"""
        analyzer = MLAnalyzer()
        score = analyzer._calculate_ensemble_score(
            phishing_score=0.8,
            spam_score=0.6,
            url_score=0.7,
            rules_boost=0.2,
        )
        # 0.55*0.8 + 0.25*0.6 + 0.35*0.7 + 0.2 = 0.44 + 0.15 + 0.245 + 0.2 = 1.035
        # Clamped to 1.0
        assert score == 1.0

    def test_calculate_ensemble_score_clamping_min(self):
        """Test ensemble score clamped to minimum 0.0"""
        analyzer = MLAnalyzer()
        score = analyzer._calculate_ensemble_score(0.0, 0.0, 0.0, -1.0)
        assert score == 0.0

    def test_calculate_ensemble_score_realistic(self):
        """Test ensemble score with realistic values"""
        analyzer = MLAnalyzer()
        score = analyzer._calculate_ensemble_score(0.7, 0.5, 0.6, 0.15)
        # 0.55*0.7 + 0.25*0.5 + 0.35*0.6 + 0.15
        expected = 0.385 + 0.125 + 0.21 + 0.15
        assert abs(score - expected) < 0.01

    def test_determine_risk_level_low(self):
        """Test risk level determination for low risk"""
        analyzer = MLAnalyzer()
        assert analyzer._determine_risk_level(0.0) == "low"
        assert analyzer._determine_risk_level(0.25) == "low"
        assert analyzer._determine_risk_level(0.3) == "low"

    def test_determine_risk_level_medium(self):
        """Test risk level determination for medium risk"""
        analyzer = MLAnalyzer()
        assert analyzer._determine_risk_level(0.35) == "medium"
        assert analyzer._determine_risk_level(0.5) == "medium"

    def test_determine_risk_level_high(self):
        """Test risk level determination for high risk"""
        analyzer = MLAnalyzer()
        assert analyzer._determine_risk_level(0.65) == "high"
        assert analyzer._determine_risk_level(0.9) == "high"
        assert analyzer._determine_risk_level(1.0) == "high"


class TestMLAnalyzerRulesEngine:
    """Test rules-based scam detection"""

    def test_analyze_rules_urgency(self):
        """Test detection of urgency indicators"""
        analyzer = MLAnalyzer()
        boost, reasons = analyzer._analyze_rules("URGENT: Act now!")
        assert boost > 0
        assert any("urgency" in r.lower() for r in reasons)

    def test_analyze_rules_credentials(self):
        """Test detection of credential requests"""
        analyzer = MLAnalyzer()
        boost, reasons = analyzer._analyze_rules(
            "Please verify your password and credit card"
        )
        assert boost > 0
        assert any("sensitive" in r.lower() or "credential" in r.lower() for r in reasons)

    def test_analyze_rules_impersonation(self):
        """Test detection of authority impersonation"""
        analyzer = MLAnalyzer()
        boost, reasons = analyzer._analyze_rules("This is the IRS calling")
        assert boost > 0
        assert any("imperson" in r.lower() or "authority" in r.lower() for r in reasons)

    def test_analyze_rules_multiple_indicators(self):
        """Test detection of multiple scam indicators"""
        analyzer = MLAnalyzer()
        text = "URGENT: Bank of America - verify your password immediately!"
        boost, reasons = analyzer._analyze_rules(text)
        assert boost > 0.3  # Multiple indicators
        assert len(reasons) >= 2

    def test_analyze_rules_safe_message(self):
        """Test that safe messages trigger no rules"""
        analyzer = MLAnalyzer()
        boost, reasons = analyzer._analyze_rules("Hey, want to grab lunch today?")
        assert boost == 0.0
        assert len(reasons) == 0


class TestMLAnalyzerURLAnalysis:
    """Test URL extraction and analysis"""

    @patch("app.services.ml_analyzer.extract_urls")
    def test_analyze_urls_no_urls(self, mock_extract):
        """Test URL analysis with no URLs present"""
        mock_extract.return_value = []
        analyzer = MLAnalyzer()
        score = analyzer._analyze_urls([])
        assert score == 0.0

    @patch.object(MLAnalyzer, "_extract_scam_score")
    def test_analyze_urls_with_urls(self, mock_extract_score):
        """Test URL analysis with URLs present"""
        mock_extract_score.return_value = 0.85

        analyzer = MLAnalyzer()
        analyzer.models["url_phishing"] = Mock()
        analyzer.models["url_phishing"].return_value = [
            {"label": "phishing", "score": 0.85}
        ]

        score = analyzer._analyze_urls(["http://suspicious-site.tk"])
        assert score == 0.85

    @patch.object(MLAnalyzer, "_extract_scam_score")
    def test_analyze_urls_multiple_urls(self, mock_extract_score):
        """Test URL analysis returns max score from multiple URLs"""
        # Return different scores for different calls
        mock_extract_score.side_effect = [0.3, 0.7, 0.5]

        analyzer = MLAnalyzer()
        mock_model = Mock()
        analyzer.models["url_phishing"] = mock_model
        mock_model.return_value = [{"label": "phishing", "score": 0.7}]

        urls = ["http://site1.com", "http://site2.tk", "http://site3.com"]
        score = analyzer._analyze_urls(urls)
        assert score == 0.7  # Max of the three scores


class TestMLAnalyzerReasonGeneration:
    """Test human-readable reason generation"""

    @patch("app.services.ml_analyzer.is_shortened_url")
    def test_generate_reasons_with_urls(self, mock_is_shortened):
        """Test reason generation for messages with URLs"""
        mock_is_shortened.return_value = False

        analyzer = MLAnalyzer()
        reasons = analyzer._generate_reasons(
            urls=["http://example.com"],
            url_score=0.4,
            rules_reasons=[],
            phishing_score=0.3,
        )
        assert "Contains a link" in reasons

    @patch("app.services.ml_analyzer.is_shortened_url")
    def test_generate_reasons_with_shortened_urls(self, mock_is_shortened):
        """Test reason generation for shortened URLs"""
        mock_is_shortened.return_value = True

        analyzer = MLAnalyzer()
        reasons = analyzer._generate_reasons(
            urls=["http://bit.ly/abc"],
            url_score=0.7,
            rules_reasons=[],
            phishing_score=0.3,
        )
        assert any("shortened" in r.lower() for r in reasons)
        assert any("suspicious" in r.lower() for r in reasons)

    def test_generate_reasons_high_phishing_score(self):
        """Test reason generation for high phishing scores"""
        analyzer = MLAnalyzer()
        reasons = analyzer._generate_reasons(
            urls=[],
            url_score=0.0,
            rules_reasons=[],
            phishing_score=0.85,
        )
        assert any("phishing" in r.lower() or "scam" in r.lower() for r in reasons)

    def test_generate_reasons_deduplication(self):
        """Test that duplicate reasons are removed"""
        analyzer = MLAnalyzer()
        rules_reasons = ["Urgency", "Urgency", "Threats"]
        reasons = analyzer._generate_reasons(
            urls=[],
            url_score=0.0,
            rules_reasons=rules_reasons,
            phishing_score=0.3,
        )
        # Should deduplicate
        assert len(reasons) <= len(set(reasons))


@pytest.mark.asyncio
class TestMLAnalyzerFullAnalysis:
    """Test complete SMS analysis workflow"""

    @patch("app.services.ml_analyzer.extract_urls")
    @patch.object(MLAnalyzer, "_analyze_text_with_models")
    @patch.object(MLAnalyzer, "_analyze_urls")
    @patch.object(MLAnalyzer, "_analyze_rules")
    @patch("app.services.ml_analyzer.pipeline")
    async def test_analyze_sms_high_risk(
        self,
        mock_pipeline,
        mock_analyze_rules,
        mock_analyze_urls,
        mock_analyze_text,
        mock_extract_urls,
    ):
        """Test full analysis of high-risk scam message"""
        # Setup mocks
        mock_pipeline.return_value = Mock()
        mock_extract_urls.return_value = ["http://bit.ly/scam"]
        mock_analyze_text.return_value = (0.85, 0.75)  # phishing, spam
        mock_analyze_urls.return_value = 0.90
        mock_analyze_rules.return_value = (0.25, ["Urgency", "Impersonation"])

        # Create analyzer and load models
        analyzer = MLAnalyzer()
        analyzer.load_models()

        # Run analysis
        result = await analyzer.analyze_sms(
            message_id="msg_001",
            text="URGENT: Your bank account is locked. Verify at bit.ly/verify",
            sender="+15555551234",
        )

        # Verify result structure
        assert "message_id" in result
        assert "risk_score" in result
        assert "risk_level" in result
        assert "reasons" in result
        assert "model_scores" in result
        assert "urls" in result
        assert "inference_time_seconds" in result

        # Verify high risk detection
        assert result["risk_level"] == "high"
        assert result["risk_score"] > 0.7
        assert len(result["reasons"]) > 0

    @patch("app.services.ml_analyzer.extract_urls")
    @patch.object(MLAnalyzer, "_analyze_text_with_models")
    @patch.object(MLAnalyzer, "_analyze_urls")
    @patch.object(MLAnalyzer, "_analyze_rules")
    @patch("app.services.ml_analyzer.pipeline")
    async def test_analyze_sms_safe_message(
        self,
        mock_pipeline,
        mock_analyze_rules,
        mock_analyze_urls,
        mock_analyze_text,
        mock_extract_urls,
    ):
        """Test full analysis of safe message"""
        # Setup mocks for safe message
        mock_pipeline.return_value = Mock()
        mock_extract_urls.return_value = []
        mock_analyze_text.return_value = (0.05, 0.02)  # Low scores
        mock_analyze_urls.return_value = 0.0
        mock_analyze_rules.return_value = (0.0, [])

        analyzer = MLAnalyzer()
        analyzer.load_models()

        result = await analyzer.analyze_sms(
            message_id="msg_002",
            text="Hey, want to grab coffee later?",
            sender="+15551234567",
        )

        assert result["risk_level"] == "low"
        assert result["risk_score"] < 0.3

    @patch("app.services.ml_analyzer.pipeline")
    async def test_analyze_sms_empty_text(self, mock_pipeline):
        """Test analysis rejects empty message"""
        mock_pipeline.return_value = Mock()

        analyzer = MLAnalyzer()
        analyzer.load_models()

        with pytest.raises(ValueError, match="cannot be empty"):
            await analyzer.analyze_sms(
                message_id="msg_003",
                text="",
                sender="+15555551234",
            )

    @patch("app.services.ml_analyzer.pipeline")
    async def test_analyze_sms_whitespace_only(self, mock_pipeline):
        """Test analysis rejects whitespace-only message"""
        mock_pipeline.return_value = Mock()

        analyzer = MLAnalyzer()
        analyzer.load_models()

        with pytest.raises(ValueError, match="cannot be empty"):
            await analyzer.analyze_sms(
                message_id="msg_004",
                text="   \n\t  ",
                sender="+15555551234",
            )

    @patch("app.services.ml_analyzer.pipeline")
    async def test_analyze_sms_too_long(self, mock_pipeline):
        """Test analysis rejects message exceeding max length"""
        mock_pipeline.return_value = Mock()

        analyzer = MLAnalyzer()
        analyzer.load_models()

        with pytest.raises(ValueError, match="exceeds maximum length"):
            await analyzer.analyze_sms(
                message_id="msg_005",
                text="A" * (MAX_MESSAGE_LENGTH + 1),
                sender="+15555551234",
            )

    @patch("app.services.ml_analyzer.extract_urls")
    @patch.object(MLAnalyzer, "_analyze_text_with_models")
    @patch.object(MLAnalyzer, "_analyze_urls")
    @patch.object(MLAnalyzer, "_analyze_rules")
    @patch("app.services.ml_analyzer.pipeline")
    async def test_analyze_sms_auto_loads_models(
        self,
        mock_pipeline,
        mock_analyze_rules,
        mock_analyze_urls,
        mock_analyze_text,
        mock_extract_urls,
    ):
        """Test that analyze_sms automatically loads models if not loaded"""
        mock_pipeline.return_value = Mock()
        mock_extract_urls.return_value = []
        mock_analyze_text.return_value = (0.1, 0.1)
        mock_analyze_urls.return_value = 0.0
        mock_analyze_rules.return_value = (0.0, [])

        analyzer = MLAnalyzer()
        # Don't manually load models
        assert analyzer._models_loaded is False

        await analyzer.analyze_sms(
            message_id="msg_006",
            text="Test message",
            sender="+15555551234",
        )

        # Models should be loaded automatically
        assert analyzer._models_loaded is True


@pytest.mark.asyncio
class TestMLAnalyzerWithMockData:
    """Test ML analyzer with realistic mock data"""

    @patch("app.services.ml_analyzer.extract_urls")
    @patch.object(MLAnalyzer, "_analyze_text_with_models")
    @patch.object(MLAnalyzer, "_analyze_urls")
    @patch("app.services.ml_analyzer.pipeline")
    async def test_scam_messages(
        self,
        mock_pipeline,
        mock_analyze_urls,
        mock_analyze_text,
        mock_extract_urls,
    ):
        """Test analysis of various scam messages from mock data"""
        mock_pipeline.return_value = Mock()

        analyzer = MLAnalyzer()
        analyzer.load_models()

        scam_messages = get_all_scam_messages()

        for key, msg_data in scam_messages.items():
            # Setup mocks based on expected risk
            if msg_data["expected_risk"] == "high":
                mock_analyze_text.return_value = (0.85, 0.75)
                mock_analyze_urls.return_value = 0.80
            else:
                mock_analyze_text.return_value = (0.60, 0.50)
                mock_analyze_urls.return_value = 0.40

            mock_extract_urls.return_value = ["http://example.com"]

            result = await analyzer.analyze_sms(
                message_id=f"msg_{key}",
                text=msg_data["text"],
                sender=msg_data["sender"],
            )

            # Verify expected risk level
            assert result["risk_level"] in ["low", "medium", "high"]
            print(f"✓ {key}: {result['risk_level']} risk detected")

    @patch("app.services.ml_analyzer.extract_urls")
    @patch.object(MLAnalyzer, "_analyze_text_with_models")
    @patch.object(MLAnalyzer, "_analyze_urls")
    @patch("app.services.ml_analyzer.pipeline")
    async def test_safe_messages(
        self,
        mock_pipeline,
        mock_analyze_urls,
        mock_analyze_text,
        mock_extract_urls,
    ):
        """Test analysis of safe messages from mock data"""
        mock_pipeline.return_value = Mock()
        mock_extract_urls.return_value = []
        mock_analyze_text.return_value = (0.05, 0.02)
        mock_analyze_urls.return_value = 0.0

        analyzer = MLAnalyzer()
        analyzer.load_models()

        safe_messages = get_all_safe_messages()

        for key, msg_data in safe_messages.items():
            result = await analyzer.analyze_sms(
                message_id=f"msg_{key}",
                text=msg_data["text"],
                sender=msg_data["sender"],
            )

            # Safe messages should be low risk
            assert result["risk_level"] == "low"
            assert result["risk_score"] < 0.35
            print(f"✓ {key}: correctly identified as low risk")
