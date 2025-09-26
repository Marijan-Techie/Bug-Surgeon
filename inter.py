#!/usr/bin/env python3
"""
Simple interactive test to verify the Bug Surgeon works
"""

import os
import sys
from pathlib import Path


def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")


def main():
    print("🔍 Bug Surgeon Interactive Test")
    print("=" * 40)

    # Load environment
    load_env_file()

    # Check if examples/auth.py exists
    auth_file = Path('examples/auth.py')
    if not auth_file.exists():
        print("❌ examples/auth.py not found")
        print("Make sure you're in the claude-bug-surgeon directory")
        return

    print("✅ Found examples/auth.py")
    print()
    print("Options:")
    print("1. Test with demo bug (uses examples/auth.py)")
    print("2. Enter custom bug description")
    print()

    while True:
        choice = input("Choose option (1 or 2): ").strip()
        if choice in ['1', '2']:
            break
        print("Please enter 1 or 2")

    if choice == '1':
        # Demo bug using existing auth.py file
        bug_description = """
I'm getting this error in my Python authentication module:

```
Traceback (most recent call last):
  File "examples/auth.py", line 42, in authenticate_user
    return user.id
AttributeError: 'NoneType' object has no attribute 'id'
```

Context:
- This error happens when users try to log in
- It was working fine before our latest deployment  
- Multiple users are reporting they can't access their accounts
- The error occurs after entering valid credentials
- Our user database and sessions table seem normal

The authenticate_user function in examples/auth.py is throwing this error on line 42.
"""
        print("🔍 Using demo bug report...")

    else:
        # Custom bug description
        print("Enter your bug description (press Enter on empty line when done):")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        bug_description = "\n".join(lines)

        if not bug_description.strip():
            print("❌ No bug description provided")
            return

    print("\n" + "=" * 50)
    print("STARTING BUG ANALYSIS")
    print("=" * 50)

    try:
        # Import and run the bug surgeon
        from debug_orchestrator import BugSurgeon

        surgeon = BugSurgeon()
        analysis = surgeon.analyze_bug(bug_description)

        if analysis:
            print("\n🎉 ANALYSIS COMPLETE")
            print("=" * 30)
            print(f"Root Cause: {analysis.root_cause}")
            print(f"Confidence: {analysis.confidence}")
            print(f"Explanation: {analysis.explanation}")

            if analysis.reasoning_trace:
                print(f"\nReasoning Steps: {len(analysis.reasoning_trace)} steps")

            print("\n✅ Bug Surgeon worked successfully!")

        else:
            print("❌ Analysis failed")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()