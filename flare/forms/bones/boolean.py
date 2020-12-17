from flare import html5
from flare.ignite import *
from flare.forms import boneSelector
from flare.i18n import translate
from .base import BaseBone, BaseEditWidget, BaseViewWidget


class BooleanEditWidget( BaseEditWidget ):
	style = [ "flr-value", "flr-value--boolean" ]

	def createWidget( self ):
		return Switch()

	def updateWidget( self ):
		if self.bone.readonly:
			self.widget.disable()
		else:
			self.widget.enable()

	def unserialize( self, value = None ):
		self.widget[ "checked" ] = bool( value )

	def serialize( self ):
		return self.widget[ "checked" ]


class BooleanViewWidget( BaseViewWidget ):

	def unserialize( self, value = None ):
		self.value = value
		self.appendChild( html5.TextNode( translate( str( bool( value ) ) ) ), replace = True )


class BooleanBone( BaseBone ):
	editWidgetFactory = BooleanEditWidget
	viewWidgetFactory = BooleanViewWidget
	multiEditWidgetFactory = None
	multiViewWidgetFactory = None

	@staticmethod
	def checkFor( moduleName, boneName, skelStructure, *args, **kwargs ):
		return skelStructure[ boneName ][ "type" ] == "bool" or skelStructure[ boneName ][ "type" ].startswith( "bool." )


boneSelector.insert( 1, BooleanBone.checkFor, BooleanBone )
