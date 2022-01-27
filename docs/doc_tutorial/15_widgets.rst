========================================
Widgets
========================================

In this tutorial, we will introduce the widgets of flare.

Reusable UI components
--------------------

Flare widgets are UI components that encapsulate one HTML element. They render their content using a template, other
widgets or a mixture of both. When using templates, placeholders can be used to fill in dynamic data, elements can be
qualified with a name to make them accessible, and events - such as a click - can have a handlers registered to.

Note that the template rendering will be performed only once, initially. After that, any changes to the content of the
widget need to be performed programmatically. This should be kept in mind, especially when deciding where to draw the
line between putting more complexity in the template and creating sub widgets.

Simple Widget
--------------------

To get acquainted with widgets, we will create a simple one that just contains some static HTML.

.. code:: python

    from flare import html5


    class SimpleWidget(html5.Div):
        def __init__(self):
            super().__init__(
                # language=HTML
                """
                <span style="color: red;">I am a </span><span style="color: blue;">Widget!</span>
                """
            )

As we can see, our SimpleWidget contains just two basic HTML ``<span>``s, wrapped in a ``<div>`` (as denoted by the
derivation from ``html5.Div``. That means, that our widget fundamentally is a ``<div>``, and can be treated as such.
For example, it can now simply be put into the DOM somewhere. Try it out by just appending it to the ``<body>``:

.. code:: python

    html5.Body().appendChild(SimpleWidget())

Placeholders
--------------------

Static widgets like the one we just created do have their uses, but most of the time, you will want to display some
dynamic data as well. For this, the template provided in the super constructor call can be enriched with placeholders,
which are then replaced with the given data when the template is being rendered.

.. code:: python

    class ParametrizedWidget(html5.Div):
        def __init__(self, number: int):
            super().__init__(
                # language=HTML
                """
                My parameter is <span style="color: red;">{{number}}</span>
                """, number=number
            )


    html5.Body().appendChild(ParametrizedWidget(5))

Now our widget expects a "number" parameter, which is then passed into the template. However, you need to tell the
template, which parameter is to be supplied with what value, which is a bit awkward. A much better approach is to
expect a ``dict`` in your constructor signature, and unpack it when passing it to the super constructor.

.. code:: python

    class ParametrizedWidget(html5.Div):
        def __init__(self, parameters: dict):
            super().__init__(
                # language=HTML
                """
                My parameter is <span style="color: red;">{{number}}</span>
                """, **parameters
            )


    html5.Body().appendChild(ParametrizedWidget({"number": 5}))

Note that the rendering of the template happens only once. If the parameters change after that, there is no built in
reactivity; you have to handle these cases yourself. Let's look into that now.

Placeholders
--------------------

What we're gonna build now is a widget that reacts to an event by increasing a number and displaying it. We will create
a counter widget that displays a number, with a button that increases the number whenever it is clicked.

.. code:: python

    class CounterWidget(html5.Div):
        value = 0

        def __init__(self):
            super().__init__(
                # language=HTML
                """
                Counter: <span [name]="valueDisplay">{{value}}</span> <button @click="increase">Increase!</button>
                """, value=self.value
            )

        def increase(self):
            self.value += 1
            self.valueDisplay.replaceChild(self.value)

First, let's take a look at the ``[name]`` attribute. This attribute registers the element on which it is defined as a
field of your widget class. As a result of that, we can simply access the ``<span>`` that contains the number in the
``increase`` method with the field name given by the ``[name]`` attribute value, which in this case is ``valueDisplay``.

Next, we are registering the ``increase`` method as a handler on the click event of the button, by using the ``@click``
attribute on the ``<button>`` element.

What the ``increase`` method then does, is increase ``value`` by one. But since, as stated, this will not do anything by
itself, it also updates the content of the ``<span>`` called ``valueDisplay``, by replacing its content with the new
value.

Conditional elements
--------------------

When working with widgets, you often want to exclude elements from being rendered in certain conditions. As an example,
your widget might combine a picture and a text, but you want to support the case that just one of both is provided.

You do not need to manipulate the DOM manually after rendering to achieve this. You can use the ``flare-if`` attribute
instead. If the expression you provide as its value is not truthy, the element on which it is placed is excluded from
rendering.

Let's build that widget that combines a picture and text.

.. code:: python

    class ImageAndTextWidget(html5.Div):
        def __init__(self, parameters: dict):
            super().__init__(
                # language=HTML
                """
                <div flare-if="pictureUrl" style="text-align: center;">
                    <img src="{{pictureUrl}}"/>
                </div>
                <p flare-if="text">{{text}}</p>
                """, **parameters
            )


    html5.Body().appendChild(ImageAndTextWidget(
        {
            "pictureUrl": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/A_kitten_on_the_lawn_%28Pixabay%29.jpg/640px-A_kitten_on_the_lawn_%28Pixabay%29.jpg",
            "text": "Look! Kitty likes the flowers!"
        }
    ))

Running this, you get a picture of a kitten with some text below. If you now play around with it, you will notice that
by omitting the ``pictureUrl``, you do not get a broken image, but the entire ``<div>`` that contains the image is gone.
The same goes for the ``<p>`` if you provide no text.