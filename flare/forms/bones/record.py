from flare import html5
from flare.forms import boneSelector, conf, formatString
from flare.forms.widgets.relational import InternalEdit
from .base import BaseBone, BaseEditWidget, BaseViewWidget


class RecordEditWidget( BaseEditWidget ):
	style = [ "flr-value", "flr-value--record" ]

	def _createWidget( self ):
		return InternalEdit(
			self.bone.boneStructure[ "using" ],
			errorInformation = self.bone.errors,
			readOnly = self.bone.readonly,
			defaultCat = None,  # fixme: IMHO not necessary
			errorQueue = self.bone.errorQueue,
			prefix = "{}.rel".format( self.bone.boneName )
		)

	def _updateWidget( self ):
		if self.bone.readonly:
			self.widget.disable()
		else:
			self.widget.enable()

	def unserialize( self, value = None ):
		self.widget.unserialize( value or { } )

	def serialize( self ):
		return self.widget.serializeForPost()  # fixme: call serializeForPost()?


class RecordViewWidget( BaseViewWidget ):
	style = [ "flr-value", "flr-value--record" ]

	def __init__( self, bone, language = None, **kwargs ):
		super().__init__( bone, **kwargs )
		self.language = language

	def unserialize( self, value = None ):
		self.value = value

		if value:
			txt = formatString(
				self.bone.boneStructure[ "format" ],
				value,
				self.bone.boneStructure[ "using" ],
				language = self.language
			)

		else:
			txt = None

		self.appendChild( html5.TextNode( txt or conf[ "emptyValue" ] ), replace = True )


class RecordBone( BaseBone ):
	editWidgetFactory = RecordEditWidget
	viewWidgetFactory = RecordViewWidget

	@staticmethod
	def checkFor( moduleName, boneName, skelStructure, *args, **kwargs ):
		return skelStructure[ boneName ][ "type" ] == "record" or skelStructure[ boneName ][ "type" ].startswith( "record." )


boneSelector.insert( 1, RecordBone.checkFor, RecordBone )
