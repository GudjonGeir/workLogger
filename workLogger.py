import requests
import datetime

def loadTogglDay():
	url = "https://toggl.com/reports/api/v2/details"
	# url = "https://www.toggl.com/api/v8/workspaces"

	auth = requests.auth.HTTPBasicAuth("12ff1b7c62aaa0a69bbd3f93274538e1", 'api_token')

	payload = {
		"user_agent" : "gudjongeir@gmail.com",
		"workspace_id" : "1487773",
		"since" : datetime.datetime.now().strftime("%Y/%m/%d") # TODO: Optional parameter
	}


	response = requests.get(url, params=payload, auth=auth)

	response.raise_for_status()

	# Parse toggl worklogs json to python object
	worklogs = response.json()['data']

	# Filter out logs that are tagged with 'logged'
	return [{'description': wl['description'], 'duration': wl['dur']} for wl in worklogs if "Logged" not in wl['tags']]

def main():
	togglLogs = loadTogglDay()
	print(togglLogs)

if __name__ == "__main__":
	main()
