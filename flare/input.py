"""Input widget with additional event handling."""

from . import html5


# todo @html5.tag? But flare-input is already specified!
class Input(html5.Input):
    def __init__(
        self,
        type="text",
        placeholder=None,
        callback=None,
        id=None,
        focusCallback=None,
        *args,
        **kwargs
    ):
        """Instantiate new Input.

        :param type: Input type. Default: "text
        :param placeholder: Placeholder text. Default: None
        :param callback: Function to be called onChanged: callback(id, value)
        :param id: Optional id of the input element. Will be passed to callback
        :return:
        """
        super().__init__(*args, **kwargs)
        self["class"] = "input"
        self["type"] = type
        if placeholder is not None:
            self["placeholder"] = placeholder

        self.callback = callback
        if id is not None:
            self["id"] = id
        self.sinkEvent("onChange")

        self.focusCallback = focusCallback
        if focusCallback:
            self.sinkEvent("onFocus")

    def onChange(self, event):
        event.stopPropagation()
        event.preventDefault()
        if self.callback is not None:
            self.callback(self, self["id"], self["value"])

    def onFocus(self, event):
        event.stopPropagation()
        event.preventDefault()
        if self.focusCallback is not None:
            self.focusCallback(self, self["id"], self["value"])

    def onDetach(self):
        super().onDetach()
        self.callback = None
