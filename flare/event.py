"""Event dispatcher for non-browser Events which occur on Widget state changes."""


class EventDispatcher(object):
    """Base class for event notifier."""

    def __init__(self, name):
        """Create a EventDispatcher."""
        super(EventDispatcher, self).__init__()
        self.queue = []
        self.name = name

    def _genTargetFuncName(self):
        """Return the name of the function called on the receiving object."""
        return "on%s" % (self.name[0].upper() + self.name[1:])

    def register(self, cb, reset=False):
        """Append "cb" to the list of objects to inform of the given Event.

        Does nothing if cb has already subscribed.
        :param cb: the object to register
        :type cb: object
        """
        assert self._genTargetFuncName() in dir(cb), (
            "cb must provide a %s method" % self._genTargetFuncName()
        )

        if reset:
            self.queue = []

        if cb not in self.queue:
            self.queue.append(cb)

    def unregister(self, cb):
        """Remove "cb" from the list of objects to inform of the given Event.

        Does nothing if cb is not in that list.
        :param cb: the object to remove
        :type cb: object
        """
        if cb in self.queue:
            self.queue.remove(cb)

    def fire(self, *args, **kwargs):
        """Fire the event.

        Informs all subscribed listeners.
        All parameters passed to the receiving function.
        """
        for cb in self.queue:
            getattr(cb, self._genTargetFuncName())(*args, **kwargs)
