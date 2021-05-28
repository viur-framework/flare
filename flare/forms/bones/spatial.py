from flare.forms import boneSelector
from .base import BaseBone, BaseEditWidget
from flare import html5


class SpatialEditWidget(BaseEditWidget):
    def createWidget(self):
        tpl = html5.Template()
        # language=HTML
        tpl.appendChild(
            self.fromHTML(
                """
            <flare-input [name]="latitude" type="number" placeholder="latitude" step="any">
            <flare-input [name]="longitude" type="number" placeholer="longitute" step="any">
            """
            )
        )
        return tpl

    def updateWidget(self):
        if self.bone.readonly:
            self.latitude.disable()
            self.longitude.disable()
        else:
            self.latitude.enable()
            self.longitude.enable()

    def unserialize(self, value=None):
        self.latitude["value"], self.longitude["value"] = value or (0, 0)

    def serialize(self):
        return {"lat": self.latitude["value"], "lng": self.longitude["value"]}


class SpatialBone(BaseBone):
    editWidgetFactory = SpatialEditWidget

    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName]["type"] == "spatial" or skelStructure[boneName][
            "type"
        ].startswith("spatial.")


boneSelector.insert(1, SpatialBone.checkFor, SpatialBone)
