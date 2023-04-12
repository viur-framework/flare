import logging, typing

from flare import html5, conf
from flare.viur import BoneSelector, InvalidBoneValueException
from flare.network import NetworkService, DeferredCall
from flare.button import Button
from flare.event import EventDispatcher
from flare.observable import StateHandler


@html5.tag("viur-form")
class ViurForm(html5.Form):
    """Handles an input form for a VIUR skeleton."""

    def __init__(
            self,
            formName: str = None,
            moduleName: str = None,
            actionName: str = "add",
            skel=None,
            structure=None,
            visible=(),
            ignore=(),
            hide=(),
            errors=None,
            context=None,
            *args,
            **kwargs
    ):
        logging.debug("ViurForm: %r, %r, %r, %r, %r, %r, %r, %r, %r, %r", formName, moduleName, actionName, skel,
                      structure, visible, ignore, hide, args, kwargs)
        super().__init__()
        self.formName = formName
        self.moduleName = moduleName
        self.actionName = actionName
        self.bones = {}
        self.skel = skel or {}
        self.errors = errors or []
        self.context = context or {}
        self.visible = visible
        self.ignore = ignore
        self.hide = hide

        if self.moduleName and self.actionName:
            self["method"] = "POST"
            self["action"] = f"{self.moduleName}/{self.actionName}"

        if isinstance(structure, list):
            self.structure = {k: v for k, v in structure}
        else:
            self.structure = structure  # fixme: What happens when structure is None?????

        self.formSuccessEvent = EventDispatcher("formSuccess")
        self.formSuccessEvent.register(self)

        self.state = StateHandler(["submitStatus"])
        self.state.register("submitStatus", self)

        self.addClass("form")
        self.sinkEvent("onChange")

    def onChange(self, event):
        DeferredCall(self.update)

    def onBoneChange(self, bone):
        DeferredCall(self.update)

    def _setModulename(self, val):
        self.moduleName = val

    def _setActionname(self, val):
        self.actionName = val

    def _setFormname(self, val):
        self.formName = val

    def buildForm(self):
        """
        Builds a form with save button.
        """
        self.buildInternalForm()
        self.appendChild(
            ViurFormSubmit(text="speichern", form=self)
        )

    def buildInternalForm(self):
        """
        Builds only the form.
        """
        for key, bone in self.structure.items():
            if key in self.ignore or (self.visible and key not in self.visible):
                continue

            bone_field = ViurFormBone(key, self, defaultvalue=bone.get("defaultvalue"))
            bone_field.onAttach()  # needed for value loading!  # fixme should be solved differently.

            # Hide invisible fields or fields with conditional flagging
            if not bone["visible"] or bone["params"].get("visibleIf"):
                bone_field.hide()

            # Disable fields with conditional flagging
            if bone["params"].get("readonlyIf"):
                bone_field.disable()

            self.appendChild(bone_field)

        self.update()  # Update conditional fields

    def registerField(self, key, widget):
        if key in self.ignore or (self.visible and key not in self.visible):
            return

        if key in self.bones:
            logging.error(
                "Double field definition in {}!, only first field will be used", self
            )
            return

        # Set change event
        if "changeEvent" in dir(widget.boneWidget):
            widget.boneWidget.changeEvent.register(self)  # onBoneChange

        self.bones[key] = widget

    def update(self):
        """
        Updates current form view state regarding conditional input fields.
        """
        values = None

        for key, desc in self.structure.items():
            for event in ("visibleIf", "readonlyIf", "evaluate"):
                if not (expr := desc["params"].get(event)):
                    continue

                # In case no conditionals are available, serialize only on first call.
                if values is None:
                    values = self.context.copy()
                    values.update(self.serialize(all=True))

                logging.debug("%r => %r", event, expr)
                #logging.debug("values = %r", values)

                # Compile expression at first run
                if isinstance(expr, str):
                    desc["params"][event] = conf["expressionEvaluator"].compile(expr)
                    if desc["params"][event] is None:
                        logging.error("Parse error: %s", expr)
                        continue

                    expr = desc["params"][event]

                try:
                    res = conf["expressionEvaluator"].execute(expr, values)
                except Exception as e:
                    logging.error("ScheißEval has thrown a useful error message for you:")
                    logging.exception(e)
                    res = False

                logging.debug("res = %r", res)

                if event == "evaluate":
                    self.bones[key].unserialize(res)

                elif res:
                    if event == "visibleIf":
                        self.bones[key].show()
                    elif event == "readonlyIf":
                        self.bones[key].disable()
                    else:
                        raise NotImplementedError("Unknown event %r", event)

                else:
                    if event == "visibleIf":
                        self.bones[key].hide()
                    elif event == "readonlyIf":
                        self.bones[key].enable()
                    else:
                        raise NotImplementedError("Unknown event %r", event)

    def submitForm(self):
        self.state.updateState("submitStatus", "sending")
        res = self.serialize()

        NetworkService.request(
            module=self.moduleName,
            url=self.actionName,
            params=res,
            secure=True,  # always with fresh skey
            successHandler=self.actionSuccess,
            failureHandler=self.actionFailed,
        )

        return res

    def unserialize(self, skel: typing.Dict = None):
        """
        Unserializes a dict of values into this form.
        :param skel: Either a dict of values to be unserialized into this form, or None for emptying all values.
        """
        self.skel = skel or {}

        for key, widget in self.bones.items():
            if "setContext" in dir(widget) and callable(widget.setContext):
                widget.setContext(self.context)

            widget.unserialize(self.skel.get(key))

        DeferredCall(self.update)

    def serialize(self, all=False) -> typing.Dict:
        """
        Serializes all bone's values into a dict to be sent to ViUR or the be evaluated.
        """
        res = {}
        if key := self.skel.get("key"):
            res["key"] = key

        for key, widget in self.bones.items():
            # ignore the key, it is stored in self.key, and read-only bones
            if key == "key" or (widget.bone.readonly and not all):
                continue

            try:
                res[key] = widget.serialize()
                if res[key] is None or res[key] == []:
                    res[key] = ""

            except InvalidBoneValueException as e:
                logging.exception(e)

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
        at_least_one_silly_error_meeeh = False

        for key, form_bone in self.bones.items():
            if errors := [error for error in self.errors
                          if error["fieldPath"][0] == key and
                             ((error["severity"] > 0 and form_bone.bone.required) or error["severity"] % 2 == 1)]:
                form_bone.setInvalid(errors)
                at_least_one_silly_error_meeeh = True
            else:
                form_bone.setValid()

        if at_least_one_silly_error_meeeh:
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
                bone_field = self.bones[boneName]  # todo dependency errors
                boneStructure = bone_field.structure[bone_field.boneName]
                if (error["severity"] % 2 == 0 and boneStructure["required"]) or error["severity"] % 2 == 1:  # invalid
                    # language=HTML
                    self.errorhint.appendChild(
                        """<span class="flr-bone--error">{{boneDescr}}: {{error}} </span>""",
                        boneDescr=boneStructure.get("descr", bone_field.boneName),
                        error=error["errorMessage"],
                    )

        self.errorhint.element.scrollIntoView()

    def actionFailed(self, req, *args, **kwargs):
        logging.debug("FAILED: %r", req)
        self.state.updateState("submitStatus", "failed")

    def onFormSuccess(self, event):
        self.createFormSuccessMessage()

    def onSubmitStatusChanged(self, value, *args, **kwargs):
        if value == "sending":
            self.addClass("is-loading")
        else:
            self.removeClass("is-loading")


@html5.tag("viur-form-bone")
class ViurFormBone(html5.Div):
    def __init__(self, boneName=None, form=None, defaultvalue=None, hidden=False, filter=None):
        logging.debug("ViurFormBone: %r, %r, %r", boneName, form, defaultvalue)
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

        self.bone = None
        self.containerWidget = None
        self.labelWidget = None
        self.boneWidget = None
        self.errorWidget = None

        self.addClass("flr-viur-form-bone")

    def onAttach(self):
        if not self.formloaded:
            if not self.boneName:
                logging.error("Please add boneName attribute to %r", self)

            if not self.form:
                logging.error("Please add :form attribute with a named form widget to %r", self)

            if self.form and "skel" not in dir(self.form) or "structure" not in dir(self.form):
                logging.error("Missing :skel and :structure data binding on referenced form %r", self.form)

            if "moduleName" not in dir(self.form):
                logging.error("Missing moduleName attribute on referenced form %r", self.form)

            # self.form existiert und form hat skel und structure
            if isinstance(self.form.structure, list):
                self.structure = {k: v for k, v in self.form.structure}
            else:
                self.structure = self.form.structure

            self.skel = self.form.skel  # fixme: do this in __setattr__
            self.moduleName = self.form.moduleName  # fixme: do this in __setattr__

            try:
                boneClass = BoneSelector.select(
                    self.moduleName,
                    self.boneName,
                    self.structure,
                    formName=self.form.formName
                )

                boneFactory = boneClass(
                    self.moduleName,
                    self.boneName,
                    self.structure,
                    self.form.errors
                )

                self.containerWidget, self.labelWidget, self.boneWidget, self.errorWidget = \
                    boneFactory.boneWidget(self.label, filter=self.filter)

                self.bone = self.boneWidget.bone

            except Exception as e:
                logging.exception(e)
                self.appendChild(f"""<div>Bone not found our invalid: {self.boneName}</div>""")
                return 0

            self.appendChild(self.containerWidget)
            self.containerWidget.onAttach() #this is needed! AGAIN!

            if self.boneName in self.form.hide or self.hidden:
                self._setHidden(True)
            else:
                self._setHidden(False)

            self.form.registerField(self.boneName, self)

            self.sinkEvent("onChange")

            value = self.skel.get(self.boneName)
            if value is None:
                value = self.defaultValue

            self.unserialize(value)
            self.formloaded = True

    def onChange(self, event, *args, **kwargs):
        pass

    def unserialize(self, data=None):
        self.boneWidget.unserialize(data)

    def serialize(self):
        return self.boneWidget.serialize()

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

    def setInvalid(self, errors=None):
        self.addClass("is-invalid")
        self.removeClass("is-valid")

        self.boneWidget.addClass("is-invalid")
        self.boneWidget.removeClass("is-valid")

        if self.labelWidget:
            self.labelWidget.addClass("is-invalid")
            self.labelWidget.removeClass("is-valid")

        if errors:
            self.errorWidget.tooltipDescr.replaceChild("<br>".join([error["errorMessage"] for error in errors]))
            self.errorWidget.show()
        else:
            self.errorWidget.hide()

    def setValid(self):
        self.addClass("is-valid")
        self.removeClass("is-invalid")

        self.boneWidget.addClass("is-valid")
        self.boneWidget.removeClass("is-invalid")

        if self.labelWidget:
            self.labelWidget.addClass("is-valid")
            self.labelWidget.removeClass("is-invalid")

        self.errorWidget.hide()


@html5.tag("viur-form-submit")
class ViurFormSubmit(Button):
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
        self.callback = self.sendViurForm

    def onAttach(self):
        if "form" not in dir(self) or not self.form:  # fixme... please solve this differenly...
            logging.debug("Please add :form attribute with a named form widget to {}.", self)
            self.element.innerHTML = "ERROR"
            self.disable()
        self.form.state.register("submitStatus", self)

    def sendViurForm(self, sender=None):
        self.form.submitForm()

    def onSubmitStatusChanged(self, value, *args, **kwargs):
        if value == "sending":
            self.addClass("is-loading")
        else:
            self.removeClass("is-loading")
