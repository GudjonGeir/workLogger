import requests
import datetime
import re
import sys
import getpass
import dateutil.parser

def formatSecondsToTimeString(seconds):
	ret = ''

	if seconds <= 0:
		return '0m'

	hour = int(seconds / 3600)
	if hour > 0:
		ret += str(hour) + 'h'

	minutes = int((seconds % 3600) / 60)
	if hour > 0 and minutes > 0:
		ret += ' '
	if minutes > 0:
		ret += str(minutes) + 'm'

	return ret

class TogglApi:
	"""docstring for TogglApi."""
	def __init__(self,):
		self.baseUrl = 'https://www.toggl.com/api/v8'
		self.getTimeEntriesRoute = '/time_entries'
		self.getMeRoute = '/me'
		self.postTagRoute = '/time_entries/{timeEntryId}'
		self.auth = ''

	def authenticate(self):
		while True:
			username = input('Toggl Username:')
			password = getpass.getpass('Toggl Password:')
			self.auth = requests.auth.HTTPBasicAuth(username, password)

			response = requests.get(self.baseUrl + self.getMeRoute, auth=self.auth)
			if response.status_code == 200:
				print('Toggl login successful\n')
				break
			else:
				print('Toggl login was not successful, please try again\n')


	def getTimeEntries(self, startDate):
		url = self.baseUrl + self.getTimeEntriesRoute

		startDate = startDate if startDate is not None else datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
		endDate = startDate + datetime.timedelta(days=1)
		payload = {
			"start_date" : startDate.isoformat() + '+00:00',
			"end_date": endDate.isoformat() + '+00:00',
		}


		response = requests.get(url, params=payload, auth=self.auth)
		if response.status_code == 401 or response.status_code == 403:
			sys.exit("Toggl login failed")

		response.raise_for_status()

		# Parse toggl time entries json to python object
		timeEntries = response.json()
		# print(response.text)
		# Filter out entries that are tagged with 'logged'
		allEntries = [TogglTimeEntry(te) for te in timeEntries if "Logged" not in te.get('tags', [])]

		# Group entries by issue number with summed up duration
		return self.groupEntries(allEntries)
	# END def getTimeEntries()

	def postTag(self, timeEntryId):
		url = self.baseUrl + self.postTagRoute.replace('{timeEntryId}', str(timeEntryId))

		payload = {
			"time_entry": {
				"tags": ['logged'],
				"tag_action": "add"
			}
		}
		response = requests.put(url, json=payload, auth=self.auth)
		response.raise_for_status()
		print('TogglAPI: Time entry marked as logged')

	def groupEntries(self, entries):
		from collections import defaultdict
		groupBy = defaultdict(list)
		for entry in entries:
			groupBy[entry.issueNumber].append(entry)

		newList = []

		for issueNumber, group in groupBy.items():
			entry = group[0]
			sum = 0
			for entry in group:
				sum += entry.durationSeconds
			entry.durationMs = sum
			newList.append(entry)
		return newList
	# END def groupEntries(entries)

class TogglTimeEntry:
	def __init__(self, json):
		self.id = json['id']
		descriptionSplit = self.splitEntryDescription(json['description'])
		self.description = descriptionSplit['description']
		self.issueNumber = descriptionSplit['issueNumber']
		self.date = dateutil.parser.parse(json['start']).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
		self.durationSeconds = json['duration']
		self.remainingEstimateSeconds = -1

	def formatDuration(self):
		return formatSecondsToTimeString(self.durationSeconds)

	def formatRemainingEstimate(self):
		if self.remainingEstimateSeconds == -1:
			raise ValueError('Remaining estimate has no value')
		return formatSecondsToTimeString(self.remainingEstimateSeconds)



	def splitEntryDescription(self, description):
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
# END class TogglTimeEntry

class JiraAPI:
	"""docstring for JiraAPI."""
	def __init__(self):
		super(JiraAPI, self).__init__()
		self.baseUrl = 'https://sendiradid.atlassian.net'
		self.getIssueRoute = '/rest/api/2/issue/{issueNumber}'
		self.getMyselfRoute = '/rest/api/2/myself'
		self.postWorklogRoute = '/rest/tempo-timesheets/3/worklogs/'

	def authenticate(self):
		while True:
			username = input('Jira Username:')
			password = getpass.getpass('Jira Password:')
			self.auth = requests.auth.HTTPBasicAuth(username, password)

			response = requests.get(self.baseUrl + self.getMyselfRoute, auth=self.auth)
			if response.status_code == 200:
				print('Jira login successful\n')
				self.username = response.json()['key']
				break
			else:
				print('ERROR: Jira login was not successful, please try again\n')

	def getIssue(self, issueNumber):
		url = self.baseUrl + self.getIssueRoute.replace('{issueNumber}', issueNumber)
		payload = {
			'fields' : 'summary,description,timetracking,customfield_10002,io.tempo.jira__account'
		}
		response = requests.get(url, params=payload, auth=self.auth)
		if response.status_code == 401:
			sys.exit("Jira login failed")
		if response.status_code == 404:
			sys.exit('Could not find issue with number: "' + issueNumber + '"' )
		response.raise_for_status()
		
		return JiraIssue(response.json())

	def postWorklog(self, timeEntry):
		comment = ''
		remainingEstimateSeconds = 0

		if timeEntry.issueNumber == 'sen-14':
			comment = 'Matur'
			remainingEstimateSeconds = timeEntry.remainingEstimateSeconds
			print('Comment: ' + comment)
			print('Remaining estimate: ' + formatSecondsToTimeString(remainingEstimateSeconds))
		else:
			comment = input('Comment: ')
			remainingEstimateSeconds = self._inputRemainingEstimate(timeEntry.remainingEstimateSeconds)

		url = self.baseUrl + self.postWorklogRoute
		payload = {
			"issue": {
				"key": timeEntry.issueNumber.upper(),
				"remainingEstimateSeconds": remainingEstimateSeconds
			},
			"timeSpentSeconds": timeEntry.durationSeconds,
			"billedSeconds": timeEntry.durationSeconds,
			"dateStarted": timeEntry.date.isoformat().split('.')[0] + '.000',
			"comment": comment,
			"author": {
				"name": self.username
			},
			'workAttributeValues': [
				{
					'value': timeEntry.account,
					'workAttribute': {
						'id': 1,
						'key': '_Account_',
						'name': 'Account',
						'type': {
							'name': 'Account',
							'value': 'ACCOUNT',
						},
						'externalUrl': '/rest/tempo-rest/1.0/accounts/json/billingKeyList/{IssueKey}',
						'required': False,
						'sequence': 0
					}
				}
			]
		}
		response = requests.post(url, json=payload, auth=self.auth)
		
		response.raise_for_status()
		print('JiraAPI: Time entry for issue \'' + timeEntry.issueNumber + '\' successfully logged')

	def _inputRemainingEstimate(self, defaultValueSeconds):
		while True:
			remainingEstimateStr = input('Remaining estimate[' + formatSecondsToTimeString(defaultValueSeconds) + ']: ')

			if remainingEstimateStr == '':
				return defaultValueSeconds

			if remainingEstimateStr == '0':
				return 0

			reMatch = re.match( r'^(([0-9]+)h)?\s*(([0-9]+)m)?$', remainingEstimateStr) # todo suppord day?
			hours = 0
			minutes = 0
			seconds = 0

			if reMatch:
				if reMatch.group(2) is not None: hours = reMatch.group(2)
				if reMatch.group(4) is not None: minutes = reMatch.group(4)

				seconds = (int(hours) * 3600) + (int(minutes) * 60)
				return seconds
			else:
				print('Unsupported time string, try again')

# END class JiraAPI


class JiraIssue:
	"""docstring for JiraIssue."""
	def __init__(self, json):
		self.issueNumber = json['key']
		timetracking = json['fields'].get('timetracking')
		self.originalEstimate = timetracking.get('originalEstimate') if timetracking is not None else None
		self.remainingEstimate = timetracking.get('remainingEstimate') if timetracking is not None else None
		self.remainingEstimateSeconds = timetracking.get('remainingEstimateSeconds') if timetracking is not None else 0
		self.timeSpent = timetracking.get('timeSpent') if timetracking is not None else None
		self.summary = json['fields']['summary']
		self.description = json['fields']['description']

		accountField = json['fields'].get('customfield_10002')
		self.account = accountField.get('key') if accountField is not None else None

	def print(self):
		print('Jira Issue:         ' + self.issueNumber)
		print('Summary:            ' + self.summary)
		if self.originalEstimate is not None: print('Original Estimate:  ' + self.originalEstimate)
		if self.timeSpent is not None: print('Time Spent:         ' + self.timeSpent)
		if self.remainingEstimate is not None: print('Remaining Estimate: ' + self.remainingEstimate)
# END class JiraIssue



def main():

	date = None
	if len(sys.argv) > 1:
		try:
			dateString = sys.argv[1]

			date = datetime.datetime.strptime(dateString, '%d/%m/%Y')
		except ValueError:
			print("Date should be on the format dd/MM/yyyy")
			sys.exit(0)


	togglApi = TogglApi()
	togglApi.authenticate()

	jiraApi = JiraAPI()
	jiraApi.authenticate()

	timeEntries = togglApi.getTimeEntries(date)

	for entry in timeEntries:
		print('-----------------------------------------------------------------')
		entry.print()

		print('-----------------------------------------------------------------')

		jiraIssue = jiraApi.getIssue(entry.issueNumber)
		jiraIssue.print()
		
		print('-----------------------------------------------------------------')

		entry.remainingEstimateSeconds = jiraIssue.remainingEstimateSeconds - entry.durationSeconds if jiraIssue.remainingEstimateSeconds is not None else 0
		entry.remainingEstimateSeconds = entry.remainingEstimateSeconds if entry.remainingEstimateSeconds > 0 else 0
		entry.account = jiraIssue.account
		
		jiraApi.postWorklog(entry)
		togglApi.postTag(entry.id)
		print('-----------------------------------------------------------------\n')

# END def main()

if __name__ == "__main__":
	main()
