import random
import time
from hashlib import sha256

from mysql.connector import connect, Error

from server.const import Dummy


# Full static class
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
	def query(query, connection=None):
		connection_ = connection if connection is not None else DB.connect()
		cursor = connection_.cursor()
		try:
			cursor.execute(query)
		except Error as e:
			raise e
		finally:
			connection_.commit()
			cursor.close()
			if connection is None:
				connection_.close()
		return True

	@staticmethod
	def check_user(user_name: str, password: str = None):
		if user_name is None:
			return False
		connection = DB.connect()
		try:
			cursor = connection.cursor()
			query = "SELECT id, file_extension, is_activated, is_admin FROM users WHERE name='%s'" % user_name
			if password is not None:
				query += "and pass_sha256='%s'" % password
			cursor.execute(query)
			row = cursor.fetchone()
			if row is not None:
				obj = Dummy()
				(obj.uid, obj.file, obj.activated, obj.admin) = row
			else:
				obj = None
		except Error as e:
			raise e
		finally:
			connection.close()
		return obj

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
			raise e
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
		c = DB.connect()
		DB.query("DELETE FROM sessions WHERE user_id=%i" % uid, c)
		DB.query("INSERT INTO sessions VALUES ('%s', %i)" % (s.get_id(), uid), c)
		c.close()

	@staticmethod
	def delete_session(id):
		DB.query("DELETE FROM sessions WHERE id='%s'" % id)

	@staticmethod
	def get_sessions():
		connection = DB.connect()
		try:
			cursor = connection.cursor()
			query = "SELECT users.name, users.is_activated, users.id, sessions.id, users.is_admin" \
					" FROM sessions INNER JOIN users ON users.id = sessions.user_id"
			cursor.execute(query)
			while True:
				row = cursor.fetchone()
				if row:
					obj = Dummy()
					(obj.name, obj.activated, obj.uid, obj.id, obj.admin) = row
					yield obj
				else:
					break
		except Error as e:
			raise e
		finally:
			connection.close()

	@staticmethod
	def write_log_record(ip, url, method, status):
		DB.query("INSERT INTO log VALUES (DEFAULT, NULL, '%s', '%s', '%s', '%s', DEFAULT)" % (url, method, status, ip))

	@staticmethod
	def write_log_msg(msg):
		DB.query("INSERT INTO log VALUES (DEFAULT, '%s', NULL, NULL, NULL, NULL, DEFAULT)" % msg)

	@staticmethod
	def activate_account(token):
		DB.query("UPDATE users SET is_activated=TRUE WHERE activation_code='%s'" % token)

		connection = DB.connect()
		try:
			cursor = connection.cursor()
			query = "SELECT name, id, file_extension, is_activated FROM users WHERE activation_code='%s'" % token
			cursor.execute(query)
			res = Dummy()
			(res.name, res.uid, res.file, res.activated) = cursor.fetchone()
		except Error as e:
			raise e
		finally:
			connection.close()
		return res

	@staticmethod
	def get_email_adress(user):
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
			raise e
		finally:
			connection.close()
		return res

	@staticmethod
	def get_friends(user=None, uid=None, accepted=1):
		if user is not None:
			uid = DB.check_user(user).uid

		connection = DB.connect()
		try:
			cursor = connection.cursor()
			query = """SELECT y.id, name, file_extension
				  	FROM (SELECT user id, accepted
					      FROM friends
					      WHERE friend = %i
					      UNION
					      SELECT friend id, accepted
					      FROM friends
					      WHERE user = %i
					     ) y
					INNER JOIN users ON y.id = users.id
					WHERE accepted = %i
					ORDER BY name""" % (uid, uid, accepted)
			cursor.execute(query)
			while True:
				res = cursor.fetchone()
				if res:
					yield res
				else:
					break
		except Error as e:
			raise e
		finally:
			connection.close()

	@staticmethod
	def get_mutual_friends(you: int, other: int, connection_=None):
		connection = DB.connect() if connection_ is None else connection_
		try:
			cursor = connection.cursor()
			query = """SELECT U.name, Y.id
					FROM (
						SELECT *
						FROM (SELECT USER id
							FROM friends
							WHERE friend = %i
							UNION
							SELECT friend id
							FROM friends
							WHERE USER = %i) F1
						WHERE id IN (
								SELECT USER id
								FROM friends
								WHERE friend = %i
								UNION
								SELECT friend id
								FROM friends
								WHERE USER = %i
						)
					) Y INNER JOIN users U ON Y.id = U.id""" % (you, you, other, other)
			cursor.execute(query)
			while True:
				res = cursor.fetchone()
				if res:
					yield res
				else:
					break
		except Error as e:
			raise e
		finally:
			if connection_ is None:
				connection.close()

	@staticmethod
	def find_user(user):
		connection = DB.connect()
		try:
			cursor = connection.cursor()
			query = "SELECT id, name, file_extension FROM users U WHERE name LIKE '%s%%' ORDER BY name" % user  # LIMIT 50
			cursor.execute(query)
			while True:
				res = cursor.fetchone()
				if res:
					yield res
				else:
					break
		except Error as e:
			raise e
		finally:
			connection.close()

	@staticmethod
	def invite_friend(user: str, friend: str):
		pass # TODO

	@staticmethod
	def accept_invite(user: str, friend: str):
		pass # TODO

	@staticmethod
	def reject_invite(user: str, friend: str):
		pass # TODO