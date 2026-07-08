import os
# a test key; in production set VERDICT_HMAC_KEY via env and never commit it.
os.environ.setdefault("VERDICT_HMAC_KEY", "test-key-not-for-production")
