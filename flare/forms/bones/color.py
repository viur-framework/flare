from flare.forms import boneSelector, conf
from .base import BaseBone, BaseEditWidget, BaseViewWidget


class ColorEditWidget( BaseEditWidget ):
	style = [ "flr-value", "flr-value--color" ]

	def _createWidget( self ):
		return self.fromHTML( """
			<input [name]="widget" type="color">
			<button [name]="unsetBtn" text="Unset" icon="cross" class="btn--delete">
		""" )

	def onUnsetBtnClick( self ):
		self.widget[ "value" ] = ""

	def serialize( self ):
		value = self.widget[ "value" ]
		return value if value else None


class ColorViewWidget( BaseViewWidget ):

	def unserialize( self, value = None ):
		self.value = value

		if value:
			self[ "style" ][ "background-color" ] = value
			self.appendChild( value )
		else:
			self.appendChild( conf[ "emptyValue" ] )


class ColorBone( BaseBone ):
	editWidgetFactory = ColorEditWidget
	viewWidgetFactory = ColorViewWidget
	multiEditWidgetFactory = None
	multiViewWidgetFactory = None

	@staticmethod
	def checkFor( moduleName, boneName, skelStructure, *args, **kwargs ):
		return skelStructure[ boneName ][ "type" ] == "color" or skelStructure[ boneName ][ "type" ].startswith( "color." )


boneSelector.insert( 1, ColorBone.checkFor, ColorBone )
