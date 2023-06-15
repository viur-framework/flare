"""Utility functions."""

from . import html5
from js import Worker


def unescape(val, maxLength=0):
    """Unquotes several HTML-quoted characters in a string.

    :param val: The value to be unescaped.
    :type val: str

    :param maxLength: Cut-off after maxLength characters.
            A value of 0 means "unlimited". (default)
    :type maxLength: int

    :returns: The unquoted string.
    :rtype: str
    """

    val = str(val)\
        .replace("&lt;", "<")\
        .replace("&gt;", ">")\
        .replace("&quot;", '"')\
        .replace("&#39;", "'")\
        .replace("&#040;", "(")\
        .replace("&#041;", ")")\
        .replace("&#061;", "=")


    if maxLength > 0:
        return val[0:maxLength]

    return val


def doesEventHitWidgetOrParents(event, widget):
    """Test if event 'event' hits widget 'widget' (or *any* of its parents)."""
    while widget:
        if event.target == widget.element:
            return widget

        widget = widget.parent()

    return None


def doesEventHitWidgetOrChildren(event, widget):
    """Test if event 'event' hits widget 'widget' (or *any* of its children)."""
    if event.target == widget.element:
        return widget

    for child in widget.children():
        if doesEventHitWidgetOrChildren(event, child):
            return child

    return None


def textToHtml(node, text):
    """Generates html nodes from text by splitting text into content and into line breaks html5.Br.

    :param node: The node where the nodes are appended to.
    :param text: The text to be inserted.
    """
    for (i, part) in enumerate(text.split("\n")):
        if i > 0:
            node.appendChild(html5.Br())

        node.appendChild(html5.TextNode(part))


def parseInt(s, ret=0):
    """Parses a value as int."""
    if not isinstance(s, str):
        return int(s)
    elif s:
        if s[0] in "+-":
            ts = s[1:]
        else:
            ts = s

        if ts and all([_ in "0123456789" for _ in ts]):
            return int(s)

    return ret


def parseFloat(s, ret=0.0):
    """Parses a value as float."""
    if not isinstance(s, str):
        return float(s)
    elif s:
        if s[0] in "+-":
            ts = s[1:]
        else:
            ts = s

        if ts and ts.count(".") <= 1 and all([_ in ".0123456789" for _ in ts]):
            return float(s)

    return ret

def createWorker( pythonCode, callback = None, errorCallback = None, context = { } ):
    """Generates and starts a Pyodide Webworker.

    def calllog(txt=None):
        result = txt.data.to_py()
        if "error" in result:
            print(result["error"])
        if "msg" in result:
            print(result["msg"])

    code='''
import statistics,time
from js import self as js_self
for i in range(0,100):
    js_self.postMessage("POST %s"%i)
'''

    createWorker(code,calllog,calllog)

    context can take variables, these are like global startparameters

    """
    worker = Worker.new( 'public/flare/js/worker.js' )
    worker.onmessage = callback
    worker.onerror = errorCallback
    worker.postMessage(python=pythonCode, **context)

    return worker
