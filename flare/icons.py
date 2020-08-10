"""
Generic icon handling, especially of embedded SVG images served from a pool of icons.
"""


import logging

from . import html5
from .config import conf
from .network import NetworkService, HTTPRequest


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

def addIconToPool(name, icon):
	"""
	Adds an icon under an name to the icon pool.
	icon can be None to mark an icon as "not found".
	"""
	conf["icons.pool"][name] = icon
	return name

def getIconHTML(icon, callback):
	"""
	Retrieve SVG/HTML-code for icon.

	It either loads the icon into the SVG pool or returns a placeholder.

	The function requires for a callback URL that is called to render the returned Icon.
	WARNING: The callback can be called twice, once for a pre-load and then after fetching.
	"""

	if icon in conf["icons.pool"]:
		svg = conf["icons.pool"].get(icon)
	else:
		HTTPRequest(
			"GET", f"{conf['icons.lookup']}/{icon}.svg",
			lambda svg: getIconHTML(addIconToPool(icon, svg), callback),
			lambda *args, **kwargs: addIconToPool(icon, None)
		)

		svg = None

	if not svg:
		# language=HTML
		svg = f"""<i class="i">{icon[0]}</i>"""

	callback(svg)


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

		getIconHTML(embedsvg, lambda *args, **kwargs: self.appendChild(*args, **kwargs, replace=True))

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
