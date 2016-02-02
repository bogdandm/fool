from unittest import TestCase

from server.database import *


class TestDB(TestCase):
	def test_check_user(self):
		x = check_user('root')
		self.assertTrue(x.uid == 1 and x.admin and x.activated)

	def test_check_email(self):
		self.assertTrue(check_email('bogdan.dm1995@yandex.ru'))

	def test_add_user_and_activate(self):
		add_user('user_for_test', '', '', 'test@test.ru')
		self.assertFalse(check_user('user_for_test').activated)
		self.assertTrue(check_email('test@test.ru'))
		exec_query("DELETE FROM users WHERE name='user_for_test'")
		self.assertTrue(check_user('user_for_test') is None)
		self.assertFalse(check_email('test@test.ru'))

