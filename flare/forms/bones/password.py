from flare.forms import boneSelector, conf, InvalidBoneValueException
from flare.i18n import translate
from .base import BaseBone, BaseEditWidget


class PasswordEditWidget(BaseEditWidget):
	style = ["flr-value", "flr-value--password", "flr-value-container", "input-group"]

	def _createWidget(self):
		self.appendChild("""<flr-input [name]="widget" type="password" class="input-group-item">""")

		user = conf["currentUser"]
		if self.bone.readonly or (user and "root" in user["access"]):
			self.verify = None
		else:
			self.appendChild("""
				<label class="label" for="{{id}}">
					{{txt}}
				</label>
				<flr-input id="{{id}}" [name]="verify" type="password">
			""",
			vars={"txt": translate("reenter password"), "id": "flr-%s-reenter" % self.bone.boneName })

	def serialize(self):
		if not self.verify or self.widget["value"] == self.verify["value"]:
			return self.widget["value"]

		raise InvalidBoneValueException()


class PasswordBone(BaseBone):
	editWidgetFactory = PasswordEditWidget

	@staticmethod
	def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
		return skelStructure[boneName]["type"] == "password" or skelStructure[boneName]["type"].startswith("password.")


boneSelector.insert(1, PasswordBone.checkFor, PasswordBone)
