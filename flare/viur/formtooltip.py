from flare import html5


class ToolTip(html5.Div):
    """Small utility class for providing tooltips."""

    def __init__(self, shortText="", longText="", *args, **kwargs):
        # fixme: Tooltip should be replaced by Summary-Tag
        '''
        super(ToolTip, self).__init__(
            # language=HTML
            """
            <summary class="msg-content" [name]="tooltipMsg">
                <flare-svg-icon icon="icon-arrow-right" title="{{shortText}}">
                <h2 class="msg-headline" [name]="tooltipHeadline">{{shortText or translate("flare.forms.tooltip")}}</h2>
                <details class="msg-descr" [name]="tooltipDescr">{{longText}}</details>
            </summary>
            """,
            shortText=shortText,
            longText=longText.replace("\n", "<br />")
        )
        '''

        super().__init__(
            # language=HTML
            """
            <flare-svg-icon value="icon-arrow-right" title="{{shortText}}">
            <div class="msg-content" [name]="tooltipMsg">
                <h2 class="msg-headline" [name]="tooltipHeadline">{{shortText or translate("flare.forms.tooltip")}}</h2>
                <div class="msg-descr" [name]="tooltipDescr">{{longText}}</div>
            </div>
            """,
            shortText=shortText,
            longText=longText.replace("\n", "<br />")
        )

        self["class"] = "vi-tooltip msg is-active"
        self.sinkEvent("onClick")  # this becomes obsolete when tooltip is a summary...

    def onClick(self, event):
        self.toggleClass("is-open")

    def _setDisabled(self, disabled):
        # Tooltip cannot be disabled...
        return
