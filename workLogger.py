import requests
import datetime
import re

def loadTogglDay():
	url = "https://toggl.com/reports/api/v2/details"
	# url = "https://www.toggl.com/api/v8/workspaces"

	auth = requests.auth.HTTPBasicAuth("12ff1b7c62aaa0a69bbd3f93274538e1", 'api_token')

	payload = {
		"user_agent" : "gudjongeir@gmail.com",
		"workspace_id" : "1487773",
		"since" : datetime.datetime.now().strftime("%Y-%m-%d") # TODO: Optional parameter
	}

	response = requests.get(url, params=payload, auth=auth)

	response.raise_for_status()

	# Parse toggl worklogs json to python object
	worklogs = response.json()['data']

	# Filter out logs that are tagged with 'logged'
	return [{'description': wl['description'], 'duration': wl['dur']} for wl in worklogs if "Logged" not in wl['tags']]

def processLogs(logs):
	for log in logs:
		desc = splitLogDescription(log['description'])
		print('Issue Number:      ' + desc['issueNumber'])
		print('Toggl Description: ' + desc['description'])
		print('Duration:          ' + str(log['duration']))
		print('-----------------------------------------------')

def splitLogDescription(description):
	reMatch = re.match( r'([a-zA-Z]+-[0-9]+)\s*(.*)', description)
	issueNumber = None
	description = description
	if reMatch:
		issueNumber = reMatch.group(1)
		description = reMatch.group(2)
	return {
		"issueNumber" : issueNumber,
		"description" : description
	}


def main():
	togglLogs = loadTogglDay()
	processLogs(togglLogs)

if __name__ == "__main__":
	main()
