"""
Unit tests for Analysis Orchestrator
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analysis_orchestrator import AnalysisOrchestrator
from app.services.mock_engines import MockRuleEngine, MockMLScorer
from app.models import Message, RiskLevel
from app.models.analysis import AnalysisResult, RuleMatch


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def mock_rule_engine():
    """Mock rule engine"""
    engine = AsyncMock(spec=MockRuleEngine)
    return engine


@pytest.fixture
def mock_ml_scorer():
    """Mock ML scorer"""
    scorer = AsyncMock(spec=MockMLScorer)
    return scorer


@pytest.fixture
def orchestrator(mock_db_session, mock_rule_engine, mock_ml_scorer):
    """Create orchestrator instance with mocked dependencies"""
    return AnalysisOrchestrator(
        db_session=mock_db_session,
        rule_engine=mock_rule_engine,
        ml_scorer=mock_ml_scorer,
    )


@pytest.fixture
def real_orchestrator(mock_db_session):
    """Create orchestrator with real mock engines"""
    return AnalysisOrchestrator(db_session=mock_db_session)


class TestHighRiskDetection:
    """Test high risk message detection"""
    
    @pytest.mark.asyncio
    async def test_high_risk_multiple_rule_matches(
        self, orchestrator, mock_rule_engine, mock_ml_scorer, mock_db_session
    ):
        """Test high risk detection with 3+ rule matches"""
        # Setup mocks
        mock_rule_engine.analyze.return_value = [
            {"rule_name": "urgency", "confidence": 0.8, "description": "Creates false urgency"},
            {"rule_name": "financial", "confidence": 0.7, "description": "Financial account manipulation"},
            {"rule_name": "suspicious_link", "confidence": 0.6, "description": "Contains suspicious link"},
        ]
        mock_ml_scorer.score.return_value = 0.4  # Low ML score
        
        # Mock database update
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        
        # Test
        result = await orchestrator.analyze_message(
            message_id=123,
            message_content="URGENT: Your account has been suspended. Click bit.ly/xyz to verify",
            sender_phone="+1234567890",
        )
        
        # Assertions
        assert result.risk_level == "HIGH_RISK"
        assert len(result.rule_matches) == 3
        assert result.ml_score == 0.4
        assert len(result.warning_signs) > 0
        assert len(result.safe_next_steps) > 0
        assert isinstance(result.analyzed_at, datetime)
        
        # Verify database was updated
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_high_risk_high_ml_score(
        self, orchestrator, mock_rule_engine, mock_ml_scorer, mock_db_session
    ):
        """Test high risk detection with high ML score"""
        # Setup mocks
        mock_rule_engine.analyze.return_value = []
        mock_ml_scorer.score.return_value = 0.85  # High ML score
        
        # Mock database update
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        
        # Test
        result = await orchestrator.analyze_message(
            message_id=124,
            message_content="You've won a prize! Click here to claim",
            sender_phone="+1234567890",
        )
        
        # Assertions
        assert result.risk_level == "HIGH_RISK"
        assert result.ml_score == 0.85
        assert len(result.warning_signs) > 0


class TestMediumRiskDetection:
    """Test medium risk message detection"""
    
    @pytest.mark.asyncio
    async def test_medium_risk_rule_matches(
        self, orchestrator, mock_rule_engine, mock_ml_scorer, mock_db_session
    ):
        """Test medium risk detection with 1-2 rule matches"""
        # Setup mocks
        mock_rule_engine.analyze.return_value = [
            {"rule_name": "urgency", "confidence": 0.7, "description": "Creates false urgency"},
        ]
        mock_ml_scorer.score.return_value = 0.3  # Low ML score
        
        # Mock database update
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        
        # Test
        result = await orchestrator.analyze_message(
            message_id=125,
            message_content="Urgent: Please verify your account",
            sender_phone="+1234567890",
        )
        
        # Assertions
        assert result.risk_level == "MEDIUM_RISK"
        assert len(result.rule_matches) == 1
    
    @pytest.mark.asyncio
    async def test_medium_risk_ml_score(
        self, orchestrator, mock_rule_engine, mock_ml_scorer, mock_db_session
    ):
        """Test medium risk detection with medium ML score"""
        # Setup mocks
        mock_rule_engine.analyze.return_value = []
        mock_ml_scorer.score.return_value = 0.65  # Medium ML score
        
        # Mock database update
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        
        # Test
        result = await orchestrator.analyze_message(
            message_id=126,
            message_content="Please update your payment information",
            sender_phone="+1234567890",
        )
        
        # Assertions
        assert result.risk_level == "MEDIUM_RISK"
        assert result.ml_score == 0.65


class TestSafeMessageClassification:
    """Test safe message classification"""
    
    @pytest.mark.asyncio
    async def test_safe_message(
        self, orchestrator, mock_rule_engine, mock_ml_scorer, mock_db_session
    ):
        """Test safe message classification"""
        # Setup mocks
        mock_rule_engine.analyze.return_value = []
        mock_ml_scorer.score.return_value = 0.2  # Low ML score
        
        # Mock database update
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        
        # Test
        result = await orchestrator.analyze_message(
            message_id=127,
            message_content="Hi, just checking in. How are you?",
            sender_phone="+1234567890",
        )
        
        # Assertions
        assert result.risk_level == "SAFE"
        assert result.ml_score == 0.2
        assert len(result.rule_matches) == 0


class TestDatabaseUpdate:
    """Test database update functionality"""
    
    @pytest.mark.asyncio
    async def test_database_update_success(
        self, orchestrator, mock_rule_engine, mock_ml_scorer, mock_db_session
    ):
        """Test successful database update"""
        # Setup mocks
        mock_rule_engine.analyze.return_value = [
            {"rule_name": "urgency", "confidence": 0.8, "description": "Creates false urgency"},
        ]
        mock_ml_scorer.score.return_value = 0.5
        
        # Mock database update
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        
        # Test
        await orchestrator.analyze_message(
            message_id=128,
            message_content="Urgent action required",
            sender_phone="+1234567890",
        )
        
        # Verify database calls
        assert mock_db_session.execute.call_count == 1
        assert mock_db_session.commit.call_count == 1
    
    @pytest.mark.asyncio
    async def test_database_update_failure_graceful(
        self, orchestrator, mock_rule_engine, mock_ml_scorer, mock_db_session
    ):
        """Test graceful handling of database update failure"""
        # Setup mocks
        mock_rule_engine.analyze.return_value = []
        mock_ml_scorer.score.return_value = 0.3
        
        # Mock database failure
        mock_db_session.execute.side_effect = Exception("Database connection failed")
        
        # Test - should not raise exception
        result = await orchestrator.analyze_message(
            message_id=129,
            message_content="Test message",
            sender_phone="+1234567890",
        )
        
        # Should still return result
        assert result is not None
        assert result.risk_level == "SAFE"


class TestErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_message_too_long(self, orchestrator):
        """Test handling of message exceeding character limit"""
        long_message = "x" * 1601
        
        with pytest.raises(ValueError, match="exceeds 1600 character limit"):
            await orchestrator.analyze_message(
                message_id=130,
                message_content=long_message,
                sender_phone="+1234567890",
            )
    
    @pytest.mark.asyncio
    async def test_rule_engine_failure_graceful(
        self, orchestrator, mock_rule_engine, mock_ml_scorer, mock_db_session
    ):
        """Test graceful degradation when rule engine fails"""
        # Setup mocks
        mock_rule_engine.analyze.side_effect = Exception("Rule engine error")
        mock_ml_scorer.score.return_value = 0.7
        
        # Mock database update
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        
        # Test - should continue with ML score only
        result = await orchestrator.analyze_message(
            message_id=131,
            message_content="Test message",
            sender_phone="+1234567890",
        )
        
        # Should still return result based on ML score
        assert result is not None
        assert result.ml_score == 0.7
    
    @pytest.mark.asyncio
    async def test_ml_scorer_failure_graceful(
        self, orchestrator, mock_rule_engine, mock_ml_scorer, mock_db_session
    ):
        """Test graceful degradation when ML scorer fails"""
        # Setup mocks
        mock_rule_engine.analyze.return_value = [
            {"rule_name": "urgency", "confidence": 0.8, "description": "Creates false urgency"},
            {"rule_name": "financial", "confidence": 0.7, "description": "Financial account manipulation"},
        ]
        mock_ml_scorer.score.side_effect = Exception("ML scorer error")
        
        # Mock database update
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        
        # Test - should continue with rule matches only
        result = await orchestrator.analyze_message(
            message_id=132,
            message_content="Urgent: Verify your account",
            sender_phone="+1234567890",
        )
        
        # Should still return result based on rule matches
        assert result is not None
        assert len(result.rule_matches) == 2


class TestRealMockEngines:
    """Test with real mock engine implementations"""
    
    @pytest.mark.asyncio
    async def test_real_mock_engines_high_risk(self, real_orchestrator, mock_db_session):
        """Test with real mock engines - high risk scenario"""
        # Mock database update
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        
        # Test with realistic scam message
        result = await real_orchestrator.analyze_message(
            message_id=133,
            message_content="URGENT: Your Social Security has been suspended. Click here to verify: bit.ly/xyz",
            sender_phone="+1234567890",
        )
        
        # Should detect high risk
        assert result.risk_level == "HIGH_RISK"
        assert len(result.rule_matches) > 0
        assert result.ml_score > 0.0
        assert len(result.warning_signs) > 0
        assert len(result.safe_next_steps) > 0

