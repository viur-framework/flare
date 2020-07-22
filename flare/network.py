"""
Wrapper to handle ViUR-related Ajax requests.
"""


import logging

import os, sys, json, string, random
from . import html5


class DeferredCall(object):
	"""
		Calls the given function with a fixed delay.
		This allows assuming that calls to NetworkService are always
		asynchronous, so its guaranteed that any initialization code can run
		before the Network-Call yields results.
	"""

	def __init__(self, func, *args, **kwargs):
		"""
			:param func: Callback function
			:type func: Callable
		"""
		super(DeferredCall, self).__init__()
		delay = 25
		if "_delay" in kwargs.keys():
			delay = kwargs["_delay"]
			del kwargs["_delay"]
		self._tFunc = func
		self._tArgs = args
		self._tKwArgs = kwargs
		html5.window.setTimeout(self.run, delay)

	def run(self):
		"""
			Internal callback that executes the callback function
		"""
		self._tFunc(*self._tArgs, **self._tKwArgs)


class HTTPRequest(object):
	"""
		Wrapper around XMLHttpRequest
	"""

	def __init__(self, *args, **kwargs):
		super(HTTPRequest, self).__init__(*args, **kwargs)
		self.req = html5.jseval("new XMLHttpRequest()")
		self.req.onreadystatechange = self.onReadyStateChange
		self.cb = None
		self.hasBeenSent = False

	def asyncGet(self, url, cb):
		"""
			Performs a GET operation on a remote server
			:param url: The url to fetch. Either absolute or relative to the server
			:type url: str
			:param cb: Target object to call "onCompletion" on success
			:type cb: object
		"""
		self.cb = cb
		self.type = "GET"
		self.payload = None
		self.content_type = None
		self.req.open("GET", url, True)

	def asyncPost(self, url, payload, cb, content_type=None):
		"""
			Performs a POST operation on a remote server
			:param url: The url to fetch. Either absolute or relative to the server
			:type url: str
			:param cb: Target object to call "onCompletion" on success
			:type cb: object
		"""
		self.cb = cb
		self.type = "POST"
		self.payload = payload
		self.content_type = content_type
		self.req.open("POST", url, True)

	def onReadyStateChange(self, *args, **kwargs):
		"""
			Internal callback.
		"""
		if self.req.readyState == 1 and not self.hasBeenSent:
			self.hasBeenSent = True  # Internet Explorer calls this function twice!

			if self.type == "POST" and self.content_type is not None:
				self.req.setRequestHeader('Content-Type', self.content_type)

			self.req.send(self.payload)

		if self.req.readyState == 4:
			if self.req.status >= 200 and self.req.status < 300:
				self.cb.onCompletion(self.req.responseText)
			else:
				self.cb.onError(self.req.responseText, self.req.status)


def NiceError(req, code, params="(no parameters provided)"):
	reason = {
		"401": "Nicht autorisierte Anfrage",
		"403": "Verboten - Fehlendes Zugriffsrecht",
		"404": "Datensatz nicht gefunden",
		"500": "Interner Server Fehler",
	}.get(str(code), "Unbekannter Fehler")

	hint = {
		"401": "\n\nBitte überprüfen Sie, ob Sie angemeldet sind,\n"
		       "und starten Sie das Programm danach erneut!",
	}.get(str(code), "")

	from . import popup
	popup.Alert(
		"<strong>%s</strong>%s\n\n<em>%s/%s/%s</em>" % (reason, hint, req.module, req.url, params),
		title="Fehler %d" % code
	)


class NetworkService(object):
	"""
		Generic wrapper around ajax requests.
		Handles caching and multiplexing multiple concurrent requests to
		the same resource. It also acts as the central proxy to notify
		currently active widgets of changes made to data on the server.
	"""
	changeListeners = []  # All currently active widgets which will be informed of changes made

	host = ""
	prefix = "/json"
	defaultFailureHandler = NiceError

	retryCodes = [0, -1]
	retryMax = 3
	retryDelay = 5000

	@staticmethod
	def notifyChange(module, **kwargs):
		"""
			Broadcasts a change made to data of module 'module' to all currently
			registered changeListeners.

			:param module: Name of the module where the change occured
			:type module: str
		"""
		for c in NetworkService.changeListeners:
			c.onDataChanged(module, **kwargs)

	@staticmethod
	def registerChangeListener(listener):
		"""
			Registers object 'listener' for change notifications.
			'listener' must provide an 'onDataChanged' function accepting
			one parameter: the name of the module. Does nothing if that object
			has already registered.
			:param listener: The object to register
			:type listener: object
		"""
		if listener in NetworkService.changeListeners:
			return

		NetworkService.changeListeners.append(listener)

	@staticmethod
	def removeChangeListener(listener):
		"""
			Unregisters the object 'listener' from change notifications.
			:param listener: The object to unregister. It must be currently registered.
			:type listener: object
		"""
		assert listener in NetworkService.changeListeners, "Attempt to remove unregistered listener %s" % str(listener)
		NetworkService.changeListeners.remove(listener)

	@staticmethod
	def genReqStr(params):
		"""
			Creates a MIME (multipart/mixed) payload for post requests transmitting
			the values given in params.
			:param params: Dictionary of key->values to encode
			:type params: dict
			:returns: (string payload, string boundary )
		"""
		boundary_str = "---" + ''.join(
			[random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for x in range(13)])
		boundary = boundary_str
		res = 'Content-Type: multipart/mixed; boundary="' + boundary + '"\r\nMIME-Version: 1.0\r\n'
		res += '\r\n--' + boundary
		for (key, value) in list(params.items()):
			if all([x in dir(value) for x in ["name", "read"]]):  # File
				try:
					(type, encoding) = mimetypes.guess_type(value.name.decode(sys.getfilesystemencoding()),
					                                        strict=False)
					type = type or "application/octet-stream"
				except:
					type = "application/octet-stream"
				res += '\r\nContent-Type: ' + type + '\r\nMIME-Version: 1.0\r\nContent-Disposition: form-data; name="' + key + '"; filename="' + os.path.basename(
					value.name).decode(sys.getfilesystemencoding()) + '"\r\n\r\n'
				res += str(value.read())
				res += '\r\n--' + boundary
			elif isinstance(value, list):
				for val in value:
					res += '\r\nContent-Type: application/octet-stream\r\nMIME-Version: 1.0\r\nContent-Disposition: form-data; name="' + key + '"\r\n\r\n'
					res += str(val)
					res += '\r\n--' + boundary
			elif isinstance(value, dict):
				for k, v in value.items():
					res += '\r\nContent-Type: application/octet-stream\r\nMIME-Version: 1.0\r\nContent-Disposition: form-data; name="' + key + b"." + k + '"\r\n\r\n'
					res += str(v)
					res += '\r\n--' + boundary
			else:
				res += '\r\nContent-Type: application/octet-stream\r\nMIME-Version: 1.0\r\nContent-Disposition: form-data; name="' + key + '"\r\n\r\n'
				res += str(value)
				res += '\r\n--' + boundary
		res += '--\r\n'
		return (res, boundary)

	@staticmethod
	def decode(req):
		"""
			Decodes a response received from the server (ie parsing the json)
			:type req: Instance of NetworkService response
			:returns: object
		"""
		return json.loads(req.result)

	@staticmethod
	def isOkay(req):
		answ = NetworkService.decode(req)
		return isinstance(answ, str) and answ == "OKAY"

	@staticmethod
	def urlForArgs(module, path):
		"""
			Constructs the final url for that request.
			If module is given, it prepends "/prefix"
			If module is None, path is returned unchanged.
			:param module: Name of the target module or None
			:type module: str or None
			:param path: Path (either relative to 'module' or absolute if 'module' is None
			:type path: str
			:returns: str
		"""
		if module:
			href = "%s/%s/%s" % (NetworkService.prefix, module, path)
		else:
			href = path

		if not href.startswith("/"):
			href = "/" + href

		return NetworkService.host + href

	def __init__(self, module, url, params, successHandler, failureHandler, finishedHandler,
	             modifies, secure, kickoff):
		"""
			Constructs a new NetworkService request.
			Should not be called directly (use NetworkService.request instead).
		"""
		super(NetworkService, self).__init__()

		self.result = None
		self.status = None
		self.waitingForSkey = False
		self.module = module
		self.url = url
		self.params = params

		self.successHandler = [successHandler] if successHandler else []
		self.failureHandler = [failureHandler] if failureHandler else []
		self.finishedHandler = [finishedHandler] if finishedHandler else []

		self.modifies = modifies
		self.secure = secure

		self.kickoffs = 0
		if kickoff:
			self.kickoff()

	def kickoff(self):
		self.status = "running"
		self.kickoffs += 1

		if self.secure:
			self.waitingForSkey = True
			self.doFetch("%s%s/skey" % (NetworkService.host, NetworkService.prefix), None, None)
		else:
			self.doFetch(NetworkService.urlForArgs(self.module, self.url), self.params, None)

	@staticmethod
	def request(module, url, params=None, successHandler=None, failureHandler=None,
	            finishedHandler=None, modifies=False, secure=False, kickoff=True):
		"""
			Performs an AJAX request. Handles caching and security-keys.

			Calls made to this function are guaranteed to be async.

			:param module: Target module on the server. Set to None if you want to call anything else
			:type module: str or None
			:param url: The path (relative to module) or a full url if module is None
			:type url: None
			:param successHandler: function beeing called if the request succeeds. Must take one argument (the request).
			:type successHandler: callable
			:param failureHandler: function beeing called if the request failes. Must take two arguments (the request and an error-code).
			:type failureHandler: callable
			:param finishedHandler: function beeing called if the request finished (regardless wherever it succeeded or not). Must take one argument (the request).
			:type finishedHandler: callable
			:param modifies: If set to True, it will automatically broadcast an onDataChanged event for that module.
			:type modifies: bool
			:param secure: If true, include a fresh securitykey in this request. Defaults to False.
			:type secure: bool

		"""
		logging.debug("NetworkService.request module=%r, url=%r, params=%r", module, url, params)

		return NetworkService(module, url, params,
		                      successHandler, failureHandler, finishedHandler,
		                      modifies, secure, kickoff)

	def doFetch(self, url, params, skey):
		"""
			Internal function performing the actual AJAX request.
		"""

		if params:
			if skey:
				params["skey"] = skey

			contentType = None

			if isinstance(params, dict):
				multipart, boundary = NetworkService.genReqStr(params)
				contentType = "multipart/form-data; boundary=" + boundary + "; charset=utf-8"
			elif isinstance(params, bytes):
				contentType = "application/x-www-form-urlencoded"
				multipart = params
			else:
				multipart = params

			HTTPRequest().asyncPost(url, multipart, self, content_type=contentType)

		else:
			if skey:
				if "?" in url:
					url += "&skey=%s" % skey
				else:
					url += "?skey=%s" % skey

			HTTPRequest().asyncGet(url, self)

	def onCompletion(self, text):
		"""
			Internal hook for the AJAX call.
		"""
		if self.waitingForSkey:
			self.waitingForSkey = False
			self.doFetch(
				NetworkService.urlForArgs(self.module, self.url),
				self.params, json.loads(text)
			)
		else:
			self.result = text
			self.status = "succeeded"
			try:
				for s in self.successHandler:
					s(self)
				for s in self.finishedHandler:
					s(self)
			except:
				if self.modifies:
					DeferredCall(
						NetworkService.notifyChange, self.module,
						key=self.params.get("key") if self.params else None,
						action=self.url,
						_delay=2500
					)
				raise

			if self.modifies:
				DeferredCall(
					NetworkService.notifyChange, self.module,
					key=self.params.get("key") if self.params else None,
					action=self.url, _delay=2500
				)

			# Remove references to our handlers
			self.clear()

	def onError(self, text, code):
		"""
			Internal hook for the AJAX call.
		"""
		self.status = "failed"
		self.result = text

		logging.debug(
			"NetworkService.onError kickoffs=%r, retryMax=%r, code=%r, retryCodes=%r",
		    self.kickoffs, self.retryMax, code, self.retryCodes
		)

		if self.kickoffs < self.retryMax and int(code) in self.retryCodes:
			# The following can be used to pass errors to a bugtracker service like Stackdriver or Bugsnag
			logError = None  # html5.window.top.logError
			if logError and self.kickoffs == self.retryMax - 1:
				logError("NetworkService.onError code:%s module:%s url:%s params:%s" % (
					code, self.module, self.url, self.params))

			logging.error("error %d, kickoff %d, will retry now", code, self.kickoffs)
			DeferredCall(self.kickoff, _delay=self.retryDelay)
			return

		for s in self.failureHandler:
			s(self, code)

		if not self.failureHandler and self.defaultFailureHandler:
			self.defaultFailureHandler(code)

		if not self.defaultFailureHandler:
			self.clear()

		for s in self.finishedHandler:
			s(self)

	def onTimeout(self, text):
		"""
			Internal hook for the AJAX call.
		"""
		self.onError(text, -1)

	def clear(self):
		self.successHandler = []
		self.finishedHandler = []
		self.failureHandler = []
		self.params = None
