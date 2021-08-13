import logging

from js import console

from flare import html5
from flare.icons import SvgIcon
from flare.forms.widgets.file import FilePreviewImage, Uploader
from flare.forms.widgets.relational import InternalEdit
from flare.forms.widgets.tree import TreeLeafWidget, TreeNodeWidget
from flare.forms.widgets.list import ListWidget
from flare.config import conf
from flare.forms import boneSelector, formatString, displayString, moduleWidgetSelector
from .base import BaseBone, BaseEditWidget, BaseMultiEditWidget


def _getDefaultValues(structure):
    """Gets defaultValues from a structure."""
    defaultValues = {}
    for k, v in {k: v for k, v in structure}.items():
        if (
            "params" in v.keys()
            and v["params"]
            and "defaultValue" in v["params"].keys()
        ):
            defaultValues[k] = v["params"]["defaultValue"]

    return defaultValues


class RelationalEditWidget(BaseEditWidget):
    style = ["flr-value", "flr-value--relational"]

    def createWidget(self):
        tpl = html5.Template()
        # language=HTML
        widgetList = self.fromHTML(
            """<div class='flr-value--relational-wrapper'>
                <div [name]="destWidget" class="input-group-item" readonly>
                <flare-button [name]="selectBtn" class="btn--select input-group-item input-group-item--last" text="Select" icon="icon-check"></flare-button>
                <flare-button hidden [name]="deleteBtn" class="btn--delete input-group-item" text="Delete" icon="icon-cross"></flare-button>
                </div>
            """
        )
        tpl.appendChild(widgetList, bindTo=self)
        return tpl

    def updateWidget(self):
        if self.bone.readonly:
            self.destWidget.disable()
            self.selectBtn.hide()
            self.deleteBtn.hide()
        else:
            self.destWidget.enable()
            self.selectBtn.show()

            # Only allow to delete entry when not multiple and not required!
            if not self.bone.multiple and not self.bone.required:
                self.deleteBtn.show()
                self.selectBtn.removeClass("input-group-item--last")

    def __init__(self, bone, language=None, **kwargs):
        super().__init__(bone)
        self.sinkEvent("onChange")

        self.value = None
        self.language = language

        # Relation edit widget
        if self.bone.dataStructure:
            self.dataWidget = InternalEdit(
                self.bone.dataStructure,
                readOnly=self.bone.readonly,
                errorInformation=kwargs.get("errorInformation"),
                defaultCat=None,  # fixme: IMHO not necessary
                errorQueue=self.bone.errorQueue,
                prefix="{}.rel".format(self.bone.boneName),
            )
            self.addClass("flr-bone--relational-using")
            self.appendChild(self.dataWidget)
        else:
            self.dataWidget = None

        # Current data state
        self.destKey = None

    def updateString(self):
        if not self.value:
            if self.dataWidget:
                self.dataWidget.disable()

            return

        if display := self.bone.boneStructure["params"].get("display"):
            displayWidgets = displayString(
                display,
                self.value,
                self.bone.boneStructure,
                self.language
            )

            self.destWidget.replaceChild(displayWidgets or conf["emptyValue"])
        else:
            self.destWidget.replaceChild(
                formatString(
                    self.bone.formatString,
                    {"value": self.value}
                ) or conf["emptyValue"]
            )

    def onChange(self, event):
        if self.dataWidget:
            self.value["rel"] = self.dataWidget.doSave()
            self.updateString()

    def unserialize(self, value=None):
        if not value:
            self.destKey = None
            self.destWidget.removeAllChildren()
        else:
            self.destKey = value["dest"]["key"]

        if self.dataWidget:
            self.dataWidget.unserialize((value["rel"] or {}) if value else {})
            self.dataWidget.enable()

        self.value = value
        self.updateString()

    def serialize(self):
        # fixme: Maybe we need a serializeForDocument also?
        if self.destKey and self.dataWidget:
            res = {"key": self.destKey}
            res.update(
                self.dataWidget.serializeForPost()
            )  # fixme: call serializeForPost()?
            return res

        return self.destKey or None

    def onSelectBtnClick(self):
        selector = conf["selectors"].get(self.bone.destModule)
        if selector is None:
            selector = moduleWidgetSelector.select(
                self.bone.destModule, self.bone.destInfo
            )
            assert selector, "No selector can be found for %r" % self.destModule

            selector = selector(self.bone.destModule, **self.bone.destInfo)

            conf["selectors"][self.bone.destModule] = selector

        # Set a context if configured so
        context = self.bone.boneStructure["params"].get("context")
        if context:
            selector.setContext(context)

        # Start widget with selector callback
        selector.setSelector(
            lambda selector, selection: self.unserialize(
                {
                    "dest": selection[0],
                    "rel": _getDefaultValues(self.bone.dataStructure)
                    if self.bone.dataStructure
                    else None,
                }
            ),
            multi=self.bone.multiple,
            allow=self.bone.selectorAllow,
        )

    def onDeleteBtnClick(self):
        self.unserialize()


class RelationalViewWidget(html5.Div):
    style = ["flr-value", "flr-value--relational"]

    def __init__(self, bone, language=None, **kwargs):
        super().__init__()
        self.bone = bone
        self.language = language
        self.value = None

    def unserialize(self, value=None):
        self.value = value

        if self.value:
            if display := self.bone.boneStructure["params"].get("display"):
                displayWidgets = displayString(
                    display,
                    value,
                    self.bone.boneStructure,
                    language=self.language,
                )

                self.replaceChild(displayWidgets or conf["emptyValue"])
            else:
                self.replaceChild(
                    formatString(
                        self.bone.formatString,
                        {"value": self.value}
                    ) or conf["emptyValue"]
                )

    def serialize(self):
        return self.value  # fixme: The format here is invalid for POST!


class RelationalMultiEditWidget(BaseMultiEditWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addBtn["text"] = "Add"
        self.addBtn["icon"] = "icon-add"
        self.addBtn.removeClass("btn--add")
        self.addBtn.addClass("btn--add")

    def onAddBtnClick(self):
        selector = conf["selectors"].get(self.bone.destModule)

        if selector is None:
            selector = moduleWidgetSelector.select(
                self.bone.destModule, self.bone.destInfo
            )
            assert selector, "No selector can be found for %r" % self.destModule

            selector = selector(self.bone.destModule, **self.bone.destInfo)

            conf["selectors"][self.bone.destModule] = selector

        # Set a context if configured so
        context = self.bone.boneStructure["params"].get("context")
        if context:
            selector.setContext(context)

        # Start widget with selector callback
        selector.setSelector(
            self._addEntriesFromSelection,
            multi=self.bone.multiple,
            allow=self.bone.selectorAllow,
        )

    def _addEntriesFromSelection(self, selector, selection):
        for entry in selection:
            self.addEntry(
                {
                    "dest": entry,
                    "rel": _getDefaultValues(self.bone.boneStructure["using"])
                    if self.bone.boneStructure["using"]
                    else None,
                }
            )
        self.parent().show()


class RelationalBone(BaseBone):
    editWidgetFactory = RelationalEditWidget
    viewWidgetFactory = RelationalViewWidget
    multiEditWidgetFactory = RelationalMultiEditWidget

    selectorAllow = (TreeNodeWidget, TreeLeafWidget)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.formatString = self.boneStructure["format"]
        self.destModule = self.boneStructure["module"]
        self.destInfo = conf["modules"].get(self.destModule, {"handler": "list"})
        self.destStructure = self.boneStructure["relskel"]
        self.dataStructure = self.boneStructure["using"]

    # logging.debug("RelationalBone: %r, %r", self.destModule, self.destInfo)

    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName]["type"] == "relational" or skelStructure[
            boneName
        ]["type"].startswith("relational.")


boneSelector.insert(1, RelationalBone.checkFor, RelationalBone)


# --- hierarchyBone ---


class HierarchyBone(
    RelationalBone
):  # fixme: this bone is obsolete! It behaves exactly as relational.
    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName]["type"] == "hierarchy" or skelStructure[
            boneName
        ]["type"].startswith("hierarchy.")


boneSelector.insert(1, HierarchyBone.checkFor, HierarchyBone)


# --- treeItemBone ---


class TreeItemBone(RelationalBone):
    selectorAllow = TreeLeafWidget

    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName]["type"] == "relational.tree.leaf"


boneSelector.insert(2, TreeItemBone.checkFor, TreeItemBone)


# --- treeDirBone ---


class TreeDirBone(RelationalBone):
    selectorAllow = TreeNodeWidget

    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName][
            "type"
        ] == "relational.tree.node" or skelStructure[boneName]["type"].startswith(
            "relational.tree.node."
        )


boneSelector.insert(2, TreeDirBone.checkFor, TreeDirBone)


# --- fileBone direct upload without repo---


class FileEditDirectWidget(RelationalEditWidget):
    style = ["flr-value", "flr-value--file"]

    def createWidget(self):
        tpl = html5.Template()
        self.previewImg = FilePreviewImage()
        self.appendChild(self.previewImg)

        def FileApiTest():
            testDiv = html5.Div()
            divparamslist = dir(testDiv.element)
            return (
                (
                    "draggable" in divparamslist
                    or ("ondragstart" in divparamslist and "ondrop" in divparamslist)
                )
                and "FormData" in dir(html5.window)
                and "FileReader" in dir(html5.window)
            )

        self.hasFileApi = FileApiTest()

        # language=html
        tpl.appendChild(
            self.fromHTML(
                """
                <div class="flr-bone-widgets">
                    <div class="flr-widgets-item input-group" [name]='filerow'>
                        <flare-input [name]="destWidget" readonly>
                        <flare-button [name]="selectBtn" class="btn--select input-group-item--last" text="Select" icon="icon-select"></flare-button>
                        <flare-button hidden [name]="deleteBtn" class="btn--delete" text="Delete" icon="icon-delete"></flare-button>
                    </div>
                    <div class="flr-widgets-item">
                        <div [name]="dropArea" class="supports-upload">
                            <flare-svg-icon value='icon-upload-file' title='Upload'> </flare-svg-icon>
                            <label for="inplace-upload" class="flr-inplace-upload-label"><strong>Datei auswählen</strong><span [name]="dropText"> oder hierhin ziehen</span>.</label>
                            <input id="inplace-upload" class="flr-inplace-upload" type="file" [name]="files" files selected"/>
                        </div>
                        <p [name]="uploadResult" style="display: none;"></p>
                    </div>
                </div>
            """
            )
        )

        self.filerow.hide()

        if not self.hasFileApi:
            self.dropText.hide()
        else:
            for event in ["onDragEnter", "onDragOver", "onDragLeave", "onDrop"]:
                setattr(self.dropArea, event, getattr(self, event))
                self.dropArea.sinkEvent(event)

        self.sinkEvent("onChange")
        return tpl

    def updateWidget(self):
        if self.bone.readonly:
            self.destWidget.disable()
            self.selectBtn.hide()
            self.deleteBtn.hide()
            self.dropArea.hide()
        else:
            self.destWidget.enable()
            self.selectBtn.show()
            self.dropArea.show()

            # Only allow to delete entry when not multiple and not required!
            if not self.bone.multiple and not self.bone.required:
                self.deleteBtn.show()
                self.selectBtn.removeClass("input-group-item--last")

    def onChange(self, event):
        if event.target.files:
            file = event.target.files[0]
            self.startUpload(file)

    def startUpload(self, file):
        uploader = Uploader(
            file, None, showResultMessage=False, module=self.bone.module
        )
        self.appendChild(uploader)
        uploader.uploadSuccess.register(self)
        uploader.uploadFailed.register(self)

    def onDragEnter(self, event):
        console.log("onDragEnter", event)
        event.stopPropagation()
        event.preventDefault()

    def onDragOver(self, event):
        console.log("onDragEnter", event)
        event.stopPropagation()
        event.preventDefault()

    def onDragLeave(self, event):
        console.log("onDragLeave", event)
        event.stopPropagation()
        event.preventDefault()

    def onDrop(self, event):
        self.uploadResult["style"]["display"] = "none"
        event.stopPropagation()
        event.preventDefault()
        files = event.dataTransfer.files
        if files.length:  # only pick first file!!!
            currentFile = files.item(0)
            self.startUpload(currentFile)

    def onUploadSuccess(self, uploader, entry):
        self.destKey = entry["key"]
        self.value = {"dest": entry, "rel": None}
        self.previewImg.setFile(entry)
        self.updateString()
        self.updateWidget()
        self.removeChild(uploader)
        self.uploadResult.hide()
        self.filerow.show()
        # self.uploadResult.element.innerHTML = "Upload erfolgreich"
        # self.uploadResult["style"]["display"] = "block"
        if not self.bone.multiple:
            self.dropArea.hide()

    def onUploadFailed(self, uploader, errorCode):
        self.removeChild(uploader)
        self.uploadResult.element.innerHTML = (
            "Upload abgebrochen mit Fehlercode {0}".format(errorCode)
        )
        self.uploadResult.show()

    def unserialize(self, value=None):
        super().unserialize(value)

        if self.value:
            self.previewImg.setFile(self.value["dest"])

            self.dropArea.hide()
            self.filerow.show()

    def onDeleteBtnClick(self):
        self.unserialize()
        self.dropArea.show()  # show drop Area
        self.uploadResult.hide()  # hide Status
        self.files["value"] = ""  # reset input
        self.previewImg.setFile(None)  # reset Preview
        self.filerow.hide()


class FileViewWidget(RelationalViewWidget):
    def unserialize(self, value=None):
        self.replaceChild(FilePreviewImage(value["dest"] if value else None))


class FileDirectBone(TreeItemBone):
    editWidgetFactory = FileEditDirectWidget
    viewWidgetFactory = FileViewWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.destInfo = conf["modules"].get(
            self.destModule, {"handler": "tree.simple.file"}
        )

    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName][
            "type"
        ] == "relational.tree.leaf.file" or skelStructure[boneName]["type"].startswith(
            "relational.tree.leaf.file."
        )


boneSelector.insert(3, FileDirectBone.checkFor, FileDirectBone)


# --- fileBone ---


class FileEditWidget(RelationalEditWidget):
    style = ["flr-value", "flr-value--relational", "flr-value--file"]

    def createWidget(self):
        self.previewImg = FilePreviewImage()
        self.appendChild(self.previewImg)

        return super().createWidget()

    def unserialize(self, value=None):
        super().unserialize(value)

        if self.value and self.value["dest"] and "downloadUrl" in self.value["dest"]:
            self.previewImg.setFile(self.value["dest"])


class FileBone(TreeItemBone):
    editWidgetFactory = FileEditWidget
    viewWidgetFactory = FileViewWidget

    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName][
            "type"
        ] == "relational.tree.leaf.file" or skelStructure[boneName]["type"].startswith(
            "relational.tree.leaf.file."
        )


boneSelector.insert(5, FileBone.checkFor, FileBone)
