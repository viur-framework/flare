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
- Stacking is performed with `widget.appendChild()`. There's also `widget.prependChild()`, `widget.insertBefore()` and `widget.removeChild()` for further insertion or removal operations.


## Parsing widgets from HTML-code

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

In this example, we just made our first custom component: The `Link`-class can be arbitrarily used.

## Widget fundamentals

Following sections describe the most widely used functions of the `html5.Widget`-class which are inherited by any widget or huger component in flare.

### Constructor

All Widgets in html5 share the same `__init__`-function, having the following signature:

```python
def Widget.__init__(self, *args, appendTo=None, style=None, **kwargs)
```

- `*args` are any positional arguments that are passed to `self.appendChild()`. These can be either other widgets or strings containing HTML-code. Non-container widgets like `html5.Br()` or `html5.Hr()` don't allow anything passed to this parameter, and throw an Exception.
- `appendTo` can be set to another html5.Widget where the constructed widget automatically will be appended to. It substitutes an additional `appendChild()`-call to insert the constructed Widget to the parent.
- `style` allows to specify CSS-classes which are added to the constructed widget using
- `**kwargs` specifies any other parameters that are passed to `appendChild()`, like variables.  

### appendChild(), prependChild(), insertBefore(), fromHTML(), removeChild()
These methods manipulate the DOM and it's html elements

#### appendChild()
Appends a new child to the parent element:
```
self.appendChild("""<ul class='navlist'></ul>""")
self.nav.appendChild("""<li>Navigation Point 1</li>""")
```
If replace=True is passed as an argument next to the html code, this method will discard all children of the parent element
and replace them.

#### prependChild()
Prepends a new child to the parent element
```
self.appendChild("""<ul class='navlist'></ul>""")
navpoint2 = self.nav.appendChild("""<li>Navigation Point 2</li>""")
navpoint2.prependChild(("""<li>Navigation Point 1</li>"""))
```
If replace=True is passed as an argument next to the html code, this method will discard all children of the parent element
and replace them.

#### insertBefore()
Inserts a new child element before the target child element
```
self.appendChild("""<ul class='navlist'></ul>""")
navpoint = self.nav.appendChild("""<li>Navigation Point 1</li>""")
navpoint3 = self.nav.appendChild(("""<li>Navigation Point 3</li>"""))
navpoint2 = self.nav.insertBefore(("""<li>Navigation Point 2</li>"""), navpoint3)
```
If the child element that the new element is supposed to be inserted before does not exist, the new element is appended to the parent instead.

#### fromHTML()
Instantiates a widget from an html string that we can access in our python code.

#### removeChild()
Removes the child from the parent element

#### removeAllChildren()
Removes all child elements from the parent element

### addClass(), removeClass(), toggleClass(), hasClass()
These methods are helpful for adding classes dynamically.

#### addClass()
Adds a class to the html5 element and checks to prevent adding the same class.
```
nav = self.appendChild("""<ul></ul>""")
nav.addClass('navlist')
```

#### removeClass()
Checks if the object has that class and removes it
```
nav = self.appendChild("""<ul class='big-red-warning-border-color'></ul>""")
nav.removeClass('big-red-warning-border-color')
```

#### toggleClass()
Toggles a class on and off, depending on wether it has already been added or not.
If the element already has the class, it is removed. If the element does not have the class already, it is added to it.

#### hasClass()
Checks if the element has a given class or not. Returns True if class name is found and False otherwise.
```
nav = self.appendChild("""<ul class='big-red-warning-border-color'></ul>""")
if nav.hasClass('big-red-warning-border-color'):
    print("Help! There is a big red border around this element! Remove the class so we can feel safe again")
```

### enable(), disable()
These methods will enable or disable an element in the DOM. Useful for forms and similar UI applications.

### hide(), show()
Will hide or show and element on demand. This is done by adding the hidden attribute to the element or removing it accordingly.

### Event handling

todo


## HTML parser reference

todo

### Widget configuration

todo

### html5.parseHTML()

todo

### html5.fromHTML()

todo

### @html5.tag

todo
