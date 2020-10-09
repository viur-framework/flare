"""
Generic icon handling, especially of embedded SVG images served from a pool of icons.
"""
import string, os

from . import html5
from .network import HTTPRequest


def getIconHTML(icon, classList=None):
	classList = " ".join(classList) if classList else ""
	#todo visibility class
	#language=HTML
	return """<img src="/static/svgs/%s.svg" class="js-svg %s" style="visibility:hidden">""" % (icon, classList)


def svgEmbedder(e):
	targetElem = e.target  # Element that just loaded

	def replaceImage(content):  # We've fetched the svg from the server
		if targetElem.parentElement:  # Ignore if it disappeared from the DOM
			tmp = html5.domCreateElement("div")
			tmp.innerHTML = content
			svgElem = tmp.querySelector("svg")

			for cls in [x for x in targetElem.classList if x != "js-svg"]:
				svgElem.classList.add(cls)

			svgElem.style.pointerEvents = "none"
			targetElem.parentElement.insertBefore(svgElem, targetElem)
			targetElem.parentElement.removeChild(targetElem)

	if targetElem.classList.contains("js-svg"):  # Start replacing only if we encountered an image with js-svg
		HTTPRequest("GET", e.target.src, callbackSuccess=replaceImage)


html5.document.addEventListener("load", svgEmbedder, True)


@html5.tag
class Icon(html5.I):

	def __init__(self, title, value=None, fallbackIcon=None, ):
		super().__init__()
		self.value = value
		self.fallbackIcon = fallbackIcon
		if title:
			self.title=title
			self["title"]=title

		self._setValue()

	def _setValue( self ):
		if not self.value:
			return

		# language=HTML
		self.appendChild( '<img [name]="image">')
		self.image.onError = lambda e: self.onError( e )
		self.image.sinkEvent( "onError" )

		if any([self.value.endswith(ext) for ext in [".jpg", ".png", ".gif", ".bmp", ".webp", ".heic", ".jpeg"]]):
			self.image["src"] = self.value

		elif self.value.endswith(".svg"):
			self.image[ "src" ] = self.value
			self.image.addClass("js-svg")
		else:
			self.image[ "src" ] = "/static/svgs/%s.svg"%self.value
			self.image.addClass( "js-svg" )

	def onError(self, event):
		if self.fallbackIcon:
			self.image[ "src" ] = "/static/svgs/%s.svg"%self.fallbackIcon
			self.image.addClass( "js-svg" )
		else:
			self.removeChild(self.image)
			self.appendChild(self["title"][0])



@html5.tag
class IconBadge(Icon):
	def __init__(self, title, value=None, fallbackIcon=None, badge=None):
		super().__init__(title,value, fallbackIcon)
		self.badge = badge
		#language=HTML
		self.appendChild('<span class="badge" [name]="badgeobject">%s</span>'%self.badge)

	def _setBadge( self, value ):
		self.badgeobject.appendChild(value, replace = True)

	def _getBadge( self ):
		return self.badge

@html5.tag
class Icon_(html5.Div):
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
		self.element.innerHTML = ""

		self.embedsvg = embedsvg

		if not embedsvg:
			return

		#self.appendChild(getIconHTML(embedsvg))
		self.element.innerHTML = getIconHTML(embedsvg)

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

	def __init__(self):
		super().__init__()
		self.fallback = None
		self.value = None
		self.badge = None
		self.baseclass = None

		self._badge = None
		self["baseclass"] = "i"

	def _setBaseclass(self, baseclass):
		if self.baseclass:
			self.removeClass(self.baseclass)

		self.baseclass = baseclass
		self.addClass(self.baseclass)

	def _getBaseclass(self):
		return self.baseclass

	def _setFallback(self, fallback):
		self.fallback = fallback
		self["value"] = self["value"]

	def _getFallback(self):
		return self.fallback

	def _setBadge(self, badge):
		self.badge = badge

		if self.badge in (None, "", False):
			if self._badge:
				self._badge.hide()

			return

		if not self._badge:
			self._badge = self.appendChild("""<span class="badge"></span>""")[0]

		self._badge.appendChild(self.badge, replace=True)
		self._badge.show()

	def _getBadge(self):
		return self.badge

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
		# Accept a string containing a path
		elif isinstance(value, str) and "/" in value and os.path.splitext(value)[1].lower() in (".jpg", ".jpeg", ".gif", ".png", ".svg"):
			self.appendChild(
				html5.Img(value)
			)
		elif isinstance(value, str):
			#we need a better detection
			if value.startswith("icon-") or value.startswith("logo-"):
				#self.appendChild(getIconHTML(value))
				self.element.innerHTML = getIconHTML(value)
			else:
				value = value.replace("-", " ") # replace dashes by spaces
				value = value.translate({ord(c): None for c in string.punctuation})  # remove all punctuations

				self.appendChild("".join([tag[0] for tag in value.split(maxsplit=1)]))  # Only allow first two words

		else:
			raise ValueError("Either provide fileBone-dict or string")

		if self._badge:
			self.appendChild(self._badge)

	def _getValue(self):
		return self.value
