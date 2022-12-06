from flare.ignite import *
from flare.viur import BoneSelector
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
        display_value = value or conf["emptyValue"]

        if len(display_value) > 200:
            display_value = display_value[:200] + "..."

        self.replaceChild(html5.Code(html5.TextNode(display_value)))


class RawBone(BaseBone):
    editWidgetFactory = RawEditWidget
    viewWidgetFactory = RawViewWidget

    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName]["type"] == "raw" or skelStructure[boneName][
            "type"
        ].startswith("raw.")


BoneSelector.insert(1, RawBone.checkFor, RawBone)
