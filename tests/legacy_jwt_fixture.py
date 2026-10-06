"""Historical issuer/verifier protocol fixture; JSON stdin/stdout, no app imports.

Executed only with LEGACY_JWT_PYTHON, an isolated compatibility environment.
Never prints keys/tokens to logs: its stdout is a captured in-memory protocol.
"""
import json
import sys

from jose import jwt

request = json.loads(sys.stdin.read())
if request["operation"] == "encode":
    result = jwt.encode(request["claims"], request["key"], algorithm="HS256")
elif request["operation"] == "decode":
    result = jwt.decode(request["token"], request["key"], algorithms=["HS256"])
else:
    raise RuntimeError("Unknown compatibility operation")
sys.stdout.write(json.dumps(result))
