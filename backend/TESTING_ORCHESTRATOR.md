# Testing the Analysis Orchestrator

There are several ways to test the Analysis Orchestrator service:

## 1. Run Unit Tests (Recommended)

Run the full test suite with pytest:

```bash
cd backend
source ../.venv/bin/activate  # or: source .venv/bin/activate if venv is in backend
pytest tests/test_analysis_orchestrator.py -v
```

Run a specific test:
```bash
pytest tests/test_analysis_orchestrator.py::TestHighRiskDetection::test_high_risk_multiple_rule_matches -v
```

## 2. Simple Standalone Test (No Database)

Quick test without needing a database connection:

```bash
cd backend
source ../.venv/bin/activate
python test_orchestrator_simple.py
```

This uses mocked database sessions, so it works immediately.

## 3. Test with Real Database

If you have a database set up, you can test with real database updates:

```bash
cd backend
source ../.venv/bin/activate
python test_orchestrator.py
```

**Note:** This requires:
- Database connection configured in `.env`
- A message record in the database (or it will log a warning)

## 4. Test via API Endpoint

Add a test endpoint to `app/main.py`:

```python
from app.database import get_db
from app.services.analysis_orchestrator import AnalysisOrchestrator

@app.post("/test/analyze")
async def test_analyze(
    message_content: str,
    sender_phone: str = "+1234567890",
    db: AsyncSession = Depends(get_db)
):
    """Test endpoint for analysis orchestrator"""
    orchestrator = AnalysisOrchestrator(db_session=db)
    result = await orchestrator.analyze_message(
        message_id=999,  # Test ID
        message_content=message_content,
        sender_phone=sender_phone,
    )
    return result.dict()
```

Then test with:
```bash
curl -X POST "http://localhost:8000/test/analyze" \
  -H "Content-Type: application/json" \
  -d '{"message_content": "URGENT: Your account is suspended. Click bit.ly/xyz"}'
```

## Expected Output

For a high-risk message like:
```
"URGENT: Your Social Security has been suspended. Click here to verify: bit.ly/xyz"
```

You should see:
- **Risk Level:** `HIGH_RISK`
- **ML Score:** `0.7-0.9` (varies)
- **Rule Matches:** `urgency`, `impersonation`, `suspicious_link`
- **Warning Signs:** Multiple warnings about urgency, impersonation, suspicious links
- **Safe Next Steps:** Instructions to not click links, delete message, etc.

## Troubleshooting

**Import errors:**
- Make sure you're in the `backend` directory
- Activate the virtual environment
- Install dependencies: `pip install -r requirements.txt`

**Database errors:**
- Use `test_orchestrator_simple.py` instead (no database needed)
- Or check your `.env` file has correct database credentials

**Test failures:**
- Check that pytest and pytest-asyncio are installed
- Run with `-v` flag for verbose output: `pytest -v`

