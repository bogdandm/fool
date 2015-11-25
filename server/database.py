import time
import random
from hashlib import sha256

from mysql.connector import connect, Error


# Полностью статический класс для взаимодействия с БД
class DB:
	config = {
		'user': 'python_flask',
		'password': '11061995',
		'host': '127.0.0.1',
		'database': 'fool_db'
	}

	@staticmethod
	def connect():
		return connect(**DB.config)

	@staticmethod
	def query(query):
		connection = DB.connect()
		cursor = connection.cursor()
		try:
			cursor.execute(query)
		except Error as e:
			return e
		finally:
			connection.commit()
			cursor.close()
			connection.close()
			return True

	@staticmethod
	def check_user(user_name: str, password: str=None) -> (bool, int):
		if user_name is None:
			return False
		connection = DB.connect()
		try:
			cursor = connection.cursor()
			query = "SELECT id, file_extension, is_activated FROM users WHERE name='%s'" % user_name
			if password is not None:
				query += "and pass_sha256='%s'" % password
			cursor.execute(query)
			row = cursor.fetchone()
			if row is not None:
				(uid, file, activated) = row
			else:
				uid = file = activated = None
			res = (cursor.rowcount > 0)
		except Error as e:
			return e
		finally:
			connection.close()
		return (res, uid, file, activated)

	@staticmethod
	def check_email(email: str) -> bool:
		if email is None:
			return False
		connection = DB.connect()
		try:
			cursor = connection.cursor()
			query = "SELECT * FROM users WHERE email='%s'" % email
			cursor.execute(query)
			cursor.fetchone()
			res = (cursor.rowcount > 0)
		except Error as e:
			return e
		finally:
			connection.close()
		return res

	@staticmethod
	def add_user(user_name, password, avatar: str, email) -> (str, bool):
		random.seed(time.time() * 256)
		activation_code = sha256(bytes(
			user_name + int(time.time() * 256).__str__() + random.randint(0, 2 ** 20).__str__() + 'email activation',
			encoding='utf-8'
		)).hexdigest()
		return (activation_code, DB.query(
			"INSERT INTO users(name, pass_sha256, email, has_avatar, activation_code, file_extension) "
			"VALUES ('%s', '%s', '%s', %s, '%s', '%s')" %
			(user_name, password, email, (avatar is not None).__str__(), activation_code, avatar)
		))

	@staticmethod
	def add_session(s, uid):
		DB.query("DELETE FROM sessions WHERE user_id=%i" % uid)
		DB.query("INSERT INTO sessions VALUES ('%s', %i)" % (s.get_id(), uid))

	@staticmethod
	def get_sessions():
		connection = DB.connect()
		try:
			cursor = connection.cursor()
			query = "SELECT users.name, users.is_activated, sessions.id" \
					" FROM sessions INNER JOIN users ON users.id = sessions.user_id"
			cursor.execute(query)
			res = cursor.fetchall()
		except Error as e:
			return e
		finally:
			connection.close()
		return res

	@staticmethod
	def write_log_record(ip, url, method, status):
		DB.query("INSERT INTO log VALUES (DEFAULT, NULL, '%s', '%s', '%s', '%s', DEFAULT)" % (url, method, status, ip))

	@staticmethod
	def write_log_msg(msg):
		DB.query("INSERT INTO log VALUES (DEFAULT, '%s', NULL, NULL, NULL, NULL, DEFAULT)" % msg)

	@staticmethod
	def activate_account(token):
		"""
		:rtype : (name, uid, file_ext, activated)
		"""
		DB.query("UPDATE users SET is_activated=TRUE WHERE activation_code='%s'" % token)

		connection = DB.connect()
		try:
			cursor = connection.cursor()
			query = "SELECT name, id, file_extension, is_activated FROM users WHERE activation_code='%s'" % token
			cursor.execute(query)
			res = cursor.fetchone()
		except Error as e:
			return e
		finally:
			connection.close()
		return res

	@staticmethod
	def get_email(user):
		random.seed(time.time() * 256)
		activation_code = sha256(bytes(
			user + int(time.time() * 256).__str__() + random.randint(0, 2 ** 20).__str__() + 'email activation',
			encoding='utf-8'
		)).hexdigest()

		DB.query("UPDATE users SET activation_code='%s' WHERE name='%s'" % (activation_code, user))

		connection = DB.connect()
		try:
			cursor = connection.cursor()
			query = "SELECT email, activation_code FROM users WHERE name='%s'" % user
			cursor.execute(query)
			res = cursor.fetchone()
		except Error as e:
			return e
		finally:
			connection.close()
		return res
