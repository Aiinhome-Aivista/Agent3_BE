"""Manual test — directly call send_medium_digest and print result."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from utils.email_notifier import send_medium_digest
from utils.common import logger
import logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(levelname)s | %(message)s")

print("=" * 50)
print("Testing send_medium_digest...")
print("=" * 50)

count = send_medium_digest()

print("=" * 50)
print(f"Result: {count} alert(s) processed")
if count == 0:
    print("No unsent open alerts found in DB (all already notified, or no open alerts exist).")
else:
    print("Email sent! Check your inbox.")
print("=" * 50)
