import aiohttp
import time
import datetime
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
	async with session.get(url) as response:
		return await response.text()


async def cache_or_load(url):
		if url not in cache or time.time() - cache[url][1] > 3600:
			async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
				string = await fetch(session, url=url)
				json = jsonify(string)
				cache[url] = (json, time.time())
				print(json)
				return json
		
		else:
			return cache[url][0]


async def search_json(url, field, query=None, get_all=False):
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
	heroes = await search_json(url=ROOT_URL + HEROES_URL, field='name', get_all=True)
	return heroes


async def get_todays_matches():
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
	
	while True:
		for i in groups:
			for j in i['matches']:
				# TODO: Rework asynchronous instantiation of these classes
				# More work needs to be done inside the constructor, and less work outside of it.
				left = await search_json(url=ROOT_URL + TEAMS_URL, field='id', query=j['left_team'])
				left = left[0]
				right = await search_json(url=ROOT_URL + TEAMS_URL, field='id', query=j['right_team'])
				right = right[0]
				match = Match({'left_team': left, 'right_team': right, 'format': j['format'], 'name': j['name'], 'datetime': j['datetime']})
				matches.append(match)
			
		break
	
	return matches


class Team:
	def __init__(self, data):
		try:
			team_data = data
			self.name = team_data['name']
			self.id = team_data['id']
			self.logo = team_data['logo']
			
		except IndexError as e:
			self.name = 'NO NAME'
			self.id = 'NO ID'
			self.logo = 'NO LOGO'
			

class Match:
	def __init__(self, data):
		self.left_team = Team(data['left_team'])
		self.right_team = Team(data['right_team'])
		self.format = data['format']
		self.when = data['datetime']
		self.name = data['name']
