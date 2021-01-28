import logging

import flare.views
from flare.observable import StateHandler
from flare.network import getUrlHashAsObject
from flare import html5
from flare.config import conf

class View():

	def __init__( self, dictOfWidgets = None, name = None ):
		'''
			dictOfWidgets: {mainAppContainer:Widget}

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

	def onActiveViewChanged( self, viewName,*args,**kwargs ):
		logging.debug("onActiveViewChanged: %r", viewName)
		if self.name == viewName:
			self.loadView()

	def loadView( self ):
		for target, widget in self.widgets.items():
			logging.debug("loadView: %r, %r, %r", target, widget, conf[ "app" ])
			try:
				targetWidget = getattr( conf[ "app" ], target )
			except Exception as err:
				logging.error( 'Target or conf["app"] %r not found!', target)
				logging.exception(err)
				ValueError( 'Target or conf["app"] %s not found!' % target)
				return

			logging.debug("before removeAllCHildren: %r, %r, %r", target, widget, targetWidget)
			targetWidget.removeAllChildren()
			logging.debug("after removeAllCHildren")

			if widget is None:
				logging.debug("widget is None: %r, %r, %r", target, widget, targetWidget)
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
					logging.debug("created view widget?: %r, %r, %r, %r", self.wdgt, self.instancename, self.widgets, self.loaded)

				if self.wdgt:
					logging.debug("updateState viewfocused: %r", self.name)
					self.wdgt.state.updateState("viewfocused", self.name)

				logging.debug("before targetWidget show and appendContent")
				targetWidget.show()
				targetWidget.appendChild( self.widgets[ target ] )


View.params = {}

class ViewWidget( html5.Div ):
	def __init__( self, view ):
		super().__init__()
		self.urlHash, self.urlParams = getUrlHashAsObject()
		self.view = view
		self.initWidget()

		self.state = StateHandler( (),self )

	def onViewfocusedChanged( self, viewname, *args, **kwargs ):
		pass

	def initWidget( self ):
		pass

	def onDetach( self ):
		super().onDetach()
