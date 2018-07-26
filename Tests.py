import unittest
import Getter
import asyncio


class GetterTestCase(unittest.TestCase):
	
	def setUp(self):
		self.loop = asyncio.get_event_loop()
	
	def test_get_heroes(self):
		heroes = self.loop.run_until_complete(Getter.get_all_heroes())
		self.assertTrue('Abathur' in heroes)
		
		
if __name__ == '__main__':
	unittest.main()
