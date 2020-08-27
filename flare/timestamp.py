"""
Widget for representing a timestamp with 'time-changing' behavior.
"""

import datetime
from . import html5
from . import utils


@html5.tag
class Timestamp(html5.Div):
	"""
	Div-Tag that represents a date-and-time value that automatically updates when time flows...
	"""

	_leafTag = True

	def __init__(self):
		super().__init__()
		self.timestamp = None
		self._updateInterval = None

	def _setValue(self, timestamp):
		if isinstance(timestamp, str):
			timestamp = utils.viurDateTimeToDateTime(timestamp)

		assert not timestamp or isinstance(timestamp, datetime.datetime)

		self.timestamp = timestamp
		self._render()

	def _render(self):
		self.removeAllChildren()

		if not self.timestamp:
			return

		now = datetime.datetime.now()
		diff = now - self.timestamp

		#todo: Translations...
		if diff.days == 0:
			if diff.seconds > 60 * 60:
				if self.timestamp.day == now.day:
					self.appendChild(self.timestamp.strftime("heute um %H:%M"))
				else:
					self.appendChild(self.timestamp.strftime("gestern um %H:%M"))
			elif diff.seconds > 2 * 60:
				self.appendChild("vor %d Minuten" % (diff.seconds / 60))
			elif diff.seconds > 60:
				self.appendChild("vor einer Minute")
			elif diff.seconds > 30:
				self.appendChild("vor weniger als einer Minute")
			else:
				self.appendChild("jetzt")

		elif diff.days == 1:
			self.appendChild(self.timestamp.strftime("gestern um %H:%M"))
		else:
			self.appendChild(self.timestamp.strftime("am %d.%m.%Y um %H:%M"))

		if self._updateInterval is None:
			self._updateInterval = html5.window.setInterval(self._render, 10 * 1000)

	def onDetach(self):
		if self._updateInterval:
			html5.window.clearInterval(self._updateInterval)

		super().onDetach()
