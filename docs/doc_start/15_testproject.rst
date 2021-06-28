================
Testproject
================

Setting up a new Python web-app with *flare* is fairly easy. This
section describes several things and ways how *flare* can be used and
configured.

HTML skeleton
--------------------

Below is a shortened version of the code from *hello.html* delivered
together with the *flare* repo. Such a skeleton must be individually
created for an app written with *flare*.

**Caution**: Depending on where you put the html files, you need to change the
source paths:

- <link rel="stylesheet" href="{path-to-flare-directory}/assets/css/style.css"/>

- <script src="{path-to-flare-directory}/assets/js/flare.js"></script>

- "path": "{path-to-flare-directory}/flare"


.. code:: html

   <!doctype html>
   <html>
   <head>
       <meta charset="UTF-8">
       <link rel="stylesheet" href="assets/css/style.css"/>

       <!-- (1) -->
       <script src="https://pyodide-cdn2.iodide.io/v0.16.1/full/pyodide.js"></script>
       <!-- <script src="pyodide/pyodide.js"></script> -->

       <!-- (2) -->
       <script src="assets/js/flare.js"></script>

       <script>
           window.addEventListener(
                   "load",
                   (event) => {
                       window.init = new flare({
                           prelude:                    // (3)
   `
   print("I'm before any fetch")
   `,
                           fetch: {                    // (4)
                               "flare": {
                                   "path": "flare"
                               }
                           },
                           kickoff:                    // (5)
   `
   from flare import *
   html5.Body().appendChild('<a href="https://www.viur.dev">Hello World</a>')
   flare.popup.Alert("Hello World")
   `
                       });
                   }
           );
       </script>
   </head>
   <body class="is-loading"> <!-- (6) -->
   </body>
   </html>


Notable are the following sections:

1. This is the include for the used Pyodide version. When quickly
   setting up a project, the default CDN version of Pyodide can be used
   and is loaded from here. Indeed, it is also possible to serve Pyodide
   on your own. For this, the utility script ``bin/get-pyodide.py`` can
   be used. This script downloads a minimal version of Pyodide delivered
   from the CDN and stores it into a folder named ``pyodide/``. In such
   a case, the CDN-include here must be removed, and replaced by the
   local include. ``get-pyodide.py`` patches some Pyodide-files to
   directly run from the URL ``/pyodide``. You can override this setting
   by specifying a variable ``window.languagePluginLoader`` before
   including the ``pyodide.js``.
2. *flare* serves a piece of JavaScript code that is necessary to
   pre-load flare itself and the Python application. For development, it
   was useful to directly fetch the py-files from the server and store
   them into a browser-internal filesystem when the Python interpreter
   from Pyodide can find it. This is done using the module in
   ``init.js`` and the configuration described next.
3. ``prelude`` is some Python code that is executed before any modules
   are fetched. It can be omitted, if not wanted.
4. ``fetch`` describes Python source modules that are being fetched
   before the application starts. This is very useful for development
   purposes. For every entry (which is the name of the Python package to
   be created), a further object describing the fetch ``path`` and an
   optional ``optional`` attribute is provided. Using the
   ``path``-attribute, the *flare* init script looks for a file
   ``files.json`` which provides a listing of the files being fetched.
   This file is generated using ``bin/gen-files-json.py`` which is
   described below. A Pyodide package can also be pre-compiled from
   source files, but this is not described in detail here, yet.
5. ``kickoff`` is the Python code that is executed when all fetching is
   done and nothing failed. It is used as the entry point to start the
   web-app. In the *hello.html* file, it is just some “Hello World”
   stuff dumped out using flare.
6. The class ``is-loading`` is automatically removed when the kickoff
   code successfully executed. It can be used to show a loading
   animation or something similar.

Writing huger apps
--------------------

When writing huger apps with multiple Python files, the above example
doesn’t satisfy. For this case, an HTML-file like above still serves as
the entry point for the app, but requires a little more configuration.

Let’s thing about the following minimal setup for a huger app:

-  ``/flare`` is the flare repo serving as a library \_ ``/myapp``
   contains our app, which exists only of the files

   -  ``index.html`` the app entry HTML
   -  ``__init__.py`` the app source code
   -  ``files.json`` which is the index file for the *flare* init script
      to find its sources

We only describe the files in ``/myapp``:

**index.html**

.. code:: html

   <!doctype html>
   <html>
   <head>
       <meta charset="UTF-8">
       <script src="https://pyodide-cdn2.iodide.io/v0.16.1/full/pyodide.js"></script>
       <script src="/flare/assets/js/flare.js"></script>
       <script>
           window.addEventListener(
                   "load",
                   (event) => {
                       window.init = new flare({
                           fetch: {
                               "flare": {
                                   "path": "/flare/flare"
                               },
                               "myapp": {
                                   "path": "."
                               }
                           }
                       }
                   );
               }
           );
       </script>
   </head>
   <body class="is-loading">
   </body>
   </html>

**init.py**:

.. code:: python

   from flare import *

   if __name__ == "myapp":
       html5.Body().appendChild('<a href="https://www.viur.dev">Hello World</a>')
       popup.Alert("Hello World")

**files.json**:

.. code:: json

   [
     "__init__.py"
   ]

The ``files.json`` was simply generated using the by
``../flare/bin/gen-files-json.py``. Whenever a Python file is added,
this must be done once. The ``files.json`` should also be added to
version control, to make the app run out-of-the-box.
