import logging
from flare import html5
from flare.forms import boneSelector, InvalidBoneValueException
from flare.network import NetworkService
from flare.button import Button
from flare.event import EventDispatcher
from flare.observable import StateHandler


@html5.tag("flare-form")
class viurForm(html5.Form):
    """Handles an input form for a VIUR skeleton."""

    def __init__(
        self,
        formName: str=None,
        moduleName: str=None,
        actionName: str="add",
        skel=None,
        structure=None,
        visible=(),
        ignore=(),
        hide=(),
        errors=None,
        defaultValues=(),
        *args,
        **kwargs
    ):
        logging.debug("viurForm: %r, %r, %r, %r, %r, %r, %r, %r, %r, %r, %r", formName, moduleName, actionName, skel, structure, visible, ignore, hide, defaultValues, args, kwargs)
        super().__init__()
        self.formName = formName
        self.moduleName = moduleName
        self.actionName = actionName
        self.bones = {}
        self.skel = skel
        self.errors = errors or []
        self.visible = visible
        self.ignore = ignore
        self.hide = hide
        self.defaultValues = defaultValues
        self["method"] = "POST"
        self["action"] = f"{self.moduleName}/{self.actionName}"

        if isinstance(structure, list):
            self.structure = {k: v for k, v in structure}
        else:
            self.structure = structure

        self.formSuccessEvent = EventDispatcher("formSuccess")
        self.formSuccessEvent.register(self)

        self.state = StateHandler( ["submitStatus"] )
        self.state.register("submitStatus",self)


        self.addClass("form")
        self.sinkEvent("onChange")

    def onChange(self, event):
        self.applyVisiblity()

    def _setModulename(self, val):
        self.moduleName = val

    def _setActionname(self, val):
        self.actionName = val

    def _setFormname(self, val):
        self.formName = val

    def buildForm(self):
        for key, bone in self.structure.items():
            if key in self.ignore:
                continue
            elif self.visible and key not in self.visible:
                continue

            boneValue = None
            if key in self.defaultValues:
                boneValue = self.defaultValues[key]
            bonefield = boneField(key, self, boneValue)
            self.appendChild(bonefield)

        submitbtn = sendForm(text="speichern", form=self)
        self.appendChild(submitbtn)

    def buildInternalForm(self):
        for key, bone in self.structure.items():
            if key in self.ignore:
                continue
            elif self.visible and key not in self.visible:
                continue

            bonefield = boneField(key, self)
            bonefield.onAttach() #needed for value loading!

            self.appendChild(bonefield)

    def registerField(self, key, widget):
        if key in self.ignore:
            return 0
        elif self.visible and key not in self.visible:
            return 0

        if key in self.bones:
            logging.debug(
                "Double field definition in {}!, only first field will be used", self
            )
            return 0

        self.bones[key] = widget

    def applyVisiblity(self):
        # only PoC!
        # WIP
        for key, boneField in self.bones.items():
            codestr = getattr(boneField, "visibleif", None)
            if not codestr:
                continue

            from flare.config import conf

            seInst = conf["safeEvalInstance"]
            seResult = seInst.execute(
                seInst.compile(codestr), self.collectCurrentFormValues()
            )

            widget = boneField.boneWidget
            if not seResult:
                boneField.hide()
            else:
                boneField.show()

    def submitForm(self):
        self.state.updateState("submitStatus","sending")
        res = self.collectCurrentFormValues()

        NetworkService.request(
            module=self.moduleName,
            url=self.actionName,
            params=res,
            secure=True,  # always with fresh skey
            successHandler=self.actionSuccess,
            failureHandler=self.actionFailed,
        )

        return res

    def collectCurrentFormValues(self):
        res = {}
        if "key" in self.skel and self.skel["key"]:
            res["key"] = self.skel["key"]

        for key, boneField in self.bones.items():
            widget = boneField.boneWidget
            # ignore the key, it is stored in self.key, and read-only bones
            if key == "key" or widget.bone.readonly:
                continue

            try:
                res[key] = widget.serialize()
                if res[key] is None or res[key] == []:
                    res[key] = ""

            except InvalidBoneValueException as e:
                print(e)
                pass

        # if validityCheck:
        # 	return None
        return res

    def actionSuccess(self, req):
        resp = NetworkService.decode(req)
        logging.debug("actionSuccess: %r", resp)
        """
        severity cases:
            NotSet = 0
            InvalidatesOther = 1 <-- relevant
            Empty = 2
            Invalid = 3			 <-- relevant
        """
        if "action" in resp and resp["action"].endswith("Success"):
            # form approved: Let's store the new skeleton values and fire the success event
            self.skel = resp["values"]
            self.formSuccessEvent.fire(self)

        else:
            # form rejected
            self.errors = resp["errors"]
            self.handleErrors()

        self.state.updateState("submitStatus", "finished")

    def handleErrors(self):
        for error in self.errors:
            if error["fieldPath"][0] in self.bones:
                boneName = error["fieldPath"][0]
                boneField = self.bones[boneName]  # todo dependency errors
                boneStructure = boneField.structure[boneField.boneName]
                if (error["severity"] % 2 == 0 and boneStructure["required"]) or (
                    error["severity"] % 2 == 1
                ):  # invalid

                    boneField.setInvalid()
                else:
                    boneField.setValid()

        self.createFormErrorMessage()

    def createFormSuccessMessage(self):
        try:
            self.removeChild(self.errorhint)
        except:
            pass

        if "successhint" not in dir(self):
            # language=HTML
            self.prependChild(
                """
						<div [name]="successhint" class="msg is-active msg--success ">Erfolgreich gespeichert!</div>
					"""
            )

    def createFormErrorMessage(self):
        try:
            self.removeChild(self.successhint)
        except:
            pass

        if "errorhint" not in dir(self):
            # language=HTML
            self.prependChild(
                """
				<div [name]="errorhint" class="msg is-active msg--error " style="flex-direction: column;"></div>
			"""
            )

        self.errorhint.removeAllChildren()
        for error in self.errors:
            if error["fieldPath"][0] in self.bones:
                boneName = error["fieldPath"][0]
                boneField = self.bones[boneName]  # todo dependency errors
                boneStructure = boneField.structure[boneField.boneName]
                if (error["severity"] % 2 == 0 and boneStructure["required"]) or (
                        error["severity"] % 2 == 1
                ):  # invalid

                    # language=HTML
                    self.errorhint.appendChild(
                        """<span class="flr-bone--error">{{boneDescr}}: {{error}} </span>""",
                        boneDescr=boneStructure.get(
                            "descr", boneField.boneName
                        ),
                        error=error["errorMessage"],
                    )

        self.errorhint.element.scrollIntoView()

    def actionFailed(self, req, *args, **kwargs):
        logging.debug("FAILED: %r", req)
        self.state.updateState("submitStatus", "failed")

    def onFormSuccess(self, event):
        self.createFormSuccessMessage()

    def onSubmitStatusChanged(self,value,*args,**kwargs):
        if value=="sending":
            self.addClass("is-loading")
        else:
            self.removeClass("is-loading")


@html5.tag("flare-form-field")
class boneField(html5.Div):
    def __init__(self, boneName=None, form=None, defaultvalue=None, hidden=False, filter=None):
        logging.debug("boneField: %r, %r, %r", boneName, form, defaultvalue)
        super().__init__()

        self.boneName = boneName
        self.form = form
        self.moduleName = self.form.moduleName if self.form else None
        self.skel = None
        self.label = True
        self.hidden = hidden
        self.placeholder = False
        self.defaultValue = defaultvalue
        self.filter = filter
        self.formloaded = False

        self.containerWidget = None
        self.labelWidget = None
        self.boneWidget = None

    def onAttach(self):
        if not self.formloaded:
            if not self.boneName:
                logging.debug("Please add boneName attribute to {}", self)

            if self.form:
                logging.debug("Please add :form attribute with a named form widget to {}.", self)

            if "skel" not in dir(self.form) or "structure" not in dir(self.form):
                logging.debug("Missing :skel and :structure data binding on referenced form", self.form)

            if "moduleName" not in dir(self.form):
                logging.debug("Missing moduleName attribute on referenced form", self.form)

            # self.form existiert und form hat skel und structure
            if isinstance(self.form.structure, list):
                self.structure = {k: v for k, v in self.form.structure}
            else:
                self.structure = self.form.structure

            self.skel = self.form.skel  #fixme: do this in __setattr__
            self.moduleName = self.form.moduleName  #fixme: do this in __setattr__

            try:
                boneClass = boneSelector.select(
                    self.moduleName,
                    self.boneName,
                    self.structure,
                    formName=self.form.formName
                )
                boneFactory = boneClass(self.moduleName, self.boneName, self.structure, self.form.errors)

                self.containerWidget, self.labelWidget, self.boneWidget, hasError = \
                    boneFactory.boneWidget(self.label, filter=self.filter)

            except Exception as e:
                logging.exception(e)
                self.appendChild(f"""<div>Bone not found our invalid: {self.boneName}</div>""")
                return 0

            self.appendChild(self.containerWidget)

            if self.boneName in self.form.hide or self.hidden:
                self._setHidden(True)
            else:
                self._setHidden(False)

            self.form.registerField(self.boneName, self)

            self.sinkEvent("onChange")

            if self.defaultValue:
                # warning overrides server default
                self.skel[self.boneName] = self.defaultValue

            self.unserialize(self.skel)
            self.formloaded = True

    def onChange(self, event, *args, **kwargs):
        pass

    def unserialize(self, data=None):
        for key, bone in self.form.bones.items():
            if data is not None:
                bone.boneWidget.unserialize(data.get(key))

    def _setBonename(self, val):
        self.boneName = val

    def _setLabel(self, val):
        if val == "True":
            self.label = True
        else:
            self.label = False

    def _setPlaceholder(self, val):
        if val:
            self.placeholder = val
        else:
            self.placeholder = False

    def _setHide(self, val):
        if val == "True":
            self.hidden = True
        else:
            self.hidden = False

    def _setValue(self, val):
        self.defaultValue = val

    def labelTemplate(self):
        return False
        """Default label."""
        # language=HTML
        return """<label [name]="boneLabel" class="input-group-item--first label flr-label flr-label--{{type}} flr-label--{{boneName}}">{{descr}}</label>"""

    def setInvalid(self):
        self.toggleClass("is-invalid", "is-valid")  # wrapper
        if self.boneLabel:
            self.boneLabel.toggleClass("is-invalid", "is-valid")  # label
        self.boneWidget.toggleClass("is-invalid", "is-valid")  # bone

    def setValid(self):
        self.toggleClass("is-valid", "is-invalid")
        if self.boneLabel:
            self.boneLabel.toggleClass("is-valid", "is-invalid")
        self.boneWidget.toggleClass("is-valid", "is-invalid")


@html5.tag("flare-form-submit")
class sendForm(Button):
    def __init__(
        self,
        text=None,
        callback=None,
        className="btn--submit btn--primary",
        icon=None,
        badge=None,
        form=None,
    ):
        super().__init__(text, callback, className, icon)
        self.form = form

    def onAttach(self):
        if "form" not in dir(self) or not self.form:
            logging.debug(
                "Please add :form attribute with a named form widget to {}.", self
            )
            self.element.innerHTML = "ERROR"
            self.disable()
        self.form.state.register("submitStatus", self)
        self.callback = self.sendViurForm

    def sendViurForm(self, widget):
        self.form.submitForm()

    def onSubmitStatusChanged(self, value, *args, **kwargs):
        if value == "sending":
            self.addClass("is-loading")
        else:
            self.removeClass("is-loading")
