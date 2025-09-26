#!/usr/bin/env python3
"""
GitHub integration test for Bug Surgeon
Tests GitHub repository integration
"""

import os
import sys
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_github_integration():
    """Test GitHub integration"""

    # Check environment variables
    required_vars = ['ANTHROPIC_API_KEY', 'GITHUB_TOKEN', 'GITHUB_REPOSITORY']
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   {var}")
        print("\nPlease set these in your .env file or environment")
        return False

    try:
        from debug_orchestrator import BugSurgeon
        surgeon = BugSurgeon()
        print("✅ BugSurgeon with GitHub integration initialized")

        if surgeon.repo:
            print(f"✅ Connected to repository: {surgeon.repo.full_name}")
            print(f"   - Stars: {surgeon.repo.stargazers_count}")
            print(f"   - Language: {surgeon.repo.language}")
            print(f"   - Issues: {surgeon.repo.get_issues(state='open').totalCount}")
        else:
            print("⚠️  No repository connection (local mode)")

        return True

    except Exception as e:
        print(f"❌ GitHub integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔗 Bug Surgeon GitHub Integration Test")
    print("=" * 40)

    success = test_github_integration()

    if success:
        print("\n🎯 GitHub integration working!")
        print("\nYou can now:")
        print("1. Test with real repository files")
        print("2. Create issues and test the workflow")
        print("3. Deploy to GitHub Actions")
    else:
        print("\n💡 Fix the issues above and try again")
        sys.exit(1)
