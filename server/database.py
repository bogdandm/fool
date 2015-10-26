from mysql.connector import connect, Error


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
	def check_user(user_name, password=None) -> bool:
		if user_name is None:
			return False
		connection = DB.connect()
		try:
			cursor = connection.cursor()
			query = "SELECT * FROM users WHERE name='%s'" % user_name
			if password is not None:
				query += "and pass_sha256='%s'" % password
			cursor.execute(query)
			cursor.fetchall()
			res = (cursor.rowcount > 0)
		except Error as e:
			return e
		finally:
			connection.close()
		return res

	@staticmethod
	def add_user(user_name, password):
		if user_name is None or password is None:
			return 'Wrong arguments'
		connection = DB.connect()
		try:
			cursor = connection.cursor()
			query = "INSERT INTO users(name, pass_sha256) VALUES ('%s', '%s')" % (user_name, password)
			cursor.execute(query)
		except Error as e:
			return e
		finally:
			connection.close()
			return 'OK'
