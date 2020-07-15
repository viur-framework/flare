from . import html5
from .config import conf


@html5.tag
class Icon(html5.Div):

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
