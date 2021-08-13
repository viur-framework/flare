from flare import html5
from flare.forms import boneSelector, formatString, displayString
from flare.config import conf
from flare.forms.widgets.relational import InternalEdit
from .base import BaseBone, BaseEditWidget, BaseViewWidget


class RecordEditWidget(BaseEditWidget):
    style = ["flr-value", "flr-value--record"]

    def createWidget(self):
        return InternalEdit(
            self.bone.boneStructure["using"],
            errorInformation=self.bone.errors,
            readOnly=self.bone.readonly,
            defaultCat=None,  # fixme: IMHO not necessary
            errorQueue=self.bone.errorQueue,
            prefix="{}.rel".format(self.bone.boneName),
        )

    def updateWidget(self):
        if self.bone.readonly:
            self.widget.disable()
        else:
            self.widget.enable()

    def unserialize(self, value=None):
        self.widget.unserialize(value or {})

    def serialize(self):
        return self.widget.serializeForPost()  # fixme: call serializeForPost()?


class RecordViewWidget(BaseViewWidget):
    style = ["flr-value", "flr-value--record"]

    def __init__(self, bone, language=None, **kwargs):
        super().__init__(bone, **kwargs)
        self.language = language

    def unserialize(self, value=None):
        self.value = value

        if self.value:
            if display := self.bone.boneStructure["params"].get("display"):
                displayWidgets = displayString(
                    display,
                    self.value,
                    self.bone.boneStructure["using"],
                    self.language
                )

                self.replaceChild(displayWidgets or conf["emptyValue"])
            else:
                self.replaceChild(
                    formatString(
                        self.bone.boneStructure["format"],
                        self.value,
                        self.bone.boneStructure["using"],
                        self.language
                    ) or conf["emptyValue"]
                )


class RecordBone(BaseBone):
    editWidgetFactory = RecordEditWidget
    viewWidgetFactory = RecordViewWidget

    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName]["type"] == "record" or skelStructure[boneName][
            "type"
        ].startswith("record.")


boneSelector.insert(1, RecordBone.checkFor, RecordBone)
