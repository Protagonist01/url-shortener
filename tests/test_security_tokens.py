"""Synthetic authentication contract and real historical JWT interoperability."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
KEY = "synthetic-jwt-compatibility-only-key-20261006"
SUBJECT = "jwt-fixture@example.com"


class AccessTokenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Settings() must first be imported from an empty cwd, not beside .env.
        cls.directory = TemporaryDirectory(prefix="jwt-contract-")
        cls.addClassCleanup(cls.directory.cleanup)
        previous = Path.cwd()
        os.environ.update({
            "APP_ENV": "test", "SECRET_KEY": KEY,
            "DATABASE_URL": "postgresql://test:test@127.0.0.1:9/test",
            "REDIS_URL": "redis://127.0.0.1:9/0",
            "CELERY_BROKER_URL": "redis://127.0.0.1:9/1",
            "CELERY_RESULT_BACKEND": "redis://127.0.0.1:9/2",
        })
        try:
            os.chdir(cls.directory.name)
            from app.core import security
            cls.security = security
            cls.old_key = security.settings.SECRET_KEY
            security.settings.SECRET_KEY = KEY
        finally:
            os.chdir(previous)
        cls.legacy_python = os.environ.get("LEGACY_JWT_PYTHON")
        if not cls.legacy_python:
            raise RuntimeError("Set LEGACY_JWT_PYTHON to an isolated historical fixture interpreter")

        cls.addClassCleanup(setattr, cls.security.settings, "SECRET_KEY", cls.old_key)

    def legacy(self, operation, **values):
        env = dict(os.environ)
        # Prevent the current app/PyJWT path from contaminating the old fixture.
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [self.legacy_python, str(ROOT / "tests/legacy_jwt_fixture.py")],
            input=json.dumps({"operation": operation, "key": KEY, **values}),
            cwd=self.directory.name, env=env, capture_output=True, text=True,
            timeout=15,
        )
        if result.returncode:
            self.fail("Historical fixture failed; no protocol/token output is disclosed")
        return json.loads(result.stdout)

    def claims(self, **extra):
        return {"sub": SUBJECT, "exp": int(datetime.now(timezone.utc).timestamp()) + 3600, **extra}

    def test_old_token_is_accepted_by_new_verifier(self):
        token = self.legacy("encode", claims=self.claims())
        self.assertEqual(self.security.decode_access_token(token), SUBJECT)

    def test_new_token_is_accepted_by_old_verifier(self):
        before = int(datetime.now(timezone.utc).timestamp())
        token = self.security.create_access_token(SUBJECT)
        claims = self.legacy("decode", token=token)
        self.assertEqual(claims["sub"], SUBJECT)
        expected = before + self.security.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        self.assertGreaterEqual(claims["exp"], expected)
        self.assertLessEqual(claims["exp"], expected + 5)
        self.assertEqual(set(claims), {"sub", "exp"})

    def test_wrong_key_is_rejected(self):
        token = self.security.jwt.encode(self.claims(), "different-synthetic-key-long-enough", algorithm="HS256")
        self.assertIsNone(self.security.decode_access_token(token))

    def test_attacker_algorithm_selection_is_rejected(self):
        for algorithm, key in (("none", None), ("HS384", KEY), ("HS512", KEY)):
            with self.subTest(algorithm=algorithm):
                token = self.security.jwt.encode(self.claims(), (key * 2) if key else key, algorithm=algorithm)
                self.assertIsNone(self.security.decode_access_token(token))

    def test_bad_subject_is_safe(self):
        for subject in (None, 1, [], {}, False):
            with self.subTest(subject_type=type(subject).__name__):
                token = self.security.jwt.encode(self.claims(sub=subject), KEY, algorithm="HS256")
                self.assertIsNone(self.security.decode_access_token(token))

    def test_expired_or_invalid_expiry_is_safe(self):
        for expiry in (1, None, "invalid", [], {}, float("inf")):
            with self.subTest(expiry_type=type(expiry).__name__):
                token = self.security.jwt.encode(self.claims(exp=expiry), KEY, algorithm="HS256")
                self.assertIsNone(self.security.decode_access_token(token))

    def test_malformed_and_non_string_input_is_safe(self):
        for token in ("", "malformed", "a.b.c", "e30.e30.a", None, 1, [], {}):
            self.assertIsNone(self.security.decode_access_token(token))

    def test_missing_subject_is_safe_and_existing_optional_expiry_is_preserved(self):
        without_subject = self.security.jwt.encode({"exp": self.claims()["exp"]}, KEY, algorithm="HS256")
        self.assertIsNone(self.security.decode_access_token(without_subject))
        # Historic verifier checked exp when present; issued app tokens always have it.
        no_expiry = self.legacy("encode", claims={"sub": SUBJECT})
        self.assertEqual(self.security.decode_access_token(no_expiry), SUBJECT)


if __name__ == "__main__":
    unittest.main()
