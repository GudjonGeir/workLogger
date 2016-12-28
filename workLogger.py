import requests
import datetime
import re
import sys

class TogglLog:
	"""docstring for TogglLog."""
	def __init__(self, log):
		descriptionSplit = self.splitLogDescription(log['description'])
		self.description = descriptionSplit['description']
		self.issueNumber = descriptionSplit['issueNumber']

		self.durationMs = log['dur']

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
		reMatch = re.match( r'([a-zA-Z0-9]+-[0-9]+)\s*(.*)', description)
		issueNumber = None
		description = description
		if reMatch:
			issueNumber = reMatch.group(1)
			description = reMatch.group(2)
		return {
			"issueNumber" : issueNumber,
			"description" : description
		}


class JiraAPI():
	"""docstring for JiraAPI."""
	def __init__(self):
		super(JiraAPI, self).__init__()
		self.baseUrl = 'https://sendiradid.atlassian.net'
		self.getIssueRoute = '/rest/api/2/issue/{issueNumber}'
		self.postWorklog = '/rest/tempo-timesheets/3/worklogs/'
		self.auth = self.authorization()

	def authorization(self):
		import getpass
		username = input('Jira Username:')
		password = getpass.getpass('Jira Password:')
		return requests.auth.HTTPBasicAuth(username, password)

	def getIssue(self, issueNumber):
		url = self.baseUrl + self.getIssueRoute.replace('{issueNumber}', issueNumber)
		payload = {
			'fields' : 'summary,description,timetracking'
		}
		response = requests.get(url, params=payload, auth=self.auth)
		if response.status_code == 401:
			sys.exit("Jira login failed")
		response.raise_for_status()

		return JiraIssue(response.json())

class JiraIssue():
	"""docstring for JiraIssue."""
	def __init__(self, json):
		self.issueNumber = json['key']
		timetracking = json['fields'].get('timetracking')
		self.originalEstimate = timetracking.get('originalEstimate') if timetracking is not None else None
		self.remainingEstimate = timetracking.get('remainingEstimate') if timetracking is not None else None
		self.timeSpent = timetracking.get('timeSpent') if timetracking is not None else None
		self.summary = json['fields']['summary']
		self.description = json['fields']['description']

	def print(self):
		print('Jira Issue:         ' + self.issueNumber)
		print('Summary:            ' + self.summary)
		if self.originalEstimate is not None: print('Original Estimate:  ' + self.originalEstimate)
		if self.timeSpent is not None: print('Time Spent:         ' + self.timeSpent)
		if self.remainingEstimate is not None: print('Remaining Estimate: ' + self.remainingEstimate)


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
	jiraApi = JiraAPI()
	for log in logs:
		print('-----------------------------------------------------------------')
		print('Toggl Description: ' + log.description)
		print('Duration:          ' + log.formatDuration())

		if log.issueNumber is None:
			log.issueNumber = input('Issue Number:      ')
		else:
			print('Issue Number:      ' + log.issueNumber)

		print('-----------------------------------------------------------------')

		jiraIssue = jiraApi.getIssue(log.issueNumber)
		jiraIssue.print()
		print('-----------------------------------------------------------------\n')

def groupLogs(logs):
	from collections import defaultdict
	groupBy = defaultdict(list)
	for log in logs:
		groupBy[log.issueNumber].append(log)

	newList = []

	for issueNumber, group in groupBy.items():
		log = group[0]
		sum = 0
		for log in group:
			sum += log.durationMs
		log.durationMs = sum
		newList.append(log)
	return newList

def main():
	togglLogs = loadTogglDay()
	togglLogs = groupLogs(togglLogs)
	processLogs(togglLogs)

if __name__ == "__main__":
	main()
