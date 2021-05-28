"""Observed values firing events when changed."""

from . import html5
from .event import EventDispatcher


class ObservableValue(object):
    value = None

    def __init__(self, key, value=None):
        self.valueChanged = EventDispatcher("%sChanged" % key)
        self.key = key
        if value:
            self.setValue(value)

    def setValue(self, value):
        self.value = value

        if isinstance(value, html5.Widget):

            class event:
                widget = value
                target = value.element

        else:
            event = value

        self.valueChanged.fire(event, value)


class StateHandler:
    def __init__(self, initialize=(), widget=None):
        self.widget = widget
        self.internalStates = {}
        for entry in initialize:
            self.internalStates.update({entry: ObservableValue(entry)})

    def updateState(self, key, value):

        if key in self.internalStates:
            self.internalStates[key].setValue(value)
        else:  # key does not exist
            self.internalStates.update({key: ObservableValue(key)})  # create observable
            if self.widget:
                self.internalStates[key].valueChanged.register(
                    self.widget
                )  # register eventhandler
            self.internalStates[key].setValue(value)  # update value

    def getState(self, key, empty=None):
        if key in self.internalStates:
            return self.internalStates[key].value
        return empty

    def register(self, key, widget):
        self.internalStates[key].valueChanged.register(widget)

    def unregister(self, key, widget):
        self.internalStates[key].valueChanged.unregister(widget)
