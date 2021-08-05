from flare.ignite import *
from flare.forms import boneSelector
from flare.config import conf
from flare import html5
from .base import BaseBone, BaseEditWidget, BaseViewWidget


class RawEditWidget(BaseEditWidget):
    style = ["flr-value", "flr-value--raw"]

    def createWidget(self):
        widget = Textarea()
        widget["readonly"] = bool(self.bone.boneStructure.get("readonly"))

        return widget

    def updateWidget(self):
        self.widget["readonly"] = self.bone.readonly


class RawViewWidget(BaseViewWidget):
    def unserialize(self, value=None):
        self.value = value
        self.replaceChild(html5.Code(value or conf["emptyValue"]))


class RawBone(BaseBone):
    editWidgetFactory = RawEditWidget
    viewWidgetFactory = RawEditWidget

    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName]["type"] == "raw" or skelStructure[boneName][
            "type"
        ].startswith("raw.")


boneSelector.insert(1, RawBone.checkFor, RawBone)
