from unittest import TestCase

from engine.engine import Card
from engine.engine import Change


class TestChange(TestCase):
	def setUp(self):
		self.c = Change('get_card', 0, '12C', 0)

	def test_filter1(self):
		self.c.filter(0)
		self.assertEqual(self.c.card, '12C')

	def test_filter2(self):
		self.c.filter(1)
		self.assertEqual(self.c.card, None)


class TestCard(TestCase):
	def test_more(self):
		self.assertTrue(Card(1, 12).more(Card(2, 12), 1))

	def test_more2(self):
		self.assertTrue(Card(1, 12).more(Card(1, 10), 1))

	def test_more3(self):
		self.assertTrue(Card(1, 2).more(Card(2, 12), 1))
