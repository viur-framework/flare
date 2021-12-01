# Test-case for addEventListener and removeEventListener with proxy bookkeeping
from flare import *


class Test(html5.Div):
    def __init__(self):
        super().__init__(
            """
            <ul>
                <li @click="select">eins</li>
                <li @click="select">zwei</li>
                <li @click="select">drei</li>
            </ul>
            """
        )
        self.lastRemoved = None

    def select(self, e, w):
        print(e, w.element.innerHTML)
        w.removeEventListener("click", self.select)
        #w.addEventListener("mouseover", self.select)

        if self.lastRemoved:
            self.children(0).appendChild(self.lastRemoved)

        w.parent().removeChild(w)
        self.lastRemoved = w


html5.Body().appendChild(Test())
