import requests
import datetime
import re

class TogglLog:
	"""docstring for TogglLog."""
	def __init__(self, log):
		descriptionSplit = self.splitLogDescription(log['description'])
		self.description = descriptionSplit['description']
		self.issueNumber = descriptionSplit['issueNumber']

		self.durationMs = log['dur']
		self.durationStr = self.formatDuration()

	def formatDuration(self):
		ret = ''
		# remove ms
		duration = self.durationMs / 1000

		hour = int(duration / 3600)
		if hour > 0:
			ret += str(hour) + 'h'

		minutes = int((duration % 3600) / 60)
		if hour > 0 and minutes > 0:
			ret += ' '
		if minutes > 0:
			 ret += str(minutes) + 'm'

		return ret;

	def splitLogDescription(self, description):
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
	return [TogglLog(wl) for wl in worklogs if "Logged" not in wl['tags']]

def processLogs(logs):
	for log in logs:
		print('Toggl Description: ' + log.description)
		print('Duration:          ' + log.durationStr)

		if log.issueNumber is None:
			log.issueNumber = input('Issue Number:      ')
		else:
			print('Issue Number:      ' + log.issueNumber)


		print('-----------------------------------------------------------------')




def main():
	togglLogs = loadTogglDay()
	processLogs(togglLogs)

if __name__ == "__main__":
	main()
