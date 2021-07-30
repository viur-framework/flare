"""Flare-styled button Widgets."""

import inspect
from . import html5
from flare.icons import SvgIcon


@html5.tag("flare-button")
class Button(html5.Button):
    """Extended version for a button with a text and icon, which binds itself to an event function."""

    def __init__(self, text=None, callback=None, className="", icon=None):
        super().__init__()
        self.addClass("btn", className)
        self.sinkEvent("onClick")
        self.icon = None
        self.initIcon = self.icon
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

    def onClick(self, event, widget=None):
        event.stopPropagation()
        event.preventDefault()

        if self.callback is not None:
            parameters = inspect.signature(self.callback).parameters

            # Allow for callback without parameter
            if len(parameters) == 0:
                self.callback()
            elif len(parameters) == 1:
                self.callback(self)
            else:
                self.callback(event, self)

    def resetIcon(self):
        self["icon"] = self.initIcon

    def update(self):
        self.removeAllChildren()
        if self.icon:
            self.prependChild(SvgIcon(self.icon, title=self.text))
        if self.text:
            self.appendChild(self.text)

    def _setIcon(self, icon):
        if not icon:
            self.icon = None
        else:
            self.icon = icon

        self.update()

    def _getIcon(self):
        return self.icon

    def _setText(self, text):
        self.text = text or ""
        self.update()

    def _getText(self):
        return self.text
