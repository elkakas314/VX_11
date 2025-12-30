#!/usr/bin/env python3
"""
Test DeepSeek R1 communication for VX11
Loads API key from .env.deepseek
Makes a simple reasoning request
"""

import sys
import os
import json
from pathlib import Path


def load_deepseek_config():
    """Load DEEPSEEK_API_KEY from .env.deepseek"""
    env_file = Path(".env.deepseek")
    if not env_file.exists():
        print("❌ .env.deepseek not found")
        return None

    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY"):
                    key = line.split("=", 1)[1].strip('"').strip("'")
                    if key:
                        return key
    except Exception as e:
        print(f"❌ Error reading .env.deepseek: {e}")

    return None


def test_deepseek_r1():
    """Test DeepSeek R1 API call"""
    api_key = load_deepseek_config()

    if not api_key:
        print("❌ DEEPSEEK_API_KEY not configured")
        return False

    print("✅ API key loaded from .env.deepseek")

    try:
        from openai import OpenAI
    except ImportError:
        print("❌ openai SDK not installed")
        return False

    print("✅ openai SDK available")

    # Create client pointing to DeepSeek API
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    print("\n🧠 Testing DeepSeek R1 reasoning...")
    print("-" * 50)

    try:
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {
                    "role": "user",
                    "content": "VX11 reasoning test: Explain in JSON format what a 'solo_madre' policy means in a containerized system. Include: definition, benefits, risks, use_cases.",
                }
            ],
            temperature=1.0,  # DeepSeek reasoner works best at T=1.0
            max_tokens=2000,
        )

        print("✅ API call successful!")
        print(f"\nModel: {response.model}")
        print(f"Tokens used: {response.usage.total_tokens}")
        print(f"Reasoning tokens: {getattr(response.usage, 'reasoning_tokens', 'N/A')}")
        print("\n📝 Response:")
        print("-" * 50)
        print(response.choices[0].message.content[:1000])
        print("..." if len(response.choices[0].message.content) > 1000 else "")

        return True

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False


if __name__ == "__main__":
    success = test_deepseek_r1()
    sys.exit(0 if success else 1)
