========================================
Views
========================================

In this tutorial, we will introduce flare's concept of views.

Building blocks
--------------------

There are two basic concepts in flare in regards to views: The view itself, and the view widgets.

In essence, a view has a name, and it consists of a collection of view widgets, with the information on where in the DOM
to actually display them. A view widget is a special kind of widget based on a html5 ``<div>``, that is being hooked
into and removed from the appropriate place in the DOM. It also gets a notification whenever view switching occurs.

Views rely on the concept of a central "app" class. Since the view mostly just contains a dictionary on which view
widget to place where, it expects to find an app class which has the target elements as fields. The view will then
use the field name as key in its view widget dictionary.


Example
--------------------

As an example, we are going to create simple flip flop views: Two views, each containing a button to show the other
view.

For this, we create a new file ``views.py`` where we put all the following code. We start off with the view widgets of
the two views:

.. code:: python

    from flare import html5, bindApp
    from flare.button import Button
    from flare.config import conf, updateConf
    from flare.views.view import View, ViewWidget
    from flare.views.helpers import addView, removeView, updateDefaultView


    class FlipViewContent(ViewWidget):
        def initWidget(self):
            self.appendChild(Button("Flip!", self.switch))
            self.appendChild(" - Flop!")

        def onViewfocusedChanged(self, viewname, *args, **kwargs):
            pass

        def switch(self):
            conf["views_state"].updateState("activeView", "flop")


    class FlopViewContent(ViewWidget):
        def initWidget(self):
            self.appendChild("Flip! - ")
            self.appendChild(Button("Flop!", self.switch))

        def onViewfocusedChanged(self, viewname, *args, **kwargs):
            pass

        def switch(self):
            conf["views_state"].updateState("activeView", "flip")

These two view widgets are virtually identical. They both contain a button that calls their ``switch`` method, which
triggers the switch over to the other view, by changing ``activeView`` to the name of the other view. Next, we define
the view classes themselves.

.. code:: python

    class FlipView(View):
        def __init__(self):
            super().__init__({
                "content": FlipViewContent
            })


    class FlopView(View):
        def __init__(self):
            super().__init__({
                "content": FlopViewContent
            })

Again, these two views are virtually identical. All they do is contain the information on where to put their respective
content. In this case, they both only have one view widget, and they both bind it to the same place: An element named
``content``. In order for this resolution to work, there needs to be an app class, which has a field named ``content``
which points to the element where the view shall be rendered. Let's build one.

.. code:: python

    class App(html5.Div):

        def __init__(self):
            super(App, self).__init__()
            html5.Body().appendChild(self)
            bindApp(self, conf)

As you can see, we derive our app class from a div, hook it into the DOM, and call ``bindApp`` to register it in the
configuration, so that the view system can access it. Now we add the ``content`` field to it, and make sure that it is
properly connected to the DOM:

.. code:: python

    class App(html5.Div):
        content = html5.Div()

        def __init__(self):
            super(App, self).__init__()
            html5.Body().appendChild(self)
            bindApp(self, conf)
            self.appendChild(self.content)

Only one final step remains: Registering the two views, setting the flip view to active, and actually running the app.


.. code:: python

    class App(html5.Div):
        content = html5.Div()

        def __init__(self):
            super(App, self).__init__()
            html5.Body().appendChild(self)
            bindApp(self, conf)
            self.appendChild(self.content)
            addView(FlipView, "flip")
            addView(FlopView, "flop")
            conf["views_state"].updateState("activeView", "flip")


    app = App()

As seen with the ``addView`` calls, we register the two view classes, giving them the names "flip" and "flop". These
names are then used to switch the ``activeView``, as we already did earlier in the ``switch`` methods of the view
widgets.

That's it. Make flare load your ``views.py`` file as described in the Hello World tutorial, and you can have fun with
flipping and flopping the two views.