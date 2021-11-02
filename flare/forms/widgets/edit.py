import logging

from flare import html5, conf
from flare.network import DeferredCall
from flare.forms.formtags import viurForm


class EditWidget(html5.Div):
    def __init__(self, structure=None, values=None, errors=None, context=None):
        super().__init__()
        self.addClass("flr-internal-edit")
        self.sinkEvent("onChange")

        self.structure = structure
        self.values = None
        self.context = context or {}

        self.bones = {}
        self.containers = {}

        self.modified = False

        if self.structure:
            self._render(values, errors, self.structure)

    def _render(self, values, errors, structure=None):
        assert structure or self.structure
        if structure:
            if isinstance(structure, list):
                # turn list of key-desc-tuples into dict
                self.structure = {k: v for k, v in structure}
            else:
                self.structure = structure

        self._form(values, errors)

    def _form(self, values, errors):
        self.removeAllChildren()

        form = viurForm(skel=values, structure=self.structure, errors=errors)
        form.buildInternalForm()
        self.appendChild(form)

        # Map form widgets to internal bones mapping
        for key, bone in form.bones.items():
            self.bones[key] = bone.boneWidget
            self.containers[key] = bone.containerWidget

    def unserialize(self, values=None, errors=()):
        self.values = values or {}

        for key, boneWidget in self.bones.items():
            if "setContext" in dir(boneWidget) and callable(boneWidget.setContext):
                boneWidget.setContext(self.context)

            boneWidget.unserialize(self.values.get(key))

        self.modified = False
        DeferredCall(self._update)

    def serialize(self):
        res = {}

        for key, boneWidget in self.bones.items():
            try:
                res[key] = boneWidget.serialize()

            except Exception as e:
                logging.exception(e)

        return res

    def _update(self):
        fields = self.serialize()

        for key, desc in self.structure.items():
            for event in ("visibleIf", "readonlyIf", "evaluate"):
                if not (expr := desc["params"].get(event)):
                    continue

                # Compile expression at first run
                if isinstance(expr, str):
                    desc["params"][event] = conf["expressionEvaluator"].compile(expr)
                    if desc["params"][event] is None:
                        logging.error("Parse error: %s", expr)
                        continue

                    expr = desc["params"][event]

                try:
                    res = conf["expressionEvaluator"].execute(expr, fields)
                except Exception as e:
                    logging.error("ScheißEval has thrown some error, probably due to its 'compatibility' to logics...")
                    logging.exception(e)
                    res = False

                if event == "evaluate":
                    self.bones[key].unserialize({key: res})
                elif res:
                    if event == "visibleIf":
                        self.containers[key].show()
                    elif event == "readonlyIf":
                        self.containers[key].disable()
                    else:
                        raise NotImplementedError("Unknown event %r", event)
                else:
                    if event == "visibleIf":
                        self.containers[key].hide()
                    elif event == "readonlyIf":
                        self.containers[key].enable()
                    else:
                        raise NotImplementedError("Unknown event %r", event)

    def onChange(self, event):
        self.modified = True
        DeferredCall(self._update)

    def onBoneChange(self, bone):
        self.modified = True
        DeferredCall(self._update)
