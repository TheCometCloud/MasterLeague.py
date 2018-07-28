import aiohttp
import time
import datetime
import ssl
from urllib import request
from bs4 import BeautifulSoup
from json import loads as jsonify

ROOT_URL = 'https://api.masterleague.net'
HEROES_URL = '/heroes.json'
MATCHES_URL = '/matches.json'
TEAMS_URL = '/teams.json'
MAPS_URL = '/maps.json'
REGIONS_URL = '/region.json'
PATCHES_URL = '/patches.json'
PLAYERS_URL = '/players.json'
TOURNAMENTS_URL = '/tournaments.json'
CALENDAR_URL = '/calendar.json'

cache = {}
"""
A dictionary that binds urls to JSONs stored in memory and the time they were stored for quick processing.

Key: a url string
Value: a tuple of type (dict, float)
"""


async def fetch(session, url):
	"""
	Grabs api text from a url.
	
	:param session: aiohttp.ClientSession object
	:param url: string url of api
	:return: string response
	"""
	async with session.get(url) as response:
		return await response.text()


async def cache_or_load(url):
	"""
	Saves already found data to the cache and loads data from the api otherwise.
	:param url: string url of the api
	:return: string response
	"""
	if url not in cache or time.time() - cache[url][1] > 3600:
		async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
			string = await fetch(session, url=url)
			json = jsonify(string)
			cache[url] = (json, time.time())
			return json
	
	else:
		return cache[url][0]


async def search_json(url, field, query=None, get_all=False):
	"""
	Searches a json's results field and queries it, returning found matches.
	:param url: string url of the json
	:param field: string field name to compare
	:param query: query to compare with, None by default
	:param get_all: boolean to get every match, False by default
	:return: list of json dictionaries that matched, empty if no matches
	"""
	results = []
	json = await cache_or_load(url)

	while True:
		for i in json['results']:
			if query:
				if i[field] == query:
					results.append(i)
				
					if not get_all:
						return results
			else:
				results.append(i[field])
				
		if not json['next']:
			break
		
		json = await cache_or_load(json['next'])
	
	return results


async def get_all_heroes():
	"""
	Gets a list of all heroes
	:return: list of hero name strings
	"""
	heroes = await search_json(url=ROOT_URL + HEROES_URL, field='name', get_all=True)
	return heroes


async def get_todays_matches():
	"""
	Gets all matches occurring today in the blizzard professional scene.
	:return: list of Match objects
	"""
	groups = []
	matches = []
	json = await cache_or_load(ROOT_URL + CALENDAR_URL)
	
	while True:
		if json['results']:
			for i in json['results']:
				if str(datetime.datetime.today()).split(' ')[0] in i['date']:
					groups.append(i)
			
		if not json['next']:
			break
		
		json = await cache_or_load(json['next'])
	
	for i in groups:
		for j in i['matches']:
			# TODO: Rework asynchronous instantiation of these classes
			# More work needs to be done inside the constructor, and less work outside of it.
			j['left_team'] = (await search_json(url=ROOT_URL + TEAMS_URL, field='id', query=j['left_team']))[0]
			j['right_team'] = (await search_json(url=ROOT_URL + TEAMS_URL, field='id', query=j['right_team']))[0]
			match = Match(j)
			matches.append(match)
			
	return matches


async def find_team(name):
	"""
	Given a team name, finds its data.
	:param name: string team name
	:return: Team object, filled with nones if the team was not found
	"""
	team_data = {}
	try:
		team_data = (await search_json(url=ROOT_URL + TEAMS_URL, field='name', query=name))[0]
		
	except IndexError:
		pass
		
	team = Team(team_data)
	return team


class Team:
	"""
	Team object for storing data about particular teams.
	"""
	def __init__(self, data):
		try:
			team_data = data
			self.name = team_data['name']
			self.id = team_data['id']
			self.logo = team_data['logo']
			self.region = team_data['region']
			
		except (IndexError, KeyError):
			self.name = 'NO NAME'
			self.id = 'NO ID'
			self.logo = 'NO LOGO'
			self.region = 0
			
	async def get_record(self):
		"""
		Fetches the record of the team in an ongoing tourney.
		:return: tuple of format (wins, losses) or None if there is no win/loss data
		"""
		tourneys = await search_json(url=ROOT_URL + TOURNAMENTS_URL, field='region', query=self.region, get_all=True)
		event = None
		for tournament in tourneys:
			if datetime.datetime.strptime(
					tournament['start_date'], "%Y-%m-%d").date() \
					< datetime.date.today() \
					< datetime.datetime.strptime(tournament['end_date'], "%Y-%m-%d").date():
				event = tournament
				break
				
		if event:
			standing = None
			url = ''
			for i in event['stages']:
				if i['name'] == 'Standings':
					url = f'https://masterleague.net/tournament/stage/{i["id"]}/'
			
			if url:
				context = ssl._create_unverified_context()
				source = request.urlopen(url, context=context).read()
				soup = BeautifulSoup(source, 'lxml')
				
				table = soup.find('table', attrs={'class': 'table table-hover table-condensed table-fixed standings'})
				table_rows = table.find_all('tr')
				
				data = []
				for tr in table_rows:
					td = tr.find_all('td')
					row = [tr.text for tr in td]
					data.append(row)
					
				for line in data:
					if len(line) >= 3:
						if line[0] == self.name:
							return line[1], line[2]
						
		return None


class Match:
	"""
	Match object for storing data about a particular match.
	"""
	def __init__(self, data):
		self.left_team = Team(data['left_team'])
		self.right_team = Team(data['right_team'])
		self.format = data['format']
		self.when = data['datetime']
		self.name = data['name']
	