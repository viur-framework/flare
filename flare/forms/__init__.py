from flare.priorityqueue import PriorityQueue
from .formconf import conf
from .formatString import formatString, displayString

boneSelector = PriorityQueue()  # Queried by editWidget to locate its bones
moduleWidgetSelector = (
    PriorityQueue()
)  # Used to select an embedded widget to represent a module
displayDelegateSelector = (
    PriorityQueue()
)  # Selects a widget used to display data from a certain module


class InvalidBoneValueException(ValueError):
    pass


from .bones import *

"""
from custom_form.bones import *
try:
	from ..custom_form.bones import *
except:
	pass
"""
