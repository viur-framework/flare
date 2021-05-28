from flare import *

html5.Head().appendChild("<style>.highlight { font-weight: bold; color: red; }</style>")


class Test(html5.Ul):
    def __init__(self):
        super().__init__()
        for i in range(5):
            self.appendChild(
                "<li @click='click{{ i if i <=2 else 2 }}'>Entry {{ i + 1 }}</li>", i=i
            )

    def click0(self):
        html5.Body().appendChild("Click0<br>")

    def click1(self, event):
        html5.Body().appendChild("Click1 %r<br>" % event)

    def click2(self, event, widget):
        html5.Body().appendChild("Click2 %r %r<br>" % (event, str(widget)))
        widget.toggleClass("highlight")


html5.Body().appendChild(Test())
