# -*- coding: utf-8 -*-
import logging

from time import time

from flare import html5, utils
from flare.forms import boneSelector, moduleWidgetSelector, displayDelegateSelector
from flare.network import NetworkService
from flare.config import conf
from flare.i18n import translate
from flare.forms.formatString import formatString
from flare.icons import SvgIcon, Icon


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

        self.structure = structure
        self.widget = widget

        self.isExpanded = False
        self.childrenLoaded = False
        self.isDragged = False

        self.sortindex = data["sortindex"] if "sortindex" in data else 0

        # fixme: HTML below contains inline styling...
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
                self.disableDragMarkers, 2000
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
            w.setTimeout(self.disableDragMarkers, 5000)

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
            NetworkService.request(
                self.module,
                "move",
                {"skelType": skelType, "key": srcKey, "parentNode": self.data["key"]},
                secure=True,
                modifies=True,
            )

        elif self.currentStatus == "top":
            parentID = self.data["parententry"]
            if parentID:
                lastIdx = 0
                for c in self.parent()._children:
                    if "data" in dir(c) and "sortindex" in c.data.keys():
                        if c == self:
                            break
                        lastIdx = float(c.data["sortindex"])
                newIdx = str((lastIdx + float(self.data["sortindex"])) / 2.0)
                req = NetworkService.request(
                    self.module,
                    "move",
                    {
                        "skelType": skelType,
                        "key": srcKey,
                        "parentNode": parentID,
                        "sortindex": newIdx,
                    },
                    secure=True,
                    modifies=True,
                )

        elif self.currentStatus == "bottom":
            parentID = self.data["parententry"]

            if parentID:
                lastIdx = time()
                doUseNextChild = False
                for c in self.parent()._children:
                    if "data" in dir(c) and "sortindex" in c.data.keys():
                        if doUseNextChild:
                            lastIdx = float(c.data["sortindex"])
                            break
                        if c == self:
                            doUseNextChild = True

                newIdx = str((lastIdx + float(self.data["sortindex"])) / 2.0)
                req = NetworkService.request(
                    self.module,
                    "move",
                    {
                        "skelType": skelType,
                        "key": srcKey,
                        "parentNode": parentID,
                        "sortindex": newIdx,
                    },
                    secure=True,
                    modifies=True,
                )

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
                    wdg = boneSelector.select(self.module, boneName, structure)

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
                    self.structure,
                    language=conf["flare.language.current"],
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

    def toggleArrow(self):
        """Leafes cant be toggled."""
        if self.skelType == "leaf":
            self.nodeToggle["style"]["width"] = "27px"

    def EntryIcon(self):
        """Leafs have a different Icon."""
        self.nodeImage.removeClass("is-hidden")
        self.nodeImage.appendChild(Icon("icon-file"))


class TreeNodeWidget(TreeItemWidget):
    skelType = "node"


class TreeWidget(html5.Div):
    """Base Widget that renders a tree."""

    nodeWidget = TreeNodeWidget
    leafWidget = TreeLeafWidget

    def __init__(self, module, rootNode=None, node=None, context=None, *args, **kwargs):
        """Instantiate TreeWidget.

        :param module: Name of the module we shall handle. Must be a hierarchy application!
        :type module: str
        :param rootNode: The repository we shall display. If none, we try to select one.
        :type rootNode: str or None
        """
        super(TreeWidget, self).__init__()

    def setSelector(self, callback, multi=True, allow=None):
        """Configures the widget as selector for a relationalBone and shows it."""
        self.selectionCallback = callback
        self.selectionAllow = allow or TreeItemWidget
        self.selectionMulti = multi

        logging.debug("TREEEE")

    @staticmethod
    def canHandle(moduleName, moduleInfo):
        return moduleInfo["handler"] == "tree" or moduleInfo["handler"].startswith(
            "tree."
        )


moduleWidgetSelector.insert(0, TreeWidget.canHandle, TreeWidget)
displayDelegateSelector.insert(0, TreeWidget.canHandle, TreeWidget)


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

    @staticmethod
    def canHandle(module, moduleInfo):
        return moduleInfo["handler"] == "tree.browser" or moduleInfo[
            "handler"
        ].startswith("tree.browser.")


moduleWidgetSelector.insert(0, TreeBrowserWidget.canHandle, TreeBrowserWidget)
displayDelegateSelector.insert(0, TreeBrowserWidget.canHandle, TreeBrowserWidget)
