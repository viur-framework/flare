import logging

from time import time

from flare import html5, utils
from flare.viur import BoneSelector, ModuleWidgetSelector, DisplayDelegateSelector
from flare.network import NetworkService
from flare.config import conf
from flare.i18n import translate
from flare.viur.formatString import formatString
from flare.icons import SvgIcon, Icon
from flare.event import EventDispatcher
import pyodide
from collections import OrderedDict

# fixme embedsvg


class TreeItemWidget(html5.Li):
    def __init__(self, module, data, structure, widget, *args, **kwargs):
        """Instantiate TreeItemWidget.

        :param module: Name of the module for which we'll display data
        :type module: str
        :param data: The data we're going to display
        :type data: dict
        :param structure: The structure of that data as received from server
        :type structure: list
        :param widget: tree widget
        """
        super(TreeItemWidget, self).__init__()
        self.addClass("vi-tree-item item has-hover is-drop-target is-draggable")
        self.module = module
        self.data = data

        self.currentStatus = None
        self.leaveElement = False

        self.structure = structure
        self.widget = widget

        self.isExpanded = False
        self.childrenLoaded = False
        self.isDragged = False

        self.sortindex = data["sortindex"] if "sortindex" in data else 0

        #language=HTML
        self.fromHTML(
            """
			<div style="flex-direction:column;width:100%" [name]="nodeWrapper">
				<div class="item" [name]="nodeGrouper">
					<a class="expandlink hierarchy-toggle" [name]="nodeToggle"></a>
					<div class="item-image is-hidden" [name]="nodeImage"></div>
					<div class="item-content" [name]="nodeContent">
						<div class="item-headline" [name]="nodeHeadline"></div>
						<div class="item-subline" [name]="nodeSubline"></div>
					</div>
					<div class="item-controls" [name]="nodeControls"></div>
				</div>

				<ol class="hierarchy-sublist is-hidden" [name]="ol"></ol>
			</div>
		"""
        )

        self["draggable"] = True

        self.sinkEvent(
            "onClick",
            "onDblClick",
            "onDragOver",
            "onDrop",
            "onDragStart",
            "onDragLeave",
            "onDragEnd",
        )

        self.setStyle()

    def setStyle(self):
        """Is used to define the appearance of the element."""
        self["class"].append("hierarchy-item")
        self.additionalDropAreas()
        self.buildDescription()
        self.toggleArrow()

    # self.EntryIcon()

    def additionalDropAreas(self):
        """Drag and Drop areas."""
        self.afterDiv = html5.Div()
        self.afterDiv["class"] = ["after-element"]
        self.afterDiv.hide()
        aftertxt = html5.TextNode(translate(u"Nach dem Element einfügen"))
        self.afterDiv.appendChild(aftertxt)
        self.nodeWrapper.appendChild(self.afterDiv)

        self.beforeDiv = html5.Div()
        self.beforeDiv["class"] = ["before-element"]
        self.beforeDiv.hide()
        beforetxt = html5.TextNode(translate(u"Vor dem Element einfügen"))
        self.beforeDiv.appendChild(beforetxt)
        self.nodeWrapper.prependChild(self.beforeDiv)

    def markDraggedElement(self):
        """Mark the current dragged Element."""
        self["style"]["opacity"] = "0.5"

    def unmarkDraggedElement(self):
        self["style"]["opacity"] = "1"

    def onDragStart(self, event):
        event.dataTransfer.setData("Text", "%s/%s" % (self.data["key"], self.skelType))
        self.isDragged = True
        self.markDraggedElement()
        event.stopPropagation()

    def onDragEnd(self, event):
        self.isDragged = False
        self.unmarkDraggedElement()

        if "afterDiv" in dir(self) or "beforeDiv" in dir(self):
            self.disableDragMarkers()

    def onDragOver(self, event):
        """Test wherever the current drag would mean.

        "make it a child of us", "insert before us" or
        "insert after us" and apply the correct classes.
        """
        if self.isDragged:
            return

        if "afterDiv" in dir(self):
            self.afterDiv.show()  # show dropzones
        if "beforeDiv" in dir(self):
            self.beforeDiv.show()

        self.leaveElement = False  # reset leaveMarker

        self["title"] = translate("vi.data-insert")
        if "beforeDiv" in dir(self) and event.target == self.beforeDiv.element:
            self.currentStatus = "top"
            self.removeClass("insert-here")
            self.beforeDiv.addClass("is-focused")
            self.afterDiv.removeClass("is-focused")

        elif "afterDiv" in dir(self) and event.target == self.afterDiv.element:
            self.currentStatus = "bottom"
            self.removeClass("insert-here")
            self.beforeDiv.removeClass("is-focused")
            self.afterDiv.addClass("is-focused")

        elif utils.doesEventHitWidgetOrChildren(event, self):
            self.currentStatus = "inner"
            self.addClass("insert-here")
            if "beforeDiv" in dir(self):
                self.beforeDiv.removeClass("is-focused")
            if "afterDiv" in dir(self):
                self.afterDiv.removeClass("is-focused")
            self["title"] = translate(u"In das Element einfügen")

        event.preventDefault()
        event.stopPropagation()

    def onDragLeave(self, event):
        """Remove all drop indicating classes."""
        # Only leave if target not before or after
        if utils.doesEventHitWidgetOrChildren(event, self.nodeWrapper):
            self.leaveElement = False
            return
        else:
            self.leaveElement = True

        if "beforeDiv" in dir(self) or "afterDiv" in dir(self):
            w = html5.window
            w.setTimeout(
                pyodide.create_once_callable(self.disableDragMarkers), 2000
            )  # test later to leave, to avoid flickering...

    def disableDragMarkers(self):
        if self.leaveElement:
            self["title"] = translate("vi.data-insert")
            self.currentStatus = None
            if self.afterDiv:
                self.afterDiv.hide()
            if self.beforeDiv:
                self.beforeDiv.hide()
            self.removeClass("insert-here")
        else:
            self.leaveElement = True
            w = html5.window
            w.setTimeout(pyodide.create_once_callable(self.disableDragMarkers), 5000)

    def moveRequest(self, params):
        """Performs the move operation with the provided params."""
        NetworkService.request(self.module, "move", params, secure=True, modifies=True)
        self.currentStatus = None

    def onDrop(self, event):
        """We received a drop.

        Test wherever its means "make it a child of us", "insert before us" or
        "insert after us" and initiate the corresponding NetworkService requests.
        """
        event.stopPropagation()
        event.preventDefault()

        data = event.dataTransfer.getData("Text")
        if not data:
            return

        srcKey, skelType = event.dataTransfer.getData("Text").split("/")

        if self.currentStatus == "inner":
            self.moveRequest({
                "skelType": skelType,
                "key": srcKey,
                "parentNode": self.data["key"]
            })

        elif self.currentStatus == "top":
            lastIdx = 0

            for c in self.parent()._children:
                if "data" in dir(c) and "sortindex" in c.data.keys():
                    if c == self:
                        break
                    lastIdx = float(c.data["sortindex"])

            self.moveRequest({
                "skelType": skelType,
                "key": srcKey,
                "parentNode": self.data["parententry"],
                "sortindex": str((lastIdx + float(self.data["sortindex"])) / 2.0),
            })

        elif self.currentStatus == "bottom":
            lastIdx = time()
            doUseNextChild = False

            for c in self.parent()._children:
                if "data" in dir(c) and "sortindex" in c.data.keys():
                    if doUseNextChild:
                        lastIdx = float(c.data["sortindex"])
                        break
                    if c == self:
                        doUseNextChild = True

            self.moveRequest({
                "skelType": skelType,
                "key": srcKey,
                "parentNode": self.data["parententry"],
                "sortindex": str((lastIdx + float(self.data["sortindex"])) / 2.0),
            })

    def EntryIcon(self):
        self.nodeImage.removeClass("is-hidden")
        # svg = embedsvg.get("icon-folder")
        svg = Icon("icon-folder")
        self.nodeImage.appendChild(svg)

    def toggleArrow(self):
        self.nodeToggle["title"] = translate("Expand/Collapse")
        self.nodeToggle.prependChild(
            SvgIcon("icon-arrow-right", title=translate("Expand/Collapse"))
        )

    def buildDescription(self):
        """Creates the visual representation of our entry."""
        # Find any bones in the structure having "frontend_default_visible" set.
        hasDescr = False

        for boneName, boneInfo in self.structure.items():
            if "params" in boneInfo.keys() and isinstance(boneInfo["params"], dict):
                params = boneInfo["params"]
                if (
                    "frontend_default_visible" in params
                    and params["frontend_default_visible"]
                ):
                    structure = {k: v for k, v in self.structure.items()}
                    wdg = BoneSelector.select(self.module, boneName, structure)

                    if wdg is not None:
                        self.nodeHeadline.appendChild(
                            wdg(self.module, boneName, structure).viewWidget(
                                self.data[boneName]
                            )
                        )
                        hasDescr = True

        # In case there is no bone configured for visualization, use a format-string
        if not hasDescr:
            format = "$(name)"  # default fallback

            if self.module in conf["modules"].keys():
                moduleInfo = conf["modules"][self.module]
                if "format" in moduleInfo.keys():
                    format = moduleInfo["format"]

            self.nodeHeadline.appendChild(
                formatString(
                    format,
                    self.data,
                    self.structure
                )
            )

            if self.data and "size" in self.data and self.data["size"]:

                def convert_bytes(num):
                    step_unit = 1000.0  # 1024 size

                    for x in ["bytes", "KB", "MB", "GB", "TB"]:
                        if num < step_unit:
                            return "%3.1f %s" % (num, x)
                        num /= step_unit

                size = convert_bytes(int(self.data["size"]))
                self.nodeSubline.appendChild(html5.TextNode(size))

    def onClick(self, event):
        if utils.doesEventHitWidgetOrChildren(event, self.nodeToggle):
            self.toggleExpand()
        else:
            self.widget.extendSelection(self)

        event.preventDefault()
        event.stopPropagation()

    def onDblClick(self, event):
        self.widget.activateSelection(self)
        if self.skelType == "node":
            self.toggleExpand()
        else:
            try:
                self.widget.parent().parent().parent().close()
            except:pass

        event.preventDefault()
        event.stopPropagation()

    def toggleExpand(self):
        """Toggle a Node and request if needed child elements."""
        if self.isExpanded:
            self.ol.addClass("is-hidden")
            self.nodeGrouper.removeClass("is-expanded")
            self.nodeGrouper.addClass("is-collapsed")
            self.removeClass("is-expanded")
            self.addClass("is-collapsed")
        else:
            self.ol.removeClass("is-hidden")
            self.nodeGrouper.addClass("is-expanded")
            self.nodeGrouper.removeClass("is-collapsed")
            self.addClass("is-expanded")
            self.removeClass("is-collapsed")

        self.isExpanded = not self.isExpanded

        if not self.childrenLoaded:
            self.childrenLoaded = True
            self.widget.requestChildren(self)


class TreeLeafWidget(TreeItemWidget):
    skelType = "leaf"

    def setStyle(self):
        """Leaf have a different color."""
        super(TreeLeafWidget, self).setStyle()
        self["style"]["background-color"] = "#f7edd2"
        self.additionalDropAreas()

    def toggleArrow(self):
        """Leafes cant be toggled."""
        if self.skelType == "leaf":
            self.nodeToggle["style"]["width"] = "27px"

    def EntryIcon(self):
        """Leafs have a different Icon."""
        self.nodeImage.removeClass("is-hidden")
        self.nodeImage.appendChild(Icon("icon-file"))

    def moveRequest(self, params):
        if self.currentStatus == "inner":
            self.currentStatus = None
            return  # do nothing, as this is a leaf.

        super().moveRequest(params)

    def onDragOver(self, event):
        if self.isDragged:
            return

        if "afterDiv" in dir(self):
            self.afterDiv.show()  # show dropzones
        if "beforeDiv" in dir(self):
            self.beforeDiv.show()

        self.leaveElement = False  # reset leaveMarker

        if "beforeDiv" in dir(self) and event.target == self.beforeDiv.element:
            super().onDragOver(event)
        elif "afterDiv" in dir(self) and event.target == self.afterDiv.element:
            super().onDragOver(event)
        else:
            event.preventDefault()
            event.stopPropagation()


class TreeNodeWidget(TreeItemWidget):
    skelType = "node"


class TreeWidget(html5.Div):
    """Base Widget that renders a tree."""

    """
    WARNING: THIS IS A (PROBABLY UNUSED), STRIPPED COPY OF THE TREEWIDGET FROM VIUR/VI!
             IN CASE YOU ARE DEBUGGING VIUR/VI, CHECK THE TREEWIDGET THERE FIRST!
    """

    nodeWidget = TreeNodeWidget
    leafWidget = TreeLeafWidget

    def __init__(self, module, rootNode=None, node=None, context=None, *args, **kwargs):
        """
            :param module: Name of the module we shall handle. Must be a hierarchy application!
            :type module: str
            :param rootNode: The repository we shall display. If none, we try to select one.
            :type rootNode: str or None
        """
        super(TreeWidget, self).__init__()
        self.addClass("vi-widget vi-widget--hierarchy is-drop-target")
        self["tabindex"] = 1
        self.sinkEvent(
            "onKeyDown",
            "onKeyUp",
            "onDrop",
            "onDragOver"
        )

        self.module = module

        # Try to get rootNode from context when available.
        if context and not (rootNode or node):
            context_var = conf["vi.context.prefix"] + "rootNode"
            if rootNode := context.get(context_var):
                del context[conf["vi.context.prefix"] + "rootNode"]

        self.context = context  # context
        self.rootNode = rootNode  # root node
        self.node = node or rootNode  # current node

        # Entry frame
        self.entryFrame = html5.Ol()
        self.entryFrame.addClass("hierarchy")
        self.appendChild(self.entryFrame)

        # States
        self._isCtrlPressed = False
        self._isShiftPressed = False
        self._ctlStartRow = None
        self._currentRow = None
        self._expandedNodes = []
        self._currentRequests = []
        self.path = []

        # Selection
        self.selectionCallback = None
        self.selectionAllow = TreeItemWidget
        self.selectionMulti = False
        self.selection = []
        self.isSelector = False

        # Events
        self.selectionChangedEvent = EventDispatcher("selectionChanged")
        self.selectionActivatedEvent = EventDispatcher("selectionActivated")
        self.rootNodeChangedEvent = EventDispatcher("rootNodeChanged")
        self.nodeChangedEvent = EventDispatcher("nodeChanged")

        self.viewLeafStructure = None
        self.viewNodeStructure = None
        self.addLeafStructure = None
        self.addNodeStructure = None
        self.editStructure = None
        self.editLeafStructure = None
        self.editNodeStructure = None

        # Either load content or get root Nodes
        if self.rootNode:
            self.requestStructure()
        else:
            NetworkService.request(
                self.module,
                "listRootNodes",
                self.context or {},
                successHandler=self.onSetDefaultRootNode,
                failureHandler=self._showErrorMsg
            )

    def requestStructure(self):
        NetworkService.request(None,
                               "/vi/getStructure/%s" % self.module,
                               successHandler=self.receivedStructure
                               )

    def receivedStructure(self, resp):
        data = NetworkService.decode(resp)
        for stype, structlist in data.items():
            structure = OrderedDict()
            for k, v in structlist:
                structure[k] = v
            if stype == "viewNodeSkel":
                self.viewNodeStructure = structure
            elif stype == "viewLeafSkel":
                self.viewLeafStructure = structure
            elif stype == "editNodeSkel":
                self.editNodeStructure = structure
            elif stype == "editLeafSkel":
                self.editLeafStructure = structure
            elif stype == "addNodeSkel":
                self.addNodeStructure = structure
            elif stype == "addLeafSkel":
                self.addLeafStructure = structure

        self.reloadData()

    def setSelector(self, callback, multi=True, allow=None):
        """
        Configures the widget as selector for a relationalBone and shows it.
        """
        self.isSelector = True
        self.selectionCallback = callback
        self.selectionAllow = allow or TreeItemWidget
        self.selectionMulti = multi
        conf["mainWindow"].stackWidget(self)

    def selectorReturn(self):
        """
        Returns the current selection to the callback configured with `setSelector`.
        """
        conf["mainWindow"].removeWidget(self)

        if self.selectionCallback:
            self.selectionCallback(self, [element.data for element in self.selection])

    def onKeyDown(self, event):
        if html5.isControl(event) or html5.getKey(event) == "Meta":
            self._isCtrlPressed = True

        elif html5.isShift(event):  # Shift
            self._isShiftPressed = True
            try:
                self._ctlStartRow = self._currentRow or self.selection[0]
            except:
                self._ctlStartRow = 0

    def onKeyUp(self, event):
        if html5.isControl(event) or html5.getKey(event) == "Meta":
            self._isCtrlPressed = False

        elif html5.isShift(event):
            self._isShiftPressed = False
            self._ctlStartRow = None

    def getActions(self):
        """
        Returns a list of actions that are being set for the ActionBar.
        Override this to provide additional actions.
        """
        return [
            "selectrootnode",
            "add",
            "add.node",
            "add.leaf",
            "edit",
            "clone",
            "delete",
            "|",
            "listview",
            "reload"
        ]

    def clearSelection(self):
        """
        Empties the current selection.
        """
        for element in self.selection:
            element.removeClass("is-focused")

        self.selection.clear()

    def extendSelection(self, element):
        """
        Extends the current selection to element.

        This is normally done by clicking or tabbing on an element.
        """

        if not isinstance(element, self.selectionAllow):
            logging.warning("Element %r not allowed for selection", element)
            return False

        # Perform selection
        if self._isCtrlPressed and self.selectionMulti:
            if element in self.selection:
                self.selection.remove(element)
                element.removeClass("is-focused")
            else:
                self.selection.append(element)
                element.addClass("is-focused")
        elif self._isShiftPressed and self.selectionMulti:
            self.selection = self.entryFrame._children[
                             min(self.entryFrame._children.index(element), self._currentRow): max(
                                 self.entryFrame._children.index(element), self._currentRow) + 1]

            for x in self.entryFrame._children:
                x.removeClass("is-focused")

            for x in self.selection:
                x.addClass("is-focused")

        else:
            self.clearSelection()
            self.selection.append(element)
            element.addClass("is-focused")

        if self.selectionMulti:
            try:
                self._currentRow = self.entryFrame.children().index(element)
            except ValueError:
                self._currentRow = None

        self.selectionChangedEvent.fire(self, self.selection)

    def activateSelection(self, element):
        """
        Activates the current selection or element.

        An activation mostly is an action like selecting or editing an item.
        This is normally done by double-clicking an element.
        """
        if self.selection:
            if self.selectionCallback:
                self.selectorReturn()
            else:
                self.selectionActivatedEvent.fire(self, self.selection)

    def requestChildren(self, element):
        self.loadNode(element.data["key"])

    def _showErrorMsg(self, req=None, code=None):
        """
            Removes all currently visible elements and displayes an error message
        """
        self.entryFrame.hide()

        errorDiv = html5.Div()
        errorDiv.addClass("popup popup--center popup--local msg msg--error is-active error_msg")
        if code and (code == 401 or code == 403):
            txt = translate("Access denied!")
        else:
            txt = translate("Error {code} occurred!", code=code)

        errorDiv.addClass("error_code_%s" % (code or 0))  # fixme: not an ignite style?
        errorDiv.appendChild(html5.TextNode(txt))
        self.appendChild(errorDiv)

    def onDataChanged(self, module, *args, **kwargs):
        if module != self.module:
            isRootNode = False
            for k, v in conf["modules"].items():
                if (k == module
                        and v.get("handler") == "list"
                        and self.module in v.get("changeInvalidates", [])):
                    isRootNode = True
                    break

            if not isRootNode:
                return

        if not self.viewNodeStructure:
            self.requestStructure()
        else:
            self.reloadData()

    def onAttach(self):
        super(TreeWidget, self).onAttach()
        NetworkService.registerChangeListener(self)

    def onDetach(self):
        super(TreeWidget, self).onDetach()

    # NetworkService.removeChangeListener(self)

    def itemForKey(self, key, elem=None):
        """
            Returns the HierarchyWidget displaying the entry with the given key.
            :param key: The key (id) of the item.
            :type key: str
            :returns: HierarchyItem
        """
        if elem is None:
            elem = self.entryFrame
        for child in elem._children:
            if child.data["key"] == key:
                return (child)
            tmp = self.itemForKey(key, child.ol)
            if tmp is not None:
                return (tmp)
        return (None)

    def onSetDefaultRootNode(self, req):
        """
            We requested the list of rootNodes for that module and that
            request just finished. Parse the respone and set our rootNode
            to the first rootNode received.
        """
        data = NetworkService.decode(req)
        if len(data) > 0:
            self.setRootNode(data[0]["key"], self.node)

    def setRootNode(self, rootNode, node=None):
        """
            Set the currently displayed hierarchy to 'rootNode'.
            :param rootNode: Key of the rootNode which children we shall display
            :type rootNode: str
        """
        self.rootNode = rootNode
        self.node = node or rootNode
        self.currentKey = self.rootNode
        self._currentCursor = None
        self.rootNodeChangedEvent.fire(rootNode)
        if node:
            self.nodeChangedEvent.fire(node)
        if not self.viewNodeStructure:
            self.requestStructure()
        else:
            self.reloadData()

    def reloadData(self):
        """
            Reload the data were displaying.
        """

        def collectExpandedNodes(currNode):
            res = []
            for c in currNode.children():
                if isinstance(c, TreeItemWidget):
                    if c.isExpanded:
                        res.append(c.data["key"])

                    res.extend(collectExpandedNodes(c.ol))

            return res

        self._expandedNodes = collectExpandedNodes(self.entryFrame)
        self._currentRequests = []
        self.entryFrame.removeAllChildren()

        self.loadNode(self.rootNode)

    def loadNode(self, node, skelType=None, cursor=None, overrideParams=None):
        """
            Fetch the (direct) children of the given node.
            Once the list is received, append them to their parent node.
            :param node: Key of the node to fetch
            :type node: str
        """
        self.node = node

        # In case no skelType was provided, reload both.
        if skelType is None:
            self._currentRequests.clear()

            self.loadNode(node, "node")
            if self.leafWidget:
                self.loadNode(node, "leaf")
            return

        params = {
            "skelType": skelType,
            "parententry": self.node,
            "orderby": "sortindex",
            "limit": 99
        }

        if cursor:
            params["cursor"] = cursor

        if overrideParams:
            params.update(overrideParams)

        if self.context:
            params.update(self.context)

        req = NetworkService.request(
            self.module, "list", params,
            successHandler=self._onRequestSucceded,
            failureHandler=self._showErrorMsg
        )
        req.skelType = skelType
        self._currentRequests.append(req)

    def _onRequestSucceded(self, req):
        """
            The NetworkRequest for a (sub)node finished.
            Create a new HierarchyItem for each entry received and add them to our view
        """
        if req not in self._currentRequests:
            # Prevent inserting old (stale) data
            return

        self._currentRequests.remove(req)
        data = NetworkService.decode(req)

        if self.node == self.rootNode:
            ol = self.entryFrame
        else:
            tmp = self.itemForKey(self.node)
            if not tmp:
                ol = self.entryFrame
            else:
                ol = tmp.ol

        for skel in data["skellist"]:
            if req.skelType == "leaf":
                hi = self.leafWidget(self.module, skel, self.viewLeafStructure, self)
            else:
                hi = self.nodeWidget(self.module, skel, self.viewNodeStructure, self)

            ol.appendChild(hi)

            if hi.data["key"] in self._expandedNodes:
                hi.toggleExpand()
                if not hi.childrenLoaded:
                    hi.childrenLoaded = True
                    self.loadNode(hi.data["key"])

        ol.sortChildren(self.getChildKey)

        if not ol.children() and ol != self.entryFrame:
            ol.parent().addClass("has-no-child")

        if data["skellist"] and data["cursor"]:
            self.loadNode(self.node, req.skelType, data["cursor"])

    def onDrop(self, event):
        """
            We got a drop event. Make that item a direct child of our rootNode
        """
        if event.target == self.element:  # only move if droped
            srcKey, skelType = event.dataTransfer.getData("Text").split("/")

            NetworkService.request(self.module, "move",
                                   {"skelType": skelType, "key": srcKey, "parentNode": self.rootNode}, secure=True,
                                   modifies=True)
            event.stopPropagation()

    def onDragOver(self, event):
        """
            Allow dropping children on the rootNode
        """
        event.preventDefault()
        event.stopPropagation()

    def getChildKey(self, widget):
        """
            Order by sortindex
        """
        name = float(widget.data.get("sortindex") or 0)
        return name

    @staticmethod
    def canHandle(moduleName, moduleInfo):
        return moduleInfo["handler"] == "tree" or moduleInfo["handler"].startswith("tree.")


ModuleWidgetSelector.insert(0, TreeWidget.canHandle, TreeWidget)
DisplayDelegateSelector.insert(0, TreeWidget.canHandle, TreeWidget)


class BrowserLeafWidget(TreeLeafWidget):
    def setStyle(self):
        self["style"]["background-color"] = "#f7edd2"
        self["class"].append("hierarchy-item")
        self.additionalDropAreas()
        self.buildDescription()


# self.toggleArrow()
# self.EntryIcon()


class BrowserNodeWidget(TreeNodeWidget):
    def setStyle(self):
        self["class"].append("hierarchy-item")
        self.additionalDropAreas()
        self.buildDescription()


# self.toggleArrow()
# self.EntryIcon()


class BreadcrumbNodeWidget(TreeNodeWidget):
    def setStyle(self):
        # self[ "style" ][ "background-color" ] = "#f7edd2"
        self.buildDescription()


# self.toggleArrow()
# self.EntryIcon()


class TreeBrowserWidget(TreeWidget):
    leafWidget = BrowserLeafWidget
    nodeWidget = BrowserNodeWidget

    def __init__(self, module, rootNode=None, node=None, context=None, *args, **kwargs):
        super(TreeBrowserWidget, self).__init__(module, rootNode, node, context, *args, **kwargs)
        self.selectionMulti = True
        self.pathList = html5.Div()
        self.pathList.addClass("vi-tree-breadcrumb")
        self.appendChild(self.pathList, self.entryFrame)


    def reloadData(self):
        super().reloadData()
        self.rebuildPath()

    def rebuildPath(self):
        """
            Rebuild the displayed path-list.
        """
        self.pathList.removeAllChildren()

        NetworkService.request(
            self.module, "view/node/%s" % self.node,
            successHandler=self.onPathRequestSucceded
        )

    def onPathRequestSucceded(self, req):
        """
            Rebuild the displayed path-list according to request data
        """
        answ = NetworkService.decode(req)
        skel = answ["values"]

        if skel["parententry"] and skel["parententry"] != skel["key"]:
            c = BreadcrumbNodeWidget(self.module, skel, {"name": {"descr": "Name"}}, self)

            NetworkService.request(
                self.module, "view/node/%s" % skel["parententry"],
                successHandler=self.onPathRequestSucceded
            )

        else:
            c = BreadcrumbNodeWidget(self.module, {"key": self.rootNode, "name": "root"}, {"name": {"descr": "Name"}},
                                     self)
            c.addClass("is-rootnode")

        self.pathList.prependChild(c)

    def activateSelection(self, element):
        if isinstance(element, TreeNodeWidget):
            self.entryFrame.removeAllChildren()
            self.loadNode(element.data["key"])
            self.rebuildPath()
        else:
            super().activateSelection(element)

    @staticmethod
    def canHandle(module, moduleInfo):
        return moduleInfo["handler"] == "tree.browser" or moduleInfo["handler"].startswith("tree.browser.")

ModuleWidgetSelector.insert(0, TreeBrowserWidget.canHandle, TreeBrowserWidget)
DisplayDelegateSelector.insert(0, TreeBrowserWidget.canHandle, TreeBrowserWidget)
