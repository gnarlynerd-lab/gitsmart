#!/bin/bash
# GitSmart Hook Installation Script

set -e

echo "🤖 Installing GitSmart git hooks..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "Please run this script from the root of your git repository"
    exit 1
fi

# Check if gitsmart is installed
if ! command -v gitsmart >/dev/null 2>&1; then
    echo "❌ Error: GitSmart not found"
    echo "Please install GitSmart first: pip install gitsmart"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy the post-commit hook
cp "$SCRIPT_DIR/hooks/post-commit" .git/hooks/post-commit

# Make it executable
chmod +x .git/hooks/post-commit

echo "✅ GitSmart post-commit hook installed successfully!"
echo ""
echo "🚀 How it works:"
echo "   • Analyzes commits for architectural changes"
echo "   • Prompts to document significant decisions"
echo "   • Auto-suggests reasoning using AI"
echo "   • Stores organizational memory in git notes"
echo ""
echo "💡 Test it: Make a commit with architectural changes"
echo "   The hook will automatically prompt you to document your reasoning"
echo ""
echo "🔧 To disable: rm .git/hooks/post-commit"
echo "🔧 To reconfigure: edit .git/hooks/post-commit"