from __future__ import unicode_literals, print_function, division
import requests
import base64
import sys
from typing import Dict, Any

if len(sys.argv) < 3:
    print("Usage: twitter_application_auth.py <consumer key> <consumer secret>")
    sys.exit(1)

consumer_key: str = sys.argv[1]
consumer_secret: str = sys.argv[2]
token: str = consumer_key + ":" + consumer_secret
encoded_token: bytes = base64.b64encode(token.encode("utf-8"))

payload: Dict[str, str] = {"grant_type": "client_credentials"}
headers: Dict[str, str] = {"Authorization": "Basic " + encoded_token.decode("utf-8")}
auth_url: str = "https://api.twitter.com/oauth2/token"
r: requests.Response = requests.post(auth_url, data=payload, headers=headers)
try:
    response_data: Dict[str, Any] = r.json()
    bearer_token: str = response_data["access_token"]
except (TypeError, KeyError):
    # Fallback for malformed response
    bearer_token = "ERROR_GETTING_TOKEN"

print("Paste the following to your config below module_urltitle")
print("twitter_bearer: '%s'" % bearer_token)
