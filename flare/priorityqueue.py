"""Select object generators by priority.

This is used when implementing pluggable features,
which can optionally be registered for specific use-cases.
"""


class PriorityQueue(object):
    def __init__(self):
        super(PriorityQueue, self).__init__()
        self._q = {}

    def insert(self, priority, validateFunc, generator):
        priority = int(priority)
        if priority not in self._q.keys():
            self._q[priority] = []

        self._q[priority].append((validateFunc, generator))

    def select(self, *args, **kwargs):
        prios = list(self._q.keys())
        prios.sort(reverse=True)

        for p in prios:
            for validateFunc, generator in self._q[p]:
                if validateFunc(*args, **kwargs):
                    return generator
