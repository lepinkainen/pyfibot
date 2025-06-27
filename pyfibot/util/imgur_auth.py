from __future__ import unicode_literals, print_function, division
import requests
from typing import Dict, Any

client_id: str = "a7a5d6bc929d48f"
client_secret: str = "57b1f90a12d4d72762b4b1bf644af5157f73fed5"

print("Open the following URL in a browser:")
print(
    "https://api.imgur.com/oauth2/authorize?client_id=%s&response_type=pin&state=auth1"
    % client_id
)

pin: str = input("enter pin:")
r: requests.Response = requests.post(
    "https://api.imgur.com/oauth2/token",
    data={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "pin",
        "pin": pin,
    },
)

response_data: Dict[str, Any] = r.json()

print("Paste the following to your configuration:")

print(
    """
module_imgur:
  album_id: YOUR_ALBUM_ID_HERE
  access_token: %s
  refresh_token: %s
"""
    % (response_data["access_token"], response_data["refresh_token"])
)
