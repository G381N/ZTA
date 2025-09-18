#!/usr/bin/env bash

# Pre-commit hook for ZTA Behavioral Monitoring System
# This script runs before each commit to ensure code quality

echo "🔍 Running pre-commit checks..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Run this from the project root directory"
    exit 1
fi

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if any checks fail
FAILED=0

# Function to print success
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error
error() {
    echo -e "${RED}❌ $1${NC}"
    FAILED=1
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

echo ""
echo "1. Checking Python syntax..."
if python3 -m py_compile main.py src/**/*.py 2>/dev/null; then
    success "Python syntax check passed"
else
    error "Python syntax errors found"
fi

echo ""
echo "2. Checking for required files..."
REQUIRED_FILES=("main.py" "requirements.txt" "README.md" "LICENSE" ".gitignore")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        success "$file exists"
    else
        error "$file is missing"
    fi
done

echo ""
echo "3. Checking project structure..."
REQUIRED_DIRS=("src" "src/api" "src/core" "src/ml" "src/monitoring" "config" "static" "templates")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        success "$dir/ directory exists"
    else
        error "$dir/ directory is missing"
    fi
done

echo ""
echo "4. Checking for sensitive files..."
SENSITIVE_PATTERNS=("*.key" "*.pem" "*.p12" "config/*local*" "*.env" "*.secret")
FOUND_SENSITIVE=0
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if ls $pattern 2>/dev/null | head -1; then
        warning "Found sensitive file pattern: $pattern"
        FOUND_SENSITIVE=1
    fi
done
if [ $FOUND_SENSITIVE -eq 0 ]; then
    success "No sensitive files detected"
fi

echo ""
echo "5. Checking database files..."
if [ -f "data/behavior.db" ]; then
    size=$(du -h data/behavior.db | cut -f1)
    warning "Database file exists (${size}) - consider if it should be committed"
else
    success "No database file to commit"
fi

echo ""
echo "6. Checking log files..."
LOG_COUNT=$(find logs/ -name "*.log" 2>/dev/null | wc -l)
if [ $LOG_COUNT -gt 0 ]; then
    warning "Found $LOG_COUNT log files - make sure they should be committed"
else
    success "No log files to commit"
fi

echo ""
echo "7. Checking code quality..."

# Check for common issues
if grep -r "TODO\|FIXME\|XXX" src/ --include="*.py" 2>/dev/null | head -5; then
    warning "Found TODO/FIXME comments"
else
    success "No TODO/FIXME comments found"
fi

if grep -r "print(" src/ --include="*.py" 2>/dev/null | head -3; then
    warning "Found print() statements - consider using logging instead"
else
    success "No print() statements found in source code"
fi

echo ""
echo "8. Checking imports..."
if python3 -c "
import sys
sys.path.append('src')
try:
    from api.main import app
    from core.database import BehaviorDatabase
    from ml.behavior_model import BehaviorModel
    print('✅ All core imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
" 2>/dev/null; then
    success "Core module imports work"
else
    error "Import errors detected"
fi

echo ""
echo "9. Checking documentation..."
if [ -s "README.md" ] && [ -s "USER_GUIDE.md" ]; then
    success "Documentation files are present and non-empty"
else
    error "Documentation files missing or empty"
fi

echo ""
echo "10. Final validation..."
if [ $FAILED -eq 0 ]; then
    success "All pre-commit checks passed! ✨"
    echo ""
    echo "📋 Commit checklist:"
    echo "   • Code syntax is valid"
    echo "   • Required files are present"
    echo "   • Project structure is intact"
    echo "   • No obvious sensitive data"
    echo "   • Core imports work"
    echo "   • Documentation is present"
    echo ""
    echo "🚀 Ready to commit!"
    exit 0
else
    error "Some pre-commit checks failed!"
    echo ""
    echo "❌ Please fix the issues above before committing."
    exit 1
fi
