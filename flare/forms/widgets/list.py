from flare import html5
from flare.forms import moduleWidgetSelector
from flare.i18n import translate
from flare.popup import Popup
from flare.handler import ListHandler
from flare.button import Button
from flare.observable import StateHandler
from flare.widgets.buttonbar import ButtonBar

class ListWidget(html5.Div):
	"""
		Provides the interface to list-applications.
		It acts as a data-provider for a DataTable and binds an action-bar
		to this table.
	"""
	def __init__(self, module, filter=None, columns=None, filterID=None, filterDescr=None,
	             batchSize = None, context = None, autoload = True, *args, **kwargs):

		super(ListWidget, self).__init__()
		self.addClass("flr-widget flr-widget--list")

		self.module = module
		self.filter = filter


	def setSelector(self, callback, multi=True, allow=None):
		"""
		Configures the widget as selector for a relationalBone and shows it.
		"""
		self.selectionCallback = callback
		self.selectionMulti = multi
		self.callback = callback

		listselectionPopup = ListSelection(self.module,self.filter)
		listselectionPopup.state.register("acceptSelection",self)


	def onAcceptSelectionChanged( self, event ):
		if event and "widget" in dir(event):
			self.callback(self,[event.widget.skel])


	@staticmethod
	def canHandle(moduleName, moduleInfo):
		return moduleInfo["handler"] == "list" or moduleInfo["handler"].startswith("list.")

moduleWidgetSelector.insert(1, ListWidget.canHandle, ListWidget)

@html5.tag
class SkellistItem(Button):

	def __init__( self, skel ):
		super().__init__()
		self.skel = skel
		self.addClass("skellist-element")
		self["style"]["width"] = "100%"
		self.buildWidget()


	def buildWidget( self ):
		self.appendChild(self.skel["name"])


	def onActiveSelectionChanged( self, event ):
		if not event:
			self.removeClass( "btn--primary" )
			return 0
		if html5.doesEventHitWidgetOrChildren( event, self ):
			self.addClass( "btn--primary" )
		else:
			self.removeClass( "btn--primary" )


class ListSelection(Popup):
	def __init__( self,modulname, filter= None, title = None, id = None, className = None, icon = None, enableShortcuts = True, closeable = True, footer=True, *args, **kwargs ):
		title = translate("select %s" %modulname)
		footer=False
		self.modulname = modulname
		self.filter = filter or {}
		super().__init__( title, id, className, icon, enableShortcuts, closeable, footer, *args, **kwargs )
		self.buildListSelection()

	def requestClients( self ):
		self.currentlistHandler = ListHandler(self.modulname,"list",params = self.filter, eventName = "requestList")
		self.currentlistHandler.requestList.register( self )
		self.currentlistHandler.requestData()

		self.state = StateHandler( self )
		self.state.updateState( "activeSelection", None )
		self.state.updateState( "acceptSelection", None )


	def onRequestList( self, skellist ):
		self.listelements.removeAllChildren()
		for skel in skellist:
			skelwidget = SkellistItem(skel)
			skelwidget.callback = self.activateSelection #real button action
			self.state.register("activeSelection", skelwidget) #register to change State for active State handling
			self.listelements.appendChild(skelwidget)

	def onActiveSelectionChanged( self,event ):
		if event:
			self.selectbtn[ "disabled" ] = False
		else:
			self.selectbtn[ "disabled" ] = True


	def activateSelection( self,widget ):
		self.state.updateState("activeSelection", widget)

	def reloadList( self ):
		self.state.updateState( "activeSelection", None )
		self.currentlistHandler.reload()


	def buildListSelection( self ):
		popupwrap = html5.Div()
		popupwrap.addClass(["box", "main-box"])

		#build Buttonbar
		self.buttonbar = ButtonBar()
		# language=HTML
		self.buttonbar.addButton( "reloadbtn", '''<ButtonBarButton text="neuladen" [name]="reloadbtn"></ButtonBarButton>''')

		#language=HTML
		self.filterbtn = self.buttonbar.addButton("filterbtn",'''<ButtonBarSearch [name]="filterbtn"></ButtonBarSearch>''')
		self.filterbtn.state.register("applyfilter",self)


		# language=HTML
		self.selectbtn = self.buttonbar.addButton( "selectbtn", '''<ButtonBarButton text="auswählen" [name]="selectbtn"></ButtonBarButton>''' )

		self.buttonbar.state.register( "activeButton", self )

		popupwrap.appendChild(self.buttonbar)



		self.listelements = html5.Div()
		popupwrap.appendChild(self.listelements)


		self.requestClients()
		self.setContent(popupwrap)

	def onApplyfilterChanged( self,value ):
		self.currentlistHandler.filter({"search":value})


	def onAcceptSelectionChanged( self,event ):
		pass

	def onActiveButtonChanged( self,event ):
		if event.widget.name == "reloadbtn":
			self.reloadList()
		elif event.widget.name == "selectbtn":
			self.acceptSelection()

	def acceptSelection( self ):
		selection = self.state.getState("activeSelection")

		if selection:
			self.state.updateState("acceptSelection", selection)

			self.close()

	def setContent( self, widget ):
		self.popupBody.appendChild(widget)
