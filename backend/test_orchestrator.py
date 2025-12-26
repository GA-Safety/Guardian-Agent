#!/usr/bin/env python3
"""
Simple test script for the Analysis Orchestrator

Run this to test the orchestrator with sample messages.
Make sure you have:
1. Activated the virtual environment: source .venv/bin/activate
2. Installed dependencies: pip install -r requirements.txt
3. Set up your .env file with database credentials
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession

# Add the app directory to the path
sys.path.insert(0, '.')

from app.database import AsyncSessionLocal
from app.services.analysis_orchestrator import AnalysisOrchestrator
from app.models import Message, ProtectedUser, User, RiskLevel
from sqlalchemy import select


async def test_orchestrator():
    """Test the orchestrator with sample messages"""
    
    print("🧪 Testing Analysis Orchestrator\n")
    print("=" * 60)
    
    # Test messages
    test_cases = [
        {
            "name": "High Risk - Urgent Scam",
            "content": "URGENT: Your Social Security has been suspended. Click here to verify: bit.ly/xyz",
            "sender": "+1234567890",
        },
        {
            "name": "High Risk - Financial Scam",
            "content": "Your account has been locked. Verify your identity immediately: tinyurl.com/verify",
            "sender": "+1987654321",
        },
        {
            "name": "Medium Risk - Suspicious",
            "content": "Please update your payment information to avoid service interruption",
            "sender": "+1555555555",
        },
        {
            "name": "Safe Message",
            "content": "Hi, just checking in. How are you doing today?",
            "sender": "+1111111111",
        },
    ]
    
    async with AsyncSessionLocal() as session:
        orchestrator = AnalysisOrchestrator(db_session=session)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📱 Test Case {i}: {test_case['name']}")
            print(f"Message: {test_case['content']}")
            print("-" * 60)
            
            try:
                # For testing, we'll create a mock message ID
                # In real usage, you'd have an actual message in the database
                message_id = 999 + i  # Use a test ID
                
                result = await orchestrator.analyze_message(
                    message_id=message_id,
                    message_content=test_case['content'],
                    sender_phone=test_case['sender'],
                )
                
                print(f"✅ Risk Level: {result.risk_level}")
                print(f"📊 ML Score: {result.ml_score:.3f}")
                print(f"🔍 Rule Matches: {len(result.rule_matches)}")
                if result.rule_matches:
                    print(f"   Matched Rules: {', '.join(result.rule_matches)}")
                print(f"⚠️  Warning Signs:")
                for sign in result.warning_signs:
                    print(f"   - {sign}")
                print(f"💡 Safe Next Steps:")
                for step in result.safe_next_steps:
                    print(f"   - {step}")
                
            except ValueError as e:
                print(f"❌ Validation Error: {e}")
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✨ Testing complete!")


if __name__ == "__main__":
    asyncio.run(test_orchestrator())

