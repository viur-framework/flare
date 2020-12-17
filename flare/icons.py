"""
Generic icon handling, especially of embedded SVG images served from a pool of icons.
"""
import string, os

from . import html5
from .network import HTTPRequest
from flare.config import conf

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

		if value:
			self.getIcon()

	def _setValue( self, value ):
		self.value = value
		self.getIcon()

	def getIcon( self ):
		if self.value and self.value.endswith(".svg"):
			url = self.value
		else:
			url = conf["basePathSvgs"]+"/%s.svg"%self.value

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
			url = conf["basePathSvgs"]+"/%s.svg" % self.fallbackIcon
		#elif self.title:
		#	#language=HTML
		#	self["viewbox"] = "0 -15 20 20"
		#	self.appendChild('''<text>%s</text>'''%self.title[0].upper())
		else:
			url = conf["basePathSvgs"]+"/icon-error.svg" #fallback

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
		if isinstance(value, dict):
			self.value = value.get("dest", {}).get("downloadUrl")
		else:
			self.value = value

		if self.value and any([self.value.endswith(ext) for ext in [".jpg", ".png", ".gif", ".bmp", ".webp", ".heic", ".jpeg"]]):
			# language=HTML
			self.appendChild( '<img [name]="image">' )
			self.image.onError = lambda e: self.onError( e )
			self.image.sinkEvent( "onError" )
			self.image["src"] = self.value
		else:
			if self.value and self.value.endswith(".svg"):
				url = self.value
			else:
				url = conf["basePathSvgs"]+"/%s.svg" % self.value
			self.appendChild( SvgIcon( url, self.fallbackIcon, self.title ) )

	def onError(self, event):
		if self.fallbackIcon:
			self.removeChild(self.image)
			self.appendChild( SvgIcon( conf["basePathSvgs"]+"/%s.svg"%self.fallbackIcon, title = self.title ) )
		elif self.title:
			self.removeChild(self.image)
			self.appendChild(self.title[0].upper())
		else:
			self.removeChild( self.image )
			self.appendChild( SvgIcon( conf["basePathSvgs"]+"/icon-error.svg", title = self.title ) )

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