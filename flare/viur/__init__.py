from flare.priorityqueue import PriorityQueue
from .formconf import conf
from .formatString import formatString, displayStringHandler

BoneSelector = PriorityQueue()  # Queried by editWidget to locate its bones
ModuleWidgetSelector = PriorityQueue()  # Used to select an embedded widget to represent a module
DisplayDelegateSelector = PriorityQueue()  # Selects a widget used to display data from a certain module


class InvalidBoneValueException(ValueError):
    pass


# Imports need to follow here because previous definitions are needed.
from .bones import *
from .forms import *
