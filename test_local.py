#!/usr/bin/env python3
"""
Complete Bug Surgeon Local Test
Tests all core functionality with proper environment loading
"""

import os
import sys
import traceback
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))


def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path('.env')

    if not env_path.exists():
        print("⚠️  No .env file found")
        print("Creating .env from template...")

        # Try to copy from template
        template_path = Path('.env.template')
        if template_path.exists():
            try:
                import shutil
                shutil.copy('.env.template', '.env')
                print("✅ Created .env from template")
                print("📝 Please edit .env and add your ANTHROPIC_API_KEY")
                return False
            except Exception as e:
                print(f"❌ Could not copy template: {e}")

        print("Please create .env file manually or run: cp .env.template .env")
        return False

    # Load environment variables
    loaded_vars = []
    try:
        with open(env_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")  # Remove quotes

                        if key and value:
                            os.environ[key] = value
                            loaded_vars.append(key)
                    except Exception as e:
                        print(f"⚠️  Warning: Could not parse line {line_num}: {line}")

        if loaded_vars:
            print(f"✅ Loaded {len(loaded_vars)} environment variables from .env file")
            print(f"   Variables: {', '.join(loaded_vars)}")
            return True
        else:
            print("⚠️  .env file exists but no valid variables found")
            return False

    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False


def check_dependencies():
    """Check if all required dependencies are installed"""
    print("\n🔍 Checking dependencies...")

    missing_deps = []

    try:
        import anthropic
        print("✅ anthropic library found")
    except ImportError:
        missing_deps.append("anthropic")

    try:
        import github
        print("✅ PyGithub library found")
    except ImportError:
        missing_deps.append("PyGithub")

    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install -r requirements.txt")
        return False

    print("✅ All dependencies installed")
    return True


def test_api_key():
    """Test if API key is properly configured"""
    print("\n🔑 Testing API key configuration...")

    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        print("\nTo fix this:")
        print("1. Make sure .env file exists")
        print("2. Add this line to .env:")
        print("   ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here")
        print("3. Get your key from: https://console.anthropic.com/")
        return False

    if api_key in ["your_anthropic_api_key_here", "your_key_here", ""]:
        print("❌ API key is still placeholder value")
        print("Please edit .env and add your real API key from https://console.anthropic.com/")
        return False

    if not api_key.startswith('sk-ant-api'):
        print("❌ API key format looks incorrect")
        print("Anthropic API keys should start with 'sk-ant-api'")
        print("Double-check your key from https://console.anthropic.com/")
        return False

    print(f"✅ API key configured correctly")
    print(f"   Format: {api_key[:12]}...{api_key[-8:]}")
    return True


def test_bug_surgeon_import():
    """Test importing the BugSurgeon class"""
    print("\n📦 Testing BugSurgeon import...")

    try:
        from debug_orchestrator import BugSurgeon
        print("✅ Successfully imported BugSurgeon")
        return BugSurgeon
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nPossible issues:")
        print("1. debug_orchestrator.py not found")
        print("2. Missing dependencies (run: pip install -r requirements.txt)")
        print("3. Python path issues")
        return None
    except Exception as e:
        print(f"❌ Unexpected error importing BugSurgeon: {e}")
        traceback.print_exc()
        return None


def test_bug_surgeon_initialization(BugSurgeon):
    """Test initializing BugSurgeon"""
    print("\n🚀 Testing BugSurgeon initialization...")

    try:
        # Set GitHub env vars to None to avoid GitHub requirement
        os.environ['GITHUB_TOKEN'] = 'dummy_token_for_local_test'
        surgeon = BugSurgeon()
        print("✅ BugSurgeon initialized successfully")
        return surgeon
    except ValueError as e:
        if "ANTHROPIC_API_KEY" in str(e):
            print(f"❌ API key error: {e}")
            return None
        elif "GITHUB_TOKEN" in str(e):
            print("❌ GitHub token error - this is expected for local testing")
            print("Setting dummy GitHub token for local test...")
            try:
                os.environ['GITHUB_TOKEN'] = 'dummy_token_for_local_test'
                surgeon = BugSurgeon()
                print("✅ BugSurgeon initialized with dummy GitHub token")
                return surgeon
            except Exception as e2:
                print(f"❌ Still failed: {e2}")
                return None
        else:
            print(f"❌ Initialization error: {e}")
            return None
    except Exception as e:
        print(f"❌ Unexpected initialization error: {e}")
        traceback.print_exc()
        return None


def test_bug_analysis(surgeon):
    """Test the actual bug analysis functionality"""
    print("\n🔍 Testing bug analysis...")

    # Comprehensive test bug report
    test_bug = """
I'm getting this error in my Python Flask web application:

Error Traceback:
```
Traceback (most recent call last):
  File "/app/auth.py", line 42, in authenticate_user
    return user.id
AttributeError: 'NoneType' object has no attribute 'id'
```

Context:
- This error happens when users try to log in to our web app
- It was working perfectly fine yesterday
- Multiple users are reporting they can't access their accounts
- The error occurs after entering valid credentials
- Our user database seems fine, sessions table also looks normal

Additional Details:
- Flask app running on Python 3.9
- Using SQLAlchemy for database ORM
- PostgreSQL database backend
- This is a critical production issue affecting all users

Expected Behavior: Users should be able to log in successfully
Actual Behavior: Getting 500 error with AttributeError on 'NoneType'

Please help identify the root cause and provide a fix.
"""

    try:
        print("📋 Analyzing comprehensive bug report...")
        print("   Bug type: Authentication error")
        print("   Error: AttributeError on NoneType")
        print("   Context: Production Flask app")

        analysis = surgeon.analyze_bug(test_bug)

        if analysis:
            print("\n" + "=" * 60)
            print("🎉 BUG ANALYSIS RESULTS")
            print("=" * 60)

            print(f"\n🔍 Root Cause:")
            print(f"   {analysis.root_cause}")

            print(f"\n📊 Confidence Level:")
            print(f"   {analysis.confidence}")

            print(f"\n📝 Detailed Explanation:")
            explanation = analysis.explanation
            # Wrap long explanations
            if len(explanation) > 100:
                words = explanation.split()
                lines = []
                current_line = ""
                for word in words:
                    if len(current_line + word) < 80:
                        current_line += word + " "
                    else:
                        lines.append(current_line.strip())
                        current_line = word + " "
                if current_line:
                    lines.append(current_line.strip())
                for line in lines:
                    print(f"   {line}")
            else:
                print(f"   {explanation}")

            print(f"\n🧠 Reasoning Steps:")
            for i, trace in enumerate(analysis.reasoning_trace, 1):
                trace_preview = trace[:100] + "..." if len(trace) > 100 else trace
                print(f"   {i}. {trace_preview}")

            print("\n✅ Bug analysis completed successfully!")
            print("🎯 The Bug Surgeon is working perfectly!")
            return True
        else:
            print("❌ Analysis failed - no results returned")
            print("This could indicate:")
            print("1. API communication issues")
            print("2. Invalid API key")
            print("3. Rate limiting")
            print("4. Bug in the analysis logic")
            return False

    except Exception as e:
        print(f"❌ Bug analysis failed with error: {e}")

        # Provide helpful debugging info
        if "API key" in str(e) or "authentication" in str(e).lower():
            print("💡 This looks like an API key issue")
            print("   - Check your key at: https://console.anthropic.com/")
            print("   - Make sure the key is active and has credits")
        elif "rate limit" in str(e).lower():
            print("💡 This looks like a rate limiting issue")
            print("   - Wait a moment and try again")
            print("   - Check your API usage at: https://console.anthropic.com/")
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            print("💡 This looks like a network connectivity issue")
            print("   - Check your internet connection")
            print("   - Try again in a moment")
        else:
            print("💡 Unexpected error - full traceback:")
            traceback.print_exc()

        return False


def run_comprehensive_test():
    """Run the complete test suite"""
    print("🚀 Bug Surgeon Comprehensive Local Test")
    print("=" * 50)

    test_results = {
        "env_loading": False,
        "dependencies": False,
        "api_key": False,
        "import": False,
        "initialization": False,
        "bug_analysis": False
    }

    # Test 1: Environment loading
    test_results["env_loading"] = load_env_file()

    # Test 2: Dependencies
    test_results["dependencies"] = check_dependencies()
    if not test_results["dependencies"]:
        print("\n❌ Cannot continue without dependencies")
        return test_results

    # Test 3: API key
    test_results["api_key"] = test_api_key()
    if not test_results["api_key"]:
        print("\n❌ Cannot continue without valid API key")
        return test_results

    # Test 4: Import
    BugSurgeon = test_bug_surgeon_import()
    test_results["import"] = BugSurgeon is not None
    if not test_results["import"]:
        print("\n❌ Cannot continue without successful import")
        return test_results

    # Test 5: Initialization
    surgeon = test_bug_surgeon_initialization(BugSurgeon)
    test_results["initialization"] = surgeon is not None
    if not test_results["initialization"]:
        print("\n❌ Cannot continue without successful initialization")
        return test_results

    # Test 6: Bug analysis (the main event!)
    test_results["bug_analysis"] = test_bug_analysis(surgeon)

    return test_results


def print_final_results(test_results):
    """Print final test results and next steps"""
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)

    total_tests = len(test_results)
    passed_tests = sum(test_results.values())

    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        test_display = test_name.replace("_", " ").title()
        print(f"{test_display:20} {status}")

    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("🎯 Your Bug Surgeon is fully functional and ready for production!")
        print("\n🚀 Next Steps:")
        print("1. Test with your own bug descriptions")
        print("2. Set up GitHub integration: python test_github.py")
        print("3. Deploy to GitHub Actions")
        print("4. Update your article with these working code examples!")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
        print("💡 Fix the failed tests above before proceeding")

        if not test_results["env_loading"]:
            print("\n🔧 To fix environment loading:")
            print("   cp .env.template .env")
            print("   # Edit .env and add your ANTHROPIC_API_KEY")

        if not test_results["api_key"]:
            print("\n🔧 To fix API key:")
            print("   Get your key from: https://console.anthropic.com/")
            print("   Add to .env: ANTHROPIC_API_KEY=sk-ant-api03-your-key")

        return False


if __name__ == "__main__":
    try:
        test_results = run_comprehensive_test()
        success = print_final_results(test_results)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        traceback.print_exc()
        sys.exit(1)