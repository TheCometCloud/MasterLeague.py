import requests
import time
import datetime

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


def cache_or_load(url):
	if url not in cache or time.time() - cache[url][1] > 3600:
		json = requests.get(url=url).json()
		cache[url] = (json, time.time())
		return json
		
	else:
		return cache[url][0]


def search_json(url, field, query=None, get_all=False):
	results = []
	json = cache_or_load(url)

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
		
		json = cache_or_load(json['next'])
	
	return results


def get_all_heroes():
	heroes = search_json(url=ROOT_URL + HEROES_URL, field='name', get_all=True)
	return heroes


def get_todays_matches():
	groups = []
	matches = []
	json = cache_or_load(ROOT_URL + CALENDAR_URL)
	
	while True:
		for i in json['results']:
			if str(datetime.datetime.today()).split(' ')[0] in i['date']:
				groups.append(i)
		
		if not json['next']:
			break
		
		json = cache_or_load(json['next'])
	
	while True:
		for i in groups:
			for j in i['matches']:
				match = Match(j)
				matches.append(match)
			
		break


class Team:
	def __init__(self, id):
		url = ROOT_URL + TEAMS_URL
		try:
			team_data = search_json(url=url, field='id', query=id)[0]
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


get_todays_matches()
