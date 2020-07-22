"""
Flare base handlers for ViUR prototypes.
"""


from .network import NetworkService
from .event import EventDispatcher


class requestHandler():
	def __init__(self, module, action, params={}, eventName="listUpdated"):
		self.module = module
		self.action = action
		self.params = params
		self.eventName = eventName
		self.cursor = None
		self.complete = False
		self.skellist = []
		self.structure = {}

		setattr(self, self.eventName, EventDispatcher(self.eventName))

	def requestData(self, *args, **kwargs):
		NetworkService.request(self.module, self.action, self.params,
		                       successHandler=self.requestSuccess,
		                       failureHandler=self.requestFailed)

	def requestSuccess(self, req):
		resp = NetworkService.decode(req)
		self.resp = resp
		getattr(self, self.eventName).fire(self.resp)

	def requestFailed(self, req, *args, **kwargs):
		print("REQUEST Failed")
		print(req)
# resp = NetworkService.decode(req)
# print(resp)


class ListHandler(requestHandler):
	def reload(self):
		self.skellist = []
		self.requestData()

	def filter(self, filterparams):
		self.params = filterparams
		self.reload()

	def getCurrentAmount(self):
		return len(self.skellist)

	def requestNext(self):
		if not self.complete:
			self.params.update({"cursor": self.cursor})
			self.requestData()

	def requestSuccess(self, req):
		resp = NetworkService.decode(req)
		self.resp = resp

		if "cursor" in resp:
			if self.cursor == resp["cursor"]:
				self.complete = True
			self.cursor = resp["cursor"]

		if not self.structure and "structure" in resp:
			self.structure = resp["structure"]
		self.skellist += resp["skellist"]

		getattr(self, self.eventName).fire(self.skellist)
