"""HTML5 Widget abstraction library.

- Provides a Widget-abstraction for each HTML-element
- Routing of attribute getter/setter and Jquery-style helpers
- Fully-integrated HTML-parser for quick Widget prototyping
"""

import string, re, logging, inspect
from types import SimpleNamespace
from typing import Any, Callable, Dict

# htmlExpressionEvaluator is used for interpreting conditional expressions
# By default, this points to a SafeEval() instance, but can be changed
# to any other interpreter providing an execute(code, vars) function.
# See for usage below.
htmlExpressionEvaluator = None

########################################################################################################################
# DOM-access functions and variables
########################################################################################################################

try:
    # Pyodide
    from js import window, eval as jseval
    import pyodide
    document = window.document

except:
    # This is only a dummy, but a demo to show how to bind html5 to another rendering environment.
    print("Emulation mode")
    from xml.dom.minidom import parseString

    jseval = None
    window = None
    document = parseString("<html><head /><body /></html>")


def domCreateAttribute(tag, ns=None):
    """Creates a new HTML/SVG/... attribute.

    :param ns: the namespace. Default: HTML. Possible values: HTML, SVG, XBL, XUL
    """
    uri = None

    if ns == "SVG":
        uri = "http://www.w3.org/2000/svg"
    elif ns == "XBL":
        uri = "http://www.mozilla.org/xbl"
    elif ns == "XUL":
        uri = "http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul"

    if uri:
        return document.createAttribute(uri, tag)

    return document.createAttribute(tag)


def domCreateElement(tag, ns=None):
    """Creates a new HTML/SVG/... tag.

    :param ns: the namespace. Default: HTML. Possible values: HTML, SVG, XBL, XUL
    """
    uri = None

    if ns == "SVG":
        uri = "http://www.w3.org/2000/svg"
    elif ns == "XBL":
        uri = "http://www.mozilla.org/xbl"
    elif ns == "XUL":
        uri = "http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul"

    if uri:
        return document.createElementNS(uri, tag)

    return document.createElement(tag)


def domCreateTextNode(txt=""):
    return document.createTextNode(txt)


def domGetElementById(idTag):
    return document.getElementById(idTag)


def domElementFromPoint(x, y):
    return document.elementFromPoint(x, y)


def domGetElementsByTagName(tag):
    items = document.getElementsByTagName(tag)
    return [
        items.item(i) for i in range(0, int(items.length))
    ]  # pyodide interprets items.length as float, so convert to int


__domParser = None


def domParseString(string, mimetype="text/html"):
    """
    Parses the given string with the optionally given mimetype using JavaScript's DOM parser.
    :param string: Any XML/HTML string processable by DOMParser.
    :param mimetype: The mimetype to use.

    :return: Returns the parsed document DOM.
    """
    global __domParser

    if jseval is None:
        return string

    if __domParser is None:
        __domParser = jseval("new DOMParser")

    return __domParser.parseFromString(string, mimetype)


def domConvertEncodedText(txt):
    """Convert HTML-encoded text (containing HTML entities) into its decoded string representation.

    The reason for this function is the handling of HTML entities, which is not properly supported by native JavaScript.

    We use the browser's DOM parser to do this, according to
    https://stackoverflow.com/questions/3700326/decode-amp-back-to-in-javascript

    :param txt: The encoded text.
    :return: The decoded text.
    """
    doc = domParseString("<!doctype html><body>" + str(txt))
    return doc.body.textContent


########################################################################################################################
# HTML Widgets
########################################################################################################################

# TextNode -------------------------------------------------------------------------------------------------------------


class TextNode(object):
    """Represents a piece of text inside the DOM.

    This is the *only* object not deriving from "Widget", as it does
    not support any of its properties.
    """

    def __init__(self, txt=None, *args, **kwargs):
        super().__init__()
        self._parent = None
        self._children = []
        self.element = domCreateTextNode(domConvertEncodedText(txt or ""))
        self._isAttached = False

    def _setText(self, txt):
        self.element.data = domConvertEncodedText(txt)

    def _getText(self):
        return self.element.data

    def __str__(self):
        return self.element.data

    def onAttach(self):
        self._isAttached = True

    def onDetach(self):
        self._isAttached = False

    def _setDisabled(self, disabled):
        return

    def _getDisabled(self):
        return False

    def children(self):
        return []


# _WidgetClassWrapper -------------------------------------------------------------------------------------------------


class _WidgetClassWrapper(list):
    def __init__(self, targetWidget):
        super().__init__()

        self.targetWidget = targetWidget

        # Initially read content of element into current wrappper
        value = targetWidget.element.getAttribute("class")
        if value:
            for c in value.split(" "):
                list.append(self, c)

    def set(self, value):
        if value is None:
            value = []
        elif isinstance(value, str):
            value = value.split(" ")
        elif not isinstance(value, list):
            raise ValueError("Value must be a str, a List or None")

        list.clear(self)
        list.extend(self, value)
        self._updateElem()

    def _updateElem(self):
        if len(self) == 0:
            self.targetWidget.element.removeAttribute("class")
        else:
            self.targetWidget.element.setAttribute("class", " ".join(self))

    def append(self, p_object):
        list.append(self, p_object)
        self._updateElem()

    def clear(self):
        list.clear(self)
        self._updateElem()

    def remove(self, value):
        try:
            list.remove(self, value)
        except:
            pass
        self._updateElem()

    def extend(self, iterable):
        list.extend(self, iterable)
        self._updateElem()

    def insert(self, index, p_object):
        list.insert(self, index, p_object)
        self._updateElem()

    def pop(self, index=None):
        list.pop(self, index)
        self._updateElem()


# _WidgetDataWrapper ---------------------------------------------------------------------------------------------------


class _WidgetDataWrapper(dict):
    def __init__(self, targetWidget):
        super().__init__()

        self.targetWidget = targetWidget
        alldata = targetWidget.element

        for data in dir(alldata.dataset):
            dict.__setitem__(self, data, getattr(alldata.dataset, data))

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.targetWidget.element.setAttribute(str("data-" + key), value)

    def update(self, E=None, **F):
        dict.update(self, E, **F)
        if E is not None and "keys" in dir(E):
            for key in E:
                self.targetWidget.element.setAttribute(
                    str("data-" + key), E["data-" + key]
                )
        elif E:
            for (key, val) in E:
                self.targetWidget.element.setAttribute(
                    str("data-" + key), "data-" + val
                )
        for key in F:
            self.targetWidget.element.setAttribute(str("data-" + key), F["data-" + key])


# _WidgetStyleWrapper --------------------------------------------------------------------------------------------------


class _WidgetStyleWrapper(dict):
    def __init__(self, targetWidget):
        super().__init__()

        self.targetWidget = targetWidget
        style = targetWidget.element.style

        for key in dir(style):
            # Convert JS-Style-Syntax to CSS Syntax (ie borderTop -> border-top)
            realKey = ""
            for currChar in key:
                if currChar.isupper():
                    realKey += "-"
                realKey += currChar.lower()
            val = style.getPropertyValue(realKey)
            if val:
                dict.__setitem__(self, realKey, val)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.targetWidget.element.style.setProperty(key, value)

    def update(self, E=None, **F):
        dict.update(self, E, **F)
        if E is not None and "keys" in dir(E):
            for key in E:
                self.targetWidget.element.style.setProperty(key, E[key])
        elif E:
            for (key, val) in E:
                self.targetWidget.element.style.setProperty(key, val)
        for key in F:
            self.targetWidget.element.style.setProperty(key, F[key])


# Widget ---------------------------------------------------------------------------------------------------------------


class Widget(object):
    _namespace = None  # Namespace
    _tagName = None  # Defines the DOM element name that is used for construction
    _leafTag = False  # Defines whether ths Widget may contain other Widgets (default) or is a leaf

    style = []  # CSS-classes to directly assign to this Widget at construction.

    def __init__(self, *args, appendTo=None, style=None, **kwargs):
        if "_wrapElem" in kwargs.keys():
            self.element = kwargs["_wrapElem"]
            del kwargs["_wrapElem"]
        else:
            assert self._tagName is not None
            self.element = domCreateElement(self._tagName, ns=self._namespace)

        self._widgetClassWrapper = None
        self._event_listeners = {}  # a map of attached event listeners, and their proxies.

        super().__init__()

        self.addClass(self.style)

        if style:
            self.addClass(style)

        self._children = []
        self._catchedEvents = {}
        self._disabledState = 0
        self._isAttached = False
        self._parent = None

        if args:
            self.appendChild(*args, **kwargs)

        if appendTo:
            appendTo.appendChild(self)

    def sinkEvent(self, *args):
        for event_attrName in args:
            event = event_attrName.lower()

            if event_attrName in self._catchedEvents or event in ["onattach", "ondetach"]:
                continue

            eventFn = getattr(self, event_attrName, None)
            assert eventFn and callable(eventFn), f"{self} must provide a {event_attrName}-function"

            self._catchedEvents[event_attrName] = eventFn

            if event.startswith("on"):
                event = event[2:]

            self.addEventListener(event, eventFn)

    def unsinkEvent(self, *args):
        for event_attrName in args:
            event = event_attrName.lower()

            if event_attrName not in self._catchedEvents:
                continue

            eventFn = self._catchedEvents[event_attrName]
            del self._catchedEvents[event_attrName]

            if event.startswith("on"):
                event = event[2:]

            self.removeEventListener(event, eventFn)

    def addEventListener(self, event, callback):
        """Adds an event listener callback to an event on a Widget.

        :param event: The event string, e.g. "click" or "mouseover"
        :param callback: The callback function to be called on the given event. \
            This callback function can either accept no parameters, \
            receive the pure Event-object from JavaScript as one parameter, \
            or receive both the pure Event-object from JavaScript and the Widget-instance \
            where the event was triggered on.
        """
        event_listener_key =  f"{event}_{hash(callback)}"
        assert event_listener_key not in self._event_listeners, f"{callback} already assigned, please remove it first"

        parameters = inspect.signature(callback).parameters
        org_callback = callback

        # Allow for callback without parameter
        if len(parameters) == 0:
            # `lambda callback: lambda _: callback()` doesn't work.
            def _wrapEventCallback(callback):
                return lambda _: callback()

            callback = _wrapEventCallback(org_callback)

        # Allow for callback with two or more parameters, to catch the event's source
        elif len(parameters) >= 2:
            # `callback = lambda callback: lambda event: callback(event, self)` doesn't work.
            def _wrapEventWidgetCallback(callback, widget):
                return lambda event: callback(event, widget)

            callback = _wrapEventWidgetCallback(org_callback, self)

        if pyodide:
            # In Pyodide, add a proxy for the callback and keep its usage
            proxy = pyodide.create_proxy(callback)
        else:
            proxy = None

        self.element.addEventListener(event, proxy or callback)

        event_listener = SimpleNamespace(
            event=event, proxy=proxy, callback=callback, org_callback=org_callback, attached=True
        )

        # print("_event_listeners add", event_listener_key)
        self._event_listeners[event_listener_key] = event_listener

    def removeEventListener(self, event, callback):
        """Removes an event listener callback from a Widget.

        The event listener must be previously added by Widget.addEventListener().

        :param event: The event string, e.g. "click" or "mouseover"
        :param callback: The callback function to be removed
        """
        event_listener_key = f"{event}_{hash(callback)}"
        assert event_listener_key in self._event_listeners, f"{callback} was not added by addEventListener previously"

        if event_listener := self._event_listeners.pop(event_listener_key, None):
            # print("_event_listeners remove", event_listener_key)
            self.element.removeEventListener(event, event_listener.proxy or event_listener.callback)
            event_listener.proxy.destroy()

    def disable(self):
        """Disables an element, in case it is not already disabled.

        On disabled elements, events are not triggered anymore.
        """
        if not self["disabled"]:
            self["disabled"] = True

    def enable(self):
        """Enables an element, in case it is not already enabled."""
        if self["disabled"]:
            self["disabled"] = False

    def _getTargetfuncName(self, key, type):
        assert type in ["get", "set"]
        return "_{}{}{}".format(type, key[0].upper(), key[1:])

    def __getitem__(self, key):
        funcName = self._getTargetfuncName(key, "get")

        if funcName in dir(self):
            return getattr(self, funcName)()

        return None

    def __setitem__(self, key, value):
        funcName = self._getTargetfuncName(key, "set")

        if funcName in dir(self):
            return getattr(self, funcName)(value)

        raise ValueError(
            "{} is no valid attribute for {}".format(key, (self._tagName or str(self)))
        )

    def __str__(self):
        return str(self.__class__.__name__)

    def __iter__(self):
        return self._children.__iter__()

    def _getData(self):
        """Custom data attributes are intended to store custom data private to the page or application, for which there are no more appropriate attributes or elements.

        :param name:
        :returns:
        """
        return _WidgetDataWrapper(self)

    def _getTranslate(self):
        """Specifies whether an elements attribute values and contents of its children are to be translated when the page is localized, or whether to leave them unchanged.

        :returns: True | False
        """
        return True if self.element.translate == "yes" else False

    def _setTranslate(self, val):
        """Specifies whether an elements attribute values and contents of its children are to be translated when the page is localized, or whether to leave them unchanged.

        :param val: True | False
        """
        self.element.translate = "yes" if val == True else "no"

    def _getTitle(self):
        """Advisory information associated with the element.

        :returns: str
        """
        return self.element.title

    def _setTitle(self, val):
        """Advisory information associated with the element.

        :param val: str
        """
        self.element.title = val

    def _getTabindex(self):
        """Specifies whether the element represents an element that is is focusable (that is, an element which is part of the sequence of focusable elements in the document), and the relative order of the element in the sequence of focusable elements in the document.

        :returns: number
        """
        return self.element.getAttribute("tabindex")

    def _setTabindex(self, val):
        """Specifies whether the element represents an element that is is focusable (that is, an element which is part of the sequence of focusable elements in the document), and the relative order of the element in the sequence of focusable elements in the document.

        :param val:  number
        """
        self.element.setAttribute("tabindex", val)

    def _getSpellcheck(self):
        """Specifies whether the element represents an element whose contents are subject to spell checking and grammar checking.

        :returns: True | False
        """
        return True if self.element.spellcheck == "true" else False

    def _setSpellcheck(self, val):
        """Specifies whether the element represents an element whose contents are subject to spell checking and grammar checking.

        :param val: True | False
        """
        self.element.spellcheck = str(val).lower()

    def _getLang(self):
        """Specifies the primary language for the contents of the element and for any of the elements attributes that contain text.

        :returns: language tag e.g. de|en|fr|es|it|ru|
        """
        return self.element.lang

    def _setLang(self, val):
        """Specifies the primary language for the contents of the element and for any of the elements attributes that contain text.

        :param val: language tag
        """
        self.element.lang = val

    def _getHidden(self):
        """Specifies that the element represents an element that is not yet, or is no longer, relevant.

        :returns: True | False
        """
        return True if self.element.hasAttribute("hidden") else False

    def _setHidden(self, val):
        """Specifies that the element represents an element that is not yet, or is no longer, relevant.

        :param val: True | False
        """
        if val:
            self.element.setAttribute("hidden", "")
        else:
            self.element.removeAttribute("hidden")

    def _getDisabled(self):
        return bool(self._disabledState)

    def _setDisabled(self, disable):
        for child in self._children:
            child._setDisabled(disable)

        if disable:
            self._disabledState += 1

            if isinstance(self, _attrDisabled) and self._disabledState == 1:
                self.element.disabled = True

        elif self._disabledState > 0:
            if isinstance(self, _attrDisabled) and self._disabledState == 1:
                self.element.disabled = False

            self._disabledState -= 1

    def _getDropzone(self):
        """Specifies what types of content can be dropped on the element, and instructs the UA about which actions to take with content when it is dropped on the element.

        :returns: "copy" | "move" | "link"
        """
        return self.element.dropzone

    def _setDropzone(self, val):
        """Specifies what types of content can be dropped on the element, and instructs the UA about which actions to take with content when it is dropped on the element.

        :param val: "copy" | "move" | "link"
        """
        self.element.dropzone = val

    def _getDraggable(self):
        """Specifies whether the element is draggable.

        :returns: True | False | "auto"
        """
        return (
            self.element.draggable
            if str(self.element.draggable) == "auto"
            else (True if str(self.element.draggable).lower() == "true" else False)
        )

    def _setDraggable(self, val):
        """Specifies whether the element is draggable.

        :param val: True | False | "auto"
        """
        self.element.draggable = str(val).lower()

    def _getDir(self):
        """Specifies the elements text directionality.

        :returns: ltr | rtl | auto
        """
        return self.element.dir

    def _setDir(self, val):
        """Specifies the elements text directionality.

        :param val: ltr | rtl | auto
        """
        self.element.dir = val

    def _getContextmenu(self):
        """The value of the id attribute on the menu with which to associate the element as a context menu.

        :returns:
        """
        return self.element.contextmenu

    def _setContextmenu(self, val):
        """The value of the id attribute on the menu with which to associate the element as a context menu.

        :param val:
        """
        self.element.contextmenu = val

    def _getContenteditable(self):
        """Specifies whether the contents of the element are editable.

        :returns: True | False
        """
        v = self.element.getAttribute("contenteditable")
        return str(v).lower() == "true"

    def _setContenteditable(self, val):
        """Specifies whether the contents of the element are editable.

        :param val: True | False
        """
        self.element.setAttribute("contenteditable", str(val).lower())

    def _getAccesskey(self):
        """A key label or list of key labels with which to associate the element; each key label represents a keyboard shortcut which UAs can use to activate the element or give focus to the element.

        :param self:
        :returns:
        """
        return self.element.accesskey

    def _setAccesskey(self, val):
        """A key label or list of key labels with which to associate the element; each key label represents a keyboard shortcut which UAs can use to activate the element or give focus to the element.

        :param self:
        :param val:
        """
        self.element.accesskey = val

    def _getId(self):
        """Specifies a unique id for an element.

        :param self:
        :returns:
        """
        return self.element.id

    def _setId(self, val):
        """Specifies a unique id for an element.

        :param self:
        :param val:
        """
        self.element.id = val

    def _getClass(self):
        """The class attribute specifies one or more classnames for an element.

        :returns:
        """
        if self._widgetClassWrapper is None:
            self._widgetClassWrapper = _WidgetClassWrapper(self)

        return self._widgetClassWrapper

    def _setClass(self, value):
        """The class attribute specifies one or more classnames for an element.

        :param self:
        :param value:
        @raise ValueError:
        """
        self._getClass().set(value)

    def _getStyle(self):
        """The style attribute specifies an inline style for an element.

        :param self:
        :returns:
        """
        return _WidgetStyleWrapper(self)

    def _getRole(self):
        """Specifies a role for an element.

        @param self:
        @return:
        """
        return self.element.getAttribute("role")

    def _setRole(self, val):
        """Specifies a role for an element.

        @param self:
        @param val:
        """
        self.element.setAttribute("role", val)

    def hide(self):
        """Hide element, if shown.

        :return:
        """
        if not self["hidden"]:
            self["hidden"] = True

    def show(self):
        """Show element, if hidden.

        :return:
        """
        if self["hidden"]:
            self["hidden"] = False

    def isHidden(self):
        """Checks if a widget is hidden.

        :return: True if hidden, False otherwise.
        """
        return self["hidden"]

    def isVisible(self):
        """Checks if a widget is visible.

        :return: True if visible, False otherwise.
        """
        return not self.isHidden()

    def onBind(self, widget, name):
        """Event function that is called on the widget when it is bound to another widget with a name.

        This is only done by the HTML parser, a manual binding by the user is not triggered.
        """
        return

    def onAttach(self):
        self._isAttached = True

        for c in self._children:
            c.onAttach()

        for event_listener in self._event_listeners.values():
            if event_listener.attached:  # only add if detached.
                continue

            if pyodide:
                assert not event_listener.proxy
                event_listener.proxy = pyodide.create_proxy(event_listener.callback)

            self.element.addEventListener(event_listener.event, event_listener.proxy or event_listener.callback)
            event_listener.attached = True  # mark as attached
            # print("_event_listeners attach", event_listener)

    def onDetach(self):
        self._isAttached = False
        for c in self._children:
            c.onDetach()

        for event_listener in self._event_listeners.values():
            if not event_listener.attached:
                continue

            self.element.removeEventListener(event_listener.event, event_listener.proxy or event_listener.callback)

            if event_listener.proxy:
                event_listener.proxy.destroy()
                event_listener.proxy = None

            event_listener.attached = False  # mark as detached
            # print("_event_listeners detach", event_listener)

    def __collectChildren(self, *args, **kwargs):
        """Internal function for collecting children from args.

        This is used by appendChild(), prependChild(), insertChild() etc.
        """
        if kwargs.get("bindTo") is None:
            kwargs["bindTo"] = self

        widgets = []
        for arg in args:
            if isinstance(arg, (str, HtmlAst)):
                widgets.extend(fromHTML(arg, **kwargs))

            elif isinstance(arg, (list, tuple)):
                for subarg in arg:
                    widgets.extend(self.__collectChildren(subarg, **kwargs))

            elif not isinstance(arg, (Widget, TextNode)):
                widgets.append(TextNode(str(arg)))

            else:
                widgets.append(arg)

        return widgets

    def insertBefore(self, insert, child, **kwargs):
        if not child:
            return self.appendChild(insert)

        assert child in self._children, "{} is not a child of {}".format(child, self)

        toInsert = self.__collectChildren(insert, **kwargs)

        for insert in toInsert:
            if insert._parent:
                insert._parent.removeChild(insert)

            self.element.insertBefore(insert.element, child.element)
            self._children.insert(self._children.index(child), insert)

            insert._parent = self
            if self._isAttached:
                insert.onAttach()

        return toInsert

    def insertAfter(self, insert, child, **kwargs):
        if not child:
            return self.appendChild(insert)

        assert child in self._children, "{} is not a child of {}".format(child, self)

        toInsert = self.__collectChildren(insert, **kwargs)

        for insert in toInsert:
            if insert._parent:
                insert._parent.removeChild(insert)

            self.element.insertBefore(insert.element, child.element.nextSibling)
            self._children.insert(self._children.index(child), insert)

            insert._parent = self
            if self._isAttached:
                insert.onAttach()

        return toInsert

    def prependChild(self, *args, **kwargs):
        if kwargs.get("replace", False):
            self.removeAllChildren()
            del kwargs["replace"]

        toPrepend = self.__collectChildren(*args, **kwargs)

        for child in toPrepend:
            if child._parent:
                child._parent._children.remove(child)
                child._parent = None

            if not self._children:
                self.appendChild(child)
            else:
                self.insertBefore(child, self.children(0))

        return toPrepend

    def appendChild(self, *args, **kwargs):
        if kwargs.get("replace", False):
            logging.warning(
                "replace=True is deprecated. Use Widget.replaceChild() for this!"
            )
            self.removeAllChildren()
            del kwargs["replace"]

        toAppend = self.__collectChildren(*args, **kwargs)

        for child in toAppend:
            if isinstance(child, Template):
                return self.appendChild(child._children)

            if child._parent:
                child._parent._children.remove(child)

            self._children.append(child)
            self.element.appendChild(child.element)
            child._parent = self

            if self._isAttached:
                child.onAttach()

        return toAppend

    def replaceChild(self, *args, **kwargs):
        self.removeAllChildren()
        self.appendChild(*args, **kwargs)

    def removeChild(self, child):
        assert child in self._children, "{} is not a child of {}".format(child, self)

        if child._isAttached:
            child.onDetach()

        self.element.removeChild(child.element)
        self._children.remove(child)
        child._parent = None

    def removeAllChildren(self):
        """Removes all child widgets of the current widget."""
        for child in self._children[:]:
            self.removeChild(child)

    def isParentOf(self, widget):
        """Checks if an object is the parent of widget.

        :type widget: Widget
        :param widget: The widget to check for.
        :return: True, if widget is a child of the object, else False.
        """
        # You cannot be your own child!
        if self == widget:
            return False

        for child in self._children:
            if child == widget:
                return True

            if child.isParentOf(widget):
                return True

        return False

    def isChildOf(self, widget):
        """Checks if an object is the child of widget.

        :type widget: Widget
        :param widget: The widget to check for.
        :return: True, if object is a child of widget, else False.
        """
        # You cannot be your own parent!
        if self == widget:
            return False

        parent = self.parent()
        while parent:
            if parent == widget:
                return True

            parent = widget.parent()

        return False

    def hasClass(self, className):
        """Determine whether the current widget is assigned the given class.

        :param className: The class name to search for.
        :type className: str
        """
        if isinstance(className, str) or isinstance(className, unicode):
            return className in self["class"]
        else:
            raise TypeError()

    def addClass(self, *args):
        """Adds a class or a list of classes to the current widget.

        If the widget already has the class, it is ignored.

        :param args: A list of class names. This can also be a list.
        :type args: list of str | list of list of str
        """
        for item in args:
            if isinstance(item, list):
                self.addClass(*item)

            elif isinstance(item, str):
                for sitem in item.split(" "):
                    if not self.hasClass(sitem):
                        self["class"].append(sitem)
            else:
                raise TypeError()

    def removeClass(self, *args):
        """Removes a class or a list of classes from the current widget.

        :param args: A list of class names. This can also be a list.
        :type args: list of str | list of list of str
        """
        for item in args:
            if isinstance(item, list):
                self.removeClass(item)

            elif isinstance(item, str):
                for sitem in item.split(" "):
                    if self.hasClass(sitem):
                        self["class"].remove(sitem)
            else:
                raise TypeError()

    def toggleClass(self, on, off=None):
        """Toggles the class ``on``.

        If the widget contains a class ``on``, it is toggled by ``off``.
        ``off`` can either be a class name that is substituted, or nothing.

        :param on: Classname to test for. If ``on`` does not exist, but ``off``, ``off`` is replaced by ``on``.
        :type on: str

        :param off: Classname to replace if ``on`` existed.
        :type off: str

        :return: Returns True, if ``on`` was switched, else False.
        :rtype: bool
        """
        if self.hasClass(on):
            self.removeClass(on)

            if off and not self.hasClass(off):
                self.addClass(off)

            return False

        if off and self.hasClass(off):
            self.removeClass(off)

        self.addClass(on)
        return True

    def onBlur(self, event):
        pass

    def onChange(self, event):
        pass

    def onContextMenu(self, event):
        pass

    def onFocus(self, event):
        pass

    def onFocusIn(self, event):
        pass

    def onFocusOut(self, event):
        pass

    def onFormChange(self, event):
        pass

    def onFormInput(self, event):
        pass

    def onInput(self, event):
        pass

    def onInvalid(self, event):
        pass

    def onReset(self, event):
        pass

    def onSelect(self, event):
        pass

    def onSubmit(self, event):
        pass

    def onKeyDown(self, event):
        pass

    def onKeyPress(self, event):
        pass

    def onKeyUp(self, event):
        pass

    def onClick(self, event, wdg=None):
        pass

    def onDblClick(self, event):
        pass

    def onDrag(self, event):
        pass

    def onDragEnd(self, event):
        pass

    def onDragEnter(self, event):
        pass

    def onDragLeave(self, event):
        pass

    def onDragOver(self, event):
        pass

    def onDragStart(self, event):
        pass

    def onDrop(self, event):
        pass

    def onMouseDown(self, event):
        pass

    def onMouseMove(self, event):
        pass

    def onMouseOut(self, event):
        pass

    def onMouseOver(self, event):
        pass

    def onMouseUp(self, event):
        pass

    def onMouseWheel(self, event):
        pass

    def onScroll(self, event):
        pass

    def onTouchStart(self, event):
        pass

    def onTouchEnd(self, event):
        pass

    def onTouchMove(self, event):
        pass

    def onTouchCancel(self, event):
        pass

    def focus(self):
        self.element.focus()

    def blur(self):
        self.element.blur()

    def parent(self):
        return self._parent

    def children(self, n=None):
        """Access children of widget.

        If ``n`` is ommitted, it returns a list of all child-widgets;
        Else, it returns the N'th child, or None if its out of bounds.

        :param n: Optional offset of child widget to return.
        :type n: int

        :return: Returns all children or only the requested one.
        :rtype: list | Widget | None
        """
        if n is None:
            return self._children[:]

        try:
            return self._children[n]
        except IndexError:
            return None

    def sortChildren(self, key, reversed=False):
        """Sorts our direct children. They are rearranged on DOM level.

        Key must be a function accepting one widget as parameter and must return
        the key used to sort these widgets.
        """
        self._children.sort(key=key)
        tmpl = self._children[:]

        if not reversed:
            tmpl.reverse()

        for c in tmpl:
            self.element.removeChild(c.element)
            self.element.insertBefore(c.element, self.element.children.item(0))

    def fromHTML(
        self, html, appendTo=None, bindTo=None, replace=False, vars=None, **kwargs
    ):
        """Parses html and constructs its elements as part of self.

        :param html: HTML code.
        :param appendTo: The entity where the HTML code is constructed below. This defaults to self in usual case.
        :param bindTo: The entity where the named objects are bound to. This defaults to self in usual case.
        :param replace: Clear entire content of appendTo before appending.
        :param vars: Deprecated; Same as kwargs.
        :param **kwargs: Additional variables provided as a dict for {{placeholders}} inside the HTML

        :return:
        """
        if appendTo is None:
            appendTo = self

        if bindTo is None:
            bindTo = self

        if replace:
            appendTo.removeAllChildren()

        # use of vars is deprecated!
        if isinstance(vars, dict):
            kwargs.update(vars)

        return fromHTML(html, appendTo=appendTo, bindTo=bindTo, **kwargs)


########################################################################################################################
# Attribute Collectors
########################################################################################################################

# _attrLabel ---------------------------------------------------------------------------------------------------------------


class _attrLabel(object):
    def _getLabel(self):
        return self.element.getAttribute("label")

    def _setLabel(self, val):
        self.element.setAttribute("label", val)


# _attrCharset --------------------------------------------------------------------------------------------------------------


class _attrCharset(object):
    def _getCharset(self):
        return self.element._attrCharset

    def _setCharset(self, val):
        self.element._attrCharset = val


# _attrCite -----------------------------------------------------------------------------------------------------------------


class _attrCite(object):
    def _getCite(self):
        return self.element._attrCite

    def _setCite(self, val):
        self.element._attrCite = val


class _attrDatetime(object):
    def _getDatetime(self):
        return self.element.datetime

    def _setDatetime(self, val):
        self.element.datetime = val


# Form -----------------------------------------------------------------------------------------------------------------


class _attrForm(object):
    def _getForm(self):
        return self.element.form

    def _setForm(self, val):
        self.element.form = val


class _attrAlt(object):
    def _getAlt(self):
        return self.element.alt

    def _setAlt(self, val):
        self.element.alt = val


class _attrAutofocus(object):
    def _getAutofocus(self):
        return True if self.element.hasAttribute("autofocus") else False

    def _setAutofocus(self, val):
        if val:
            self.element.setAttribute("autofocus", "")
        else:
            self.element.removeAttribute("autofocus")


class _attrDisabled(object):
    pass


class _attrChecked(object):
    def _getChecked(self):
        return self.element.checked

    def _setChecked(self, val):
        self.element.checked = val


class _attrIndeterminate(object):
    def _getIndeterminate(self):
        return self.element.indeterminate

    def _setIndeterminate(self, val):
        self.element.indeterminate = val


class _attrName(object):
    def _getName(self):
        return self.element.getAttribute("name")

    def _setName(self, val):
        self.element.setAttribute("name", val)


class _attrValue(object):
    def _getValue(self):
        return self.element.value

    def _setValue(self, val):
        self.element.value = val


class _attrAutocomplete(object):
    def _getAutocomplete(self):
        return True if self.element.autocomplete == "on" else False

    def _setAutocomplete(self, val):
        self.element.autocomplete = "on" if val == True else "off"


class _attrRequired(object):
    def _getRequired(self):
        return True if self.element.hasAttribute("required") else False

    def _setRequired(self, val):
        if val:
            self.element.setAttribute("required", "")
        else:
            self.element.removeAttribute("required")


class _attrMultiple(object):
    def _getMultiple(self):
        return True if self.element.hasAttribute("multiple") else False

    def _setMultiple(self, val):
        if val:
            self.element.setAttribute("multiple", "")
        else:
            self.element.removeAttribute("multiple")


class _attrSize(object):
    def _getSize(self):
        return self.element.size

    def _setSize(self, val):
        self.element.size = val


class _attrFor(object):
    def _getFor(self):
        return self.element.getAttribute("for")

    def _setFor(self, val):
        self.element.setAttribute("for", val)


class _attrInputs(_attrRequired):
    def _getMaxlength(self):
        return self.element.maxLength

    def _setMaxlength(self, val):
        self.element.maxLength = val

    def _getPlaceholder(self):
        return self.element.placeholder

    def _setPlaceholder(self, val):
        self.element.placeholder = val

    def _getReadonly(self):
        return True if self.element.hasAttribute("readonly") else False

    def _setReadonly(self, val):
        if val:
            self.element.setAttribute("readonly", "")
        else:
            self.element.removeAttribute("readonly")


class _attrFormhead(object):
    def _getFormaction(self):
        return self.element.formaction

    def _setFormaction(self, val):
        self.element.formaction = val

    def _getFormenctype(self):
        return self.element.formenctype

    def _setFormenctype(self, val):
        self.element.formenctype = val

    def _getFormmethod(self):
        return self.element.formmethod

    def _setFormmethod(self, val):
        self.element.formmethod = val

    def _getFormtarget(self):
        return self.element.formtarget

    def _setFormtarget(self, val):
        self.element.formtarget = val

    def _getFormnovalidate(self):
        return True if self.element.hasAttribute("formnovalidate") else False

    def _setFormnovalidate(self, val):
        if val:
            self.element.setAttribute("formnovalidate", "")
        else:
            self.element.removeAttribute("formnovalidate")


# _attrHref -----------------------------------------------------------------------------------------------------------------


class _attrHref(object):
    def _getHref(self):
        """Url of a Page.

        :param self:
        """
        return self.element.href

    def _setHref(self, val):
        """Url of a Page.

        :param val: URL
        """
        self.element.href = val

    def _getHreflang(self):
        return self.element.hreflang

    def _setHreflang(self, val):
        self.element.hreflang = val


class _attrTarget(object):
    def _getTarget(self):
        return self.element.target

    def _setTarget(self, val):
        self.element.target = val


# _attrMedia ----------------------------------------------------------------------------------------------------------------


class _attrType(object):
    def _getType(self):
        return self.element.type

    def _setType(self, val):
        self.element.type = val


class _attrMedia(_attrType):
    def _getMedia(self):
        return self.element.media

    def _setMedia(self, val):
        self.element.media = val


class _attrDimensions(object):
    def _getWidth(self):
        return self.element.width

    def _setWidth(self, val):
        self.element.width = val

    def _getHeight(self):
        return self.element.height

    def _setHeight(self, val):
        self.element.height = val


class _attrUsemap(object):
    def _getUsemap(self):
        return self.element.usemap

    def _setUsemap(self, val):
        self.element.usemap = val


class _attrMultimedia(object):
    def _getAutoplay(self):
        return True if self.element.hasAttribute("autoplay") else False

    def _setAutoplay(self, val):
        if val:
            self.element.setAttribute("autoplay", "")
        else:
            self.element.removeAttribute("autoplay")

    def _getPlaysinline(self):
        return True if self.element.hasAttribute("playsinline") else False

    def _setPlaysinline(self, val):
        if val:
            self.element.setAttribute("playsinline", "")
        else:
            self.element.removeAttribute("playsinline")

    def _getControls(self):
        return True if self.element.hasAttribute("controls") else False

    def _setControls(self, val):
        if val:
            self.element.setAttribute("controls", "")
        else:
            self.element.removeAttribute("controls")

    def _getLoop(self):
        return True if self.element.hasAttribute("loop") else False

    def _setLoop(self, val):
        if val:
            self.element.setAttribute("loop", "")
        else:
            self.element.removeAttribute("loop")

    def _getMuted(self):
        return True if self.element.hasAttribute("muted") else False

    def _setMuted(self, val):
        if val:
            self.element.setAttribute("muted", "")
        else:
            self.element.removeAttribute("muted")

    def _getPreload(self):
        return self.element.preload

    def _setPreload(self, val):
        self.element.preload = val


# _attrRel ------------------------------------------------------------------------------------------------------------------


class _attrRel(object):
    def _getRel(self):
        return self.element.rel

    def _setRel(self, val):
        self.element.rel = val


# _attrSrc ------------------------------------------------------------------------------------------------------------------


class _attrSrc(object):
    def _getSrc(self):
        return self.element.src

    def _setSrc(self, val):
        self.element.src = val


########################################################################################################################
# HTML Elements
########################################################################################################################

# A --------------------------------------------------------------------------------------------------------------------


class A(Widget, _attrHref, _attrTarget, _attrMedia, _attrRel, _attrName):
    _tagName = "a"

    def _getDownload(self):
        """The download attribute specifies the path to a download.

        :returns: filename
        """
        return self.element.download

    def _setDownload(self, val):
        """The download attribute specifies the path to a download.

        :param val: filename
        """
        self.element.download = val


# Area -----------------------------------------------------------------------------------------------------------------


class Area(A, _attrAlt):
    _tagName = "area"
    _leafTag = True

    def _getCoords(self):
        return self.element.coords

    def _setCoords(self, val):
        self.element.coords = val

    def _getShape(self):
        return self.element.shape

    def _setShape(self, val):
        self.element.shape = val


# Audio ----------------------------------------------------------------------------------------------------------------


class Audio(Widget, _attrSrc, _attrMultimedia):
    _tagName = "audio"


class Bdo(Widget):
    _tagName = "bdo"


# Blockquote -----------------------------------------------------------------------------------------------------------


class Blockquote(Widget):
    _tagName = "blockquote"

    def _getBlockquote(self):
        return self.element.blockquote

    def _setBlockquote(self, val):
        self.element.blockquote = val


# Body -----------------------------------------------------------------------------------------------------------------


class BodyCls(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(_wrapElem=domGetElementsByTagName("body")[0], *args, **kwargs)
        self._isAttached = True


_body = None


def Body():
    global _body

    if _body is None:
        _body = BodyCls()

    return _body


# Canvas ---------------------------------------------------------------------------------------------------------------


class Canvas(Widget, _attrDimensions):
    _tagName = "canvas"


# Command --------------------------------------------------------------------------------------------------------------


class Command(Widget, _attrLabel, _attrType, _attrDisabled, _attrChecked):
    _tagName = "command"

    def _getIcon(self):
        return self.element.icon

    def _setIcon(self, val):
        self.element.icon = val

    def _getRadiogroup(self):
        return self.element.radiogroup

    def _setRadiogroup(self, val):
        self.element.radiogroup = val


# _Del -----------------------------------------------------------------------------------------------------------------


class _Del(Widget, _attrCite, _attrDatetime):
    _tagName = "_del"


# Dialog --------------------------------------------------------------------------------------------------------------


class Dialog(Widget):
    _tagName = "dialog"

    def _getOpen(self):
        return True if self.element.hasAttribute("open") else False

    def _setOpen(self, val):
        if val:
            self.element.setAttribute("open", "")
        else:
            self.element.removeAttribute("open")


# Elements -------------------------------------------------------------------------------------------------------------


class Abbr(Widget):
    _tagName = "abbr"


class Address(Widget):
    _tagName = "address"


class Article(Widget):
    _tagName = "article"


class Aside(Widget):
    _tagName = "aside"


class B(Widget):
    _tagName = "b"


class Bdi(Widget):
    _tagName = "bdi"


class Br(Widget):
    _tagName = "br"
    _leafTag = True


class Caption(Widget):
    _tagName = "caption"


class Cite(Widget):
    _tagName = "cite"


class Code(Widget):
    _tagName = "code"


class Datalist(Widget):
    _tagName = "datalist"


class Dfn(Widget):
    _tagName = "dfn"


class Div(Widget):
    _tagName = "div"


class Em(Widget):
    _tagName = "em"


class Embed(Widget, _attrSrc, _attrType, _attrDimensions):
    _tagName = "embed"
    _leafTag = True


class Figcaption(Widget):
    _tagName = "figcaption"


class Figure(Widget):
    _tagName = "figure"


class Footer(Widget):
    _tagName = "footer"


class Header(Widget):
    _tagName = "header"


class H1(Widget):
    _tagName = "h1"


class H2(Widget):
    _tagName = "h2"


class H3(Widget):
    _tagName = "h3"


class H4(Widget):
    _tagName = "h4"


class H5(Widget):
    _tagName = "h5"


class H6(Widget):
    _tagName = "h6"


class Hr(Widget):
    _tagName = "hr"
    _leafTag = True


class I(Widget):
    _tagName = "i"


class Kdb(Widget):
    _tagName = "kdb"


class Legend(Widget):
    _tagName = "legend"


class Mark(Widget):
    _tagName = "mark"


class Noscript(Widget):
    _tagName = "noscript"


class P(Widget):
    _tagName = "p"


class Rq(Widget):
    _tagName = "rq"


class Rt(Widget):
    _tagName = "rt"


class Ruby(Widget):
    _tagName = "ruby"


class S(Widget):
    _tagName = "s"


class Samp(Widget):
    _tagName = "samp"


class Section(Widget):
    _tagName = "section"


class Small(Widget):
    _tagName = "small"


class Strong(Widget):
    _tagName = "strong"


class Sub(Widget):
    _tagName = "sub"


class Summery(Widget):
    _tagName = "summery"


class Sup(Widget):
    _tagName = "sup"


class U(Widget):
    _tagName = "u"


class Var(Widget):
    _tagName = "var"


class Wbr(Widget):
    _tagName = "wbr"


# Form -----------------------------------------------------------------------------------------------------------------


class Button(
    Widget,
    _attrDisabled,
    _attrType,
    _attrForm,
    _attrAutofocus,
    _attrName,
    _attrValue,
    _attrFormhead,
):
    _tagName = "button"


class Fieldset(Widget, _attrDisabled, _attrForm, _attrName):
    _tagName = "fieldset"


class Form(Widget, _attrDisabled, _attrName, _attrTarget, _attrAutocomplete):
    _tagName = "form"

    def _getNovalidate(self):
        return True if self.element.hasAttribute("novalidate") else False

    def _setNovalidate(self, val):
        if val:
            self.element.setAttribute("novalidate", "")
        else:
            self.element.removeAttribute("novalidate")

    def _getAction(self):
        return self.element.action

    def _setAction(self, val):
        self.element.action = val

    def _getMethod(self):
        return self.element.method

    def _setMethod(self, val):
        self.element.method = val

    def _getEnctype(self):
        return self.element.enctype

    def _setEnctype(self, val):
        self.element.enctype = val

    def _getAccept_attrCharset(self):
        return getattr(self.element, "accept-charset")

    def _setAccept_attrCharset(self, val):
        self.element.setAttribute("accept-charset", val)


class Input(
    Widget,
    _attrDisabled,
    _attrType,
    _attrForm,
    _attrAlt,
    _attrAutofocus,
    _attrChecked,
    _attrIndeterminate,
    _attrName,
    _attrDimensions,
    _attrValue,
    _attrFormhead,
    _attrAutocomplete,
    _attrInputs,
    _attrMultiple,
    _attrSize,
    _attrSrc,
):
    _tagName = "input"
    _leafTag = True

    def _getAccept(self):
        return self.element.accept

    def _setAccept(self, val):
        self.element.accept = val

    def _getList(self):
        return self.element.list

    def _setList(self, val):
        self.element.list = val

    def _getMax(self):
        return self.element.max

    def _setMax(self, val):
        self.element.max = val

    def _getMin(self):
        return self.element.min

    def _setMin(self, val):
        self.element.min = val

    def _getPattern(self):
        return self.element.pattern

    def _setPattern(self, val):
        self.element.pattern = val

    def _getStep(self):
        return self.element.step

    def _setStep(self, val):
        self.element.step = val


class Label(Widget, _attrForm, _attrFor):
    _tagName = "label"
    autoIdCounter = 0

    def __init__(self, *args, forElem=None, **kwargs):
        super().__init__(*args, **kwargs)

        if forElem:
            if not forElem["id"]:
                idx = Label.autoIdCounter
                Label.autoIdCounter += 1
                forElem["id"] = "label-autoid-for-{}".format(idx)

            self["for"] = forElem["id"]


class Optgroup(Widget, _attrDisabled, _attrLabel):
    _tagName = "optgroup"


class Option(Widget, _attrDisabled, _attrLabel, _attrValue):
    _tagName = "option"

    def _getSelected(self):
        return True if self.element.selected else False

    def _setSelected(self, val):
        if val:
            self.element.selected = True
        else:
            self.element.selected = False


class Output(Widget, _attrForm, _attrName, _attrFor):
    _tagName = "output"


class Select(
    Widget,
    _attrDisabled,
    _attrForm,
    _attrAutofocus,
    _attrName,
    _attrRequired,
    _attrMultiple,
    _attrSize,
):
    _tagName = "select"

    def _getSelectedIndex(self):
        return self.element.selectedIndex

    def _getOptions(self):
        return self.element.options


class Textarea(
    Widget, _attrDisabled, _attrForm, _attrAutofocus, _attrName, _attrInputs, _attrValue
):
    _tagName = "textarea"

    def _getCols(self):
        return self.element.cols

    def _setCols(self, val):
        self.element.cols = val

    def _getRows(self):
        return self.element.rows

    def _setRows(self, val):
        self.element.rows = val

    def _getWrap(self):
        return self.element.wrap

    def _setWrap(self, val):
        self.element.wrap = val


# Head -----------------------------------------------------------------------------------------------------------------


class HeadCls(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(_wrapElem=domGetElementsByTagName("head")[0], *args, **kwargs)
        self._isAttached = True


_head = None


def Head():
    global _head
    if _head is None:
        _head = HeadCls()
    return _head


# Iframe ---------------------------------------------------------------------------------------------------------------


class Iframe(Widget, _attrSrc, _attrName, _attrDimensions):
    _tagName = "iframe"

    def _getSandbox(self):
        return self.element.sandbox

    def _setSandbox(self, val):
        self.element.sandbox = val

    def _getSrcdoc(self):
        return self.element.src

    def _setSrcdoc(self, val):
        self.element.src = val

    def _getSeamless(self):
        return True if self.element.hasAttribute("seamless") else False

    def _setSeamless(self, val):
        if val:
            self.element.setAttribute("seamless", "")
        else:
            self.element.removeAttribute("seamless")


# Img ------------------------------------------------------------------------------------------------------------------


class Img(Widget, _attrSrc, _attrDimensions, _attrUsemap, _attrAlt):
    _tagName = "img"
    _leafTag = True

    def __init__(self, src=None, *args, **kwargs):
        super().__init__()
        if src:
            self["src"] = src

    def _getCrossorigin(self):
        return self.element.crossorigin

    def _setCrossorigin(self, val):
        self.element.crossorigin = val

    def _getIsmap(self):
        return self.element.ismap

    def _setIsmap(self, val):
        self.element.ismap = val


# Ins ------------------------------------------------------------------------------------------------------------------


class Ins(Widget, _attrCite, _attrDatetime):
    _tagName = "ins"


# Keygen ---------------------------------------------------------------------------------------------------------------


class Keygen(Form, _attrAutofocus, _attrDisabled):
    _tagName = "keygen"

    def _getChallenge(self):
        return True if self.element.hasAttribute("challenge") else False

    def _setChallenge(self, val):
        if val:
            self.element.setAttribute("challenge", "")
        else:
            self.element.removeAttribute("challenge")

    def _getKeytype(self):
        return self.element.keytype

    def _setKeytype(self, val):
        self.element.keytype = val


# Link -----------------------------------------------------------------------------------------------------------------


class Link(Widget, _attrHref, _attrMedia, _attrRel):
    _tagName = "link"
    _leafTag = True

    def _getSizes(self):
        return self.element.sizes

    def _setSizes(self, val):
        self.element.sizes = val


# List -----------------------------------------------------------------------------------------------------------------


class Ul(Widget):
    _tagName = "ul"


class Ol(Widget):
    _tagName = "ol"


class Li(Widget):
    _tagName = "li"


class Dl(Widget):
    _tagName = "dl"


class Dt(Widget):
    _tagName = "dt"


class Dd(Widget):
    _tagName = "dd"


# Map ------------------------------------------------------------------------------------------------------------------


class Map(Label, _attrType):
    _tagName = "map"


# Menu -----------------------------------------------------------------------------------------------------------------


class Menu(Widget):
    _tagName = "menu"


# Meta -----------------------------------------------------------------------------------------------------------------


class Meta(Widget, _attrName, _attrCharset):
    _tagName = "meta"
    _leafTag = True

    def _getContent(self):
        return self.element.content

    def _setContent(self, val):
        self.element.content = val


# Meter ----------------------------------------------------------------------------------------------------------------


class Meter(Form, _attrValue):
    _tagName = "meter"

    def _getHigh(self):
        return self.element.high

    def _setHigh(self, val):
        self.element.high = val

    def _getLow(self):
        return self.element.low

    def _setLow(self, val):
        self.element.low = val

    def _getMax(self):
        return self.element.max

    def _setMax(self, val):
        self.element.max = val

    def _getMin(self):
        return self.element.min

    def _setMin(self, val):
        self.element.min = val

    def _getOptimum(self):
        return self.element.optimum

    def _setOptimum(self, val):
        self.element.optimum = val


# Nav ------------------------------------------------------------------------------------------------------------------


class Nav(Widget):
    _tagName = "nav"


# Object -----------------------------------------------------------------------------------------------------------------


class Object(Form, _attrType, _attrName, _attrDimensions, _attrUsemap):
    _tagName = "object"


# Param -----------------------------------------------------------------------------------------------------------------


class Param(Widget, _attrName, _attrValue):
    _tagName = "param"
    _leafTag = True


# Progress -------------------------------------------------------------------------------------------------------------


class Progress(Widget, _attrValue):
    _tagName = "progress"

    def _getMax(self):
        return self.element.max

    def _setMax(self, val):
        self.element.max = val


# Q --------------------------------------------------------------------------------------------------------------------


class Q(Widget, _attrCite):
    _tagName = "q"


# Script ----------------------------------------------------------------------------------------------------------------


class Script(Widget, _attrSrc, _attrCharset):
    _tagName = "script"

    def _getAsync(self):
        return True if self.element.hasAttribute("async") else False

    def _setAsync(self, val):
        if val:
            self.element.setAttribute("async", "")
        else:
            self.element.removeAttribute("async")

    def _getDefer(self):
        return True if self.element.hasAttribute("defer") else False

    def _setDefer(self, val):
        if val:
            self.element.setAttribute("defer", "")
        else:
            self.element.removeAttribute("defer")


# Source ---------------------------------------------------------------------------------------------------------------


class Source(Widget, _attrMedia, _attrSrc):
    _tagName = "source"
    _leafTag = True


# Span -----------------------------------------------------------------------------------------------------------------


class Span(Widget):
    _tagName = "span"


# Details --------------------------------------------------------------------------------------------------------------


class Details(Widget):
    _tagName = "details"

    def _getOpen(self):
        return True if self.element.hasAttribute("open") else False

    def _setOpen(self, val):
        if val:
            self.element.setAttribute("open", "")
        else:
            self.element.removeAttribute("open")


# Summary --------------------------------------------------------------------------------------------------------------


class Summary(Widget):
    _tagName = "summary"


# Style ----------------------------------------------------------------------------------------------------------------


class Style(Widget, _attrMedia):
    _tagName = "style"

    def _getScoped(self):
        return True if self.element.hasAttribute("scoped") else False

    def _setScoped(self, val):
        if val:
            self.element.setAttribute("scoped", "")
        else:
            self.element.removeAttribute("scoped")


# Table ----------------------------------------------------------------------------------------------------------------


class Tr(Widget):
    _tagName = "tr"

    def _getRowspan(self):
        span = self.element.getAttribute("rowspan")
        return span if span else 1

    def _setRowspan(self, span):
        assert span >= 1, "span may not be negative"
        self.element.setAttribute("rowspan", span)
        return self


class Td(Widget):
    _tagName = "td"

    def _getColspan(self):
        span = self.element.getAttribute("colspan")
        return span if span else 1

    def _setColspan(self, span):
        assert span >= 1, "span may not be negative"
        self.element.setAttribute("colspan", span)
        return self

    def _getRowspan(self):
        span = self.element.getAttribute("rowspan")
        return span if span else 1

    def _setRowspan(self, span):
        assert span >= 1, "span may not be negative"
        self.element.setAttribute("rowspan", span)
        return self


class Th(Td):
    _tagName = "th"


class Thead(Widget):
    _tagName = "thead"


class Tbody(Widget):
    _tagName = "tbody"


class ColWrapper(object):
    def __init__(self, parentElem, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parentElem = parentElem

    def __getitem__(self, item):
        assert isinstance(item, int), "Invalid col-number. Expected int, got {}".format(
            str(type(item))
        )
        if item < 0 or item > len(self.parentElem._children):
            return None

        return self.parentElem._children[item]

    def __setitem__(self, key, value):
        col = self[key]
        assert col is not None, "Cannot assign widget to invalid column"

        col.removeAllChildren()

        if isinstance(value, list) or isinstance(value, tuple):
            for el in value:
                if isinstance(el, Widget) or isinstance(el, TextNode):
                    col.appendChild(value)

        elif isinstance(value, Widget) or isinstance(value, TextNode):
            col.appendChild(value)


class RowWrapper(object):
    def __init__(self, parentElem, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parentElem = parentElem

    def __getitem__(self, item):
        assert isinstance(item, int), "Invalid row-number. Expected int, got {}".format(
            str(type(item))
        )
        if item < 0 or item > len(self.parentElem._children):
            return None

        return ColWrapper(self.parentElem._children[item])


class Table(Widget):
    _tagName = "table"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.head = Thead()
        self.body = Tbody()
        self.appendChild(self.head)
        self.appendChild(self.body)

    def prepareRow(self, row):
        assert row >= 0, "Cannot create rows with negative index"

        for child in self.body._children:
            row -= child["rowspan"]
            if row < 0:
                return

        while row >= 0:
            self.body.appendChild(Tr())
            row -= 1

    def prepareCol(self, row, col):
        assert col >= 0, "Cannot create cols with negative index"
        self.prepareRow(row)

        for rowChild in self.body._children:
            row -= rowChild["rowspan"]

            if row < 0:
                for colChild in rowChild._children:
                    col -= colChild["colspan"]
                    if col < 0:
                        return

                while col >= 0:
                    rowChild.appendChild(Td())
                    col -= 1

                return

    def prepareGrid(self, rows, cols):
        for row in range(self.getRowCount(), self.getRowCount() + rows):
            self.prepareCol(row, cols)

    def clear(self):
        for row in self.body._children[:]:

            for col in row._children[:]:
                row.removeChild(col)

            self.body.removeChild(row)

    def _getCell(self):
        return RowWrapper(self.body)

    def getRowCount(self):
        cnt = 0

        for tr in self.body._children:
            cnt += tr["rowspan"]

        return cnt


# Time -----------------------------------------------------------------------------------------------------------------


class Time(Widget, _attrDatetime):
    _tagName = "time"


# Track ----------------------------------------------------------------------------------------------------------------


class Track(Label, _attrSrc):
    _tagName = "track"
    _leafTag = True

    def _getKind(self):
        return self.element.kind

    def _setKind(self, val):
        self.element.kind = val

    def _getSrclang(self):
        return self.element.srclang

    def _setSrclang(self, val):
        self.element.srclang = val

    def _getDefault(self):
        return True if self.element.hasAttribute("default") else False

    def _setDefault(self, val):
        if val:
            self.element.setAttribute("default", "")
        else:
            self.element.removeAttribute("default")


# Video ----------------------------------------------------------------------------------------------------------------


class Video(Widget, _attrSrc, _attrDimensions, _attrMultimedia):
    _tagName = "video"

    def _getPoster(self):
        return self.element.poster

    def _setPoster(self, val):
        self.element.poster = val


# Template -------------------------------------------------------------------------------------------------------------


class Template(Widget):
    _tagName = "template"


########################################################################################################################
# Utilities
########################################################################################################################


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
    val = (
        val.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )

    if maxLength > 0:
        return val[0:maxLength]

    return val


def doesEventHitWidgetOrParents(event, widget):
    """Test if event 'event' hits widget 'widget' (or *any* of its parents)."""
    while widget:
        if event.target == widget.element:
            return True

        widget = widget.parent()

    return False


def doesEventHitWidgetOrChildren(event, widget):
    """Test if event 'event' hits widget 'widget' (or *any* of its children)."""
    if event.target == widget.element:
        return True

    for child in widget._children:
        if doesEventHitWidgetOrChildren(event, child):
            return True

    return False


def textToHtml(node, text):
    """Generates html nodes from text by splitting text into content and into line breaks html5.Br.

    :param node: The node where the nodes are appended to.
    :param text: The text to be inserted.
    """
    for (i, part) in enumerate(text.split("\n")):
        if i > 0:
            node.appendChild(Br())

        node.appendChild(TextNode(part))


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


########################################################################################################################
# Keycodes
########################################################################################################################


def getKey(event):
    """Returns the Key Identifier of the given event.

    Available Codes: https://www.w3.org/TR/2006/WD-DOM-Level-3-Events-20060413/keyset.html#KeySet-Set
    """
    if hasattr(event, "key"):
        return event.key

    elif hasattr(event, "keyIdentifier"):
        if event.keyIdentifier in ["Esc", "U+001B"]:
            return "Escape"
        else:
            return event.keyIdentifier

    return None


def isArrowLeft(event):
    return getKey(event) in ["ArrowLeft", "Left"]


def isArrowUp(event):
    return getKey(event) in ["ArrowUp", "Up"]


def isArrowRight(event):
    return getKey(event) in ["ArrowRight", "Right"]


def isArrowDown(event):
    return getKey(event) in ["ArrowDown", "Down"]


def isEscape(event):
    return getKey(event) == "Escape"


def isReturn(event):
    return getKey(event) == "Enter"


def isControl(event):  # The Control (Ctrl) key.
    return getKey(event) == "Control"


def isShift(event):
    return getKey(event) == "Shift"

def isMeta(event):
    return getKey(event) == "Meta"

########################################################################################################################
# HTML parser
########################################################################################################################

# Global variables required by HTML parser & renderer
__tags = None
__reVarReplacer = re.compile("{{(([^}]|}[^}])*)}}")


def registerTag(tagName, widgetClass, override=True):
    assert issubclass(widgetClass, Widget), "widgetClass must be a sub-class of Widget!"
    global __tags

    if __tags is None:
        _buildTags()

    if not override and tagName.lower() in __tags:
        return

    attr = []

    for fname in dir(widgetClass):
        if fname.startswith("_set"):
            attr.append(fname[4:].lower())

    __tags[tagName.lower()] = (widgetClass, attr)


def tag(arg):
    """Decorator to register a sub-class of html5.Widget either under its class-name or an associated tag-name.

    Examples
    --------
    ```python
    # register class Foo as <foo>-Tag
    @html5.tag
    class Foo(html5.Div):
        pass

    # register class Bar as <baz>-Tag
    @html5.tag("baz")
    class Bar(html5.Div):
        pass
    ```

    """
    if isinstance(arg, str):

        def wrapper(cls):
            # print("%r registered as <%s>" % (cls, arg))
            registerTag(arg, cls)
            return cls

        return wrapper

    else:
        cls = arg
        assert issubclass(cls, Widget), "Decorated class must be a sub-class of Widget!"

        # when inside html5, use cls._tagName as the tagName
        if str(cls.__module__).split(".")[-2] == "html5":
            tagName = cls._tagName or cls.__name__
        else:
            tagName = cls.__name__

        #print("%r registered as <%s>" % (cls, tagName))
        registerTag(tagName, cls)
        return cls


def _buildTags(debug=False):
    """Generates a dictionary of all to the html5-library known tags and their associated objects and attributes."""
    global __tags

    if __tags is not None:
        return

    if __tags is None:
        __tags = {}

    for cname in globals().keys():
        if cname.startswith("_"):
            continue

        cls = globals()[cname]

        try:
            if not issubclass(cls, Widget):
                continue
        except:
            continue

        registerTag(cls._tagName or cls.__name__, cls, override=False)

    if debug:
        for tag in sorted(__tags.keys()):
            print("{}: {}".format(tag, ", ".join(sorted(__tags[tag][1]))))


class HtmlAst(list):
    """Abstract syntax tree element used by parseHTML()."""


def parseHTML(html: str, debug: bool = False) -> HtmlAst:
    """Parses the provided HTML-code according to the tags registered by html5.registerTag() or components that used the html5.tag-decorator."""

    def scanWhite(l):
        """Scan and return whitespace."""
        ret = ""
        while l and l[0] in " \t\r\n":
            ret += l.pop(0)

        return ret

    def scanWord(l):
        """Scan and return a word."""
        ret = ""
        while l and l[0] not in " \t\r\n" + "<>=\"'":
            ret += l.pop(0)

        return ret

    stack = []

    # Obtain tag descriptions, if not already done!
    global __tags

    if __tags is None:
        _buildTags(debug=debug)

    # Prepare stack and input
    stack.append((None, None, HtmlAst()))
    html = [ch for ch in html]

    # Parse
    while html:
        tag = None
        text = ""

        # Auto-close leaf elements, e.g. like <hr>, <br>, etc.
        while stack and stack[-1][0] and __tags[stack[-1][0]][0]._leafTag:
            stack.pop()

        if not stack:
            break

        parent = stack[-1][2]

        while html:
            ch = html.pop(0)

            # Comment
            if html and ch == "<" and "".join(html[:3]) == "!--":
                html = html[3:]
                while html and "".join(html[:3]) != "-->":
                    html.pop(0)

                html = html[3:]

            # Opening tag
            elif html and ch == "<" and html[0] != "/":
                tag = scanWord(html)
                if tag.lower() in __tags:
                    break

                text += ch + tag

            # Closing tag
            elif html and stack[-1][0] and ch == "<" and html[0] == "/":
                junk = ch
                junk += html.pop(0)

                tag = scanWord(html)
                junk += tag

                if stack[-1][0] == tag.lower():
                    junk += scanWhite(html)
                    if html and html[0] == ">":
                        html.pop(0)
                        stack.pop()
                        tag = None
                        break

                text += junk
                tag = None

            else:
                text += ch

        # Append plain text (if not only whitespace)
        if (
            text
            and (len(text) == 1 and text in ["\t "])
            or not all([ch in " \t\r\n" for ch in text])
        ):
            # print("text", text)
            parent.append(domConvertEncodedText(text))

        # Create tag
        if tag:
            tag = tag.lower()
            # print("tag", tag)

            elem = (tag, {}, HtmlAst())

            stack.append(elem)
            parent.append(elem)

            while html:
                scanWhite(html)
                if not html:
                    break

                # End of tag >
                if html[0] == ">":
                    html.pop(0)
                    break

                # Closing tag at end />
                elif html[0] == "/":
                    html.pop(0)
                    scanWhite(html)

                    if html[0] == ">":
                        stack.pop()
                        html.pop(0)
                        break

                val = att = scanWord(html).lower()

                if not att:
                    html.pop(0)
                    continue

                scanWhite(html)
                if html[0] == "=":
                    html.pop(0)
                    scanWhite(html)

                    if html[0] in "\"'":
                        ch = html.pop(0)

                        val = ""
                        while html and html[0] != ch:
                            val += html.pop(0)

                        html.pop(0)

                if att not in elem[1]:
                    elem[1][att] = val
                else:
                    elem[1][att] += " " + val

                continue

    while stack and stack[-1][0]:
        stack.pop()

    return stack[0][2]


def fromHTML(
    html: [str, HtmlAst],
    appendTo: Widget = None,
    bindTo: Widget = None,
    debug: bool = False,
    **kwargs,
) -> [Widget]:
    """Parses the provided HTML code according to the objects defined in the html5-library.

    html can also be pre-compiled by `parseHTML()` so that it executes faster.

    Constructs all objects as DOM nodes. The first level is chained into appendTo.
    If no appendTo is provided, appendTo will be set to html5.Body().

    If bindTo is provided, objects are bound to this widget.

    ```python
    from vi import html5

    div = html5.Div()
    html5.parse.fromHTML('''
        <div>Yeah!
            <a href="hello world" [name]="myLink" class="trullman bernd" disabled>
            hah ala malla" bababtschga"
            <img src="/static/images/icon_home.svg" style="background-color: red;"/>st
            <em>ah</em>ralla <i>malla tralla</i> da
            </a>lala
        </div>''', div)

    div.myLink.appendChild("appended!")
    ```
    """
    # Handle defaults
    if bindTo is None:
        bindTo = appendTo

    if isinstance(html, str):
        html = parseHTML(html, debug=debug)

    assert isinstance(html, HtmlAst)

    # Deprecated: vars-variable
    vars = kwargs.get("vars")
    if vars and isinstance(vars, dict):
        logging.warning(
            "Using fromHTML(vars=...) is deprecated. Please directly provide your variables as kwargs."
        )
        kwargs.update(vars)

    def replaceVars(txt, vars):
        if not htmlExpressionEvaluator:
            return txt

        # Internal function for replacing {{ values["from"][4]["string"] + 1 }}...
        ret = ""

        while match := __reVarReplacer.search(txt):
            ret += txt[: match.start()]
            txt = txt[match.end() :]

            val = htmlExpressionEvaluator.execute(match.group(1), vars)
            ret += str(val) if val is not None else ""

        return ret + txt

    def interpret(parent, items, vars):
        ifResult = None
        ret = []

        for item in items:
            if isinstance(item, str):
                txt = TextNode(replaceVars(item, vars))

                if parent:
                    parent.appendChild(txt)

                ret.append(txt)
                continue

            # Extract tags, atts and children from HtmlAst
            tag = item[0]
            atts = item[1]
            children = item[2]

            # Early attribute checking for the conditional stuff
            haveConditional = False
            for att in ("if", "elif", "else") if htmlExpressionEvaluator else ():
                val = atts.get(f"flare-{att}")
                if val is None:
                    continue

                # print(att, val, ifResult)

                haveConditional = True
                val = replaceVars(val, vars)

                if att in ("if", "elif"):
                    if att == "elif":
                        assert (
                            ifResult is not None
                        ), "flare-elif without preceding flare-if/flare-elif"
                        if ifResult:
                            item = None
                            break

                    if not htmlExpressionEvaluator.execute(val, vars):
                        item = None
                        ifResult = False
                    else:
                        ifResult = True

                    break

                elif att == "else":
                    assert (
                        ifResult is not None
                    ), "flare-else without preceding flare-if/flare-elif"
                    if ifResult:
                        item = None

                    ifResult = None
                    break

            if not item:
                continue

            if not haveConditional:
                ifResult = None

            # Special handling for tables: A "thead" and "tbody" are already part of table!
            if tag in ["thead", "tbody"] and isinstance(parent, Table):
                wdg = getattr(parent, tag[1:])

            # Usual way: Construct new element and chain it into the parent.
            else:
                wdg = __tags[tag][0]()

            for att, val in atts.items():
                # Ignore any flare-prefixed attributes here
                if att.startswith("flare-"):
                    continue

                val = replaceVars(val, vars)

                # The [name] attribute binds the current widget to bindTo under the provided name!
                if att == "[name]":
                    # Allow disable binding!
                    if not bindTo:
                        logging.warning(
                            "html5: Unable to evaluate %r due unset bindTo", att
                        )
                        continue

                    if getattr(bindTo, val, None):
                        pass  # logging.warning("html5: Cannot assign name %r because it already exists in %r", val, bindTo)

                    elif not (
                        any([val.startswith(x) for x in string.ascii_letters + "_"])
                        and all(
                            [
                                x in string.ascii_letters + string.digits + "_"
                                for x in val[1:]
                            ]
                        )
                    ):
                        logging.warning(
                            "html5: Cannot assign name %r because it contains invalid characters",
                            val,
                        )

                    else:
                        setattr(bindTo, val, wdg)
                        wdg.onBind(bindTo, val)

                    if debug:  # fixme: remove debug flag!
                        logging.debug("html5: %r assigned to %r", val, bindTo)

                # Class is handled via Widget.addClass()
                elif att == "class":
                    # print(tag, att, val.split())
                    wdg.addClass(*val.split())

                elif att == "disabled":
                    # print(tag, att, val)
                    if val == "disabled":
                        wdg.disable()

                elif att == "hidden":
                    # print(tag, att, val)
                    if val == "hidden":
                        wdg.hide()

                # style-attributes must be split into its separate parts to be mapped into the dict.
                elif att == "style":
                    for dfn in val.split(";"):
                        if ":" not in dfn:
                            continue

                        att, val = dfn.split(":", 1)

                        # print(tag, "style", att.strip(), val.strip())
                        wdg["style"][att.strip()] = val.strip()

                # data attributes are mapped into a related dict.
                elif att.startswith("data-"):
                    wdg["data"][att[5:]] = val

                # transfer attributes from the binder into current widget
                elif att.startswith(":"):
                    if bindTo:
                        try:
                            setattr(wdg, att[1:], getattr(bindTo, val))
                        except Exception as e:
                            logging.exception(e)

                    else:
                        logging.error("html5: bindTo is unset, can't use %r here", att)

                # add event listener on current widget to callbacks on the binder
                elif att.startswith("@"):
                    if bindTo:
                        try:
                            callback = getattr(bindTo, val)
                            assert callable(callback), f"{callback} is not callable"

                        except Exception as e:
                            logging.exception(e)
                            continue

                        # print(wdg, att, hash(callback))
                        wdg.addEventListener(att[1:], callback)

                    else:
                        logging.error("html5: bindTo is unset, can't use %r here", att)

                # Otherwise, either store widget attribute or save value on widget.
                else:
                    try:
                        wdg[att] = parseInt(val, val)

                    except ValueError:
                        if att in dir(wdg):
                            logging.error(
                                "html5: Attribute %r already defined for %r", att, wdg
                            )
                        else:
                            setattr(wdg, att, val)

                    except Exception as e:
                        logging.exception(e)

            # Repeat children within this element?
            if htmlExpressionEvaluator and (val := atts.get("flare-for")):
                val = htmlExpressionEvaluator.execute(val, vars)

                if val:
                    lvars = vars.copy()

                    if isinstance(val, dict):
                        for k, v in val.items():
                            lvars["key"] = k
                            lvars["value"] = v
                            interpret(wdg, children, lvars)

                    elif isinstance(val, list):
                        for v in val:
                            lvars["value"] = v
                            interpret(wdg, children, lvars)

                    else:
                        lvars["value"] = val
                        interpret(wdg, children, lvars)
            else:
                interpret(wdg, children, vars)

            if parent and not wdg.parent():
                parent.appendChild(wdg)

            ret.append(wdg)

        return ret

    return interpret(appendTo, html, kwargs)


if __name__ == "__main__":
    print(globals())
