from flare import html5
from flare.button import Button
from flare.observable import ObservableValue, StateHandler

class ButtonBar( html5.Div ):

	def __init__( self ):
		super().__init__()
		self.addClass( "bar" )

		self.state = StateHandler( self )
		self.state.updateState( "activeButton", None )

	def onActiveButtonChanged( self, event ):
		pass

	def addButton( self, name, btnStr ):
		self.appendChild( btnStr )
		if name in dir(self):
			btn = getattr( self, name )
			btn.name = name
			btn.callback = self.buttonClicked
			self.state.register( "activeButton", btn )
			return btn
		return None

	def buttonClicked( self, widget ):
		self.state.updateState( "activeButton", widget )


@html5.tag
class ButtonBarButton( Button ):

	def __init__( self ):
		super().__init__()

	def onActiveButtonChanged( self, event ):
		if html5.doesEventHitWidgetOrChildren( event, self ):
			self.addClass( "btn--primary" )
		else:
			self.removeClass( "btn--primary" )
