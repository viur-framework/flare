from flare.forms import boneSelector, InvalidBoneValueException
from flare.i18n import translate
from .base import BaseBone, BaseEditWidget


class PasswordEditWidget(BaseEditWidget):
    style = ["flr-value", "flr-value--password", "flr-value-container", "input-group"]

    def createWidget(self):
        self.appendChild(
            """<flare-input [name]="widget" type="password" class="flr-input input-group-item">"""
        )

        if self.bone.readonly:
            self.verify = None
        else:
            self.appendChild(
                """
				<label class="label" for="{{id}}">
					{{txt}}
				</label>
				<flare-input id="{{id}}" [name]="verify" type="password">
			""",
                txt=translate("reenter password"),
                id="flr-%s-reenter" % self.bone.boneName,
            )

            self.widget.element.autocomplete = "new-password"
        return self.widget

    def updateWidget(self):
        if self.bone.readonly:
            self.widget.disable()
            if self.verify:
                self.verify.disable()
        else:
            self.widget.enable()
            if self.verify:
                self.verify.enable()

    def serialize(self):
        if not self.verify or self.widget["value"] == self.verify["value"]:
            return self.widget["value"]

        raise InvalidBoneValueException()


class PasswordBone(BaseBone):
    editWidgetFactory = PasswordEditWidget

    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName]["type"] == "password" or skelStructure[boneName][
            "type"
        ].startswith("password.")


boneSelector.insert(1, PasswordBone.checkFor, PasswordBone)
