# Quick Start Guide

## 🚀 Running Tests

### Easy Way (Recommended)
```bash
./run_tests.sh          # Run all 55 tests
./run_tests.sh quick    # Fast run
./run_tests.sh new      # Only new tests (35)
./run_tests.sh old      # Only old tests (20)
```

### Manual Way
```bash
# 1. Activate venv
source venv/bin/activate

# 2. Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 3. Run tests
python -m pytest tests/test_ml_analyzer_complete.py -v
```

**IMPORTANT:** Always use `python -m pytest`, NOT just `pytest`

## ❓ Troubleshooting

### "ModuleNotFoundError: No module named 'transformers'"

You're using the wrong Python. Fix:
```bash
source venv/bin/activate
which python  # Should show .../backend/venv/bin/python
python -m pytest tests/test_ml_analyzer_complete.py -v
```

### VSCode showing wrong interpreter

1. Open Command Palette (Cmd+Shift+P)
2. Type "Python: Select Interpreter"
3. Choose "Enter interpreter path..."
4. Paste: `/Users/davidreyes/Documents/ColorStack/Guardian-Agent/backend/venv/bin/python`

## 🧹 Cleanup

```bash
./cleanup.sh  # Remove cache files and duplicates
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── config/
│   │   └── ml_config.py      ← ML configuration (NEW)
│   ├── services/
│   │   └── ml_analyzer.py    ← ML analyzer
│   └── utils/
│       └── url_extractor.py  ← URL utilities
├── tests/
│   ├── mock_data.py          ← Test data (NEW)
│   ├── test_ml_analyzer_complete.py  ← 35 tests (NEW)
│   └── test_ml_analyzer_logic.py     ← 20 tests (UPDATED)
├── venv/                     ← Virtual environment
├── run_tests.sh              ← Test runner (NEW)
├── cleanup.sh                ← Cleanup script (NEW)
└── requirements.txt          ← Dependencies
```

## ✅ What Was Done

1. Created `ml_config.py` - Fixed missing import
2. Created `mock_data.py` - 17 realistic test messages
3. Created `test_ml_analyzer_complete.py` - 35 comprehensive tests
4. Updated `test_ml_analyzer_logic.py` - Fixed 8 failing tests
5. Created `run_tests.sh` - Easy test runner
6. Created `cleanup.sh` - Project cleanup
7. Created `.gitignore` - Ignore cache files

## 📊 Test Results

✅ **55/55 tests passing (100%)**
- 35 new comprehensive tests
- 20 updated logic tests
- ~3 seconds runtime

## 🏗️ Architecture

**Orchestrator** → Combines Rule Engine + ML Analyzer
**ML Analyzer** → 3 HuggingFace models + rules
**Cache Service** → Ready for integration (not yet connected)

See `ML_ANALYZER_DOCUMENTATION.md` for full details.
