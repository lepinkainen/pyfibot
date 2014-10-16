import requests

client_id = "a7a5d6bc929d48f"
client_secret = "57b1f90a12d4d72762b4b1bf644af5157f73fed5"

print "Open the following URL in a browser:"
print "https://api.imgur.com/oauth2/authorize?client_id=%s&response_type=pin&state=auth1" % client_id

pin = raw_input("enter pin:")
r = requests.post("https://api.imgur.com/oauth2/token", data={'client_id': client_id,
                                                              'client_secret': client_secret,
                                                              'grant_type': 'pin',
                                                              'pin': pin})

print "Paste the following to your configuration:"

print """
module_imgur:
  album_id: YOUR_ALBUM_ID_HERE
  access_token: %s
  refresh_token: %s
""" % (r.json()['access_token'], r.json()['refresh_token'])
