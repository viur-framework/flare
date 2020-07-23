from flare.forms import boneSelector
from .base import BaseBone, BaseEditWidget


class SpatialEditWidget( BaseEditWidget ):

	def _createWidget( self ):
		return self.fromHTML(
			"""
			<flr-input [name]="latitude" type="number" placeholder="latitude">
			<flr-input [name]="longitude" type="number" placeholer="longitute">
			"""
		)

	def unserialize( self, value = None ):
		self.latitude[ "value" ], self.longitude[ "value" ] = value or (0, 0)

	def serialize( self ):
		return {
			"lat": self.latitude[ "value" ],
			"lng": self.longitude[ "value" ]
		}


class SpatialBone( BaseBone ):
	editWidgetFactory = SpatialEditWidget

	@staticmethod
	def checkFor( moduleName, boneName, skelStructure, *args, **kwargs ):
		return skelStructure[ boneName ][ "type" ] == "spatial" or skelStructure[ boneName ][ "type" ].startswith( "spatial." )


boneSelector.insert( 1, SpatialBone.checkFor, SpatialBone )
