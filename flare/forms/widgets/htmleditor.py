import logging

from js import Event as JSevent, encodeURI as JSencodeURI

try:
	from js import summernoteEditor
except:
	summernoteEditor = None

from flare import html5
from flare.network import DeferredCall
from flare.config import conf
from flare.i18n import translate
from flare.button import Button
from flare.popup import Alert
from .file import FileWidget

class TextInsertImageAction(Button):
	def __init__(self, summernote=None, boneName="", *args, **kwargs):
		if summernote is None:
			summernote = self

		super(TextInsertImageAction, self).__init__(translate("Insert Image"), *args, **kwargs)
		self["class"] = "icon text image viur-insert-image-btn"
		self["title"] = translate("Insert Image")
		self["style"]["display"] = "none"
		self.element.setAttribute("data-bonename", boneName)
		self.summernote = summernote

	def onClick(self, sender=None):
		currentSelector = FileWidget("file", selectMode="multi")
		currentSelector.selectionActivatedEvent.register(self)
		conf["mainWindow"].stackWidget(currentSelector)

	def onSelectionActivated(self, selectWdg, selection):
		logging.debug("onSelectionActivated")

		if not selection:
			return

		for item in selection:

			if "mimetype" in item.data.keys() and item.data["mimetype"].startswith("image/"):
				dataUrl = "/file/download/%s/%s" % (item.data["dlkey"], JSencodeURI(item.data["name"]))

				self.summernote.summernote("editor.insertImage", dataUrl, item.data["name"].replace("\"", ""))
				logging.debug("insert img %r", dataUrl)
			else:
				dataUrl = "/file/download/%s/%s" % (item.data["dlkey"], JSencodeURI(item.data["name"]))

				text = str(self.summernote.summernote("createRange")) # selected text
				if not text:
					text = item.data["name"].replace("\"", "")

				self.summernote.summernote("editor.createLink",{"url":dataUrl, "text": text, "isNewWindow": True})
				logging.debug("insert link %r<%r> ", text, dataUrl)

	@staticmethod
	def isSuitableFor(modul, handler, actionName):
		return (actionName == "text.image")

	def resetLoadingState(self):
		pass


class HtmlEditor(html5.Textarea):
	initSources = False

	def __init__(self, *args, **kwargs):
		super(HtmlEditor, self).__init__(*args, **kwargs)

		self.value = ""
		self.summernote = None
		self.enabled = True
		self.summernoteContainer = self
		self.boneName = ""

	def _attachSummernote(self, retry=0):
		elem = self.summernoteContainer.element
		lang = conf["currentLanguage"]

		try:
			self.summernote = summernoteEditor(elem, lang)
		except:
			if retry >= 3:
				Alert("Unable to connect summernote, please contact technical support...")
				return

			logging.debug("Summernote initialization failed, retry will start in 1sec")
			DeferredCall(self._attachSummernote, retry=retry + 1, _delay=1000)
			return

		imagebtn = TextInsertImageAction(summernote=self.summernote, boneName=self.boneName)
		self.parent().appendChild(imagebtn)

		if not self.enabled:
			self.summernote.summernote("disable")

		if self.value:
			self["value"] = self.value

	def onAttach(self):
		super(HtmlEditor, self).onAttach()

		if self.summernote:
			return

		self._attachSummernote()

		self.element.setAttribute("data-bonename", self.boneName)

	def onDetach(self):
		super(HtmlEditor, self).onDetach()
		self.value = self["value"]
		if self.summernote:
			self.summernote.summernote("destroy")
			self.summernote = None

	def onEditorChange(self, e, *args, **kwargs):
		if self.parent():
			e = JSevent.new('keyup')# JS("new Event('keyup')")
			self.parent().element.dispatchEvent(e)

	def _getValue(self):
		if not self.summernote:
			return self.element.value

		ret = self.summernote.summernote("code")
		return ret

	def _setValue(self, val):
		if not self.summernote:
			self.element.value = val
			return

		self.summernote.off("summernote.change")
		self.summernote.summernote("reset")  # reset history and content
		self.summernote.summernote("code", val)
		'''
			a importet JQuery object cant use jquery's on function!
			used vanilla JS Eventlistener till we now why:

			> Uncaught Error: AttributeError: 'method' object has no attribute 'guid'

		'''
		self.summernote.get(0).addEventListener("summernote.change", self.onEditorChange) #ARGGGGG! WTF

	def enable(self):
		super(HtmlEditor, self).enable()

		self.enabled = True
		self.removeClass("is-disabled")

		if self.summernote:
			self.summernote.summernote("enable")

	def disable(self):
		super(HtmlEditor, self).disable()

		self.enabled = False
		self.addClass("is-disabled")

		if self.summernote:
			self.summernote.summernote("disable")
