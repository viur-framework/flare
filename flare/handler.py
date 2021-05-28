"""Flare base handlers for ViUR prototypes."""

from .network import NetworkService
from .event import EventDispatcher
from .observable import StateHandler


class requestHandler:
    def __init__(
        self, module, action, params=(), eventName="listUpdated", secure=False
    ):
        self.module = module
        self.action = action
        self.params = params
        self.eventName = eventName
        self.secure = secure
        setattr(self, self.eventName, EventDispatcher(self.eventName))
        self.requestFailed = EventDispatcher("requestFailed")
        self.state = StateHandler((), self)
        self.state.updateState("listStatus", "init")

    def requestData(self, *args, **kwargs):
        self.state.updateState("listStatus", "loading")
        NetworkService.request(
            self.module,
            self.action,
            self.params,
            successHandler=self.requestSuccess,
            failureHandler=self._requestFailed,
            secure=self.secure,
        )

    def requestSuccess(self, req):
        self.state.updateState("listStatus", "success")
        resp = NetworkService.decode(req)
        self.resp = resp

        if self.action == "view":
            resp["values"] = self.buildSelectDescr(resp["values"], resp["structure"])

        getattr(self, self.eventName).fire(self.resp)

    def _requestFailed(self, req, *args, **kwargs):
        self.state.updateState("listStatus", "failed")
        print("REQUEST Failed")
        print(req)
        # resp = NetworkService.decode(req)
        # print(resp)
        self.requestFailed.fire(req)

    def onListStatusChanged(self, event, *args, **kwargs):
        pass

    def getDescrFromValue(self, definition, val):
        return dict(definition["values"])[val]

    def buildSelectDescr(self, skel, structure):
        for bone, definition in dict(structure).items():
            if definition["type"].startswith("relational.") and definition["using"]:
                if isinstance(skel[bone], list):
                    skel[bone] = [
                        {
                            "dest": relskel["dest"],
                            "rel": self.buildSelectDescr(
                                relskel["rel"], definition["using"]
                            ),
                        }
                        for relskel in skel[bone]
                    ]
                else:
                    try:
                        skel[bone]["rel"] = self.buildSelectDescr(
                            skel[bone]["rel"], definition["using"]
                        )
                    except:
                        pass

            if definition["type"] != "select":
                continue
            try:
                if isinstance(skel[bone], str):
                    descr = self.getDescrFromValue(definition, skel[bone])
                elif isinstance(skel[bone], list):
                    descr = [
                        self.getDescrFromValue(definition, val) for val in skel[bone]
                    ]
                else:
                    descr = None

                skel[bone + "_descr"] = descr
            except:
                skel[bone + "_descr"] = None
        return skel


class ListHandler(requestHandler):
    def __init__(
        self, module, action, params=(), eventName="listUpdated", secure=False
    ):
        self.cursor = None
        self.complete = False
        self.skellist = []
        self.structure = {}
        super().__init__(module, action, params, eventName, secure)

    def reload(self):
        self.skellist = []
        self.requestData()

    def filter(self, filterparams):
        self.params = filterparams
        self.reload()

    def getCurrentAmount(self):
        return len(self.skellist)

    def requestNext(self):
        if not self.complete:
            self.params.update({"cursor": self.cursor})
            self.requestData()

    def requestSuccess(self, req):
        self.state.updateState("listStatus", "success")
        resp = NetworkService.decode(req)
        self.resp = resp

        if "cursor" in resp and not resp["cursor"]:
            self.complete = True
            self.cursor = resp["cursor"]

        if not self.structure and "structure" in resp:
            self.structure = resp["structure"]
        # self.skellist += resp["skellist"]
        self.skellist = []
        for skel in resp["skellist"]:
            skel = self.buildSelectDescr(skel, self.structure)
            self.skellist.append(skel)

        getattr(self, self.eventName).fire(self.skellist)
