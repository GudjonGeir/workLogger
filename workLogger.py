import requests
import base64

def loadTogglDay():
	url = "https://toggl.com/reports/api/v2/details"
	# url = "https://www.toggl.com/api/v8/workspaces"

	auth = requests.auth.HTTPBasicAuth("12ff1b7c62aaa0a69bbd3f93274538e1", 'api_token')

	payload = {
		"user_agent" : "gudjongeir@gmail.com",
		"workspace_id" : "1487773"
	}


	response = requests.get(url, params=payload, auth=auth)


	response.raise_for_status()

	worklogs = response.json()
	for value in worklogs['data']:
		print(value['description'])


if __name__ == "__main__":
	loadTogglDay()
