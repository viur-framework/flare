"""
Generic icon handling, especially of embedded SVG images served from a pool of icons.
"""


import logging, string

from . import html5
from .config import conf
from .network import NetworkService


def fetchIconsFromJSON(url, then=None):
	"""
	Utility function that is used to fetch icons from an URL using NetworkRequest,
	and adding these icons to the icon pool.
	"""

	def _fetchIconsSuccess(req):
		try:
			icons = NetworkService.decode(req)
			assert isinstance(icons, dict)
			conf["icons.pool"].update(icons)
		except Exception as e:
			logging.error("Error while parsing icons fetched from %r", url)
			logging.exception(e)

		if then:
			then()

	def _fetchIconsFailure(req, code):
		logging.error("Error %r while trying to fetch icons from %r", code, url)

		if then:
			then()

	logging.info("Starting to fetch icons from %r", url)

	NetworkService.request(
		None, url,
		successHandler=_fetchIconsSuccess,
		failureHandler=_fetchIconsFailure
	)

def getIconHTML(icon):
	"""
	Retrieve SVG/HTML-code for icon, either from conf["icons.pool"] or a generated <i>-Tag
	"""
	svg = conf["icons.pool"].get(icon)

	if not svg:
		# language=HTML
		return f"""<i class="i">{icon[0]}</i>"""

	return svg


@html5.tag
class Icon(html5.Div):
	"""
	The Icon-widget & tag either loads an icon from the icon pool
	or generates a dummy icon from the first letter.

	The icon pool can be loaded by fetchIconsFromJSON.
	"""

	def __init__(self, embedsvg=None, icon=None):
		super().__init__()
		self.embedsvg = None
		self.icon = None

		if embedsvg:
			self["embedsvg"] = embedsvg

		if icon:
			self["icon"] = icon

	def _setEmbedsvg(self, embedsvg):
		self.removeAllChildren()
		if not embedsvg:
			return

		self.embedsvg = embedsvg
		self.appendChild(getIconHTML(embedsvg))

	def _getEmbedsvg(self):
		return self.embedsvg

	def _setIcon(self, icon):
		self["embedsvg"] = icon
		self.icon = icon

		if icon:
			self.addClass("icon-wrap")
		else:
			self.removeClass("icon-wrap")

	def _getIcon(self):
		return self.icon

@html5.tag
class Noci(html5.I):
	"""
	Next-generation icon component:
	Represents either an image, or an icon or a placeholder text using an <i>-tag.
	"""
	_leafTag = True
	style = ["i"]

	def __init__(self):
		super().__init__()
		self.fallback = None
		self.value = None

	def _setFallback(self, fallback):
		self.fallback = fallback
		self["value"] = self["value"]

	def _getFallback(self):
		return self.fallback

	def _setValue(self, value):
		self.removeAllChildren()
		self.element.innerHTML = ""

		self.value = value

		# Accept empty value
		if not value:
			if self.fallback:
				self["value"] = self.fallback

			return

		# Accept a fileBone entry
		elif isinstance(value, dict):
			self.appendChild(
				html5.Img(value.get("dest", {}).get("downloadUrl") or self.fallback)
			)
		elif isinstance(value, str):
			icon = conf["icons.pool"].get(value)

			if icon:
				self.element.innerHTML = icon
			else:
				value = value.replace("-", " ") # replace dashes by spaces
				value = value.translate({ord(c): None for c in string.punctuation})  # remove all punctuations

				self.appendChild("".join([tag[0] for tag in value.split(maxsplit=2)]))

		else:
			raise ValueError("Either provide fileBone-dict or string")

	def _getValue(self):
		return self.value
