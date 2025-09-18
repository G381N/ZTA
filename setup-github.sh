#!/bin/bash

# GitHub Setup Script for ZTA Behavioral Monitoring System
# This script prepares the repository for GitHub push

echo "🛡️ ZTA Behavioral Monitoring System - GitHub Setup"
echo "=================================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️ $1${NC}"
}

echo ""
print_step "Step 1: Repository Status Check"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_step "Initializing Git repository..."
    git init
    print_success "Git repository initialized"
else
    print_success "Git repository exists"
fi

echo ""
print_step "Step 2: Pre-commit Validation"
if [ -x "scripts/pre-commit-check.sh" ]; then
    ./scripts/pre-commit-check.sh
    if [ $? -eq 0 ]; then
        print_success "Pre-commit checks passed"
    else
        echo "❌ Pre-commit checks failed. Please fix issues before proceeding."
        exit 1
    fi
else
    print_info "Pre-commit script not found or not executable"
fi

echo ""
print_step "Step 3: Cleaning up files that shouldn't be committed"

# Remove large database files
if [ -f "data/behavior.db" ]; then
    print_info "Moving database file to backup location"
    mkdir -p backups
    mv data/behavior.db backups/behavior_backup_$(date +%Y%m%d_%H%M%S).db
    print_success "Database backed up and removed from commit"
fi

# Remove log files
if [ -d "logs" ] && [ "$(ls -A logs/)" ]; then
    print_info "Cleaning log files"
    mkdir -p backups/logs
    mv logs/*.log backups/logs/ 2>/dev/null || true
    print_success "Log files cleaned"
fi

# Remove trained models (they can be retrained)
if [ -f "models/behavior_model.pkl" ]; then
    print_info "Backing up trained model"
    mkdir -p backups/models  
    mv models/behavior_model.pkl backups/models/model_backup_$(date +%Y%m%d_%H%M%S).pkl
    print_success "Model backed up and removed from commit"
fi

echo ""
print_step "Step 4: Git Configuration"

# Check if Git user is configured
if ! git config user.name >/dev/null; then
    echo "Git user name not configured."
    read -p "Enter your Git username: " git_username
    git config user.name "$git_username"
fi

if ! git config user.email >/dev/null; then
    echo "Git user email not configured."
    read -p "Enter your Git email: " git_email  
    git config user.email "$git_email"
fi

print_success "Git user configured: $(git config user.name) <$(git config user.email)>"

echo ""
print_step "Step 5: Adding files to Git"

# Add all necessary files
git add .
git status

echo ""
print_step "Step 6: Creating initial commit"

# Create commit if there are changes
if git diff --cached --quiet; then
    print_info "No changes to commit"
else
    git commit -m "🚀 Initial commit: ZTA Behavioral Monitoring System

✨ Features:
- AI-powered anomaly detection with Isolation Forest
- Real-time behavioral monitoring and trust scoring  
- Interactive web dashboard with live updates
- Comprehensive API with 15+ endpoints
- Management tools for system administration
- Complete documentation and user guides

🛡️ Security:
- 55-dimensional behavioral feature analysis
- Dynamic trust scoring (0-100)
- Real-time threat classification
- Privacy-focused design (local storage only)

📊 Architecture:  
- FastAPI backend with async processing
- SQLite database for behavioral data
- Machine learning with scikit-learn
- Responsive web interface
- Cross-platform compatibility

Ready for production deployment and further development!"

    print_success "Initial commit created"
fi

echo ""
print_step "Step 7: Repository Information"

echo ""
echo "📊 Repository Statistics:"
echo "========================"
echo "📁 Files: $(find . -type f -not -path "./.git/*" -not -path "./backups/*" | wc -l)"
echo "📄 Python files: $(find . -name "*.py" -not -path "./.git/*" | wc -l)"
echo "📝 Documentation: $(find . -name "*.md" -not -path "./.git/*" | wc -l)"
echo "⚙️ Config files: $(find . -name "*.json" -o -name "*.yml" -o -name "*.yaml" | wc -l)"
echo "🧪 Test files: $(find . -name "*test*.py" -not -path "./.git/*" | wc -l)"

echo ""
echo "📋 Next Steps for GitHub:"
echo "========================"
echo ""
echo "1. 🌐 Create GitHub Repository:"
echo "   • Go to https://github.com/new"
echo "   • Repository name: zta-behavioral-monitoring"
echo "   • Description: AI-Powered Zero Trust Architecture with Behavioral Monitoring"
echo "   • Choose Public or Private"
echo "   • Don't initialize with README (we have one)"
echo ""
echo "2. 🔗 Connect Local Repository:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/zta-behavioral-monitoring.git"
echo ""
echo "3. 🚀 Push to GitHub:"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "4. ⚙️ Configure Repository Settings:"
echo "   • Enable Issues and Projects"
echo "   • Set up branch protection rules"
echo "   • Configure Actions for CI/CD"
echo "   • Add repository topics: machine-learning, cybersecurity, behavioral-analysis, zero-trust"
echo ""
echo "5. 📄 Update Repository Details:"
echo "   • Add comprehensive description"
echo "   • Set website URL (if deploying)"
echo "   • Add relevant topics/tags"
echo "   • Configure license (MIT included)"
echo ""
echo "6. 🔒 Security Setup:"
echo "   • Review Security tab"
echo "   • Enable Dependabot alerts"
echo "   • Set up code scanning (optional)"
echo ""

print_success "Repository is ready for GitHub! 🎉"

echo ""
echo "🛡️ ZTA System Features Ready for Showcase:"
echo "• ✅ AI-powered anomaly detection"
echo "• ✅ Real-time behavioral monitoring"
echo "• ✅ Interactive web dashboard"  
echo "• ✅ Comprehensive API (15+ endpoints)"
echo "• ✅ Management and admin tools"
echo "• ✅ Complete documentation"
echo "• ✅ Quick start scripts"
echo "• ✅ Professional project structure"
echo "• ✅ CI/CD pipeline configuration"
echo "• ✅ Security policies and guidelines"
echo ""
echo "🚀 Ready to showcase your advanced cybersecurity project!"
