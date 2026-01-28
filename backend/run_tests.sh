#!/bin/bash

# Test runner script for ML Analyzer
# Makes testing easier without remembering all the commands

cd "$(dirname "$0")"

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "📦 Setting PYTHONPATH..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo ""
echo "================================================"
echo "   ML Analyzer Test Suite"
echo "================================================"
echo ""

# Parse command line arguments
TEST_TYPE="${1:-all}"

case "$TEST_TYPE" in
    "all")
        echo "Running ALL ML analyzer tests..."
        python -m pytest tests/test_ml_analyzer_*.py -v
        ;;
    "new")
        echo "Running NEW comprehensive tests only..."
        python -m pytest tests/test_ml_analyzer_complete.py -v
        ;;
    "old")
        echo "Running OLD logic tests only..."
        python -m pytest tests/test_ml_analyzer_logic.py -v
        ;;
    "quick")
        echo "Running quick test (no verbose)..."
        python -m pytest tests/test_ml_analyzer_*.py -q
        ;;
    "coverage")
        echo "Running tests with coverage report..."
        python -m pytest tests/test_ml_analyzer_complete.py --cov=app.services.ml_analyzer --cov-report=term-missing
        ;;
    "class")
        if [ -z "$2" ]; then
            echo "❌ Error: Please specify a test class"
            echo "Example: ./run_tests.sh class TestMLAnalyzerScoring"
            exit 1
        fi
        echo "Running test class: $2"
        python -m pytest tests/test_ml_analyzer_complete.py::$2 -v
        ;;
    "help")
        echo "Usage: ./run_tests.sh [option]"
        echo ""
        echo "Options:"
        echo "  all       - Run all ML analyzer tests (default)"
        echo "  new       - Run only new comprehensive tests"
        echo "  old       - Run only old logic tests"
        echo "  quick     - Quick run without verbose output"
        echo "  coverage  - Run with code coverage report"
        echo "  class     - Run specific test class (requires class name)"
        echo "  help      - Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh"
        echo "  ./run_tests.sh new"
        echo "  ./run_tests.sh coverage"
        echo "  ./run_tests.sh class TestMLAnalyzerScoring"
        ;;
    *)
        echo "❌ Unknown option: $TEST_TYPE"
        echo "Run './run_tests.sh help' for usage information"
        exit 1
        ;;
esac
