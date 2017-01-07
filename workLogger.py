import requests
import datetime
import re
import sys
import getpass

class TogglApi:
	"""docstring for TogglApi."""
	def __init__(self,):
		self.baseUrl = 'https://www.toggl.com/api/v8'
		self.getLogsRoute = '/time_entries'
		self.portTagsRoute = 'TODO'
		self.auth = self.authorization()

	def authorization(self):
		username = input('Toggl Username:')
		password = getpass.getpass('Toggl Password:')
		return requests.auth.HTTPBasicAuth(username, password)


	def getLogs(self, sinceDate=None):
		url = self.baseUrl + self.getLogsRoute

		sinceDate = sinceDate if sinceDate is not None else datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
		payload = {
			"start_date" : sinceDate.isoformat() + '+00:00'
		}

		response = requests.get(url, params=payload, auth=self.auth)
		if response.status_code == 401 or response.status_code == 403:
			sys.exit("Toggl login failed")

		response.raise_for_status()

		# Parse toggl worklogs json to python object
		worklogs = response.json()
		# print(response.text)
		# Filter out logs that are tagged with 'logged'
		allLogs = [TogglLog(wl) for wl in worklogs if "Logged" not in wl.get('tags', [])]

		# Group logs by issue number with summed up duration
		return self.groupLogs(allLogs)
	# END def getLogs()

	def groupLogs(self, logs):
		from collections import defaultdict
		groupBy = defaultdict(list)
		for log in logs:
			groupBy[log.issueNumber].append(log)

		newList = []

		for issueNumber, group in groupBy.items():
			log = group[0]
			sum = 0
			for log in group:
				sum += log.durationSeconds
			log.durationMs = sum
			newList.append(log)
		return newList
	# END def groupLogs(logs)

class TogglLog:
	"""docstring for TogglLog."""
	def __init__(self, log):
		descriptionSplit = self.splitLogDescription(log['description'])
		self.description = descriptionSplit['description']
		self.issueNumber = descriptionSplit['issueNumber']

		self.durationSeconds = log['duration']

	def formatDuration(self):
		ret = ''
		# remove ms
		duration = self.durationSeconds

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

	def print(self):
		print('Toggl Description: ' + self.description)
		print('Duration:          ' + self.formatDuration())

		if self.issueNumber is None:
			self.issueNumber = input('Issue Number:      ')
		else:
			print('Issue Number:      ' + self.issueNumber)
# END class TogglLog

class JiraAPI:
	"""docstring for JiraAPI."""
	def __init__(self):
		super(JiraAPI, self).__init__()
		self.baseUrl = 'https://sendiradid.atlassian.net'
		self.getIssueRoute = '/rest/api/2/issue/{issueNumber}'
		self.postWorklog = '/rest/tempo-timesheets/3/worklogs/'
		self.auth = self.authorization()

	def authorization(self):
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
		if response.status_code == 404:
			sys.exit('Could not find issue with number: "' + issueNumber + '"' )
		response.raise_for_status()

		return JiraIssue(response.json())
# END class JiraAPI


class JiraIssue:
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
# END class JiraIssue



def main():
	togglApi = TogglApi()
	jiraApi = JiraAPI()

	togglLogs = togglApi.getLogs()

	for log in togglLogs:
		print('-----------------------------------------------------------------')
		log.print()

		print('-----------------------------------------------------------------')

		jiraIssue = jiraApi.getIssue(log.issueNumber)
		jiraIssue.print()
		print('-----------------------------------------------------------------\n')

# END def main()

if __name__ == "__main__":
	main()
