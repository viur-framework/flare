from flare import html5, utils
from flare.forms import boneSelector, conf
from .base import BaseBone, BaseEditWidget, BaseViewWidget


class StringEditWidget( BaseEditWidget ):
	style = [ "flr-value", "flr-value--string" ]

	def _createWidget( self ):
		self.appendChild( """
			<flr-input class="input-group-item" [name]="widget">
			<div class="label input-group-item input-group-item--last" [name]="length">0</div>
			<div class="label" [name]="maxlength" hidden>0</div> <!-- fixme: add later ... -->
		""" )

		self.sinkEvent( "onChange", "onKeyUp" )
		self.timeout = None

	def onChange( self, event ):
		if self.timeout:
			html5.window.clearTimeout( self.timeout )

		self.renderTimeout()

	def onKeyUp( self, event ):
		if self.timeout:
			html5.window.clearTimeout( self.timeout )

		self.timeout = html5.window.setTimeout( self.renderTimeout, 125 )
		event.stopPropagation()

	def renderTimeout( self ):
		self.timeout = None
		self.updateLength()

	def updateLength( self ):
		self.length.appendChild( len( self.widget[ "value" ] or "" ), replace = True )

	def unserialize( self, value = None ):
		self.widget[ "value" ] = utils.unescape( str( value or "" ) )  # fixme: is utils.unescape() still required?
		self.updateLength()

	def serialize( self ):
		return self.widget[ "value" ]


class StringViewWidget( BaseViewWidget ):
	# fixme: Do we really need this? BaseViewWidget should satisfy,
	#           the call to utils.unescape() is the only difference.

	def unserialize( self, value = None ):
		self.value = value
		self.appendChild( html5.TextNode( utils.unescape( value or conf[ "emptyValue" ] ) ), replace = True )


class StringBone( BaseBone ):
	editWidgetFactory = StringEditWidget
	viewWidgetFactory = StringViewWidget

	@staticmethod
	def checkFor( moduleName, boneName, skelStructure, *args, **kwargs ):
		return skelStructure[ boneName ][ "type" ] == "str" or skelStructure[ boneName ][ "type" ].startswith( "str." )


boneSelector.insert( 1, StringBone.checkFor, StringBone )
