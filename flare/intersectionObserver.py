from flare import conf
from js import IntersectionObserver as js_intersectionObserver


class IntersectionObserver:
    """Python wrapper for IntersectionObserver.

    Usage:
    myObserver = IntersectionObserver(myChangeFunction)
    myObserver.observe(aWidget)
    """

    jsObserver = None
    observableWidgets = []

    def __init__(self, callback, rootWidget=None, rootMargin="0px", threshold=0.2):
        observerOptions = {
            "root": conf["app"].element if not rootWidget else rootWidget.element,
            "rootMargin": rootMargin,
            "threshold": threshold,
        }

        self.jsObserver = js_intersectionObserver.new(callback, **observerOptions)

    def observe(self, widget):
        self.observableWidgets.append(widget)
        self.jsObserver.observe(widget.element)

    def unobserve(self, widget):
        self.observableWidgets.remove(widget)
        self.jsObserver.unobserve(widget.element)
