"""Popout menu that is expanded when hovering.

Example:
-------
```html
<popout icon="icon-arrowhead-down">
	<popout-item @click="onEdit">edit</popout-item>
	<popout-item @click="onLeave">leave</popout-item>
	<popout-item @click="onDelete">delete</popout-item>
</popout>
```

"""

from . import html5, icons  # icons import is required here for <flare-icon>


@html5.tag("flare-popout-item")
class PopoutItem(html5.Div):
    """It's an item in a popout menu."""

    style = ["item", "has-hover"]


@html5.tag("flare-popout")
class Popout(html5.Div):
    """Popout menu."""

    style = ["popout-opener", "popout-anchor"]

    def __init__(self, *args, **kwargs):
        # language=HTML
        super().__init__(*args, **kwargs)

        self.appendChild(
            """
                <flare-icon [name]="icon" hidden></flare-icon>
                <span [name]="text" hidden></span>

                <div class="popout">
                    <div [name]="popoutItemList" class="list"></div>
                </div>
            """
        )

        self._text = ""

        # Overriding appendChild and fromHTML to insert
        self.appendChild = self.popoutItemList.appendChild
        self.fromHTML = (
            lambda *args, **kwargs: self.popoutItemList.fromHTML(*args, **kwargs)
            if kwargs.get("bindTo")
            else self.popoutItemList.fromHTML(bindTo=self, *args, **kwargs)
        )

    def _setIcon(self, icon):
        if icon:
            self.icon["value"] = icon
            self.icon.show()
        else:
            self.icon["value"] = None
            self.icon.hide()

    def _getIcon(self):
        return self.icon["icon"]

    def _setText(self, text):
        self._text = text

        if self._text:
            self.text.replaceChild(str(self._text))
            self.text.show()
        else:
            self.text.hide()

    def _getText(self):
        return self._text
