import random
import time
from hashlib import sha256

from mysql.connector import connect, Error

from server.const import Dummy


def connect_():
	config = {
		'user': 'python_flask',
		'password': '11061995',
		'host': '127.0.0.1',
		'database': 'fool_db'
	}
	return connect(**config)


def exec_query(query, connection=None):
	connection_ = connection if connection is not None else connect_()
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


def check_user(user_name: str, sha256: str = None):
	if user_name is None:
		return False
	connection = connect_()
	try:
		cursor = connection.cursor()
		query = "SELECT id, file_extension, is_activated, is_admin, email FROM users WHERE BINARY name='%s'" % user_name
		if sha256 is not None:
			query += "and pass_sha256='%s'" % sha256
		cursor.execute(query)
		row = cursor.fetchone()
		if row is not None:
			obj = Dummy()
			(obj.uid, obj.file, obj.activated, obj.admin, obj.email) = row
		else:
			obj = None
	except Error as e:
		raise e
	finally:
		connection.close()
	return obj


def check_email(email: str) -> bool:
	if email is None:
		return False
	connection = connect_()
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


def add_user(user_name, sha256, avatar: str, email) -> (str, bool):
	random.seed(time.time() * 256)
	activation_code = sha256(bytes(
		user_name + int(time.time() * 256).__str__() + random.randint(0, 2 ** 20).__str__() + 'email activation',
		encoding='utf-8'
	)).hexdigest()
	return (activation_code, exec_query(
		"INSERT INTO users(name, pass_sha256, email, has_avatar, activation_code, file_extension) "
		"VALUES ('%s', '%s', '%s', %s, '%s', '%s')" %
		(user_name, sha256, email, (avatar is not None).__str__(), activation_code, avatar)
	))


def set_avatar_ext(user, ext):
	exec_query("UPDATE users SET file_extension='%s' WHERE name='%s'" % (ext, user))

def set_new_pass(user, sha256):
	exec_query("UPDATE users SET pass_sha256='%s' WHERE name='%s'" % (sha256, user))


def add_session(s, uid):
	c = connect_()
	exec_query("DELETE FROM sessions WHERE user_id=%i" % uid, c)
	exec_query("INSERT INTO sessions VALUES ('%s', %i)" % (s.get_id(), uid), c)
	c.close()


def delete_session(id):
	exec_query("DELETE FROM sessions WHERE id='%s'" % id)


def get_sessions():
	connection = connect_()
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


def write_log_record(ip, url, method, status):
	exec_query("INSERT INTO log VALUES (DEFAULT, NULL, '%s', '%s', '%s', '%s', DEFAULT)" % (url, method, status, ip))


def write_log_msg(msg):
	exec_query("INSERT INTO log VALUES (DEFAULT, '%s', NULL, NULL, NULL, NULL, DEFAULT)" % msg)


def activate_account(token):
	exec_query("UPDATE users SET is_activated=TRUE WHERE activation_code='%s'" % token)

	connection = connect_()
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


def get_email_adress(user):
	random.seed(time.time() * 256)
	activation_code = sha256(bytes(
		user + int(time.time() * 256).__str__() + random.randint(0, 2 ** 20).__str__() + 'email activation',
		encoding='utf-8'
	)).hexdigest()

	exec_query("UPDATE users SET activation_code='%s' WHERE name='%s'" % (activation_code, user))

	connection = connect_()
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


def get_friends(user=None, uid=None, accepted=1):
	if user is not None:
		uid = check_user(user).uid

	connection = connect_()
	try:
		cursor = connection.cursor()
		if accepted:
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
				WHERE accepted = 1
				ORDER BY name""" % (uid, uid)
		else:
			query = """SELECT y.id, name, file_extension
				FROM ( SELECT user id, accepted
					   FROM friends
					   WHERE friend = %i
					 ) y
				  INNER JOIN users ON y.id = users.id
				WHERE accepted = 0
				ORDER BY name""" % uid
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


def is_friend(user: str, friend: str):
	connection = connect_()
	try:
		cursor = connection.cursor()
		query = """SELECT * FROM friends
		WHERE user IN (SELECT id FROM users WHERE name = '%s' UNION SELECT id FROM users WHERE name = '%s')
		AND friend IN (SELECT id FROM users WHERE name = '%s' UNION SELECT id FROM users WHERE name = '%s')
		""" % (user, friend, user, friend)
		cursor.execute(query)
		res = cursor.fetchone()
	except Error as e:
		res = False
	finally:
		connection.close()
	return bool(res)


def get_mutual_friends(you: int, other: int, connection_=None):
	connection = connect_() if connection_ is None else connection_
	try:
		cursor = connection.cursor()
		query = """SELECT U.name, Y.id
				FROM (
					SELECT *
					FROM (SELECT user id
						FROM friends
						WHERE friend = %i
						UNION
						SELECT friend id
						FROM friends
						WHERE user = %i) F1
					WHERE id IN (
							SELECT user id
							FROM friends
							WHERE friend = %i
							UNION
							SELECT friend id
							FROM friends
							WHERE user = %i
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


def find_user(user):
	connection = connect_()
	try:
		cursor = connection.cursor()
		query = """
			SELECT id, name, file_extension FROM users WHERE name = '%s'
			UNION
			SELECT id, name, file_extension FROM users WHERE name LIKE '%s%%' ORDER BY name LIMIT 50
		""" % (user, user)
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


def invite_friend(user: str, friend: str):
	exec_query("""
		INSERT INTO friends (id, user, friend, accepted) VALUES (
		  DEFAULT,
		  (SELECT id FROM users WHERE name = '%s'),
		  (SELECT id FROM users WHERE name = '%s'),
		  0)""" % (user, friend))


def accept_invite(user: str, friend: str):
	exec_query("""UPDATE friends SET accepted=1
		WHERE user IN (SELECT id FROM users WHERE name = '%s' UNION SELECT id FROM users WHERE name = '%s')
		AND friend IN (SELECT id FROM users WHERE name = '%s' UNION SELECT id FROM users WHERE name = '%s')"""
			   % (user, friend, user, friend))


def reject_invite(user: str, friend: str):
	exec_query("""DELETE FROM friends
		WHERE user IN (SELECT id FROM users WHERE name = '%s' UNION SELECT id FROM users WHERE name = '%s')
		AND friend IN (SELECT id FROM users WHERE name = '%s' UNION SELECT id FROM users WHERE name = '%s')"""
			   % (user, friend, user, friend))
