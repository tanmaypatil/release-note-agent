"""
Verify ANTHROPIC_API_KEY is present in .env before running the agent.

Run from the project root:
    python tests/check_env.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

key = os.getenv('ANTHROPIC_API_KEY', '')

if not key:
    print('ANTHROPIC_API_KEY is not set — add it to .env')
    sys.exit(1)

print(f'ANTHROPIC_API_KEY: {key[:8]}...  PASS')
