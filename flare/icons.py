"""
Generic icon handling, especially of embedded SVG images served from a pool of icons.
"""
import string, os

from . import html5
from .network import HTTPRequest

@html5.tag
class SvgIcon(html5.svg.Svg):
	def __init__(self, value=None, fallbackIcon=None, title="" ):
		super().__init__()
		self.value = value
		self.title = title
		self.fallbackIcon = fallbackIcon

		self["xmlns"] = "http://www.w3.org/2000/svg"
		self["class"] = ["icon"] #mostly used

		if title:
			self["title"]=title

		self.getIcon()

	def getIcon( self ):
		if self.value.endswith(".svg"):
			url = self.value
		else:
			url = "/static/svgs/%s.svg"%self.value

		HTTPRequest( "GET", url, callbackSuccess = self.replaceSVG, callbackFailure = self.requestFallBack )

	def replaceSVG( self, icondata ):
		self.removeAllChildren()
		svgnode = html5.fromHTML(icondata)[0]
		self["viewbox"] = svgnode["viewbox"]
		self["class"] = svgnode["class"]
		self.appendChild(svgnode._children)

	def requestFallBack(self, data, status):
		url = None
		if self.fallbackIcon:
			url = "/static/svgs/%s.svg" % self.fallbackIcon
		#elif self.title:
		#	#language=HTML
		#	self["viewbox"] = "0 -15 20 20"
		#	self.appendChild('''<text>%s</text>'''%self.title[0].upper())
		else:
			url = "/static/svgs/icon-error.svg" #fallback

		if url:
			HTTPRequest( "GET", url, callbackSuccess = self.replaceSVG )

@html5.tag
class Icon(html5.I):

	def __init__(self, value=None, fallbackIcon=None, title="", classes=[] ):
		super().__init__()
		self[ "class" ] = ["i"]+classes
		self.title=title
		self["title"]=title
		self.fallbackIcon = fallbackIcon
		self.value = value
		if value:
			self["value"] = value

	def _setValue( self,value ):
		self.value = value
		if self.value and any([self.value.endswith(ext) for ext in [".jpg", ".png", ".gif", ".bmp", ".webp", ".heic", ".jpeg"]]):
			# language=HTML
			self.appendChild( '<img [name]="image">' )
			self.image.onError = lambda e: self.onError( e )
			self.image.sinkEvent( "onError" )
			self.image["src"] = self.value
		else:
			if self.value.endswith(".svg"):
				url = self.value
			else:
				url = "/static/svgs/%s.svg" % self.value
			self.appendChild( SvgIcon( url, self.fallbackIcon, self.title ) )

	def onError(self, event):
		if self.fallbackIcon:
			self.removeChild(self.image)
			self.appendChild( SvgIcon( "/static/svgs/%s.svg"%self.fallbackIcon, title = self.title ) )
		elif self.title:
			self.removeChild(self.image)
			#language=HTML
			self.appendChild(self.title[0].upper())
		else:
			self.removeChild( self.image )
			self.appendChild( SvgIcon( "/static/svgs/icon-error.svg", title = self.title ) )

@html5.tag
class BadgeIcon(Icon):
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
