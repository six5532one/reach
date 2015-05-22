import json
import time
import requests

user_handle="banunu_dog"
params = {"uname": user_handle, "stat": 0}
r = requests.get('http://reach-backend.elasticbeanstalk.com:2678/data', params=params)
if "OK" in r.text:
	print "here"
	params = {"uname": user_handle, "stat": 1}
	r = requests.get('http://reach-backend.elasticbeanstalk.com:2678/data', params=params)
	
	user_analytics = json.loads(r.text)["an2"]
	for entry in user_analytics:
		print entry
		print entry["count"]
		print entry["hashtag"]
		print "______"

else:
	print r.text
