"""
Observed values firing events when changed.
"""


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

		self.valueChanged.fire(event)
