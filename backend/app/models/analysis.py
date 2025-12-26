"""
Pydantic models for analysis results
"""
from datetime import datetime
from typing import List, Literal
from pydantic import BaseModel, Field


class RuleMatch(BaseModel):
    """Individual rule match result"""
    rule_name: str = Field(..., description="Name of the matched rule")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    description: str = Field(..., description="Human-readable description of the match")


class AnalysisResult(BaseModel):
    """Complete analysis result for an SMS message"""
    risk_level: Literal["HIGH_RISK", "MEDIUM_RISK", "SAFE"] = Field(
        ..., description="Final risk assessment"
    )
    ml_score: float = Field(..., ge=0.0, le=1.0, description="ML model score 0-1")
    rule_matches: List[str] = Field(
        ..., description="List of matched rule names"
    )
    warning_signs: List[str] = Field(
        ..., description="Human-readable warning signs identified"
    )
    safe_next_steps: List[str] = Field(
        ..., description="Recommended safe next steps for the user"
    )
    analyzed_at: datetime = Field(
        ..., description="Timestamp when analysis was performed"
    )

