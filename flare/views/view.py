import flare.views
from flare.observable import StateHandler
from flare.network import getUrlHashAsObject
from flare import html5
from flare.config import conf

class View():

	def __init__( self, dictOfWidgets = None, name = None ):
		'''
			dictOfWidgets: {mainAppConteiner:Widget}

			mainAppConteiner musst be a widget which is on parent Widget available
			Widget musst inheriance from ViewWidget

		'''
		if name:
			self.name = name
		else:
			self.name = self.__class__.__name__.lower()

		self.widgets = dictOfWidgets
		self.loaded = False

		flare.views.conf[ "views_state" ].register( "activeView", self )

	def onActiveViewChanged( self, viewName,wdg ):
		if self.name == viewName:
			self.loadView()

	def loadView( self ):
		for target, widget in self.widgets.items():
			try:
				targetWidget = getattr( conf[ "app" ], target )
			except:
				ValueError( 'Target or conf["app"] %s not found!' % target )
				return

			targetWidget.removeAllChildren()

			if widget is None:
				targetWidget.hide()
			else:
				if not self.loaded:

					# try:
					self.wdgt = widget( self )
					self.instancename = self.name
					# except Exception as e:
					#	print(e)
					#	ValueError("ERROR: widget must have a view parameter")
					#	wdgt = html5.Div("ERROR: widget must have a view parameter")
					self.widgets.update( { target: self.wdgt } )
					self.loaded = True

				if self.wdgt:
					self.wdgt.state.updateState("viewfocused",self.name)

				targetWidget.show()
				targetWidget.appendChild( self.widgets[ target ] )


class ViewWidget( html5.Div ):
	def __init__( self, view ):
		super().__init__()
		self.urlHash, self.urlParams = getUrlHashAsObject()
		self.view = view
		self.initWidget()

		self.state = StateHandler( self )
		self.state.updateState( "viewfocused", None )

	def onViewfocusedChanged( self, viewname ):
		pass

	def initWidget( self ):
		pass

	def onDetach( self ):
		super().onDetach()
