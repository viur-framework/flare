# html5

**flare** is entirely established on top of a library called *html5*.

This library manages access to the browser's DOM and its items, by implementing a Python object wrapper class for every HTML5-element. This is called a *widget*. For example `html5.Div()` is the widget representing a div-element, or `html5.A()` a widget representing an a-element.

The document's body and head can directly be accessed by the static widgets `html5.Head()` and `html5.Body()`.
All these widgets are inheriting from an abstract widget wrapper class called `html5.Widget`. `html5.Widget` is the overall superclass which contains most of the functions used when working with DOM elements. Therefore, all widgets are usually handled the same way.

## First steps

When working with native HTML5 widgets, every widget must be created separately and stacked together in the desired order. This practise is well known from JavaScript's createElement-function.

Here's a little code sample.

```python
from flare import *

# Creating a new a-widget
a = html5.A()
a["href"] = "https://www.viur.dev"  # assign value to href-attribute
a["target"] = "_blank"              # assign value to target-attribute
a.addClass("link")                  # Add style class "link" to element

# Append text node "Hello World" to the a-element
a.appendChild(html5.TextNode("Hello World"))

# Append the a-widget to the body-widget
html5.Body().appendChild(a)
```

Summarized:

- `html5.Xyz()` creates an instance of the desired widget (the notation is that the first letter is always uppercase, rest is hold lowercase, therefore `html5.Textarea()` for a textarea is used)
- Attributes are accessable via attribute indexing, like `widget["attribute"]`. There are some special attributes like `style` or `data` that are providing a dict-like access, so `widget["style"]["border"] = "1px solid red"` is used.
- Stacking is performed with `widget.appendChild()`. There's also `widget.prependChild()`, `widget.insertChild()` and `widget.removeChild()` for further insertion or removal operations.

## The build-in HTML5 parser

Above result can also be achieved much faster, when the build-in HTML5 parser is used. 

```python
from flare import *

html5.Body().appendChild(
    "<a href='https://www.viur.dev' target='_blank' class='viur'>Hello World</a>"
)
```

Much simpler, right? This is a very handy feature for prototyping and to quickly integrate new HTML layouts.
`Widget.appendChild()` and other, corresponding functions, allow for an arbitrary number of elements to be added. HTML-code, more widgets, text or even lists or tuples can be given to these functions, like so

```python
ul = html5.Ul()
ul.appendChild("<li>lol</li>")
ul.prependChild(html5.Li(1337 * 42))
ul.appendChild("<li>me too</li>", html5.Li("and same as I"))
```

## Inheritance is normal

In most cases, both methods shown above are used together where necessary and useful. Especially when creating new Widgets with a custom behavior inside your app, knowledge of both worlds is required.

To create new components, inheriting from existing widgets is usual. If we would like to add our link multiple times within our app, with additional click tracking, we can make it a separate widget, like so:

```python
import logging
from flare import *

class Link(html5.A):
    def __init__(self, url, *args, target="_blank", **kwargs):
        super().__init__()
        self.addClass("link")
        self["href"] = url
        self["target"] = "_blank"

        self.appendChild(*args, **kwargs)
        self.sinkEvent("onClick")

    def onClick(self, event):
        logging.info(f"The link to {self['href']} has been clicked")

html5.Body().appendChild(
    # Create a link with text
    Link("https://www.viur.dev", "ViUR Framework"),

    "<br>",

    # Create link with logo
    Link("https://www.python.org", """
        <img src="https://www.python.org/static/community_logos/python-powered-h-50x65.png"
            title="Python Programming Language">
    """)
)
```
