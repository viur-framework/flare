"""Wrapper to handle ViUR-related Ajax requests."""

import logging
from flare.event import EventDispatcher
import os, sys, json, string, random
from . import html5, i18n


class DeferredCall(object):
    """Calls the given function with a fixed delay.

    This allows assuming that calls to NetworkService are always
    asynchronous, so its guaranteed that any initialization code can run
    before the Network-Call yields results.
    """

    def __init__(self, func, *args, **kwargs):
        """Instantiate DeferredCall.

        :param func: Callback function
        :type func: Callable
        """
        super(DeferredCall, self).__init__()
        delay = 25
        self._callback = None

        if "_delay" in kwargs.keys():
            delay = kwargs["_delay"]
            del kwargs["_delay"]

        if "_callback" in kwargs.keys():
            self._callback = kwargs["_callback"]
            del kwargs["_callback"]

        self._tFunc = func
        self._tArgs = args
        self._tKwArgs = kwargs
        html5.window.setTimeout(self.run, delay)

    def run(self):
        """Internal callback that executes the callback function."""
        self._tFunc(*self._tArgs, **self._tKwArgs)
        if self._callback:
            self._callback(self)


class HTTPRequest(object):
    """Wrapper around XMLHttpRequest."""

    def __init__(
        self,
        method,
        url,
        callbackSuccess=None,
        callbackFailure=None,
        payload=None,
        content_type=None,
        response_type=None,
        asynchronous=True
    ):
        super(HTTPRequest, self).__init__()

        method = method.upper()
        assert method in ["GET", "POST"]

        self.method = method
        self.callbackSuccess = callbackSuccess
        self.callbackFailure = callbackFailure
        self.hasBeenSent = False
        self.payload = payload
        self.content_type = content_type

        self.req = html5.jseval("new XMLHttpRequest()")
        self.req.onreadystatechange = self.onReadyStateChange
        self.req.open(method, url, asynchronous)
        try:
            if response_type in ["blob", "arraybuffer", "document"]:
                self.req.responseType = response_type
            else:
                self.req.responseType = ""
        except:
            pass

    def onReadyStateChange(self, *args, **kwargs):
        """Internal callback."""
        if self.req.readyState == 1 and not self.hasBeenSent:
            self.hasBeenSent = True  # Internet Explorer calls this function twice!

            if self.method == "POST" and self.content_type is not None:
                self.req.setRequestHeader("Content-Type", self.content_type)

            self.req.send(self.payload)

        if self.req.readyState == 4:
            if 200 <= self.req.status < 300:
                if self.callbackSuccess:
                    if self.req.responseType in ["blob", "arraybuffer", "document"]:
                        self.callbackSuccess(self.req.response)
                    else:
                        self.callbackSuccess(self.req.responseText)
            # todo: report to log?
            else:
                if self.callbackFailure:
                    self.callbackFailure(self.req.responseText, self.req.status)
            # todo: report to log?


def NiceError(req, code, params="", then=None):
    """Displays a descriptive error message using an Alert dialog to the user."""
    reason = i18n.translate(
        f"flare.network.error.{code}", fallback=i18n.translate("flare.network.error")
    )
    hint = i18n.translate(f"flare.network.hint.{code}", fallback="")

    from . import popup

    popup.Alert(
        # language=HTML
        f"<strong>{reason}</strong>{hint}\n\n<em>{req.module}/{req.url}/{req.params}</em>",
        title=i18n.translate("flare.label.error") + " " + str(code),
        icon="icon-error",
        okCallback=then,
    )


def NiceErrorAndThen(function):
    """Returns a callback which first displays a descriptive error message to the user and then calls another function."""
    assert callable(function)
    return lambda *args, **kwargs: NiceError(
        *args, **kwargs, then=lambda *args, **kwargs: function()
    )


skeyRequestQueue = []


def processSkelQueue():
    if len(skeyRequestQueue) == 0:
        return 0

    if skeyRequestQueue[0].status not in ["running", "succeeded", "failed"]:
        skeyRequestQueue[0].status = "start"
        skeyRequestQueue[0].kickoff()
    else:
        DeferredCall(
            processSkelQueue, _delay=2000
        )  # try later, to ensure that all requests are finished


class NetworkService(object):
    """Generic wrapper around ajax requests.

    Handles caching and multiplexing multiple concurrent requests to
    the same resource. It also acts as the central proxy to notify
    currently active widgets of changes made to data on the server.
    """

    changeListeners = (
        []
    )  # All currently active widgets which will be informed of changes made

    host = ""
    prefix = "/json"
    defaultFailureHandler = NiceError

    retryCodes = [0, -1]
    retryMax = 3
    retryDelay = 5000

    @staticmethod
    def notifyChange(module, **kwargs):
        """Broadcasts a change made to data of module 'module' to all currently registered changeListeners.

        :param module: Name of the module where the change occured
        :type module: str
        """
        for c in NetworkService.changeListeners:
            c.onDataChanged(module, **kwargs)

    @staticmethod
    def registerChangeListener(listener):
        """Registers object 'listener' for change notifications.

        'listener' must provide an 'onDataChanged' function accepting
        one parameter: the name of the module. Does nothing if that object
        has already registered.
        :param listener: The object to register
        :type listener: object
        """
        if listener in NetworkService.changeListeners:
            return

        NetworkService.changeListeners.append(listener)

    @staticmethod
    def removeChangeListener(listener):
        """Unregisters the object 'listener' from change notifications.

        :param listener: The object to unregister. It must be currently registered.
        :type listener: object
        """
        assert (
            listener in NetworkService.changeListeners
        ), "Attempt to remove unregistered listener %s" % str(listener)
        NetworkService.changeListeners.remove(listener)

    @staticmethod
    def genReqStr(params):
        boundary_str = "---" + "".join(
            [
                random.choice(
                    string.ascii_lowercase + string.ascii_uppercase + string.digits
                )
                for x in range(13)
            ]
        )
        boundary = boundary_str

        res = f'Content-Type: multipart/mixed; boundary="{boundary}"\r\nMIME-Version: 1.0\r\n'
        res += "\r\n--" + boundary

        def expand(key, value):
            ret = ""

            if all([x in dir(value) for x in ["name", "read"]]):  # File
                type = "application/octet-stream"
                filename = os.path.basename(value.name).decode(
                    sys.getfilesystemencoding()
                )

                ret += (
                    f"\r\nContent-Type: {type}"
                    f"\r\nMIME-Version: 1.0"
                    f'\r\nContent-Disposition: form-data; name="{key}"; filename="{filename}"\r\n\r\n'
                )
                ret += str(value.read())
                ret += "\r\n--" + boundary

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
                ret += (
                    "\r\nContent-Type: application/octet-stream"
                    "\r\nMIME-Version: 1.0"
                    f'\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n'
                )
                ret += str(value) if value is not None else ""
                ret += "\r\n--" + boundary

            return ret

        for key, value in params.items():
            res += expand(key, value)

        res += "--\r\n"

        # fixme: DEBUG!
        # print(res)

        return res, boundary

    @staticmethod
    def decode(req):
        """Decodes a response received from the server (ie parsing the json).

        :type req: Instance of NetworkService response
        :returns: object
        """
        return json.loads(req.result)

    @staticmethod
    def isOkay(req):
        answ = NetworkService.decode(req)
        return isinstance(answ, str) and answ == "OKAY"

    @staticmethod
    def urlForArgs(module, path):
        """Constructs the final url for that request.

        If module is given, it prepends "/prefix"
        If module is None, path is returned unchanged.
        :param module: Name of the target module or None
        :type module: str or None
        :param path: Path (either relative to 'module' or absolute if 'module' is None
        :type path: str
        :returns: str
        """
        if module:
            href = "%s/%s/%s" % (NetworkService.prefix, module, path)
        else:
            href = path

        if not href.startswith("/"):
            href = "/" + href

        return NetworkService.host + href

    def __init__(
        self,
        module,
        url,
        params,
        successHandler,
        failureHandler,
        finishedHandler,
        modifies,
        secure,
        kickoff,
        group=None,
    ):
        """Constructs a new NetworkService request.

        Should not be called directly (use NetworkService.request instead).
        """
        super(NetworkService, self).__init__()

        self.result = None
        self.status = None
        self.waitingForSkey = False
        self.module = module
        self.url = url
        self.group = group

        if params and not isinstance(params, dict):
            self.url += "/%s" % params
            params = {}

        self.params = params

        self.successHandler = [successHandler] if successHandler else []
        self.failureHandler = [failureHandler] if failureHandler else []
        self.finishedHandler = [finishedHandler] if finishedHandler else []

        self.requestFinishedEvent = EventDispatcher("finished")
        self.requestFinishedEvent.register(self)
        self.modifies = modifies
        self.secure = secure

        self.kickoffs = 0
        if kickoff:
            self.kickoff()

    def kickoff(self):
        if not self.status and self.secure:
            # if the request not started and is secure add it to queue
            if len(skeyRequestQueue) == 0:
                skeyRequestQueue.append(self)
                processSkelQueue()
            else:
                skeyRequestQueue.append(self)

            return 0

        else:
            self.status = "running"
            self.kickoffs += 1

        if self.secure:
            self.waitingForSkey = True
            self.doFetch(
                "%s%s/skey" % (NetworkService.host, NetworkService.prefix), None, None
            )
        else:
            self.doFetch(
                NetworkService.urlForArgs(self.module, self.url), self.params, None
            )

    @staticmethod
    def request(
        module,
        url,
        params=None,
        successHandler=None,
        failureHandler=None,
        finishedHandler=None,
        modifies=False,
        secure=False,
        kickoff=True,
        group=None,
    ):
        """Performs an AJAX request. Handles caching and security-keys.

        Calls made to this function are guaranteed to be async.

        :param module: Target module on the server. Set to None if you want to call anything else
        :type module: str or None
        :param url: The path (relative to module) or a full url if module is None
        :type url: str or None
        :param successHandler: function beeing called if the request succeeds. Must take one argument (the request).
        :type successHandler: callable
        :param failureHandler: function beeing called if the request failes. Must take two arguments (the request and an error-code).
        :type failureHandler: callable
        :param finishedHandler: function beeing called if the request finished (regardless wherever it succeeded or not). Must take one argument (the request).
        :type finishedHandler: callable
        :param modifies: If set to True, it will automatically broadcast an onDataChanged event for that module.
        :type modifies: bool
        :param secure: If true, include a fresh securitykey in this request. Defaults to False.
        :type secure: bool

        """
        logging.debug(
            "NetworkService.request module=%r, url=%r, params=%r", module, url, params
        )

        if group:
            # grouped requests will always be handled later
            kickoff = False

        dataRequest = NetworkService(
            module,
            url,
            params,
            successHandler,
            failureHandler,
            finishedHandler,
            modifies,
            secure,
            kickoff,
            group,
        )

        if group:
            group.addRequest(dataRequest)

        return dataRequest

    def doFetch(self, url, params, skey):
        """Internal function performing the actual AJAX request."""
        if params:
            if skey:
                params["skey"] = skey

            contentType = None

            if isinstance(params, dict):
                multipart, boundary = NetworkService.genReqStr(params)
                contentType = (
                    "multipart/form-data; boundary=" + boundary + "; charset=utf-8"
                )
            elif isinstance(params, bytes):
                contentType = "application/x-www-form-urlencoded"
                multipart = params
            else:
                multipart = params

            HTTPRequest(
                "POST",
                url,
                self.onCompletion,
                self.onError,
                payload=multipart,
                content_type=contentType,
            )

        else:
            if skey:
                if "?" in url:
                    url += "&skey=%s" % skey
                else:
                    url += "?skey=%s" % skey

            HTTPRequest("GET", url, self.onCompletion, self.onError)

    def onCompletion(self, text):
        """Internal hook for the AJAX call."""
        if self.waitingForSkey:
            self.waitingForSkey = False
            self.doFetch(
                NetworkService.urlForArgs(self.module, self.url),
                self.params,
                json.loads(text),
            )
        else:
            self.result = text
            self.status = "succeeded"
            try:
                for s in self.successHandler:
                    s(self)
                for s in self.finishedHandler:
                    s(self)
                self.requestFinishedEvent.fire(True)
            except:
                if self.modifies:
                    DeferredCall(
                        NetworkService.notifyChange,
                        self.module,
                        key=self.params.get("key") if self.params else None,
                        action=self.url,
                        _delay=2500,
                    )
                raise

            if self.modifies:
                DeferredCall(
                    NetworkService.notifyChange,
                    self.module,
                    key=self.params.get("key") if self.params else None,
                    action=self.url,
                    _delay=2500,
                )

            # Remove references to our handlers
            self.clear()

    def onError(self, text, code):
        """Internal hook for the AJAX call."""
        self.status = "failed"
        self.result = text

        logging.debug(
            "NetworkService.onError kickoffs=%r, retryMax=%r, code=%r, retryCodes=%r",
            self.kickoffs,
            self.retryMax,
            code,
            self.retryCodes,
        )

        if self.kickoffs < self.retryMax and int(code) in self.retryCodes:
            # The following can be used to pass errors to a bugtracker service like Stackdriver or Bugsnag
            logError = None  # html5.window.top.logError
            if logError and self.kickoffs == self.retryMax - 1:
                logError(
                    "NetworkService.onError code:%s module:%s url:%s params:%s"
                    % (code, self.module, self.url, self.params)
                )

            logging.error("error %d, kickoff %d, will retry now", code, self.kickoffs)
            DeferredCall(self.kickoff, _delay=self.retryDelay)
            return

        for s in self.failureHandler:
            s(self, code)

        if not self.failureHandler and self.defaultFailureHandler:
            self.defaultFailureHandler(code)

        if not self.defaultFailureHandler:
            self.clear()

        for s in self.finishedHandler:
            s(self)

        self.requestFinishedEvent.fire(False)

    def onTimeout(self, text):
        """Internal hook for the AJAX call."""
        self.onError(text, -1)

    def clear(self):
        self.successHandler = []
        self.finishedHandler = []
        self.failureHandler = []
        self.params = None

    def onFinished(self, success):
        if self.secure and skeyRequestQueue:
            skeyRequestQueue.remove(self)
            processSkelQueue()


class requestGroup:
    def __init__(self, callback=None):
        self.callback = callback
        self.requestList = []
        self.allRequestsSuccessful = True

    def addRequest(self, request):
        self.requestList.append(request)

    def call(self):
        req = self.requestList.pop(0)  # get first request.
        req.requestFinishedEvent.register(self)
        req.kickoff()

    def onFinished(self, success):
        if not success:
            self.allRequestsSuccessful = False

        if len(self.requestList) > 0:
            self.call()
        else:
            self.callback(self.allRequestsSuccessful)


def getUrlHashAsString(urlHash=None):
    if not urlHash:
        urlHash = html5.window.location.hash

    if not urlHash:
        return None, None

    if "?" in urlHash:
        hashStr = urlHash[1 : urlHash.find("?")]
        paramsStr = urlHash[urlHash.find("?") + 1 :]
    else:
        hashStr = urlHash[1:]
        paramsStr = ""

    return hashStr, paramsStr


def getUrlHashAsObject(urlHash=None):
    hashStr, paramsStr = getUrlHashAsString(urlHash)
    if hashStr:
        hash = [x for x in hashStr.split("/") if x]
    else:
        hash = []
    param = {}

    if paramsStr:
        for pair in paramsStr.split("&"):
            if not "=" in pair:
                continue

            key = pair[: pair.find("=")]
            value = pair[pair.find("=") + 1 :]

            if not (key and value):
                continue

            if key in param.keys():
                if not isinstance(param[key], list):
                    param[key] = [paramsStr[key]]

                param[key].append(value)
            else:
                param[key] = value

    return hash, param


def setUrlHash(hash, param=None):
    if not isinstance(hash,str):
        try:
            hashStr = "/".join(hash)
        except:
            return 0

    if not param:
        hash = html5.window.location.hash
        if "?" in hash:
            paramsStr = hash.split("?", 1)[1]
        else:
            paramsStr = ""
    else:
        paramsStr = "&".join(["%s=%s" % (k, v) for k, v in param.items()])

    if paramsStr:
        paramsStr = "?" + paramsStr

    html5.window.location.hash = hashStr + paramsStr
