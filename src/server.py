#!/usr/bin/env python

# ===========================================
#			IMPORTING LIBRARIES
# ===========================================

from simple_websocket_server import WebSocketServer, WebSocket
import ssl, socket

try:
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer, SimpleHTTPRequestHandler


# ===========================================
#				SERVER CLASS
# ===========================================

class Server(WebSocketServer):
	
	def __init__(self, ip = 'auto', port = 8000, useSsl = True, sslLoc = ''):
		self.ip = Server.getIp() if (ip == 'auto') else ip
		self.port = port
		self.useSsl = useSsl
		
		if useSsl:
			super().__init__(self.ip, self.port, WebSocket, ssl_version=ssl.PROTOCOL_TLS, certfile=sslLoc + 'cert.pem', keyfile=sslLoc + 'key.pem')
		else:
			super().__init__(self.ip, self.port, WebSocket)
	
	
	# https://stackoverflow.com/a/28950776
	def getIp():
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		try:
			s.connect(('1.2.3.4', 1))
			ip = s.getsockname()[0]
		except Exception:
			ip = socket.gethostbyname(socket.gethostname())
		finally:
			s.close()
		return ip
		
		
	def waitForConnection(self):
	
		print('Websocket server listening : ws' + ('s' if self.useSsl else '') + '://' + self.ip + ':' + str(self.port))
		# wait for a client to connect
		while self.connections == {}:
			self.handle_request()
		# ensure that the connection is well established
		for i in range(0,10):
			self.handle_request()
		# store the resuliting websocket
		self.client = list(self.connections.values())[0]
		print('Connected successfully to', self.client.address,'!')

		
		
	def split(self):
		self.client.send_message('splitorstart')
		self.handle_request()
		
		
	def firstSplit(self):
		self.client.send_message('reset')
		self.handle_request()
		self.split()
		

