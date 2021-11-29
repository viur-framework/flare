# -*- coding: utf-8 -*-
import datetime, logging
from flare import html5
from flare.forms import boneSelector
from flare.config import conf
from flare.i18n import translate
from .base import BaseBone, BaseEditWidget, BaseViewWidget


class DateEditWidget(BaseEditWidget):
    style = ["flr-value", "flr-value--date"]

    def createWidget(self):
        self.serverToClient = []

        self.hasDate = self.bone.boneStructure.get("date", True)
        self.hasTime = self.bone.boneStructure.get("time", True)

        self.dateInput = None
        self.timeInput = None

        tpl = html5.Template()
        # language=HTML
        tpl.appendChild(
            """
					<div class='flr-wrapper'>
						<flare-input type="date" flare-if="{{hasDate}}" class="input-group-item" [name]="dateInput">
						<flare-input type="time" step="1" flare-if="{{hasTime}}" class="input-group-item" [name]="timeInput">
					</div>
				""",
            hasDate=self.hasDate,
            hasTime=self.hasTime,
            bindTo=self,
        )

        if self.hasDate:
            self.serverToClient.append("%d.%m.%Y")

        if self.hasTime:
            self.serverToClient.append("%H:%M:%S")

        return tpl

    def updateWidget(self):
        if self.hasDate:
            self.dateInput["required"] = self.bone.required

            if self.bone.readonly:
                self.dateInput.disable()
            else:
                self.dateInput.enable()

        if self.hasTime:
            self.timeInput["required"] = self.bone.required

            if self.bone.readonly:
                self.timeInput.disable()
            else:
                self.timeInput.enable()

    def unserialize(self, value=None):
        if value:

            # core sends iso date since PR240
            # https://github.com/viur-framework/viur-core/pull/240
            try:
                value = datetime.datetime.fromisoformat(value)
            except:
                try:
                    value = datetime.datetime.strptime(
                        value, " ".join(self.serverToClient)
                    )
                except Exception as e:
                    logging.exception(e)
                    value = None

            if value:
                if self.dateInput:
                    self.dateInput["value"] = value.strftime("%Y-%m-%d")

                if self.timeInput:
                    self.timeInput["value"] = value.strftime("%H:%M:%S")

    def serialize(self):
        value = datetime.datetime.strptime("00:00:00", "%H:%M:%S")
        haveTime = False
        haveDate = False

        if self.dateInput:
            if self.dateInput["value"]:
                try:
                    date = datetime.datetime.strptime(
                        self.dateInput["value"], "%Y-%m-%d"
                    )
                    value = value.replace(
                        year=date.year, month=date.month, day=date.day
                    )
                    haveDate = True

                except Exception as e:
                    logging.exception(e)
        else:
            haveDate = True

        if self.timeInput:
            if self.timeInput["value"]:
                if len(self.timeInput["value"].split(":")) < 3:
                    self.timeInput["value"] = self.timeInput["value"] + ":00"
                try:
                    time = datetime.datetime.strptime(
                        self.timeInput["value"], "%H:%M:%S"
                    )
                    value = value.replace(
                        hour=time.hour, minute=time.minute, second=time.second
                    )
                    haveTime = True

                except Exception as e:
                    logging.exception(e)
            else:
                # date without time is OK!
                haveTime = haveDate and self.dateInput
        else:
            haveTime = True

        if haveDate and haveTime:
            return value.strftime(" ".join(self.serverToClient))

        return ""


class DateViewWidget(BaseViewWidget):
    def unserialize(self, value=None):
        if value:
            serverToClient = []

            if self.bone.boneStructure.get("date", True):
                serverToClient.append("%d.%m.%Y")  # fixme: Again german format??

            if self.bone.boneStructure.get("time", True):
                serverToClient.append("%H:%M:%S")

            try:
                try:
                    self.value = datetime.datetime.fromisoformat(value)
                except:
                    self.value = datetime.datetime.strptime(
                        value or "", " ".join(serverToClient)
                    )

                value = self.value.strftime(
                    translate("vi.bone.date.at").join(serverToClient)
                )  # fixme: hmm...
            except:
                value = "Invalid Datetime Format"

        self.replaceChild(html5.TextNode(value or conf["emptyValue"]))


class DateBone(BaseBone):
    editWidgetFactory = DateEditWidget
    viewWidgetFactory = DateViewWidget

    @staticmethod
    def checkFor(moduleName, boneName, skelStructure, *args, **kwargs):
        return skelStructure[boneName]["type"] == "date" or skelStructure[boneName][
            "type"
        ].startswith("date.")


boneSelector.insert(1, DateBone.checkFor, DateBone)
