from flare import html5
from flare.i18n import translate
from flare.icons import SvgIcon


class ToolTip(html5.Div):
    """Small utility class for providing tooltips."""

    def __init__(self, shortText="", longText="", *args, **kwargs):
        super(ToolTip, self).__init__(*args, **kwargs)
        self["class"] = "vi-tooltip msg is-active"
        self.sinkEvent("onClick")

        self.prependChild(SvgIcon("icon-arrow-right", title=shortText))

        # language=HTMl
        self.fromHTML(
            """
			<div class="msg-content" [name]="tooltipMsg">
				<h2 class="msg-headline" [name]="tooltipHeadline">{{shortText or translate("flare.forms.tooltip")}}</h2>
				<div class="msg-descr" [name]="tooltipDescr">{{longText}}</div>
			</div>
		    """,
            shortText=shortText,
            longText=longText.replace("\n", "<br />")
        )

    def onClick(self, event):
        self.toggleClass("is-open")

    def _setDisabled(self, disabled):
        return

    def _getDisabled(self):
        return False
