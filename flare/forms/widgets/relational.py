from flare.log import getLogger

logger = getLogger(__name__)

from flare import html5
from flare.forms.formtags import viurForm

class InternalEdit(html5.Div):
	style = ["flr-internal-edit"]

	def __init__( self, skelStructure, values = None, errorInformation = None, readOnly = False,
				  context = None, defaultCat = "", module = None, boneparams = None ):
		super().__init__()
		self.form = viurForm( moduleName=module, skel=values, structure=skelStructure )
		self.form.buildInternalForm()
		self.appendChild( self.form )

	def unserialize( self, data = None ):

		for key, boneField in self.form.bones.items():
			if data is not None:
				boneField.bonewidget.unserialize( data.get( key ) )

	def serializeForPost( self, validityCheck = False ):
		res = { }

		for key, boneField in self.form.bones.items():
			try:
				res[ key ] = boneField.bonewidget.serialize()

			except Exception as e:
				logger.exception(e)
				pass
				#if validityCheck:
				#return None

		return res

	def serializeForDocument( self ):
		res = { }

		for key, boneField in self.form.bones.items():
			try:
				res[ key ] = boneField.bonewidget.serialize()
			except Exception as e:
				res[ key ] = str( e )

		return res
