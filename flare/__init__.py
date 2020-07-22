"""
Flare is an application development framework
for writing software frontends in pure Python.
"""

import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

from . import html5
from . import button
from . import cache
from . import event
from . import handler
from . import i18n
from . import icons
from . import ignite
from . import input
from . import network
from . import observable
from . import popup
from . import utils

from .config import conf


# Monkey patch some html5.Widget-functions for better ignite-integration
# Reason for this can be found in issue #2.

def _html5WidgetSetHidden(widget, hidden):
	html5.Widget._super_setHidden(widget, hidden)

	if hidden:
		widget.addClass("is-hidden")
	else:
		widget.removeClass("is-hidden")

html5.Widget._super_setHidden = html5.Widget._setHidden
html5.Widget._setHidden = _html5WidgetSetHidden


def _html5WidgetSetDisabled(widget, disabled):
	html5.Widget._super_setDisabled(widget, disabled)

	if disabled:
		widget.addClass("is-disabled")
	else:
		widget.removeClass("is-disabled")

html5.Widget._super_setDisabled = html5.Widget._setDisabled
html5.Widget._setDisabled = _html5WidgetSetDisabled
