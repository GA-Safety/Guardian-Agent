#!/usr/bin/env python3
"""
Simple standalone test for the Analysis Orchestrator (no database required)

This version uses mocked database sessions so you can test without a real database.
"""
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock

# Add the app directory to the path
sys.path.insert(0, '.')

from app.services.analysis_orchestrator import AnalysisOrchestrator


async def test_orchestrator_simple():
    """Test the orchestrator with mocked database"""
    
    print("🧪 Testing Analysis Orchestrator (No Database Required)\n")
    print("=" * 60)
    
    # Create a mock database session
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_session.execute.return_value = mock_result
    mock_session.commit = AsyncMock()
    
    # Create orchestrator
    orchestrator = AnalysisOrchestrator(db_session=mock_session)
    
    # Test messages
    test_cases = [
        {
            "name": "High Risk - Urgent Scam",
            "content": "URGENT: Your Social Security has been suspended. Click here to verify: bit.ly/xyz",
        },
        {
            "name": "High Risk - Financial Scam",
            "content": "Your account has been locked. Verify your identity immediately: tinyurl.com/verify",
        },
        {
            "name": "Medium Risk - Suspicious",
            "content": "Please update your payment information to avoid service interruption",
        },
        {
            "name": "Safe Message",
            "content": "Hi, just checking in. How are you doing today?",
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📱 Test Case {i}: {test_case['name']}")
        print(f"Message: {test_case['content']}")
        print("-" * 60)
        
        try:
            result = await orchestrator.analyze_message(
                message_id=100 + i,
                message_content=test_case['content'],
                sender_phone="+1234567890",
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
    asyncio.run(test_orchestrator_simple())

