from flare.icons import SvgIcon
from flare.i18n import translate
from flare import html5


def collectBoneErrors(errorList, currentKey, boneStructure):
    """Collect Errors from given errorList.

    severity:
        NotSet = 0
        InvalidatesOther = 1
        Empty = 2
        Invalid = 3
    """
    boneErrors = []

    for error in errorList or []:
        if error["fieldPath"] and error["fieldPath"][0] == currentKey:
            isError = False
            if (error["severity"] == 0 or error["severity"] == 2) and boneStructure["required"]:
                isError = True
            elif error["severity"] == 3:
                isError = True
            # ToDO Field dependency!

            if isError:
                thisError = error.copy()
                thisError["fieldPath"] = error["fieldPath"][1:]
                boneErrors.append(thisError)

    return boneErrors


class ToolTipError(html5.Div):
    """Small utility class for providing tooltips."""

    def __init__(self, shortText="", longText="", *args, **kwargs):
        super(ToolTipError, self).__init__(*args, **kwargs)
        self["class"] = "vi-tooltip msg msg--error is-active is-open"
        self.sinkEvent("onClick")

        self.prependChild(SvgIcon("icon-arrow-right", title=shortText))

        # language=HTMl
        self.fromHTML(
            """
            <div class="msg-content" [name]="tooltipMsg">
                <h2 class="msg-headline" [name]="tooltipHeadline"></h2>
                <div class="msg-descr" [name]="tooltipDescr"></div>
            </div>
        """
        )

        self.tooltipHeadline.element.innerHTML = translate("vi.tooltip.error")
        self.tooltipDescr.element.innerHTML = longText.replace("\n", "<br />")

    def onClick(self, event):
        self.toggleClass("is-open")

    def _setDisabled(self, disabled):
        return

    def _getDisabled(self):
        return False
