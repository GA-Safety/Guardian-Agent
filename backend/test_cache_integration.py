"""
Integration test: Cache service with Analysis Orchestrator

Tests how the cache service integrates with the existing orchestrator.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.cache_service import CacheService
from app.services.analysis_orchestrator import AnalysisOrchestrator
from app.services.mock_engines import MockRuleEngine, MockMLScorer


async def test_orchestrator_with_cache():
    """
    Test how cache would be used in the orchestrator.
    
    This is a demonstration of how to integrate caching.
    """
    print("=" * 60)
    print("Cache Integration Test with Analysis Orchestrator")
    print("=" * 60)
    print()
    
    # Create cache service
    cache = CacheService()
    
    # Test message
    test_message = "URGENT: Your account is suspended. Click bit.ly/xyz to verify."
    
    print("📝 Test Message:")
    print(f"   '{test_message}'")
    print()
    
    # Step 1: Check cache first (simulating orchestrator behavior)
    print("Step 1: Check cache for existing analysis...")
    cached_result = await cache.get_cached_analysis(test_message)
    
    if cached_result:
        print("   ✅ Cache HIT - Using cached result")
        print(f"   Risk Level: {cached_result.get('risk_level')}")
        print(f"   ML Score: {cached_result.get('ml_score')}")
        print(f"   Warning Signs: {cached_result.get('warning_signs')}")
        print()
        print("   ⚡ Analysis complete in <1ms (from cache)")
        return cached_result
    else:
        print("   ❌ Cache MISS - Need to run analysis")
        print()
    
    # Step 2: Run analysis (simulating orchestrator)
    print("Step 2: Running analysis (this would use orchestrator)...")
    
    # Create mock orchestrator components
    rule_engine = MockRuleEngine()
    ml_scorer = MockMLScorer()
    
    # Run analysis
    rule_matches_raw = await rule_engine.analyze(test_message)
    ml_score = await ml_scorer.score(test_message)
    
    # Determine risk level (simplified)
    if ml_score >= 0.8 or len(rule_matches_raw) >= 3:
        risk_level = "HIGH_RISK"
    elif ml_score >= 0.5 or len(rule_matches_raw) >= 1:
        risk_level = "MEDIUM_RISK"
    else:
        risk_level = "SAFE"
    
    # Generate warning signs
    warning_signs = [match["description"] for match in rule_matches_raw]
    if ml_score >= 0.8:
        warning_signs.append("High scam probability detected by AI analysis")
    
    print(f"   Analysis Results:")
    print(f"   - ML Score: {ml_score:.3f}")
    print(f"   - Rule Matches: {len(rule_matches_raw)}")
    print(f"   - Risk Level: {risk_level}")
    print(f"   - Warning Signs: {warning_signs}")
    print()
    
    # Step 3: Cache the result
    print("Step 3: Caching analysis result...")
    cache_success = await cache.cache_analysis_result(
        message_content=test_message,
        ml_score=ml_score,
        rule_matches=rule_matches_raw,
        risk_level=risk_level,
        warning_signs=warning_signs,
        model_scores={"phishing_text": ml_score, "sms_spam": ml_score * 0.9},
    )
    
    if cache_success:
        print("   ✅ Result cached successfully")
    else:
        print("   ⚠️  Failed to cache (Redis may be unavailable)")
    print()
    
    # Step 4: Verify cache works for next request
    print("Step 4: Simulating second request (should hit cache)...")
    cached_result = await cache.get_cached_analysis(test_message)
    
    if cached_result:
        print("   ✅ Cache HIT on second request!")
        print(f"   Risk Level: {cached_result.get('risk_level')}")
        print(f"   ML Score: {cached_result.get('ml_score')}")
        print()
        print("   ⚡ Analysis complete in <1ms (from cache)")
        print("   💰 Saved: No ML inference needed!")
    else:
        print("   ❌ Cache miss (unexpected)")
    
    print()
    print("=" * 60)
    print("Integration test complete!")
    print()
    print("Next step: Integrate cache checks into AnalysisOrchestrator")
    print("  - Check cache at start of analyze_message()")
    print("  - Return cached result if found")
    print("  - Cache result after analysis completes")


if __name__ == "__main__":
    asyncio.run(test_orchestrator_with_cache())

