"""
debug.py
--------
Run this to diagnose exactly what's going wrong.
Usage: python debug.py
"""

import os
import sys

print("=" * 50)
print("MediQuery Debug Checker")
print("=" * 50)

# ── 1. Check .env file exists ─────────────────────────────────────────────────
print("\n[1] Checking .env file...")
if os.path.exists(".env"):
    print("    ✅ .env file found")
else:
    print("    ❌ .env file NOT found in current directory")
    print(f"    Current directory: {os.getcwd()}")
    print("    Fix: Make sure .env is in the same folder as your Python files")
    sys.exit(1)

# ── 2. Load dotenv and check key ──────────────────────────────────────────────
print("\n[2] Loading environment variables...")
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("    ❌ ANTHROPIC_API_KEY is empty or missing in .env")
    print("    Fix: Open .env and set ANTHROPIC_API_KEY=sk-ant-...")
    sys.exit(1)
elif api_key == "your_claude_api_key_here":
    print("    ❌ ANTHROPIC_API_KEY is still the placeholder value")
    print("    Fix: Replace it with your actual key from https://console.anthropic.com")
    sys.exit(1)
else:
    # Only show first/last 4 chars for safety
    masked = api_key[:8] + "..." + api_key[-4:]
    print(f"    ✅ API key found: {masked}")

# ── 3. Check DB credentials ───────────────────────────────────────────────────
print("\n[3] Checking DB config in .env...")
db_fields = ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"]
for field in db_fields:
    val = os.getenv(field)
    if val:
        display = val if field != "DB_PASSWORD" else "*" * len(val)
        print(f"    ✅ {field} = {display}")
    else:
        print(f"    ⚠️  {field} is not set (will use default)")

# ── 4. Test Claude API call ───────────────────────────────────────────────────
print("\n[4] Testing Claude API...")
try:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        messages=[{"role": "user", "content": "Reply with just: API OK"}],
    )
    reply = msg.content[0].text.strip()
    print(f"    ✅ Claude responded: '{reply}'")
    print(f"    ✅ Tokens used: {msg.usage.input_tokens} in / {msg.usage.output_tokens} out")
except anthropic.AuthenticationError:
    print("    ❌ Authentication failed — API key is invalid")
    print("    Fix: Get a valid key from https://console.anthropic.com")
    sys.exit(1)
except anthropic.RateLimitError:
    print("    ❌ Rate limit hit — wait a moment and retry")
    sys.exit(1)
except Exception as e:
    print(f"    ❌ Unexpected error: {e}")
    sys.exit(1)

# ── 5. Test DB connection ─────────────────────────────────────────────────────
print("\n[5] Testing MySQL connection...")
try:
    from db_connector import test_connection
    ok, msg = test_connection()
    if ok:
        print(f"    ✅ {msg}")
    else:
        print(f"    ❌ {msg}")
        print("    Fix: Check DB_HOST, DB_USER, DB_PASSWORD, DB_NAME in .env")
except Exception as e:
    print(f"    ❌ Could not import db_connector: {e}")

print("\n" + "=" * 50)
print("All checks passed! You're good to go 🚀")
print("=" * 50)