#!/usr/bin/env python3
"""
Quick API format test to verify Anthropic API is working
"""

import os
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


def test_api_call():
    """Test a simple API call to verify format"""
    load_env_file()

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return False

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)

        # Test the correct API format
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            system="You are a helpful assistant.",  # System prompt as separate parameter
            messages=[
                {"role": "user", "content": "Say hello and confirm you can help with debugging."}
            ]
        )

        result = response.content[0].text
        print("✅ API call successful!")
        print(f"Response: {result}")
        return True

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Quick API Format Test")
    print("=" * 30)

    if test_api_call():
        print("\n✅ API format is working correctly!")
        print("Now try: python test_local.py")
    else:
        print("\n❌ API test failed - check your setup")