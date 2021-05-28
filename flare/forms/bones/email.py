from flare.forms import boneSelector
from flare.config import conf
from .base import BaseBone, BaseEditWidget, BaseViewWidget


class EmailEditWidget(BaseEditWidget):
    def updateWidget(self):
        self.widget["type"] = "email"
        self.widget.addClass("input-group-item")

        if self.bone.readonly:
            self.widget.disable()
        else:
            self.widget.enable()


class EmailViewWidget(BaseViewWidget):
    def unserialize(self, value=None):
        self.value = value

        if value:
            # """<a href="mailto:{{value}}">{{value}}</a>""", #fixme style parameter to activate mailTo link
            self.replaceChild("""{{value}}""", value=value)
        else:
            self.replaceChild(conf["emptyValue"])


class EmailBone(BaseBone):
    editWidgetFactory = EmailEditWidget
    viewWidgetFactory = EmailViewWidget

    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName]["type"] == "str.email" or skelStructure[
            boneName
        ]["type"].startswith("str.email.")


boneSelector.insert(2, EmailBone.checkFor, EmailBone)
