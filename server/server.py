# -*- coding: utf-8 -*-
import hashlib
import os
from datetime import datetime, timedelta
from json import dumps
from re import search
from types import GeneratorType

import gevent
from flask import Flask, Response, make_response, request, redirect, render_template, send_from_directory
from gevent.queue import Queue
from werkzeug.contrib.cache import SimpleCache

import server.const as const
import server.email as email_
from server.database import DB
from server.server_classes import RoomPvE, RoomPvP, Session, Logger


# TODO: write session documentation
class Server:
	service_pages = [
		'\/api\/ping(\?data=[0-9]+)?$',
		'\/api\/getRequestPerSec$',
		'\/api\/get_table\?(table=.+)$'
	]

	def __init__(self, ip, domain=None, seed=None):
		self.ip = ip
		self.domain = domain if domain != '' else None
		self.app = Flask(__name__)
		self.app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

		self.sessions = dict()
		self.sessions_by_user_name = dict()
		for obj in DB.get_sessions():
			s = Session(obj.name, obj.activated, obj.uid, obj.id, obj.admin)
			self.sessions[obj.id] = s
			self.sessions_by_user_name[obj.name] = s
		self.rooms = dict()
		self.logger = Logger()
		self.logger.write_msg('==Server run at %s==' % ip)
		self.seed = seed
		self.cache = SimpleCache(default_timeout=60 * 60 * 24 * 30)

		def update_status(this):
			while True:
				delta = timedelta(minutes=5)
				now = datetime.now()
				for s in this.sessions.values():
					if not s.last_request or (s.last_request + delta < now and s.status == Session.ONLINE):
						s.status = Session.OFFLINE
				gevent.sleep(5 * 60 + 1)

		gevent.spawn(update_status, self)

		@self.app.after_request
		def after_request(response):
			session = self.get_session(request)
			if session:
				session['ip'] = request.remote_addr
				session.last_request = datetime.now()
				if session.status == Session.OFFLINE:
					session.status = Session.ONLINE
			if const.FILTRATE_REQUEST_FOR_LOG:
				for item in self.service_pages:
					if search(item, request.url):
						break
				else:
					self.logger.write_record(request, response)
			else:
				self.logger.write_record(request, response)
			return response

		@self.app.route('/')  # static
		def send_root():
			session = self.get_session(request)
			if session:
				name = session.user
				return render_template('main_menu.html', user_name=name, admin=bool(session.admin))
			elif session is None:
				return redirect('/static/login.html')
			else:
				session = self.sessions[request.cookies['sessID']]
				session.update_activation_status()
				return redirect('/static/errors/not_activated.html')

		@self.app.route('/static_/svg/<path:path>')  # static
		def send_svg(path):
			data = self.cache.get(path)
			if data is None:
				data = open("./server/static/svg/" + path).read()
				self.cache.set(path, data)
			response = make_response(data)
			response.headers["Content-type"] = "image/svg+xml"
			response.headers["Cache-Control"] = "max-age=1000000, public"
			return response

		@self.app.route('/favicon.ico')  # static
		def send_favicon():
			return send_from_directory(
				os.path.join(self.app.root_path, 'static'),
				'favicon.ico', mimetype='image/vnd.microsoft.icon'
			)

		@self.app.errorhandler(404)
		def page_not_found(e):
			return send_from_directory(
				os.path.join(self.app.root_path, 'static'),
				'errors/404.html', mimetype='text/html'
			), 404

		@self.app.errorhandler(400)
		def page_not_found(e):
			return send_from_directory(
				os.path.join(self.app.root_path, 'static'),
				'errors/400.html', mimetype='text/html'
			), 400

		@self.app.errorhandler(500)
		def page_not_found(e):
			return send_from_directory(
				os.path.join(self.app.root_path, 'static'),
				'errors/500.html', mimetype='text/html'
			), 500

		@self.app.route('/api')  # static
		def send_api_methods():
			# TODO: rewrite documentation
			return redirect('/static/api_methods.html')

		@self.app.route('/arena')  # static; need: get@mode
		def send_arena():
			return redirect('/static/arena.html?mode=' + request.args.get('mode'))

		@self.app.route('/static/server_statistic.html')  # static; need: session@admin
		def send_server_statistic_file():
			session = self.get_session(request)
			if session:
				if self.get_session(request).admin:
					file = open(const.SERVER_FOLDER + const.STATIC_FOLDER + '/server_statistic.html',
								encoding='utf-8').read()
					response = make_response(file)
					response.headers["Content-type"] = "text/html"
					return response
				else:
					return 'Permission denied'
			else:
				return redirect('/')

		@self.app.route('/api/activate_account')  # need: get@token
		def activate_account():
			token = request.args.get('token')
			if not search('^[a-zA-Z0-9]+$', token):
				return 'Bad token'
			result = DB.activate_account(token)
			if result is None:
				return 'Bad token'

			session = Session(result.name, result.activated, result.uid)
			self.sessions[session.get_id()] = session
			session['avatar'] = result.file
			DB.add_session(session, result.uid)

			response = redirect('/')
			session.add_cookie_to_resp(response)
			return response

		@self.app.route('/api/resend_email')  # need: session
		def resend_email():
			if 'sessID' in request.cookies and request.cookies['sessID'] in self.sessions:
				session = self.sessions[request.cookies['sessID']]
			else:
				return 'Fail', 401

			(email, activation_token) = DB.get_email_adress(session.user)
			email_.send_email(
				"Для подтвеждения регистрации пожалуйста перейдите по ссылке "
				"http://{domain}/api/activate_account?token={token}".format(
					domain=(self.domain if self.domain is not None else self.ip),
					token=activation_token
				),
				"Account activation",
				email
			)
			return 'OK'

		@self.app.route("/api/subscribe_allow")
		def subscribe_allow():
			session = self.get_session(request)
			if not session:
				return 'Fail', 401
			return 'False' if 'cur_room' in session.data else 'True'

		@self.app.route("/api/subscribe")  # need: session
		def subscribe():  # Create queue for updates from server
			def gen(sess_id):
				q = Queue()
				session = self.sessions[sess_id]
				session['msg_queue'] = q

				def notify():
					q.put('init')

				gevent.spawn(notify)

				while True:  # MainLoop for SSE, use threads
					result = q.get()
					if str(result) != 'stop':
						ev = ServerSentEvent(str(result))
						yield ev.encode()
					else:
						break
				if q is session['msg_queue']:
					del session['msg_queue']
				del q

			session = self.get_session(request)
			if not session:
				return 'Fail', 401
			session.status = Session.PLAY

			return Response(gen(session.id), mimetype="text/event-stream")

		@self.app.route("/api/unsubscribe")  # need: session@msg_queue
		def unsubscribe():
			session = self.get_session(request)
			if not session:
				response = make_response('Fail', 401)
				response.headers["Cache-Control"] = "no-store"
				return response

			def notify():
				session['msg_queue'].put('stop')

			if 'msg_queue' in session.data:
				gevent.spawn(notify)

			session.status = Session.ONLINE
			room = session['cur_room']
			response = make_response('OK')
			response.headers["Cache-Control"] = "no-store"
			if room is None:
				return response
			room_id = room.id
			if room.type == const.MODE_PVE:
				del self.rooms[room_id]
				del session['cur_room']
				del room

				return response
			elif room.type == const.MODE_PVP:
				if room.is_ready():
					room.remove_player(session['player_n'])
					self.merge_room(room)
				else:
					del self.rooms[room_id]
					del room
				del session['cur_room']

				return response

		@self.app.route("/api/join")  # need: session@msg_queue, get@mode
		def join_room():
			session = self.get_session(request)
			if not self.get_session(request):
				return 'Fail', 401

			mode = int(request.args.get('mode'))
			if mode == const.MODE_PVE:
				room = RoomPvE(session, seed=self.seed)
				self.rooms[room.id] = session['cur_room'] = room
				session['player_n'] = const.PLAYER_HAND
				room.send_player_inf()
				room.send_changes()
			elif mode == const.MODE_PVP:
				for room in self.rooms.values():
					if room.type == const.MODE_PVP and not room.is_ready():
						break
				else:
					room = RoomPvP(seed=self.seed)
					self.rooms[room.id] = room

				session['player_n'] = room.add_player(session)
				session['cur_room'] = room
				if room.is_ready():
					room.send_player_inf()
					room.send_changes()
					room.send_msg(dumps({
						'data': [{
							'type': 'wait',
							'player': room.game.turn,
							'card': None,
							'inf': None
						}]
					}))
				else:
					room.send_msg('wait')

			return 'OK'

		@self.app.route("/api/attack", methods=['GET'])  # need: session@cur_room, get@card
		def attack():
			session = self.get_session(request)
			if not session:
				return 'Fail', 401

			room = session['cur_room']
			card = int(request.args.get('card'))
			result = room.attack(session['player_n'], card)
			if result == 'END':
				room_id = room.id
				if room.type == const.MODE_PVE:
					del self.rooms[room_id]
					del session['cur_room']
					return 'OK'
			return result

		@self.app.route("/api/defense", methods=['GET'])  # need: session@cur_room, get@card
		def defense():
			session = self.get_session(request)
			if not session:
				return 'Fail', 401

			room = session['cur_room']
			card = int(request.args.get('card'))
			result = room.defense(session['player_n'], card)
			if result == 'END':
				room_id = room.id
				if room.type == const.MODE_PVE:
					del self.rooms[room_id]
					del session['cur_room']
					return 'OK'
			return result

		@self.app.route("/api/chat", methods=['POST'])  # need: session@cur_room, post@msg
		def send_msg_to_chat():
			session = self.get_session(request)
			if not session:
				return 'Fail', 401

			room = session['cur_room']
			msg = request.form.get('msg')

			room.send_msg(dumps({
				'msg': msg,
				'from': session.user,
				'hand': session['player_n']
			}))

			return 'OK'

		@self.app.route("/api/check_user", methods=['POST'])  # -> bool or Error
		# (need: post@user_name; maybe: post@pass) XOR need: post@email
		def check_user():
			password = request.form.get('pass')
			sha256 = hashlib.sha256(bytes(password, encoding='utf-8')).hexdigest() if password is not None else None
			email = request.form.get('email')
			name = request.form.get('name')

			if name is not None:
				result = DB.check_user(name, sha256)
				response = make_response((not result).__str__())
			elif email is not None:
				result = DB.check_email(email)
				response = make_response((not result).__str__())
			else:
				response = make_response('Bad request', 400)
			response.headers["Content-type"] = "text/plain"
			return response

		@self.app.route("/api/avatar", methods=['GET'])
		# need: get@user; maybe: get@source := menu | any
		def get_avatar():
			user = request.args.get('user')
			if user == 'AI' or user == 'root':
				if request.args.get('source') == 'menu':
					return "/static_/svg/ic_computer_24px.svg"
				else:
					return "/static_/svg/ic_computer_24px_white.svg"
			file_ext = DB.check_user(user).file
			if file_ext is not None and file_ext != 'None':
				return "/static/avatar/{user_name}{file_ext}".format(user_name=user, file_ext=file_ext)
			else:
				if request.args.get('source') == 'menu':
					return "/static_/svg/ic_person_24px.svg"
				else:
					return "/static_/svg/ic_person_24px_white.svg"

		@self.app.route("/api/add_user", methods=['POST'])
		# need: post@user_name, post@pass, post@email; maybe: post@file(image)
		def add_user():
			sha256 = hashlib.sha256(bytes(request.form.get('pass'), encoding='utf-8')).hexdigest()
			name = request.form.get('name')
			email = request.form.get('email')

			result = not DB.check_user(name) and not DB.check_email(email)

			if not (search('^.+@.+\..+$', email) and search('^[a-zA-Z0-9_]+$', name) and result):
				return make_response('Wrong data', 400)

			if request.files:
				file = request.files['file']
				if file.mimetype in const.IMAGES:
					file_ext = const.IMAGES[file.mimetype]
					file.save("./server/static/avatar/{}{}".format(name, file_ext))
				else:
					return make_response('Wrong data', 400)
			else:
				file_ext = None

			(activation_token, result) = DB.add_user(name, sha256, file_ext, email)

			if result:
				response = make_response('OK')

				result2 = DB.check_user(name, sha256)
				if result2:
					session = Session(name, result2.activated, result2.uid)
					self.sessions[session.get_id()] = session
					session['avatar'] = result2.file
					DB.add_session(session, result2.uid)
					session.add_cookie_to_resp(response)

					email_.send_email(
						"Для подтвеждения регистрации пожалуйста перейдите по ссылке "
						"http://{domain}/api/activate_account?token={token}".format(
							domain=(self.domain if self.domain is not None else self.ip),
							token=activation_token
						),
						"Account activation",
						email)
				else:
					self.logger.write_msg("Something wrong with registration ({})".format(name))

				response.headers["Content-type"] = "text/plain"
				return response
			else:
				return 'Error', 500

		@self.app.route("/api/init_session", methods=['POST'])
		# need: post@user_name, post@pass
		def init_session():
			if self.get_session(request) is not None:
				response = make_response('OK')
				response.headers["Content-type"] = "text/plain"
				return response

			user_name = request.form.get('user_name')
			password = request.form.get('pass')
			if user_name is None or password is None:
				return 'Bad request', 400

			sha256 = hashlib.sha256(bytes(password, encoding='utf-8')).hexdigest()
			result = DB.check_user(request.form.get('user_name'), sha256)
			if result:
				if user_name in self.sessions_by_user_name:
					session = self.sessions_by_user_name[user_name]
				else:
					session = Session(user_name, result.activated, result.uid, admin=result.admin)
					self.sessions[session.get_id()] = session
					self.sessions_by_user_name[user_name] = session
					session['avatar'] = result.file
					DB.add_session(session, result.uid)
				session['ip'] = request.remote_addr

				response = make_response('True')
				response.headers["Content-type"] = "text/plain"
				session.add_cookie_to_resp(response)
				return response
			else:
				response = make_response('False')
				response.headers["Content-type"] = "text/plain"
				return response

		@self.app.route("/api/destroy_session")
		# need: session
		def destroy_session():
			session = self.get_session(request)
			if not session:
				return 'Fail', 401

			response = make_response('OK')
			session.delete_cookie(response)
			DB.delete_session(session.id)
			del self.sessions_by_user_name[session.user]
			del self.sessions[session.id]
			return response

		@self.app.route('/api/ping')
		# maybe: get@data
		def ping():
			data = request.args.get('data')
			return data if data is not None else 'Pong'

		@self.app.route('/api/getRequestPerSec')
		# need: session@admin
		def get_request_per_sec():
			session = self.get_session(request)
			if session:
				if self.get_session(request).admin:
					return self.logger.time_log[-1].__str__()
				else:
					return 'Permission denied', 401
			else:
				return 'Fail', 401

		@self.app.route('/api/get_table', methods=['GET'])
		# need: session@admin, get@table
		def get_sessions():
			session = self.get_session(request)
			if session:
				if self.get_session(request).admin:
					table_s = request.args.get('table')
					if table_s == 'sessions':
						table = self.sessions
					elif table_s == 'rooms':
						table = self.rooms
					else:
						return 'Bad request', 400
					result = list(map(lambda s: s.to_json(), table.values()))
					return dumps(result)
				else:
					return 'Permission denied', 401
			else:
				return 'Fail', 401

		@self.app.route('/api/get_friends')  # test only, will be deleted later
		# need: session@admin
		def get_friends():
			session = self.get_session(request)
			if session:
				if self.get_session(request).admin:
					friends, edges = DB.get_friends_table()
					result = {
						"nodes": friends,
						"edges": list(map(lambda edge: {
							"src": edge["name1"],
							"dest": edge["name2"]
						}, edges))
					}
					return dumps(result)
				else:
					return 'Permission denied', 401
			else:
				return 'Fail', 401

		@self.app.route('/api/users/find', methods=['GET'])
		# need: session; get@name
		def find_user():
			session = self.get_session(request)
			if not session:
				return 'Fail', 401

			name = request.args.get('name')
			if name and len(name) > 3:
				return dumps(list(self.users_to_JSON(DB.find_user(name), session)))
			else:
				return 'Bad request', 400

		@self.app.route('/api/users/send_friend_invite', methods=['GET'])
		def send_friend_invite():
			pass

		@self.app.route('/api/users/get_friend_list')
		# need: session;
		def get_friend_list():
			session = self.get_session(request)
			if not session:
				return 'Fail', 401

			return dumps(list(self.users_to_JSON(DB.get_friends(uid=session.uid), session)))

		@self.app.route('/api/users/check_online', methods=['GET'])
		def check_online():
			pass

	def get_session(self, request_) -> Session:  # -> Session | False | None
		if 'sessID' in request_.cookies and request_.cookies['sessID'] in self.sessions:
			session = self.sessions[request_.cookies['sessID']]
			if session.activated:
				return session
			else:
				return False
		else:
			return None

	def merge_room(self, room):
		for thin_room in self.rooms.values():
			if thin_room.is_ready() or thin_room is room: continue
			session = room.players[0] if room.players[0] is not None else room.players[1]
			session['player_n'] = thin_room.add_player(session)
			session['cur_room'] = thin_room
			if thin_room.is_ready():
				thin_room.send_player_inf()
				thin_room.send_changes()
				thin_room.send_msg(dumps({
					'data': [{
						'type': 'wait',
						'player': thin_room.game.turn,
						'card': None,
						'inf': None
					}]
				}))
			del self.rooms[room.id]
			return thin_room
		return None

	def users_to_JSON(self, users: GeneratorType, session):
		for uid, u_name, u_avatar in users:
			if u_name in self.sessions_by_user_name:
				tmp_session = self.sessions_by_user_name[u_name]
				if tmp_session.status == Session.ONLINE:
					status = "Online"
				elif tmp_session.status == Session.PLAY:
					room = tmp_session['cur_room']
					if room:
						if room.type == const.MODE_PVE:
							status = "Играет с AI"
						else:
							player = room.players[1 - tmp_session['player_n']]
							status = ("Играет с " + player.user) if player is not None else 'Ожидает оппонента'
					else:
						status = "Online"
				else:
					status = "Offline"
			else:
				status = 'Offline'

			if u_avatar is not None and u_avatar != 'None':
				u_avatar = "/static/avatar/{user_name}{file_ext}".format(user_name=u_name, file_ext=u_avatar)
			else:
				u_avatar = "/static_/svg/account-circle.svg"

			c = DB.connect()
			mutual_friends = list(map(lambda x: x[0], DB.get_mutual_friends(session.uid, uid, c)))
			c.close()

			yield {
				'name': u_name,
				'status': status,
				'avatar': u_avatar,
				'mutual_friends': mutual_friends
			}


class ServerSentEvent(object):
	def __init__(self, data):
		self.data = data
		self.event = None
		self.id = None
		self.desc_map = {
			self.data: "data",
			self.event: "event",
			self.id: "id"
		}

	def encode(self):
		if not self.data:
			return ""
		lines = ["%s: %s" % (v, k) for k, v in self.desc_map.items() if k]
		return "%s\n\n" % "\n".join(lines)
