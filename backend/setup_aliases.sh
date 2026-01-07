#!/bin/bash

# Setup convenient aliases for Guardian Agent development
# Run: source setup_aliases.sh

export GUARDIAN_BACKEND="/Users/davidreyes/Documents/ColorStack/Guardian-Agent/backend"

# Alias to activate venv from anywhere
alias guardian-activate="cd $GUARDIAN_BACKEND && source venv/bin/activate && export PYTHONPATH=\"\${PYTHONPATH}:\$(pwd)\""

# Alias to run tests
alias guardian-test="cd $GUARDIAN_BACKEND && ./run_tests.sh"

# Alias to cleanup
alias guardian-clean="cd $GUARDIAN_BACKEND && ./cleanup.sh"

echo "✅ Guardian Agent aliases loaded!"
echo ""
echo "Available commands:"
echo "  guardian-activate  - Activate venv and set PYTHONPATH"
echo "  guardian-test      - Run tests"
echo "  guardian-clean     - Cleanup project"
echo ""
echo "Example usage:"
echo "  guardian-activate"
echo "  guardian-test quick"
