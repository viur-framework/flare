from . import html5, icons


@html5.tag
class PopoutItem(html5.Div):
	_parserTagName = "popout-item"
	style = ["item", "has-hover"]


@html5.tag
class Popout(html5.Div):
	style = ["popout-opener", "popout-anchor", "popout--se"]

	def __init__(self, *args, **kwargs):
		#language=HTML
		super().__init__(*args, **kwargs)

		self.appendChild("""
			<icon [name]="icon" hidden></icon>
			<span [name]="text" hidden></span>

			<div class="popout">
				<div [name]="popoutItemList" class="list"></div>
			</div>
		</div>
		""")

		self._text = ""
		self.appendChild = self.popoutItemList.appendChild
		self.fromHTML = lambda *args, **kwargs: self.popoutItemList.fromHTML(*args, **kwargs) if kwargs.get("bindTo") else self.popoutItemList.fromHTML(bindTo=self, *args, **kwargs)

	def _setIcon(self, icon):
		if icon:
			self.icon["icon"] = icon
			self.icon.show()
		else:
			self.icon["icon"] = None
			self.icon.hide()

	def _getIcon(self):
		return self.icon["icon"]

	def _setText(self, text):
		self._text = text

		if self._text:
			self.text.appendChild(str(self._text), replace=True)
			self.text.show()
		else:
			self.text.hide()

	def _getText(self):
		return self._text
