========================================
html5 (core library)
========================================

Any **flare** components are entirely established on top of the
*html5*-library.

The :mod:`html5 library <flare.html5>` is flare's core module and key feature, and manages
access to the browser's DOM and its items, by implementing a Python
object wrapper class for any HTML-element. Such an element is called
*widget*. For example, ``html5.Div()`` is the widget representing a
div-element, or ``html5.A()`` a widget representing an a-element.
Widgets can be sub-classed into specialized components, which contain
other widgets and components and interact together.

The document's body and head can directly be accessed by the static
widgets ``html5.Head()`` and ``html5.Body()``.

All these widgets are inheriting from an abstract widget wrapper called
``html5.Widget``. ``html5.Widget`` is the overall superclass which
contains most of the functions used when working with DOM elements.
Therefore, all widgets are usually handled the same way, except
leaf-type widgets, which may not contain any children.

First steps
-----------

When working with native html5-widgets, every widget must be created
separately and stacked together in the desired order. This is well known
from JavaScript's createElement-function.

Here's a little code sample.

.. code:: python

    from flare import html5

    # Creating a new a-widget
    a = html5.A()
    a["href"] = "https://www.viur.dev"  # assign value to href-attribute
    a["target"] = "_blank"              # assign value to target-attribute
    a.addClass("link")                  # Add style class "link" to element

    # Append text node "Hello World" to the a-element
    a.appendChild(html5.TextNode("Hello World"))

    # Append the a-widget to the body-widget
    html5.Body().appendChild(a)

Summarized:

-  ``html5.Xyz()`` creates an instance of the desired widget. The
   notation is that the first letter is always in uppercase-order, the
   rest is hold in lowercase-order, therefore e.g.
   :class:`html5.Textarea() <flare.html5.Textarea>` is used for a textarea.
-  Attributes are accessible via the attribute indexing syntax, like
   ``widget["attribute"]``. There are some special attributes like
   ``style`` or ``data`` that are providing a dict-like access, so
   ``widget["style"]["border"] = "1px solid red"`` is used.
-  Stacking is performed with ``widget.appendChild()``. There are also some additional
   functions for easier element stacking and child modification, these are
   - ``widget.prependChild()`` to prepend children,
   - ``widget.insertBefore()`` to insert a child before another child,
   - ``widget.removeChild()`` to remove a child.
-  To access existing child widgets, use ``widget.children(n)`` to
   access the *n*-th child, or without *n* to retrieve a list of a
   children.

Parsing widgets from HTML-code
------------------------------

Above result can also be achieved much faster, by using the build-in
`html5-parser and renderer <#html-parser-reference>`__.

.. code:: python

    from flare import *

    html5.Body().appendChild(
        "<a href='https://www.viur.dev' target='_blank' class='viur'>Hello World</a>"
    )

That's quite simpler, right? This is a very handy feature for
prototyping and to quickly integrate new HTML layouts.

``Widget.appendChild()`` and other, corresponding functions, allow for
an arbitrary number of elements to be added. HTML-code, widgets, text or
even lists or tuples of those can be given, like so

.. code:: python

    ul = html5.Ul()
    ul.appendChild("<li class='is-active'>lol</li>")
    ul.prependChild(html5.Li(1337 * 42))
    ul.appendChild("<li>me too</li>", html5.Li("and same as I"))

The HTML parser can also do more: When component classes (any class that
inherits directly from html5.Widget, like html5.Div or so) are decorated
with the `html5.tag <#html5tag>`__-decorator, these are automatically
made available in the HTML-parser for recognition.

Inheritance is normal
---------------------

In most cases, both methods shown above are used together where
necessary and useful. Especially when creating new components with a
custom behavior inside your app, knowledge of both worlds is required.

To create new components, inheriting from existing widgets is usual. If
we would like to add our link multiple times within our app, with
additional click tracking, we can make it a separate component, like so:

.. code:: python

    import logging
    from flare import *

    class Link(html5.A):  # inherit Link from html5.A widget
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

In this example, we just made our first custom component: The
``Link``-class can be arbitrarily used.

Widget basics
-------------

Following sections describe the most widely used functions of the
:class:```html5.Widget`` <flare.html5.Widget>`-class which are inherited by any widget or huger
component in flare.

Constructor
~~~~~~~~~~~

All widgets share the same ``__init__``-function, having the following
signature:

.. code:: python

    def __init__(self, *args, appendTo=None, style=None, **kwargs)

-  ``*args`` are any positional arguments that are passed to
   ``self.appendChild()``. These can be either other widgets or strings
   containing HTML-code. Non-container widgets like ``html5.Br()`` or
   ``html5.Hr()`` don't allow anything passed to this parameter, and
   throw an Exception.
-  ``appendTo`` can be set to another html5.Widget where the constructed
   widget automatically will be appended to. It substitutes an
   additional :meth:`appendChild() <flare.html5.Widget.appendChild>`-call to insert the constructed Widget to
   the parent.
-  ``style`` allows to specify CSS-classes which are added to the
   constructed widget using
-  ``**kwargs`` specifies any other parameters that are passed to
   ``appendChild()``, like variables.

Insertion and removal
~~~~~~~~~~~~~~~~~~~~~

These methods manipulate the DOM and it's nodes

appendChild()
^^^^^^^^^^^^^

Appends another html5.Widget as child to the parent element:

.. code:: python

    self.appendChild("""<ul class='navlist'></ul>""")
    self.nav.appendChild("""<li>Navigation Point 1</li>""")

prependChild()
^^^^^^^^^^^^^^

Prepends a new child to the parent element

.. code:: python

    self.appendChild("""<ul class='navlist'></ul>""")
    navpoint2 = self.nav.appendChild("""<li>Navigation Point 2</li>""")
    navpoint2.prependChild(("""<li>Navigation Point 1</li>"""))

replaceChild()
^^^^^^^^^^^^^^

Same as appendChild(), but removes the current children of the Widget
first.

insertBefore()
^^^^^^^^^^^^^^

Inserts a new child element before the target child element

.. code:: python

    self.appendChild("""<ul class='navlist'></ul>""")
    navpoint = self.nav.appendChild("""<li>Navigation Point 1</li>""")
    navpoint3 = self.nav.appendChild("""<li>Navigation Point 3</li>""")
    navpoint2 = self.nav.insertBefore("""<li>Navigation Point 2</li>""", navpoint3)

If the child element that the new element is supposed to be inserted
before does not exist, the new element is appended to the parent
instead.

removeChild(), removeAllChildren()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Either removes one child from the parent element or any available
children.

Visibility and usability
~~~~~~~~~~~~~~~~~~~~~~~~

Widgets can be switched hidden or disabled. Form elements, for example,
might be disabled when a specific condition isn't met. These functions
here help to quickly change visibility and usability of widgets,
including their child widgets which are switched recursively.

hide(), show()
^^^^^^^^^^^^^^

Hides or shows a widget on demand.

To check whether a widget is hidden or not, evaluate
``widget["hidden"]``. In the HTML-parser, this flag can be set using the
``hidden`` attribute, e.g. ``<div hidden>You can't see me.</div>``.

enable(), disable()
^^^^^^^^^^^^^^^^^^^

Enable or disable the widget in the DOM. Useful for forms and similar UI
applications.

To check whether a widget is disabled or not, evaluate
``widget["disabled"]``. In the HTML-parser, this flag can be set using
the ``disabled`` attribute, e.g. ``<div disabled>I'm disabled</div>``.

class-attribute modification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These methods are helpful for adding CSS-classes quickly.

addClass()
^^^^^^^^^^

Adds a class to the html5.Widget and checks to prevent adding the same
class multiple times.

::

    nav = self.appendChild("""<ul></ul>""")
    nav.addClass('navlist')

Adding a class multiple times might be wanted and is valid. In this
case, modify the widget's ``class``-attribute directly by assigning a
list to it.

removeClass()
^^^^^^^^^^^^^

Checks if the widget has that class and removes it

::

    nav = self.appendChild("""<ul class='big-red-warning-border-color'></ul>""")
    nav.removeClass('big-red-warning-border-color')

toggleClass()
^^^^^^^^^^^^^

Toggles a class *on* or *off*, depending on whether it has the specified
class already or not.

hasClass()
^^^^^^^^^^

Checks if the element has a given class or not. Returns True if class
name is found and False otherwise.

::

    nav = self.appendChild("""<ul class='big-red-warning-border-color'></ul>""")
    if nav.hasClass('big-red-warning-border-color'):
        print("Help! There is a big red border around this element! Remove the class so we can feel safe again")

HTML parser reference
---------------------

The html5-library built into flare brings its own HTML-parser.
Using this parser, any HTML-code can directly be turned into a flare DOM.

Additionally, some nice extensions regarding flare component and widget
customization and conditional rendering is supported, as the HTML-renderer
automatically creates the DOM from a parsed input and serves as some kind of
template processor.

Data-based rendering
~~~~~~~~~~~~~~~~~~~~

Using variables
^^^^^^^^^^^^^^^

Any variables provided via kwargs to :meth:`html5.fromHTML() <flare.html5.core.fromHTML>`
can be inserted in attributes or as TextNode-elements with their particular content
when surrounded by ``{{`` and ``}}``. Inside this notation, full Python expression syntax
is allowed, so that even calculations or concatenations can be done.

.. code:: python

    html5.Body().appendChild("""
        <div class="color-{{ l[1] + 40 }}">{{ d["world"] + "World" * 3 }} and {{ d }}</div>
    """, l=[1,2,3], d={"world": "Hello"})

renders into

.. code:: html

    <div class="color-42">HelloWorldWorldWorld and {'world': 'Hello'}</div>

flare-if, flare-elif, flare-else
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The attributes ``flare-if``, ``flare-elif`` and ``flare-else`` can be
used on all tags for conditional rendering.

This allows for any simple Python expression that evaluates to True or
any computed non-boolean value representing True.

.. code:: python

    html5.Body().appendChild("""
        <div>begin</div>
        <div flare-if="i <= 10">i is just low</div>
        <div flare-elif="i <= 50 and j >=100">i and j have normal values</div>
        <div flare-elif="i > 50 and j >= 50">i and j have moderate values</div>
        <div flare-else>i and j are something different</div>
        <div>end</div>
    """, i=50, j=151)

As variables, any arguments given to
:meth:`html5.fromHTML() <flare.html5.core.fromHTML>` (or related functions) as kwargs
can be used.

html5.parseHTML()
~~~~~~~~~~~~~~~~~

.. code:: python

    def parseHTML(html: str, debug: bool=False) -> HtmlAst

Parses the provided HTML-code according to the tags registered by
html5.registerTag() or components that use the
:meth:`@tag <flare.html5.core.tag>`-decorator.

The function returns an abstract syntax tree representation (HtmlAst) of
the HTML-code that can be rendered by :meth:`html5.fromHTML() <flare.html5.core.fromHTML>`.

html5.fromHTML()
~~~~~~~~~~~~~~~~

.. code:: python

    def fromHTML(html: [str, HtmlAst], appendTo: Widget=None, bindTo: Widget=None, debug: bool=False, **kwargs) -> [Widget]

Renders HTML-code or compiled HTML-code (HtmlAst).

-  appendTo: Defines the Widget where to append the generated widgets to
-  bindTo: Defines the Widget where to bind widgets using the
   ``[name]``-attribute to
-  debug: Debugging output
-  \*\*kwargs: Any specified kwargs are available as `variables to any
   expressions <#using-variables>`__.

HTML-code can optionally be pre-compiled with
:meth:`html5.parseHTML() <flare.html5.core.parseHTML>`, and then executed multiple
times (but with different variables) by fromHTML. This is useful when
generating lists of same elements with only replaced variable data.

@html5.tag
~~~~~~~~~~

Decorator to register a sub-class of ``html5.Widget`` either under its
class-name, or an associated tag-name.

Examples:

.. code:: python

    from flare import html5

    # register class Foo as <foo>-Tag
    @html5.tag
    class Foo(html5.Div):
        pass

    # register class Bar as <baz>-Tag
    @html5.tag("baz")
    class Bar(html5.Div):
        pass

