"""
Analysis Orchestrator Service

Combines rule-based detection and ML scoring to analyze SMS messages for scam indicators.
"""
import logging
import time
import functools
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from ..models import Message, RiskLevel
from ..models.analysis import AnalysisResult, RuleMatch
from ..config.risk_config import RISK_THRESHOLDS, SAFE_NEXT_STEPS
from .mock_engines import MockRuleEngine, MockMLScorer

logger = logging.getLogger(__name__)


def measure_performance(func):
    """Decorator to measure and log function execution time"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{func.__name__} completed in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
            raise
    return wrapper


class AnalysisOrchestrator:
    """
    Orchestrates analysis of SMS messages using rule engine and ML scorer.
    
    Combines results from both engines to determine final risk level.
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        rule_engine: Optional[MockRuleEngine] = None,
        ml_scorer: Optional[MockMLScorer] = None,
    ):
        """
        Initialize the orchestrator.
        
        Args:
            db_session: Database session for updating message records
            rule_engine: Rule engine instance (defaults to MockRuleEngine)
            ml_scorer: ML scorer instance (defaults to MockMLScorer)
        """
        self.db_session = db_session
        self.rule_engine = rule_engine or MockRuleEngine()
        self.ml_scorer = ml_scorer or MockMLScorer()
    
    def _determine_risk_level(
        self, ml_score: float, rule_match_count: int
    ) -> RiskLevel:
        """
        Determine risk level based on ML score and rule match count.
        
        Rules:
        - HIGH_RISK: ML score > ml_high threshold OR 3+ rule matches
        - MEDIUM_RISK: ML score 0.5-0.8 OR 1-2 rule matches
        - SAFE: otherwise
        
        Args:
            ml_score: ML model score (0.0-1.0)
            rule_match_count: Number of rule matches
            
        Returns:
            RiskLevel enum value
        """
        ml_high = RISK_THRESHOLDS["ml_high"]
        ml_medium = RISK_THRESHOLDS["ml_medium"]
        rule_high = RISK_THRESHOLDS["rule_high"]
        rule_medium = RISK_THRESHOLDS["rule_medium"]
        
        # High risk conditions
        if ml_score >= ml_high or rule_match_count >= rule_high:
            return RiskLevel.HIGH_RISK
        
        # Medium risk conditions
        if ml_score >= ml_medium or rule_match_count >= rule_medium:
            return RiskLevel.MEDIUM_RISK
        
        # Safe otherwise
        return RiskLevel.SAFE
    
    def _generate_warning_signs(
        self, rule_matches: List[RuleMatch], ml_score: float
    ) -> List[str]:
        """
        Generate human-readable warning signs from analysis results.
        
        Args:
            rule_matches: List of matched rules
            ml_score: ML model score
            
        Returns:
            List of warning sign descriptions
        """
        warning_signs = []
        
        # Add rule-based warnings
        for match in rule_matches:
            warning_signs.append(match.description)
        
        # Add ML-based warning if score is high
        if ml_score >= RISK_THRESHOLDS["ml_high"]:
            warning_signs.append("High scam probability detected by AI analysis")
        elif ml_score >= RISK_THRESHOLDS["ml_medium"]:
            warning_signs.append("Moderate scam indicators detected")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_warnings = []
        for warning in warning_signs:
            if warning not in seen:
                seen.add(warning)
                unique_warnings.append(warning)
        
        return unique_warnings
    
    @measure_performance
    async def analyze_message(
        self,
        message_id: int,
        message_content: str,
        sender_phone: str,
    ) -> AnalysisResult:
        """
        Analyze an SMS message for scam indicators.
        
        Args:
            message_id: Database ID of the message to analyze
            message_content: The SMS message text (up to 1600 characters)
            sender_phone: Phone number of the message sender
            
        Returns:
            AnalysisResult with risk level, scores, and recommendations
            
        Raises:
            ValueError: If message content exceeds 1600 characters
            Exception: If database update fails (logged but not re-raised)
        """
        # Validate message length
        if len(message_content) > 1600:
            raise ValueError(
                f"Message content exceeds 1600 character limit: {len(message_content)}"
            )
        
        logger.info(f"Starting analysis for message_id={message_id}")
        
        # Run rule engine and ML scorer in parallel (graceful degradation)
        rule_matches = []
        ml_score = 0.0
        
        try:
            rule_matches_raw = await self.rule_engine.analyze(message_content)
            rule_matches = [RuleMatch(**match) for match in rule_matches_raw]
            logger.info(f"Rule engine found {len(rule_matches)} matches for message_id={message_id}")
        except Exception as e:
            logger.error(f"Rule engine failed for message_id={message_id}: {e}")
            # Continue with ML score only
        
        try:
            ml_score = await self.ml_scorer.score(message_content)
            logger.info(f"ML scorer returned score {ml_score:.3f} for message_id={message_id}")
        except Exception as e:
            logger.error(f"ML scorer failed for message_id={message_id}: {e}")
            # Continue with rule matches only
        
        # Determine risk level
        rule_match_count = len(rule_matches)
        risk_level = self._determine_risk_level(ml_score, rule_match_count)
        
        # Generate warning signs
        warning_signs = self._generate_warning_signs(rule_matches, ml_score)
        
        # Get safe next steps
        safe_next_steps = SAFE_NEXT_STEPS.get(risk_level.value, SAFE_NEXT_STEPS["SAFE"])
        
        # Create analysis result
        from datetime import timezone
        analyzed_at = datetime.now(timezone.utc)
        result = AnalysisResult(
            risk_level=risk_level.value,
            ml_score=ml_score,
            rule_matches=[match.rule_name for match in rule_matches],
            warning_signs=warning_signs,
            safe_next_steps=safe_next_steps,
            analyzed_at=analyzed_at,
        )
        
        # Update database
        try:
            await self._update_message_in_db(
                message_id=message_id,
                risk_level=risk_level,
                ml_score=ml_score,
                rule_match_count=rule_match_count,
                rule_matches=rule_matches,
                warning_signs=warning_signs,
                safe_next_steps=safe_next_steps,
                analyzed_at=analyzed_at,
            )
            logger.info(f"Successfully updated message_id={message_id} with analysis results")
        except Exception as e:
            logger.error(f"Failed to update database for message_id={message_id}: {e}", exc_info=True)
            # Don't re-raise - return result even if DB update fails
        
        return result
    
    async def _update_message_in_db(
        self,
        message_id: int,
        risk_level: RiskLevel,
        ml_score: float,
        rule_match_count: int,
        rule_matches: List[RuleMatch],
        warning_signs: List[str],
        safe_next_steps: List[str],
        analyzed_at: datetime,
    ) -> None:
        """
        Update message record in database with analysis results.
        
        Args:
            message_id: Database ID of the message
            risk_level: Determined risk level
            ml_score: ML model score
            rule_match_count: Number of rule matches
            rule_matches: List of rule match objects
            warning_signs: List of warning sign descriptions
            safe_next_steps: List of safe next step recommendations
            analyzed_at: Analysis timestamp
        """
        # Prepare update data
        # Note: Currently rule_matches is Integer in schema, storing count
        # TODO: When schema is updated to JSONB, store full match details
        update_data = {
            "risk_level": risk_level,
            "ml_score": str(round(ml_score, 3)),  # Store as string per schema
            "rule_matches": rule_match_count,  # Store count
            "analyzed_at": analyzed_at,
        }
        
        # Execute update
        stmt = (
            update(Message)
            .where(Message.id == message_id)
            .values(**update_data)
        )
        
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        
        if result.rowcount == 0:
            logger.warning(f"No message found with id={message_id} to update")
        else:
            logger.debug(
                f"Updated message_id={message_id}: risk_level={risk_level.value}, "
                f"ml_score={ml_score:.3f}, rule_matches={rule_match_count}"
            )

