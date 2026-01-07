#!/bin/bash

# Cleanup script for Guardian Agent backend
# Removes cache files, duplicate tests, and temporary files

cd "$(dirname "$0")"

echo "🧹 Cleaning up Guardian Agent backend..."
echo ""

# Remove Python cache files
echo "1️⃣ Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null
echo "   ✅ Python cache cleaned"

# Remove duplicate test files from root (keep only tests/ directory)
echo ""
echo "2️⃣ Removing duplicate test files from root directory..."
rm -f test_cache_*.py
rm -f test_orchestrator*.py
echo "   ✅ Duplicate test files removed"
echo "   ℹ️  All tests are in tests/ directory"

# Remove .DS_Store files (macOS)
echo ""
echo "3️⃣ Removing macOS .DS_Store files..."
find . -name ".DS_Store" -delete 2>/dev/null
echo "   ✅ .DS_Store files removed"

# Remove unnecessary documentation files (optional)
echo ""
read -p "4️⃣ Remove ML_ANALYZER_DOCUMENTATION.md? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f ML_ANALYZER_DOCUMENTATION.md
    echo "   ✅ Documentation removed"
else
    echo "   ⏭️  Skipped"
fi

echo ""
echo "✨ Cleanup complete!"
echo ""
echo "📁 Remaining structure:"
echo "   ├── app/              (source code)"
echo "   ├── tests/            (all tests)"
echo "   ├── venv/             (virtual environment)"
echo "   ├── run_tests.sh      (test runner)"
echo "   └── requirements.txt  (dependencies)"
echo ""
