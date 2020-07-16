from . import html5
from .icons import Icon


@html5.tag
class Button(html5.Button):
	"""
	Extended version for a button with a text and icon, which binds itself to an event function.
	"""

	def __init__(self, text=None, callback=None, className="", icon=None):
		super(Button, self).__init__()
		self.addClass("btn", className)
		self.sinkEvent("onClick")
		self.icon = None
		self.text = ""

		if icon is not None:
			self["icon"] = icon

		if text is not None:
			self["text"] = text

		self.callback = callback

	def onBind(self, widget, name):
		if self.callback is None:
			funcName = "on" + name[0].upper() + name[1:] + "Click"
			if funcName in dir(widget):
				self.callback = getattr(widget, funcName)

	def onClick(self, event):
		event.stopPropagation()
		event.preventDefault()

		if self.callback is not None:
			try:
				self.callback(self)
			except:
				self.callback()

	def update(self):
		self.removeAllChildren()

		if self.icon:
			self.appendChild(self.icon)

		self.appendChild(self.text)

	def _setIcon(self, icon):
		if not icon:
			self.icon = None
		else:
			self.icon = Icon(icon=icon)

		self.update()

	def _setText(self, text):
		self.text = text or ""
		self.update()
