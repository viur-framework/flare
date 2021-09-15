import json, pyodide
from flare.ignite import *
from flare.icons import Icon
from flare.i18n import translate
from flare.popup import Popup
from flare.event import EventDispatcher
from flare.forms import moduleWidgetSelector, displayDelegateSelector
from flare.network import NetworkService, DeferredCall
from flare.button import Button
from flare.forms.widgets.tree import TreeNodeWidget, TreeLeafWidget, TreeBrowserWidget


def getImagePreview(data, cropped=False, size=150):
    if "downloadUrl" not in data:  # fixme is there a possibility show a preview?
        return None

    return data["downloadUrl"]


class Search(html5.Div):
    def __init__(self, *args, **kwargs):
        super(Search, self).__init__(*args, **kwargs)
        self.startSearchEvent = EventDispatcher("startSearch")
        self.addClass("flr-search")
        self.searchLbl = html5.H2()
        self.searchLbl.appendChild(html5.TextNode(translate("Fulltext search")))
        self.searchLbl.addClass("flr-search-label")
        self.appendChild(self.searchLbl)
        self.searchInput = Input()
        self.searchInput["type"] = "text"
        self.appendChild(self.searchInput)
        self.btn = Button(translate("Search"), callback=self.doSearch)
        self.appendChild(self.btn)
        self.sinkEvent("onKeyDown")
        self.last_search = ""

    def doSearch(self, *args, **kwargs):
        if self.searchInput["value"] != self.last_search:
            if len(self.searchInput["value"]):
                self.startSearchEvent.fire(self.searchInput["value"])
            else:
                self.resetSearch()

            self.last_search = self.searchInput["value"]

    def resetSearch(self):
        self.startSearchEvent.fire(None)

    def onKeyDown(self, event):
        if html5.isReturn(event):
            self.doSearch()
            event.preventDefault()
            event.stopPropagation()

    def resetLoadingState(self):
        if "is-loading" in self.btn["class"]:
            self.btn.removeClass("is-loading")

    def reevaluate(self):
        self.doSearch()

    def focus(self):
        self.searchInput.focus()


class FileImagePopup(Popup):
    def __init__(self, preview, *args, **kwargs):
        super(FileImagePopup, self).__init__(
            title=preview.currentFile.get("name", translate("Unnamed Image")),
            className="image-viewer",
            *args,
            **kwargs
        )
        self.sinkEvent("onClick")
        self.preview = preview

        img = html5.Img()
        img["src"] = getImagePreview(preview.currentFile, size=None)
        self.popupBody.appendChild(img)

        btn = Button(translate("Download"), self.onDownloadBtnClick)
        btn.addClass("btn--download")
        self.popupFoot.appendChild(btn)

        btn = Button(translate("Close"), self.onClick)
        btn.addClass("btn--close")
        self.popupFoot.appendChild(btn)

    def onClick(self, event):
        self.close()

    def onDownloadBtnClick(self, sender=None):
        self.preview.imageDownload = True
        self.preview.download()


class FilePreviewImage(html5.Div):
    def __init__(self, file=None, size=150, *args, **kwargs):
        super(FilePreviewImage, self).__init__(*args, **kwargs)
        self.addClass("flr-file-imagepreview")
        self.sinkEvent("onClick")

        self.size = size

        self.downloadA = html5.A()
        self.downloadA.hide()
        self.appendChild(self.downloadA)
        self.isImage = False
        self.downloadOnly = False
        self.currentFile = None
        self.previewIcon = None
        self.setFile(file)
        self.imageDownload = False

    def setFile(self, file):
        if self.previewIcon:
            self.removeChild(self.previewIcon)
            self.previewIcon = None

        if not file:
            self.addClass("is-hidden")
            return

        self.removeClass("is-hidden")

        svg = None
        self.currentFile = file

        preview = getImagePreview(file, cropped=True, size=self.size) if file else None

        if preview:
            self.downloadOnly = self.isImage = True

        else:
            self.isImage = False
            self.downloadOnly = True

            if file:
                mime = file.get("mimetype")
                if mime:
                    for mimesplit in mime.split("/"):
                        for icon in ["text", "pdf", "image", "audio", "video", "zip"]:
                            if icon in mimesplit:
                                svg = "icon-%s-file" % icon
                                self.downloadOnly = False
                                break
            else:
                self.addClass("no-preview")

            if not svg:
                svg = "file"

        if preview:
            self.removeClass("no-preview")

        self.previewIcon = Icon(
            preview or svg,
            fallbackIcon="icon-image-file",
            title=self.currentFile.get("name"),
        )
        self.appendChild(self.previewIcon)

        if self.currentFile:
            self.addClass("is-clickable")
        else:
            self.removeClass("is-clickable")

    def download(self):
        if not self.currentFile:
            return

        self.downloadA["href"] = self.currentFile["downloadUrl"]
        self.downloadA["target"] = "_blank"
        self.downloadA.element.click()

    def onClick(self, sender=None):
        if not self.currentFile:
            return

        if self.isImage and not self.imageDownload:
            FileImagePopup(self)
        else:
            self.imageDownload = False
            if self.downloadOnly:
                self.download()
                return

            if self.currentFile.get("name"):
                file = "%s/fileName=%s" % (
                    self.currentFile["downloadUrl"],
                    self.currentFile["name"],
                )

            html5.window.open(file)


class Uploader(Progress):
    """Uploads a file to the server while providing visual feedback of the progress."""

    def __init__(
        self,
        file,
        node,
        context=None,
        showResultMessage=True,
        module="file",
        *args,
        **kwargs
    ):
        """Instantiate uploader.

        :param file: The file to upload
        :type file: A javascript "File" Object
        :param node: Key of the desired node of our parents tree application or None for an anonymous upload.
        :type node: str or None
        :param showResultMessage: if True replaces progressbar with complete message on success
        :type showResultMessage: bool
        """
        super(Uploader, self).__init__()
        self.uploadSuccess = EventDispatcher("uploadSuccess")
        self.uploadFailed = EventDispatcher("uploadFailed")
        self.responseValue = None
        self.targetKey = None
        self.module = module
        self.showResultMessage = showResultMessage
        self.context = context

        params = {"fileName": file.name, "mimeType": (file.type or "application/octet-stream")}
        if node:
            params["node"] = node

        r = NetworkService.request(
            module,
            "getUploadURL",
            params=params,
            successHandler=self.onUploadUrlAvailable,
            failureHandler=self.onFailed,
            secure=True,
        )
        r.file = file
        r.node = node
        self.node = node

    # self.parent().addClass("is-uploading")

    def onUploadUrlAvailable(self, req):
        """Internal callback - the actual upload url (retrieved by calling /file/getUploadURL) is known."""
        params = NetworkService.decode(req)["values"]

        self.proxy_callback = pyodide.create_proxy(self.onLoad)

        if "uploadKey" in params:  # New Resumeable upload format
            self.targetKey = params["uploadKey"]
            html5.window.fetch(params["uploadUrl"], **{"method": "POST", "body": req.file, "mode": "no-cors"}).then(
                self.proxy_callback)
        else:
            formData = html5.jseval("new FormData();")

            for key, value in params["params"].items():
                if key == "key":
                    self.targetKey = value[:-16]  # Truncate source/file.dat
                    fileName = req.file.name
                    value = value.replace("file.dat", fileName)

                formData.append(key, value)
            formData.append("file", req.file)

            html5.window.fetch(params["url"], **{"method": "POST", "body": formData, "mode": "no-cors"}).then(
                self.proxy_callback)

    def onSkeyAvailable(self, req):
        """Internal callback - the Security-Key is known.

        # Only for core 2.x needed
        """
        formData = html5.jseval("new FormData();")
        formData.append("file", req.file)

        if self.context:
            for k, v in self.context.items():
                formData.append(k, v)

        if req.node and str(req.node) != "null":
            formData.append("node", req.node)

        formData.append("skey", NetworkService.decode(req))
        self.xhr = html5.jseval("new XMLHttpRequest()")
        self.xhr.open("POST", req.destUrl)
        self.xhr.onload = self.onLoad
        self.xhr.upload.onprogress = self.onProgress
        self.xhr.send(formData)

    def onLoad(self, *args, **kwargs):
        """Internal callback - The state of our upload changed."""
        NetworkService.request(
            self.module, "add", {
                "key": self.targetKey,
                "node": self.node,
                "skelType": "leaf"
            },
            successHandler=self.onUploadAdded,
            failureHandler=self.onFailed,
            secure=True
        )

    def onUploadAdded(self, req):
        self.responseValue = NetworkService.decode(req)
        DeferredCall(self.onSuccess, _delay=1000)

    def onProgress(self, event):
        """Internal callback - further bytes have been transmitted."""
        if event.lengthComputable:
            complete = int(event.loaded / event.total * 100)
            self["value"] = complete
            self["max"] = 100

    def onSuccess(self, *args, **kwargs):
        """Internal callback - The upload succeeded."""
        if isinstance(self.responseValue["values"], list):
            for v in self.responseValue["values"]:
                self.uploadSuccess.fire(self, v)

        else:
            self.uploadSuccess.fire(self, self.responseValue["values"])

        NetworkService.notifyChange("file")
        if self.showResultMessage:
            self.replaceWithMessage("Upload complete", isSuccess=True)

    def onFailed(self, errorCode, *args, **kwargs):
        if self.showResultMessage:
            self.replaceWithMessage(
                "Upload failed with status code %s" % errorCode, isSuccess=False
            )
        self.uploadFailed.fire(self, errorCode)

    def replaceWithMessage(self, message, isSuccess):
        self.parent().removeClass("is-uploading")
        self.parent().removeClass("log-progress")
        if isSuccess:
            self.parent().addClass("log-success")
        else:
            self.parent().addClass("log-failed")
        msg = html5.Span()
        msg.appendChild(html5.TextNode(message))
        self.parent().appendChild(msg)
        self.parent().removeChild(self)


class FileLeafWidget(TreeLeafWidget):
    def EntryIcon(self):
        self.previewImg = FilePreviewImage(self.data)
        self.nodeImage.appendChild(self.previewImg)
        self.nodeImage.removeClass("is-hidden")

    def setStyle(self):
        self.buildDescription()
        self.EntryIcon()


class FileNodeWidget(TreeNodeWidget):
    def setStyle(self):
        self.buildDescription()
        self.EntryIcon()


class FileWidget(TreeBrowserWidget):
    leafWidget = FileLeafWidget
    nodeWidget = FileNodeWidget

    def __init__(
        self,
        module,
        rootNode=None,
        selectMode=None,
        node=None,
        context=None,
        *args,
        **kwargs
    ):
        super(FileWidget, self).__init__(
            module, rootNode, selectMode, node, context, *args, **kwargs
        )
        self.searchWidget()
        self.addClass("supports-upload")
        self.entryFrame.addClass("flr-tree-selectioncontainer")
        self.entryFrame["title"] = "Ziehe Deine Dateien hier her."

    def searchWidget(self):
        searchBox = html5.Div()
        searchBox.addClass("flr-search-wrap")
        self.appendChild(searchBox)

        self.search = Search()
        self.search.addClass("input-group")
        searchBox.appendChild(self.search)
        self.search.searchLbl.addClass("label")
        self.search.startSearchEvent.register(self)

    def onStartSearch(self, searchStr, *args, **kwargs):
        if not searchStr:
            self.setRootNode(self.rootNode)
        else:
            for c in self.entryFrame._children[:]:
                self.entryFrame.removeChild(c)

            for c in self.pathList._children[:]:
                self.pathList.removeChild(c)
            s = html5.Span()
            s.appendChild(html5.TextNode("Search"))
            self.pathList.appendChild(s)
            self.loadNode(node=self.rootNode, overrideParams={"search": searchStr})

    def getChildKey(self, widget):
        """Derives a string used to sort the entries on each level."""
        name = str(widget.data.get("name")).lower()

        if isinstance(widget, self.nodeWidget):
            return "0-%s" % name
        elif isinstance(widget, self.leafWidget):
            return "1-%s" % name
        else:
            return "2-"

    @staticmethod
    def canHandle(module, moduleInfo):
        return moduleInfo["handler"].startswith("tree.file") or moduleInfo[
            "handler"
        ].startswith("tree.simple.file")


moduleWidgetSelector.insert(0, FileWidget.canHandle, FileWidget)
displayDelegateSelector.insert(0, FileWidget.canHandle, FileWidget)
