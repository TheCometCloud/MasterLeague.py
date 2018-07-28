import unittest
import Getter
import asyncio


class GetterTestCase(unittest.TestCase):
	
	def setUp(self):
		self.loop = asyncio.get_event_loop()
		
	def tearDown(self):
		del self.loop
	
	def test_get_heroes(self):
		heroes = self.loop.run_until_complete(Getter.get_all_heroes())
		self.assertTrue('Abathur' in heroes)
		
	def test_get_games(self):
		matches = self.loop.run_until_complete(Getter.get_todays_matches())
		self.assertTrue(len(matches) > 0)
		
	def test_get_record(self):
		team = Getter.Team({
			'id': 29,
			'region': 2,
			'logo': 'https://c.masterleague.net/media/team/logo/1515844114.jpg.300x300_q85.jpg',
			'name': 'Tempo Storm'
		})
		self.loop.run_until_complete(team.get_record())
		self.assertTrue(team)
		
	def test_find_team_by_name(self):
		name = 'Tempo Storm'
		team = self.loop.run_until_complete(Getter.find_team(name))
		self.assertTrue(team.name == name)
		
	def test_returns_none(self):
		name = 'Theres no way that this is a team name.'
		team = self.loop.run_until_complete(Getter.find_team(name))
		self.assertTrue(team.name == 'NO NAME')
		
		
if __name__ == '__main__':
	unittest.main()
