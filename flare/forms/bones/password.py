from flare.forms import boneSelector, conf, InvalidBoneValueException
from flare.i18n import translate
from .base import BaseBone, BaseEditWidget


class PasswordEditWidget( BaseEditWidget ):
	style = [ "flr-value", "flr-value--password", "flr-value-container" ]

	def _createWidget( self ):
		self.appendChild( """<flr-input [name]="widget" type="password">""" )

		user = conf[ "currentUser" ]
		if self.bone.readonly or (user and "root" in user[ "access" ]):
			self.verify = None
		else:
			self.appendChild( """
				<label>
					{{txt}}
					<flr-input [name]="verify" type="password">
				</label>
			""",
							  vars = { "txt": translate( "reenter password" ) } )

	def serialize( self ):
		if not self.verify or self.widget[ "value" ] == self.verify[ "value" ]:
			return self.widget[ "value" ]

		raise InvalidBoneValueException()


class PasswordBone( BaseBone ):
	editWidgetFactory = PasswordEditWidget

	@staticmethod
	def checkFor( moduleName, boneName, skelStructure, *args, **kwargs ):
		return skelStructure[ boneName ][ "type" ] == "password" or skelStructure[ boneName ][ "type" ].startswith( "password." )


boneSelector.insert( 1, PasswordBone.checkFor, PasswordBone )
