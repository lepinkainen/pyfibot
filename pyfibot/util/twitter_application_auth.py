import requests
import base64
import sys

if len(sys.argv) < 3:
    print "Usage: twitter_application_auth.py <consumer key> <consumer secret>"
    sys.exit(1)

consumer_key = sys.argv[1]
consumer_secret = sys.argv[2]
token = consumer_key+":"+consumer_secret
encoded_token = base64.b64encode(token)

payload = {'grant_type': 'client_credentials'}
headers = {'Authorization': 'Basic '+encoded_token}
auth_url = "https://api.twitter.com/oauth2/token"
r = requests.post(auth_url, payload, headers=headers)
try:
    bearer_token = r.json()['access_token']
except TypeError:
    bearer_token = r.json['access_token']

print "Bearer token:"
print bearer_token

