"""
ViUR-user-module-related tools and widgets.
"""
from . import html5
from .icons import Icon
from .config import conf


@html5.tag("flare-avatar")
class Avatar(Icon):
	"""
	Icon-Component that represents a user avatar.

	When the user is not, it is automatically fetched into the cache for further usage.
	"""

	def __init__(self):
		super().__init__()
		self.user = {}
		self.fallbackClass = None
		self.myvalue = None

	def _setValue(self, value):
		# print("Avatar:_setValue: new value = %r" % value)
		if isinstance(value, dict) and "key" in value:
			if "image" not in value:
				if "firstname" in value:
					self.user["firstname"] = value["firstname"]
				if "lastname" in value:
					self.user["lastname"] = value["lastname"]
				value = value["key"]
				print("Avatar:_setValue: value = %r" % value)

		self.myvalue = value

		# request missing data
		if isinstance(value, str):
			# print("Avatar:_setValue: requesting user/view for: %r" % value)
			conf["flare.cache"].request({
					"module": "!user",
					"action": "view",
					"params": value
				},
				finishHandler=self._onUserAvailable,
				failureHandler=self._onUserFailed
			)
		# try to set Image
		elif isinstance(value, dict) and all([k in value for k in ["key", "image"]]) and value["image"]:
			# print("Avatar:_setValue: got user with image! ")
			self.user = value
			if self.fallbackClass:
				self.removeClass(self.fallbackClass)
			super()._setValue(value["image"])
		else:
			self._tryFallbacks()

	def _tryFallbacks(self):
		# print("Avatar:_setValue:_tryFallbacks self.myvalue = %r" % self.myvalue)
		# print("Avatar:_setValue:_tryFallbacks self.user = %r" % self.user)
		# if not fallback use initials
		if not self.fallbackIcon:
			if isinstance(self.myvalue, dict) and \
				"key" in self.myvalue and ("firstname" in self.myvalue or "lastname" in self.myvalue):
				super()._setTitle(" ".join(
					[self.myvalue["firstname"] if "firstname" in self.myvalue else "",
						self.myvalue["lastname"] if "lastname" in self.myvalue else ""]))
				return
			elif isinstance(self.user, dict) and \
				("firstname" in self.user or "lastname" in self.user):
				super()._setTitle(" ".join(
					[self.user["firstname"] if "firstname" in self.user else "",
						self.user["lastname"] if "lastname" in self.user else ""]))
				return
		# if a fallback is set use this instead
		if self.fallbackIcon:
			if self.fallbackClass:
				self.addClass(self.fallbackClass)
			super()._setValue(self.fallbackIcon)
		# if no fallback und no first- and lastname available use hardcoded icon
		else:
			super()._setValue("icon-user")

	def _onUserAvailable(self, res):
		# print("Avatar:_setValue: _onUserAvailable: res = %r" % res)
		if res["user"]:
			# print("Avatar:_setValue: _onUserAvailable: recursive call with %r" % res["user"])
			# recursively calls _setValue
			self["value"] = res["user"]
		else:
			self._onUserFailed(res)

	def _onUserFailed(self, res):
		# print("Avatar:_setValue: _onUserFailed: res = %r" % res)
		self._tryFallbacks()

	def _setFallbackclass(self, value):
		self.fallbackClass = value


@html5.tag("flare-username")
class Username(html5.Div):
	"""
	Div-Tag that represents a user name.

	When the user is not, it is automatically fetched into the cache for further usage.
	"""
	_leafTag = True

	def __init__(self):
		super().__init__()
		self.user = None

	def _setValue(self, value):
		self.removeAllChildren()

		if isinstance(value, dict) and not all([k in value for k in ["key", "firstname", "lastname"]]):
			value = value["key"]

		if isinstance(value, str):
			conf["flare.cache"].request({
					"module": "!user",
					"action": "view",
					"params": value
				},
				finishHandler=self._onUserAvailable
			)

		elif isinstance(value, dict) and "key" in value:
			self.user = value

			if all([k in value for k in ["firstname", "lastname"]]):
				self.appendChild(" ".join([value["firstname"], value["lastname"]]))
			else:
				self.appendChild(value["key"])

		else:
			self.appendChild("???")  # I cannot render this user

	def _onUserAvailable(self, res):
		self["value"] = res["user"]
