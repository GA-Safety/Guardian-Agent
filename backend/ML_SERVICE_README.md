# ML SMS Scam Analyzer Service

Production-ready ML-based SMS scam detection service using HuggingFace pretrained models and ensemble scoring.

## Features

- **Ensemble ML Detection**: Combines 3 HuggingFace models for high accuracy
  - BERT-based phishing text classifier
  - DistilBERT SMS spam detector
  - URL phishing classifier
- **Rules-Based Detection**: Pattern matching for common scam indicators
- **URL Analysis**: Extracts and analyzes URLs from messages
- **Human-Friendly Output**: Risk scores and plain-English explanations
- **Production Ready**: Includes caching, error handling, logging, and monitoring

## Quick Start

### Local Development

1. **Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Set environment variables** (optional):
```bash
export LOG_LEVEL=INFO
export ML_HIGH_THRESHOLD=0.8
export ML_MEDIUM_THRESHOLD=0.5
```

3. **Run the server**:
```bash
uvicorn app.main:app --reload --port 8000
```

4. **Check health**:
```bash
curl http://localhost:8000/ml_health
```

### Docker Deployment

1. **Build the image**:
```bash
docker build -t sms-scam-analyzer .
```

2. **Run the container**:
```bash
docker run -p 8000:8000 sms-scam-analyzer
```

## API Endpoints

### POST /analyze_sms

Analyze an SMS message for scam indicators.

**Request**:
```bash
curl -X POST http://localhost:8000/analyze_sms \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "msg_123",
    "text": "URGENT: Your account has been locked. Verify at bit.ly/verify",
    "sender": "+1-555-0123",
    "received_ts": "2024-01-05T10:30:00Z"
  }'
```

**Response**:
```json
{
  "message_id": "msg_123",
  "risk_score": 0.847,
  "risk_level": "high",
  "reasons": [
    "Contains a link",
    "Link looks suspicious",
    "Uses shortened URL (hard to verify)",
    "Urgent language",
    "Mentions account lock or suspension",
    "Message resembles phishing/scam language"
  ],
  "model_scores": {
    "phishing_text": 0.892,
    "sms_spam": 0.754,
    "url_phishing": 0.921,
    "rules": 0.350
  },
  "urls": [
    "http://bit.ly/verify"
  ],
  "version": "1.0.0",
  "inference_time_seconds": 0.342
}
```

### GET /ml_health

Check ML service health and model status.

**Request**:
```bash
curl http://localhost:8000/ml_health
```

**Response**:
```json
{
  "status": "ok",
  "models_loaded": true,
  "device": "CPU"
}
```

## Risk Scoring

### Ensemble Formula

```
final_score = clamp(
  0.55 * phishing_text_score +
  0.25 * sms_spam_score +
  0.35 * url_phishing_score +
  rules_boost,
  0.0, 1.0
)
```

### Risk Levels

- **Low** (< 0.35): Message appears safe
- **Medium** (0.35 - 0.70): Be cautious, verify sender
- **High** (> 0.70): High scam probability, do not engage

### Rules-Based Indicators

The service detects common scam patterns:

1. **Urgency** (+0.15): "urgent", "act now", "expires today"
2. **Account Issues** (+0.20): "account locked", "suspended"
3. **Credential Requests** (+0.25): "OTP", "verification code"
4. **Money Transfer** (+0.20): "wire money", "gift card", "bitcoin"
5. **Impersonation** (+0.15): "IRS", "bank", "police"
6. **Link Shorteners** (+0.10): "bit.ly", "t.co", "tinyurl"

## Testing

### Run Unit Tests

```bash
# Test URL extraction
pytest tests/test_url_extractor.py -v

# Test scoring logic
pytest tests/test_ml_analyzer_logic.py -v

# Run all tests
pytest tests/ -v
```

### Manual Testing with Example Messages

```bash
# Test with example scam message
curl -X POST http://localhost:8000/analyze_sms \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "message_id": "test_001",
  "text": "URGENT: Your Bank of America account has been suspended. Verify at bit.ly/boa-verify",
  "sender": "+1-555-0123"
}
EOF

# Test with safe message
curl -X POST http://localhost:8000/analyze_sms \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "message_id": "test_002",
  "text": "Hi Mom! Just landed. Will call you soon.",
  "sender": "+1-555-1111"
}
EOF
```

### Use Example Messages File

The `example_messages.json` file contains 10 curated test cases (5 scams, 5 safe).

```bash
# Extract and test a scam message
jq '.scam_messages[0]' example_messages.json | \
  jq '{message_id, text, sender}' | \
  curl -X POST http://localhost:8000/analyze_sms \
    -H "Content-Type: application/json" \
    -d @-
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEIGHT_PHISHING_TEXT` | 0.55 | Weight for phishing model |
| `WEIGHT_SMS_SPAM` | 0.25 | Weight for spam model |
| `WEIGHT_URL_PHISHING` | 0.35 | Weight for URL model |
| `RISK_LOW_THRESHOLD` | 0.35 | Low risk upper bound |
| `RISK_MEDIUM_THRESHOLD` | 0.70 | Medium risk upper bound |
| `MAX_MESSAGE_LENGTH` | 1600 | Max SMS length (chars) |

### Model Configuration

Models are defined in `app/config/ml_config.py`:

```python
MODELS = {
    "phishing_text": "ealvaradob/bert-finetuned-phishing",
    "sms_spam": "mariagrandury/distilbert-base-uncased-finetuned-sms-spam-detection",
    "url_phishing": "CrabInHoney/urlbert-tiny-v4-phishing-classifier",
}
```

## Performance

### Model Loading

- First startup: ~30-60 seconds (downloads models from HuggingFace)
- Subsequent startups: ~5-10 seconds (models cached locally)
- Models are loaded once at startup and cached in memory

### Inference Time

- **CPU**: ~300-500ms per message
- **GPU**: ~100-200ms per message (if CUDA available)

### Optimization Tips

1. **Use GPU**: Set `CUDA_VISIBLE_DEVICES` if GPU available
2. **Increase workers**: Run multiple uvicorn workers for parallel requests
3. **Add Redis caching**: Cache results for duplicate messages (already implemented in main app)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI App                          │
├─────────────────────────────────────────────────────────┤
│  POST /analyze_sms  │  GET /ml_health                   │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│                  ML Analyzer Service                     │
├─────────────────────────────────────────────────────────┤
│  • URL Extraction                                        │
│  • Text Classification (Phishing + Spam models)          │
│  • URL Classification                                    │
│  • Rules-Based Detection                                 │
│  • Ensemble Scoring                                      │
│  • Reason Generation                                     │
└─────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│              HuggingFace Models (Cached)                 │
├─────────────────────────────────────────────────────────┤
│  1. BERT Phishing Detector                               │
│  2. DistilBERT Spam Detector                             │
│  3. URLBert Phishing Classifier                          │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
backend/
├── app/
│   ├── config/
│   │   └── ml_config.py          # ML model config, weights, thresholds
│   ├── models/
│   │   └── ml_analysis.py        # Pydantic request/response models
│   ├── services/
│   │   └── ml_analyzer.py        # Core ML analysis service
│   ├── utils/
│   │   └── url_extractor.py      # URL extraction utilities
│   └── main.py                   # FastAPI app with endpoints
├── tests/
│   ├── test_url_extractor.py     # URL extraction tests
│   └── test_ml_analyzer_logic.py # Scoring logic tests
├── example_messages.json         # Test message samples
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container definition
└── ML_SERVICE_README.md          # This file
```

## Troubleshooting

### Models Not Loading

```bash
# Check logs
tail -f logs/app.log

# Verify HuggingFace connectivity
python -c "from transformers import pipeline; print('OK')"

# Clear HuggingFace cache and retry
rm -rf ~/.cache/huggingface/
```

### Out of Memory

```bash
# Use CPU instead of GPU
export CUDA_VISIBLE_DEVICES=""

# Reduce batch size or use lighter models
```

### Slow Inference

```bash
# Check if models are loaded
curl http://localhost:8000/ml_health

# Monitor resource usage
htop  # or `docker stats` for containers
```

## Production Deployment

### Recommended Setup

1. **Use GPU instance** (e.g., AWS g4dn, GCP with T4)
2. **Add load balancer** for high availability
3. **Enable Redis caching** (already integrated)
4. **Set up monitoring** (Prometheus + Grafana)
5. **Configure logging** (structured JSON logs to CloudWatch/Stackdriver)

### Example Docker Compose

```yaml
version: '3.8'
services:
  ml-analyzer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## License

MIT

## Support

For issues or questions, please open an issue in the repository.
