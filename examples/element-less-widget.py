from flare import *

class Test(html5.Widget):
    def __init__(self, name):
        super().__init__()

        self.appendChild(
            "<h1 [name]='title' @click='remove'></h1>"
            "Sejelfluchzeusch."
        )
        self.title.replaceChild(name)

    def remove(self):
        self.parent().removeChild(self)


a = Test("A")
b = Test("B")
c = Test("C")
d = Test("D")

html5.Body().appendChild(a, b)
b.title.replaceChild("ROFL!")
html5.Body().insertBefore(c, b)
c.title.replaceChild("COPTER!")
html5.Body().insertAfter(d, a)
d.title.replaceChild("LAST!")
