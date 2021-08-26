"""Flare base handlers for ViUR prototypes."""

from .network import NetworkService, HTTPRequest
from .event import EventDispatcher
from .observable import StateHandler
import string, random, os, json


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
        print(f'{self.module} request')
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
        self.cursor = None
        self.complete = False
        if "cursor" in self.params:
            del self.params["cursor"]
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

        resp = NetworkService.decode(req)
        self.resp = resp

        if "cursor" in resp and not resp["cursor"]:
            self.complete = True

        self.cursor = resp.get("cursor","")

        if not self.structure and "structure" in resp:
            self.structure = resp["structure"]

        for skel in resp["skellist"]:
            skel = self.buildSelectDescr(skel, self.structure)
            self.skellist.append(skel)
        self.state.updateState("listStatus", "success")
        getattr(self, self.eventName).fire(self.skellist)

class SyncHandler(object):
    @staticmethod
    def request(url, params=None, jsonResult=None):
        request = SyncHandler()._request(url, params)

        if request.status == "failed":
            return request.status

        if not jsonResult:
            return request.result

        return json.loads(request.result)

    def genReqStr(self, params):
        boundary_str = "---" + ''.join(
            [random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for x in range(13)])
        boundary = boundary_str

        res = f"Content-Type: multipart/mixed; boundary=\"{boundary}\"\r\nMIME-Version: 1.0\r\n"
        res += "\r\n--" + boundary

        def expand(key, value):
            ret = ""

            if all([x in dir(value) for x in ["name", "read"]]):  # File
                type = "application/octet-stream"
                filename = os.path.basename(value.name).decode(sys.getfilesystemencoding())

                ret += \
                    f"\r\nContent-Type: {type}" \
                    f"\r\nMIME-Version: 1.0" \
                    f"\r\nContent-Disposition: form-data; name=\"{key}\"; filename=\"{filename}\"\r\n\r\n"
                ret += str(value.read())
                ret += '\r\n--' + boundary

            elif isinstance(value, list):
                if any([isinstance(entry, dict) for entry in value]):
                    for idx, entry in enumerate(value):
                        ret += expand(key + "." + str(idx), entry)
                else:
                    for entry in value:
                        ret += expand(key, entry)

            elif isinstance(value, dict):
                for key_, entry in value.items():
                    ret += expand(((key + ".") if key else "") + key_, entry)

            else:
                ret += \
                    "\r\nContent-Type: application/octet-stream" \
                    "\r\nMIME-Version: 1.0" \
                    f"\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n"
                ret += str(value) if value is not None else ""
                ret += '\r\n--' + boundary

            return ret

        for key, value in params.items():
            res += expand(key, value)

        res += "--\r\n"
        return res, boundary

    def __init__(self):
        self.result = None
        self.status = None

    def _request(self, url, params):
        if params:
            method = "POST"

            contentType = None

            if isinstance(params, dict):
                multipart, boundary = self.genReqStr(params)
                contentType = "multipart/form-data; boundary=" + boundary + "; charset=utf-8"
            elif isinstance(params, bytes):
                contentType = "application/x-www-form-urlencoded"
                multipart = params
            else:
                multipart = params

            HTTPRequest(method, url, self.onCompletion, self.onError, payload=multipart, content_type=contentType,
                        asynchronous=False)
        else:
            method = "GET"
            HTTPRequest(method, url, self.onCompletion, self.onError, asynchronous=False)
        return self

    def onCompletion(self, text):
        self.result = text
        self.status = "succeeded"

    def onError(self, text, code):
        self.status = "failed"
        self.result = text
        self.code = code
