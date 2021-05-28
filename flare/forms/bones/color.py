from flare import html5
from flare.forms import boneSelector
from flare.config import conf
from .base import BaseBone, BaseEditWidget, BaseViewWidget


class ColorEditWidget(BaseEditWidget):
    style = ["flr-value", "flr-value--color"]

    def createWidget(self):
        tpl = html5.Template()
        # language=HTML
        tpl.appendChild(
            """
							<input [name]="widget" type="color" class="input flr-input">
							<flare-button [name]="unsetBtn" text="Unset" icon="icon-cross" class="btn--delete">
						""",
            bindTo=self,
        )

        return tpl

    def updateWidget(self):
        if self.bone.readonly:
            self.widget.disable()
            self.unsetBtn.disable()
        else:
            self.widget.enable()
            self.unsetBtn.enable()

    def onUnsetBtnClick(self):
        self.widget["value"] = ""

    def serialize(self):
        value = self.widget["value"]
        return value if value else None


class ColorViewWidget(BaseViewWidget):
    def unserialize(self, value=None):
        self.value = value

        if value:
            self["style"]["background-color"] = value
            self.appendChild(value)
        else:
            self.appendChild(conf["emptyValue"])


class ColorBone(BaseBone):
    editWidgetFactory = ColorEditWidget
    viewWidgetFactory = ColorViewWidget

    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName]["type"] == "color" or skelStructure[boneName][
            "type"
        ].startswith("color.")


boneSelector.insert(1, ColorBone.checkFor, ColorBone)
