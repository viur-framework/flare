"""Pre-defined dialog widgets for user interaction."""

from . import html5, utils, icons, i18n
from .button import Button


class Popup(html5.Div):
    def __init__(
            self,
            title="",
            id=None,
            className=None,
            icon=None,
            enableShortcuts=True,
            closeable=True,
            *args,
            **kwargs
    ):
        # language=HTML
        super().__init__(
            """
            <div class="box" [name]="popupBox" style="height: 100%">
                <div class="box-head" [name]="popupHead">
                    <div class="item" [name]="popupHeadItem">
                        <div class="item-image">
                            <flare-icon class="i i--small" [name]="popupIcon"></flare-icon>
                        </div>
                        <div class="item-content">
                            <div class="item-headline" [name]="popupHeadline">
                                {{title}}
                            </div>
                        </div>

                        <flare-icon value="icon-cross" @click="onClose"
                            flare-if="closeable" title="{{ translate('flare.label.close') }}"
                            class="item-action btn--transparent btn--icon">
                    </div>
                </div>
                <div class="box-body box--content" [name]="popupBody" style="height: 100%"></div>
                <div class="box-foot box--content bar" [name]="popupFoot"></div>
            </div>
            """,
            title=title,
            closeable=closeable,
        )

        self.appendChild = self.popupBody.appendChild
        self.fromHTML = (
            lambda *args, **kwargs: self.popupBody.fromHTML(*args, **kwargs)
            if kwargs.get("bindTo")
            else self.popupBody.fromHTML(bindTo=self, *args, **kwargs)
        )

        self["class"] = "popup popup--center is-active"
        if className:
            self.addClass(className)

        self.popupIcon["value"] = icon
        self.popupIcon["title"] = title

        # id can be used to pass information to callbacks
        self.id = id

        # FIXME: Implement a global overlay! One popupOverlay next to a list of popups.
        self.popupOverlay = html5.Div()
        self.popupOverlay["class"] = "popup-overlay is-active"

        self.enableShortcuts = enableShortcuts
        self.onDocumentKeyDownMethod = None

        self.popupOverlay.appendChild(self)
        html5.Body().appendChild(self.popupOverlay)

    # FIXME: Close/Cancel every popup with click on popupCloseBtn without removing the global overlay.

    def onAttach(self):
        super(Popup, self).onAttach()

        if self.enableShortcuts:
            self.onDocumentKeyDownMethod = (
                self.onDocumentKeyDown
            )  # safe reference to method
            html5.document.addEventListener("keydown", self.onDocumentKeyDownMethod)

    def onDetach(self):
        super(Popup, self).onDetach()

        if self.enableShortcuts:
            html5.document.removeEventListener("keydown", self.onDocumentKeyDownMethod)

    def onDocumentKeyDown(self, event):
        if html5.isEscape(event):
            self.close()

    def close(self):
        if self.popupOverlay:
            html5.Body().removeChild(self.popupOverlay)
        self.popupOverlay = None

    def onClose(self):
        self.close()


class Prompt(Popup):
    def __init__(
            self,
            text,
            value="",
            successHandler=None,
            abortHandler=None,
            successLbl=None,
            abortLbl=None,
            placeholder="",
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.addClass("popup--prompt")

        self.sinkEvent("onKeyDown", "onKeyUp")

        if successLbl is None:
            successLbl = i18n.translate("flare.label.ok")

        if abortLbl is None:
            abortLbl = i18n.translate("flare.label.cancel")

        self.successHandler = successHandler
        self.abortHandler = abortHandler

        self.fromHTML(
            # language=HTML
            """
            <div class="input-group">
                <label class="label">
                    {{text}}
                </label>
                <input class="input" [name]="inputElem" value="{{value}}" placeholder="{{placeholder}}" />
            </div>
            """,
            text=text,
            value=value,
            placeholder=placeholder,
        )

        # Cancel
        self.popupFoot.appendChild(
            Button(abortLbl, self.onCancel, className="btn--cancel btn--danger")
        )

        # Okay
        self.okayBtn = Button(
            successLbl, self.onOkay, className="btn--okay btn--primary"
        )
        if not value:
            self.okayBtn.disable()

        self.popupFoot.appendChild(self.okayBtn)
        self.inputElem.focus()

    def onKeyDown(self, event):
        if html5.isReturn(event) and self.inputElem["value"]:
            event.stopPropagation()
            event.preventDefault()
            self.onOkay()

    def onKeyUp(self, event):
        if self.inputElem["value"]:
            self.okayBtn.enable()
        else:
            self.okayBtn.disable()

    def onDocumentKeyDown(self, event):
        if html5.isEscape(event):
            event.stopPropagation()
            event.preventDefault()
            self.onCancel()

    def onOkay(self, *args, **kwargs):
        if self.successHandler:
            self.successHandler(self, self.inputElem["value"])
        self.close()

    def onCancel(self, *args, **kwargs):
        if self.abortHandler:
            self.abortHandler(self, self.inputElem["value"])
        self.close()


class Alert(Popup):
    """Just displaying an alerting message box with OK-button."""

    def __init__(
            self,
            msg,
            title=None,
            className=None,
            okCallback=None,
            okLabel=None,
            icon="icon-info",
            closeable=True,
            *args,
            **kwargs
    ):
        super().__init__(
            title,
            className=None,
            icon=icon,
            closeable=closeable,
            enableShortcuts=closeable,
            *args,
            **kwargs
        )
        self.addClass("popup--alert")

        if className:
            self.addClass(className)

        if okLabel is None:
            okLabel = i18n.translate("flare.label.ok")

        self.okCallback = okCallback

        message = html5.Span()
        message.addClass("alert-msg")
        self.popupBody.appendChild(message)

        if isinstance(msg, str):
            msg = msg.replace("\n", "<br>")

        message.appendChild(msg, bindTo=False)

        self.sinkEvent("onKeyDown")

        if closeable:
            self.onClose = self.onOkBtnClick

            okBtn = Button(okLabel, callback=self.onOkBtnClick)
            okBtn.addClass("btn--okay btn--primary")
            self.popupFoot.appendChild(okBtn)

            okBtn.focus()

    def drop(self):
        self.okCallback = None
        self.close()

    def onOkBtnClick(self):
        if self.okCallback:
            self.okCallback(self)

        self.drop()

    def onKeyDown(self, event):
        if html5.isReturn(event):
            event.stopPropagation()
            event.preventDefault()
            self.onOkBtnClick()


class Confirm(Popup):
    def __init__(
            self,
            question,
            title=None,
            yesCallback=None,
            noCallback=None,
            yesLabel=None,
            noLabel=None,
            icon="icon-question",
            closeable=True,
            *args,
            **kwargs
    ):
        super().__init__(title, closeable=closeable, icon=icon, *args, **kwargs)
        self.addClass("popup--confirm")

        if yesLabel is None:
            yesLabel = i18n.translate("flare.label.yes")

        if noLabel is None:
            noLabel = i18n.translate("flare.label.no")

        self.yesCallback = yesCallback
        self.noCallback = noCallback

        lbl = html5.Span()
        lbl["class"].append("question")
        self.popupBody.appendChild(lbl)

        if isinstance(question, html5.Widget):
            lbl.appendChild(question)
        else:
            utils.textToHtml(lbl, question)

        if len(noLabel):
            btnNo = Button(noLabel, className="btn--no", callback=self.onNoClicked)
            self.popupFoot.appendChild(btnNo)

        btnYes = Button(yesLabel, callback=self.onYesClicked)
        btnYes.addClass("btn--yes", "btn--primary")
        self.popupFoot.appendChild(btnYes)

        self.sinkEvent("onKeyDown")
        btnYes.focus()

    def onKeyDown(self, event):
        if html5.isReturn(event):
            event.stopPropagation()
            event.preventDefault()
            self.onYesClicked()

    def onDocumentKeyDown(self, event):
        if html5.isEscape(event):
            event.stopPropagation()
            event.preventDefault()
            self.onNoClicked()

    def drop(self):
        self.yesCallback = None
        self.noCallback = None
        self.close()

    def onYesClicked(self, *args, **kwargs):
        if self.yesCallback:
            self.yesCallback(self)

        self.drop()

    def onNoClicked(self, *args, **kwargs):
        if self.noCallback:
            self.noCallback(self)

        self.drop()


class TextareaDialog(Popup):
    def __init__(
            self,
            text,
            value="",
            successHandler=None,
            abortHandler=None,
            successLbl=None,
            abortLbl=None,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.addClass("popup--textareadialog")

        if successLbl is None:
            successLbl = i18n.translate("flare.label.ok")

        if abortLbl is None:
            abortLbl = i18n.translate("flare.label.cancel")

        self.successHandler = successHandler
        self.abortHandler = abortHandler

        span = html5.Span()
        span.element.innerHTML = text
        self.popupBody.appendChild(span)

        self.inputElem = html5.Textarea()
        self.inputElem["value"] = value
        self.popupBody.appendChild(self.inputElem)

        okayBtn = Button(successLbl, self.onOkay)
        okayBtn["class"].append("btn--okay")
        self.popupFoot.appendChild(okayBtn)

        cancelBtn = Button(abortLbl, self.onCancel)
        cancelBtn["class"].append("btn--cancel")
        self.popupFoot.appendChild(cancelBtn)

        self.sinkEvent("onKeyDown")

        self.inputElem.focus()

    def onDocumentKeyDown(self, event):
        if html5.isEscape(event):
            event.stopPropagation()
            event.preventDefault()
            self.onCancel()

    def onOkay(self, *args, **kwargs):
        if self.successHandler:
            self.successHandler(self, self.inputElem["value"])
        self.close()

    def onCancel(self, *args, **kwargs):
        if self.abortHandler:
            self.abortHandler(self, self.inputElem["value"])
        self.close()


class radioButtonDialog(Popup):
    def __init__(
            self,
            title,
            radioValues: list,
            radioButtonGroupName="radioButtonGroup",
            checkedValue=None,
            icon="icon-question",
            closeable=True,
            successHandler=None,
            abortHandler=None,
            successLbl=None,
            abortLbl=None,
            *args,
            **kwargs
    ):
        """
        Creates a radioButton Popup

        radioValues list should contain tuples with displayValue and value e.g.: ('Barzahlung', 'cash')
        """

        super().__init__(title=title, icon=icon, closeable=closeable, *args, **kwargs)
        self.addClass("popup--radioButtonDialog")

        if successLbl is None:
            successLbl = i18n.translate("flare.label.ok")

        if abortLbl is None:
            abortLbl = i18n.translate("flare.label.cancel")

        self.successHandler = successHandler
        self.abortHandler = abortHandler

        okayBtn = Button(successLbl, self.onOkay)
        okayBtn["class"].append("btn--okay")
        self.popupFoot.appendChild(okayBtn)

        cancelBtn = Button(abortLbl, self.onCancel)
        cancelBtn["class"].append("btn--cancel")
        self.popupFoot.appendChild(cancelBtn)

        # Create HTML Form
        self.formElement = html5.Form()

        # Create radio Input and Label for all items provided
        if type(radioValues) is list:
            for displayValue, value in radioValues:
                # Generate element and add attributes
                radioElement = html5.Input()
                radioElement["type"] = "radio"
                radioElement["name"] = radioButtonGroupName
                radioElement["value"] = value

                # Auto generate id using the first and last char of the 'value' string. An id is required to add a Label
                radioElement["id"] = f"{value[0].lower() + value[-1].lower()}"

                # check if checkedValue is set. Check the radio button with the same value if it exist
                if value is checkedValue and type(checkedValue) is str:
                    radioElement["checked"] = "true"

                # styling
                radioElement.addClass("check-input")

                self.formElement.appendChild(radioElement)

                label = html5.Label()
                label.appendChild(displayValue)
                label["for"] = f"{value[0].lower() + value[-1].lower()}"
                label.addClass("check-label")
                self.formElement.appendChild(label)
        else:
            assert TypeError(f"radioValues param ({radioValues}) is not a list")

        # Append HTML Form to Popupbody
        self.popupBody.appendChild(self.formElement)

    # Fire events

    def onOkay(self, *args, **kwargs):
        if self.successHandler:

            children = self.formElement.children()
            for child in children:
                if child["checked"] and type(child) == html5.Input:
                    self.successHandler(self, child)  # return self and the checked child

        self.close()

    def onCancel(self, *args, **kwargs):
        if self.abortHandler:
            self.abortHandler(self, self.formElement.children())
        self.close()
