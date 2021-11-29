from flare.priorityqueue import PriorityQueue
from .formconf import conf
from .formatString import formatString, displayStringHandler
from .bones import *
from .forms import *

BoneSelector = PriorityQueue()  # Queried by editWidget to locate its bones
moduleWidgetSelector = PriorityQueue()  # Used to select an embedded widget to represent a module
displayDelegateSelector = PriorityQueue()  # Selects a widget used to display data from a certain module


class InvalidBoneValueException(ValueError):
    pass
