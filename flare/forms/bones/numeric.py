import re, logging
from flare import utils
from flare.ignite import *
from flare.forms import boneSelector
from flare.config import conf
from .base import BaseBone, BaseEditWidget, BaseViewWidget


def _formatCurrencyValue(value, bone):
    """Internal helper function that formats a numeric value which is a string according to the bone's formatting"""
    value = str(value).split(".")

    if value[0].startswith("-"):
        value[0] = value[0][1:]
        neg = True
    else:
        neg = False

    ival = ""
    for i in range(0, len(value[0])):
        if ival and i % 3 == 0:
            ival = bone.currencyThousandDelimiter + ival

        ival = value[0][-(i + 1)] + ival

    return (
        ("-" if neg else "")
        + ival
        + (
            (bone.currencyDecimalDelimiter + value[1])
            if len(value) > 1
            else ""
        )
        + " "
        + (bone.currency or "")
    )

class NumericEditWidget(BaseEditWidget):
    style = ["flr-value", "flr-value--numeric"]

    def createWidget(self):
        self.value = None

        tpl = html5.Template()
        # language=html
        tpl.appendChild(
            """
			<flare-input [name]="widget" type="{{inputType}}" class="input-group-item flr-input" />
		""",
            inputType="text" if self.bone.currency else "number",
            bindTo=self,
        )

        self.sinkEvent("onChange")

        return tpl

    def updateWidget(self):
        if not self.bone.currency:
            if self.bone.precision:
                if self.bone.precision <= 16:
                    self.widget["step"] = "0." + ("0" * (self.bone.precision - 1)) + "1"
                else:
                    self.widget["step"] = "any"

            else:  # Precision is zero, treat as integer input
                self.widget["step"] = 1

            if self.bone.min is not None:
                self.widget["min"] = self.bone.min

            if self.bone.max is not None:
                self.widget["max"] = self.bone.max
        else:
            self.widget["type"] = self.widget["step"] = \
                self.widget["min"] = self.widget["max"] = None

        if self.bone.readonly:
            self.widget.disable()
        else:
            self.widget.enable()

    def setValue(self, value):
        if not self.bone.currency:
            if self.bone.precision:
                self.value = utils.parseFloat(value or 0)
            else:
                self.value = utils.parseInt(value or 0)

            return self.value

        if value is None or not str(value).strip():
            self.value = None
            return ""

        if isinstance(value, float):
            value = str(value).replace(".", self.bone.currencyDecimalDelimiter)

        value = str(value).strip()

        if self.widget and self.bone.currencyPattern.match(value):
            self.widget.removeClass("is-invalid")

            try:
                # Remove any characters which are not digits, signs or the decimal delimiter
                value = re.sub(r"[^-0-9%s]" % self.bone.currencyDecimalDelimiter, "", value)
                # Replace the decimal delimiter by dot to parse the value as float
                value = value.replace(self.bone.currencyDecimalDelimiter, ".")

                if self.bone.precision == 0:
                    self.value = int(float(value))
                    value = str(self.value)
                else:
                    self.value = float("%.*f" % (self.bone.precision, float(value)))
                    value = "%.*f" % (self.bone.precision, self.value)

                # Check boundaries
                if self.bone.min is not None and self.value < self.bone.min:
                    return self.setValue(self.bone.min)
                elif self.bone.max is not None and self.value > self.bone.max:
                    return self.setValue(self.bone.max)

                return _formatCurrencyValue(value, self.bone)

            except Exception as e:
                self.widget.addClass("is-invalid")
                logging.exception(e)

        return value

    def onChange(self, event):
        self.widget["value"] = self.setValue(self.widget["value"])

    def unserialize(self, value=None):
        self.widget["value"] = self.setValue(value)

    def serialize(self):
        return self.value


class NumericViewWidget(BaseViewWidget):
    def unserialize(self, value=None):
        self.value = value

        if value is not None:
            if self.bone.precision:
                try:
                    value = "%0.*f" % (self.bone.precision, float(value))
                except ValueError:
                    value = None

            if self.bone.currency:
                value = _formatCurrencyValue(value, self.bone)

        self.replaceChild(html5.TextNode(conf["emptyValue"] if value is None else value))


class NumericBone(BaseBone):
    editWidgetFactory = NumericEditWidget
    viewWidgetFactory = NumericViewWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Numeric bone precision, min and max
        self.precision = self.boneStructure.get("precision") or 0
        self.min = utils.parseFloat(str(self.boneStructure.get("min")), None)
        self.max = utils.parseFloat(str(self.boneStructure.get("max")), None)

        # Currency mode
        self.currency = None
        self.currencyDecimalDelimiter = ","
        self.currencyThousandDelimiter = "."

        # Style parameters
        style = (self.boneStructure.get("params") or {}).get("style", "")
        for s in style.split(" "):
            if s.lower().startswith("currency"):
                if "." in s:
                    self.currency = s.split(".", 1)[1]
                else:
                    self.currency = "€"

                if self.precision is None:
                    self.precision = 2

            if s.lower().startswith("delimiter."):
                fmt = s.split(".", 1)[1]
                if fmt == "dot":
                    self.currencyDecimalDelimiter = "."
                    self.currencyThousandDelimiter = ","
            # elif: ... fixme are there more configs?

        self.precision = self.precision or 0  # yes, this must be done twice in this code!

        assert self.currencyThousandDelimiter[0] not in "^-+()[]"
        assert self.currencyDecimalDelimiter[0] not in "^-+()[]"

        self.currencyPattern = re.compile(
            r"-?((\d{1,3}[%s])*|\d*)[%s]\d+|-?\d+"
            % (self.currencyThousandDelimiter[0], self.currencyDecimalDelimiter[0])
        )

    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName]["type"] == "numeric" or skelStructure[boneName][
            "type"
        ].startswith("numeric.")


boneSelector.insert(1, NumericBone.checkFor, NumericBone)
