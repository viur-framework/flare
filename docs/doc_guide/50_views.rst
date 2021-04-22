========================================
Views
========================================
Views allow switching between different widgets. A view must inherit from the View class abd can update multiple View-Widgets of the conf["app"]. Additionally, the dictOfWidgets must be filled in the constructor before the super call.
The key of the dictionary must be present in the conf["app"] widget.

A view widget is the actual content that is then inserted into a widget in the main app. These view widgets must inherit from ViewWidget.

The currently active view is stored in a global state under conf["views_state"].

create a View
~~~~~~~~~~~~~~~~~~~~

.. code-block:: Python

	from flare.views.view import View, ViewWidget

	class myView(View):

		def __init__(self):
			dictOfWidgets = {
				"content"     : myViewContent
				#each key muss exists as instancevariable in conf["app"]
			}
			super().__init__(dictOfWidgets)

	class myViewContent(ViewWidget):

		def initWidget( self ):
			self.appendChild("Hello View")

		def onViewfocusedChanged( self, viewname, *args, **kwargs ):
			pass #here we can execute code, which muss be called wenn e View gets focus


register a View
~~~~~~~~~~~~~~~~~~~~
At this point, we have created a view. We have defined that the widget content from the main app should be replaced by the one from myViewContent.
Now we need to register this view.

.. code-block:: Python

		from flare.views.helpers import addView, removeView

		addView(myView,"page1")

In this example, the view myView is registered under the name page1. A view can also be registered under multiple names.
removeView removes the view again.

activate / switch a view
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To activate a view the view instance of the state conf["views_state"] must be updated.
The status stores the name of the view that is currently displayed and can be updated as follows.

.. code-block:: Python

	conf["views_state"].updateState("activeView", "page1")


Views with ViUR
~~~~~~~~~~~~~~~~~~~~~~~
In ViUR, modules have different views depending on the handler.
generateView here encapsulates module name, actionname and data away in a params dictionary, which is then available in the view and can be loaded from the view in any ViewWidget.

.. code-block:: Python

	#item is a adminInfo Entry

	# generate a unique instancename, because a edit can be opened multiple times with same parameters
	instancename = "%s___%s" % (item[ "moduleName" ]+item[ "handler" ], str( time.time() ).replace( ".", "_" ))

	#create new viewInstance
	viewInst = generateView( myView, item[ "moduleName" ], item[ "handler" ], data = item, name=instancename )

	#register this new view
	conf[ "views_registered" ].update( { instancename: viewInst } )

	# somewhere else in code, i.e in a Navigation
	conf["views_state"].updateState("activeView", instancename)






