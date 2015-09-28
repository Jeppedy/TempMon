import urllib2
import json
f = urllib2.urlopen('http://api.wunderground.com/api/939d46d3584b09b6/geolookup/conditions/q/IL/Chicago.json')
json_string = f.read()
parsed_json = json.loads(json_string)
location = parsed_json['location']['city']
temp_f = parsed_json['current_observation']['temp_f']
print "Current temperature in %s is: %s" % (location, temp_f)
f.close()

