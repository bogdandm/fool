# -*- coding: utf-8 -*-
import hashlib
from re import search
from json import dumps

import gevent
from gevent.queue import Queue
from flask import Flask, Response, make_response, request, redirect, render_template

import server.const as const
from server.server_classes import RoomPvE, RoomPvP, ServerCache, Session, Logger
from server.database import DB


# TODO: write session documentation
class Server:
	def __init__(self, ip):
		self.ip = ip
		self.app = Flask(__name__)
		self.cache = ServerCache(const.STATIC_FOLDER, const.SERVER_FOLDER)
		res = DB.get_sessions()
		self.sessions = dict()
		if res is not None:
			for row in res:
				self.sessions[row[1]] = Session(*row)
		self.rooms = dict()
		self.logger = Logger()
		self.logger.write_msg('==Server run at %s==' % ip)

		@self.app.after_request
		def after_request(response):
			self.logger.write_record(request, response)
			return response

		@self.app.route('/static_/svg/<path:path>')
		def send_static_file(path):
			response = make_response(self.cache.get(const.SERVER_FOLDER + const.STATIC_FOLDER + '/svg/' + path))
			if search('^.*\.html$', path):
				response.headers["Content-type"] = "text/html"
			elif search('^.*\.css$', path):
				response.headers["Content-type"] = "text/css"
			elif search('^.*\.js$', path):
				response.headers["Content-type"] = "text/javascript"
			elif search('^.*\.svg', path):
				response.headers["Content-type"] = "image/svg+xml"
			return response

		@self.app.route('/')
		def send_root():
			if self.check_session(request):
				name = self.sessions[request.cookies['sessID']].user
				return render_template('main_menu.html', user_name=name)
			else:
				return redirect('/static/login.html')

		@self.app.route('/arena')  # need: get@mode
		def send_arena():
			return redirect('/static/arena.html?mode=' + request.args['mode'])

		@self.app.route('/api')
		def send_api_methods():
			return redirect('/static/api_methods.html')  # TODO: rewrite documentation

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
				del session['msg_queue']

			if not self.check_session(request):
				return 'Fail'
			return Response(gen(request.cookies['sessID']), mimetype="text/event-stream")

		@self.app.route("/api/unsubscribe")  # need: session
		def unsubscribe():
			if not self.check_session(request):
				return 'Fail'

			session = self.sessions[request.cookies['sessID']]

			def notify():
				session['msg_queue'].put('stop')

			gevent.spawn(notify)
			return 'OK'

		@self.app.route("/api/join")  # need: session@queue, get@mode
		def join_room():
			if not self.check_session(request):
				return 'Fail'

			mode = int(request.args['mode'])
			session = self.sessions[request.cookies['sessID']]
			if mode == const.MODE_PVE:
				room = RoomPvE(session)
				self.rooms[room.id] = room
				session['cur_room'] = room
				session['player_n'] = const.PLAYER_HAND
				room.send_player_inf()
				room.send_changes()
			elif mode == const.MODE_PVP:
				for _, room in self.rooms.items():
					if room.type == const.MODE_PVP and not room.is_ready():
						break
				else:
					room = RoomPvP()
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

		@self.app.route("/api/leave")  # need: session@cur_room
		def leave_room():
			if not self.check_session(request):
				return 'Fail'

			session = self.sessions[request.cookies['sessID']]
			room = session['cur_room']
			if room is None: return 'OK'
			room_id = room.id
			if room.type == const.MODE_PVE:
				del self.rooms[room_id]
				del session['cur_room']
				return 'OK'
			elif room.type == const.MODE_PVP:
				if room.is_ready():
					room.remove_player(session['player_n'])
					room.send_msg('wait')
				else:
					del self.rooms[room_id]
				del session['cur_room']
				return 'OK'

		@self.app.route("/api/attack")  # need: session@cur_room, get@card
		def attack():
			if not self.check_session(request):
				return 'Fail'

			session = self.sessions[request.cookies['sessID']]
			room = session['cur_room']
			card = int(request.args['card'])
			result = room.attack(session['player_n'], card)
			if result == 'END':
				room_id = room.id
				if room.type == const.MODE_PVE:
					del self.rooms[room_id]
					del session['cur_room']
					return 'OK'
			return result

		@self.app.route("/api/defense")  # need: session@cur_room, get@card
		def defense():
			if not self.check_session(request):
				return 'Fail'

			session = self.sessions[request.cookies['sessID']]
			room = session['cur_room']
			card = int(request.args['card'])
			result = room.defense(session['player_n'], card)
			if result == 'END':
				room_id = room.id
				if room.type == const.MODE_PVE:
					del self.rooms[room_id]
					del session['cur_room']
					return 'OK'
			return result

		@self.app.route("/api/check_user", methods=['POST'])  # need: post@user_name; maybe: post@pass
		def check_user():
			password = request.form.get('pass')
			sha256 = hashlib.sha256(bytes(password, encoding='utf-8')).hexdigest() if password is not None else None

			(result, uid) = DB.check_user(request.form.get('user_name'), sha256)
			response = make_response(result.__str__())
			response.headers["Content-type"] = "text/plain"
			return response

		@self.app.route("/api/add_user", methods=['POST'])  # need: post@user_name, post@pass
		def add_user():
			# TODO: we need more security!
			password = request.form.get('pass')
			sha256 = hashlib.sha256(bytes(password, encoding='utf-8')).hexdigest() if password is not None else None

			result = DB.add_user(request.form.get('user_name'), sha256)
			if result:
				return 'OK'
			else:
				pass  # TODO

		@self.app.route("/api/init_session", methods=['POST'])  # -> bool
		def init_session():
			if self.check_session(request):
				response = make_response('OK')
				response.headers["Content-type"] = "text/plain"
				return response
			user_name = request.form.get('user_name')
			password = request.form.get('pass')
			sha256 = hashlib.sha256(bytes(password, encoding='utf-8')).hexdigest() if password is not None else None
			(result, uid) = DB.check_user(request.form.get('user_name'), sha256)
			if result:
				s = Session(user_name)
				self.sessions[s.get_id()] = s
				DB.add_session(s, uid)

				response = make_response('True')
				response.headers["Content-type"] = "text/plain"
				s.add_cookie_to_resp(response)
				return response
			else:
				response = make_response('False')
				response.headers["Content-type"] = "text/plain"
				return response

		@self.app.route("/api/destroy_session")  # -> bool
		def destroy_session():
			if not self.check_session(request):
				return 'Fail'

			response = make_response('OK')
			self.sessions[request.cookies['sessID']].delete_cookie(response)
			del self.sessions[request.cookies['sessID']]
			return response

	def check_session(self, request_):
		return 'sessID' in request_.cookies and request_.cookies['sessID'] in self.sessions


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
