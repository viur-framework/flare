from flare import html5
from flare.forms import moduleWidgetSelector
from flare.i18n import translate
from flare.popup import Popup
from flare.handler import ListHandler
from flare.button import Button
from flare.observable import StateHandler
from flare.widgets.buttonbar import ButtonBar


class ListWidget(html5.Div):
    """Provides the interface to list-applications.

    It acts as a data-provider for a DataTable and binds an action-bar
    to this table.
    """

    def __init__(
        self,
        module,
        filter=None,
        columns=None,
        filterID=None,
        filterDescr=None,
        batchSize=None,
        context=None,
        autoload=True,
        *args,
        **kwargs
    ):
        super(ListWidget, self).__init__()
        self.addClass("flr-widget flr-widget--list")

        self.module = module
        self.filter = filter

    def setSelector(self, callback, multi=True, allow=None):
        """Configures the widget as selector for a relationalBone and shows it."""
        self.selectionCallback = callback
        self.selectionMulti = multi
        self.callback = callback

        listselectionPopup = ListSelection(self.module, self.filter)
        listselectionPopup.state.register("acceptSelection", self)

    def onAcceptSelectionChanged(self, event, *args, **kwargs):
        if event and "widget" in dir(event):
            self.callback(self, [event.widget.skel])

    @staticmethod
    def canHandle(moduleName, moduleInfo):
        return moduleInfo["handler"] == "list" or moduleInfo["handler"].startswith(
            "list."
        )


moduleWidgetSelector.insert(0, ListWidget.canHandle, ListWidget)


# @html5.tag  # fixme: What should be the tag-name for this?
class SkellistItem(Button):
    def __init__(self, skel):
        super().__init__()
        self.skel = skel
        self.addClass("skellist-element")
        self["style"]["width"] = "100%"
        self.buildWidget()

    def buildWidget(self):
        if "firstname" in self.skel and "lastname" in self.skel:
            self.appendChild(self.skel["firstname"] + " " + self.skel["lastname"])
        else:
            self.appendChild(self.skel["name"])

    def onActiveSelectionChanged(self, event, *args, **kwargs):
        if not event:
            self.removeClass("btn--primary")
            return 0
        if html5.doesEventHitWidgetOrChildren(event, self):
            self.addClass("btn--primary")
        else:
            self.removeClass("btn--primary")


class ListSelection(Popup):
    def __init__(
        self,
        modulname,
        filter=None,
        title=None,
        id=None,
        className=None,
        icon=None,
        enableShortcuts=True,
        closeable=True,
        footer=True,
        *args,
        **kwargs
    ):
        title = translate("Select %s" % modulname)
        footer = False
        self.modulname = modulname
        self.filter = filter or {}
        super().__init__(
            title,
            id,
            className,
            icon,
            enableShortcuts,
            closeable,
            footer,
            *args,
            **kwargs
        )
        self.addClass("popup--wide")
        self.buildListSelection()

    def requestClients(self):
        self.currentlistHandler = ListHandler(
            self.modulname, "list", params=self.filter, eventName="requestList"
        )
        self.currentlistHandler.requestList.register(self)
        self.currentlistHandler.requestData()

        self.state = StateHandler((), self)
        self.state.updateState("activeSelection", None)
        self.state.updateState("acceptSelection", None)

    def onRequestList(self, skellist):
        self.listelements.removeAllChildren()
        for skel in skellist:
            skelwidget = SkellistItem(skel)
            skelwidget.callback = self.activateSelection  # real button action
            self.state.register(
                "activeSelection", skelwidget
            )  # register to change State for active State handling
            self.listelements.appendChild(skelwidget)

    def onActiveSelectionChanged(self, event, *args, **kwargs):
        if event:
            self.selectbtn["disabled"] = False
        else:
            self.selectbtn["disabled"] = True

    def activateSelection(self, widget):
        self.state.updateState("activeSelection", widget)

    def reloadList(self):
        self.state.updateState("activeSelection", None)
        self.currentlistHandler.reload()

    def buildListSelection(self):
        popupwrap = html5.Div()
        popupwrap.addClass(["box", "main-box"])

        # build Buttonbar
        self.buttonbar = ButtonBar()
        # language=HTML
        self.buttonbar.addButton(
            "reloadbtn",
            """<flare-buttonbar-button text="neuladen" [name]="reloadbtn"></flare-buttonbar-button>""",
        )

        # language=HTML
        self.filterbtn = self.buttonbar.addButton(
            "filterbtn",
            """<flare-buttonbar-search [name]="filterbtn"></flare-buttonbar-search>""",
        )
        self.filterbtn.state.register("applyfilter", self)

        # language=HTML
        self.selectbtn = self.buttonbar.addButton(
            "selectbtn",
            """<flare-buttonbar-button text="auswählen" [name]="selectbtn"></flare-buttonbar-button>""",
        )

        self.buttonbar.state.register("activeButton", self)

        popupwrap.appendChild(self.buttonbar)

        self.listelements = html5.Div()
        popupwrap.appendChild(self.listelements)

        self.requestClients()
        self.setContent(popupwrap)

    def onApplyfilterChanged(self, value, *args, **kwargs):
        self.currentlistHandler.filter({"search": value})

    def onAcceptSelectionChanged(self, event, *args, **kwargs):
        pass

    def onActiveButtonChanged(self, event, *args, **kwargs):
        if event.widget.name == "reloadbtn":
            self.reloadList()
        elif event.widget.name == "selectbtn":
            self.acceptSelection()

    def acceptSelection(self):
        selection = self.state.getState("activeSelection")

        if selection:
            self.state.updateState("acceptSelection", selection)

            self.close()

    def setContent(self, widget):
        self.popupBody.appendChild(widget)
