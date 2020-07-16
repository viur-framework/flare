import logging

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

		svg = conf["icons.pool"].get(embedsvg)
		self.embedsvg = embedsvg

		if not svg:
			self.appendChild("""<i class="i">{{letter}}</i>""", letter=embedsvg[0])
		else:
			self.appendChild(svg)

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
