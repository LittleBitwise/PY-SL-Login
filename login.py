import hashlib, xmlrpc
import xmlrpc.client

def login(first: str, last: str, password: str):
	params = {
		'first': first,
		'last': last,
		'passwd': '$1$' + hashlib.md5(password.encode()).hexdigest(),
		'start': 'last',

		# client identification
		'channel': 'login.py',
		'version': '0.0.0',
		'platform': 'Win',

		# device identification
		'mac': '',
		'id0': '',

		'viewer_digest': '',
		'agree_to_tos': 'true',
		'options': [],
	}

	uri = 'https://login.agni.lindenlab.com/cgi-bin/login.cgi'
	proxy = xmlrpc.client.ServerProxy(uri)
	return proxy.login_to_simulator(params)

result = login("first", "last", "password")

print(result)
