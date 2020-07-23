from flare.forms import boneSelector, conf
from .base import BaseBone, BaseEditWidget, BaseViewWidget

class EmailEditWidget(BaseEditWidget):
	def _updateWidget(self):
		self.widget["type"] = "email"
		self.widget.addClass("input-group-item")

class EmailViewWidget(BaseViewWidget):
	def unserialize(self, value=None):
		self.value = value

		if value:
			self.appendChild(
				"""<a href="mailto:{{value}}">{{value}}</a>""",
				vars={"value": value},
				replace=True
			)
		else:
			self.appendChild(conf["emptyValue"], replace=True)

class EmailBone(BaseBone):
	editWidgetFactory = EmailEditWidget
	viewWidgetFactory = EmailViewWidget

	@staticmethod
	def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
		return skelStructure[boneName]["type"] == "str.email" or skelStructure[boneName]["type"].startswith("str.email.")


boneSelector.insert(2, EmailBone.checkFor, EmailBone)
