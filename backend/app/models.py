"""
Database models for Guardian SMS
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import enum

from .database import Base


class AccessLevel(str, enum.Enum):
    """Guardian access levels"""
    VIEW_ALL = "VIEW_ALL"
    VIEW_SHARED_ONLY = "VIEW_SHARED_ONLY"


class RiskLevel(str, enum.Enum):
    """Message risk levels"""
    SAFE = "SAFE"
    MEDIUM_RISK = "MEDIUM_RISK"
    HIGH_RISK = "HIGH_RISK"


class User(Base):
    """Users table - base user accounts"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    protected_user = relationship("ProtectedUser", back_populates="user", uselist=False)


class ProtectedUser(Base):
    """Protected users table - elderly users being protected"""
    __tablename__ = "protected_users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="protected_user")
    guardians = relationship("Guardian", back_populates="protected_user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="protected_user", cascade="all, delete-orphan")


class Guardian(Base):
    """Guardians table - family members who monitor protected users"""
    __tablename__ = "guardians"
    
    id = Column(Integer, primary_key=True, index=True)
    protected_user_id = Column(Integer, ForeignKey("protected_users.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    name = Column(String(255), nullable=True)
    access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.VIEW_SHARED_ONLY, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    invitation_code = Column(String(64), unique=True, nullable=True, index=True)
    invitation_expires_at = Column(DateTime(timezone=True), nullable=True)
    invitation_accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    protected_user = relationship("ProtectedUser", back_populates="guardians")
    shared_messages = relationship("SharedMessage", back_populates="guardian", cascade="all, delete-orphan")


class Message(Base):
    """Messages table - analyzed SMS messages"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    protected_user_id = Column(Integer, ForeignKey("protected_users.id"), nullable=False, index=True)
    sender_phone = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    rule_matches = Column(Integer, default=0, nullable=False)
    ml_score = Column(String(10), nullable=True)  # Store as string to preserve precision
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    job_id = Column(String(255), nullable=True)  # For async processing
    
    # Relationships
    protected_user = relationship("ProtectedUser", back_populates="messages")
    shared_messages = relationship("SharedMessage", back_populates="message", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-calculate expires_at if not provided (7 days from analyzed_at)
        if self.expires_at is None and self.analyzed_at:
            self.expires_at = self.analyzed_at + timedelta(days=7)


class SharedMessage(Base):
    """Shared messages table - messages shared with guardians"""
    __tablename__ = "shared_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    guardian_id = Column(Integer, ForeignKey("guardians.id"), nullable=False, index=True)
    encrypted_content = Column(Text, nullable=False)  # AES-256 encrypted
    shared_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    message = relationship("Message", back_populates="shared_messages")
    guardian = relationship("Guardian", back_populates="shared_messages")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-calculate expires_at if not provided (48 hours from shared_at)
        if self.expires_at is None and self.shared_at:
            self.expires_at = self.shared_at + timedelta(hours=48)


class GuardianInvitation(Base):
    """Guardian invitations table - tracks invitation codes"""
    __tablename__ = "guardian_invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    protected_user_id = Column(Integer, ForeignKey("protected_users.id"), nullable=False, index=True)
    guardian_email = Column(String(255), nullable=False)
    invitation_code = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    protected_user = relationship("ProtectedUser")


# Create indexes as specified in acceptance criteria
Index("idx_messages_expires_at", Message.expires_at)
Index("idx_messages_analyzed_at", Message.analyzed_at)
Index("idx_messages_protected_user_id", Message.protected_user_id)
Index("idx_shared_messages_expires_at", SharedMessage.expires_at)
Index("idx_guardian_invitations_code", GuardianInvitation.invitation_code)

