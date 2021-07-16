========================================
Hello World
========================================

In this tutorial, we will create a basic project that makes use of flare to create a simple web-app.

Project setup
--------------------

In order to make flare accessible in your project, either download the flare master branch from github and extract it
into a ``flare`` subdirectory in your project, or - if you are using git - clone it into a git submodule of your
project by calling ``git submodule add git@github.com:viur-framework/flare.git``.

Once this is done, you can create an ``index.html`` file that will make use of the now available flare assets.

The HTML
--------------------

Basically all you need to do is add the flare CSS sheet and javascript file to your HTML file and you are good to go.

.. code:: html

	<link rel="stylesheet" href="flare/assets/css/style.css"/>
	<script src="flare/assets/js/flare.js"></script>

A simple ``index.html`` file that uses flare might now look like this:

.. code:: html

    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Hello World</title>
        <link rel="stylesheet" href="flare/assets/css/style.css"/>
        <script src="flare/assets/js/flare.js"></script>
        <script>
            window.addEventListener("load", () => {
                new flare({
                    fetch: {
                        "flare": {
                            "path": "flare/flare"
                        }
                    },
                    kickoff:
    `
    from flare import *
    flare.popup.Alert("Hello World")
    `
                });
            });
        </script>
    </head>
    <body class="is-loading">
    </body>
    </html>

Building from there
--------------------
The ``fetch`` block is where the flare python modules are being loaded at application start. It is advisable to add
your own python module structure fairly quickly.

1. Add a subdirectory ``helloworld`` next to your ``index.html``.
2. Add a file ``__init__.py``:

.. code:: python

    from . import helloworld

3. Add a file ``helloworld.py``:

.. code:: python

    from flare import *


    class HelloWorld(object):
        _message = None

        def __init__(self, message="Hello World"):
            self._message = message

        def show(self):
            popup.Alert(self._message)

4. Run the ``flare/bin/gen-files-json.py`` utility script in your module directory. This will generate a ``files.json``
file, that will look like this:

.. code:: json

    [
        "__init__.py",
        "helloworld.py"
    ]

5. Add a second block to the `fetch` in your index.html:

.. code:: html

    fetch: {
        "flare": {
            "path": "flare/flare"
        },
        "helloworld": {
            "path": "helloworld"
        }
    },

6. Change your kickoff script to run the code in your module, instead:

.. code:: python

    from helloworld import *
    helloworld.HelloWorld("Hello module world!").show()

Note that you do not need to maintain the ``files.json`` list of your module yourself. Whenever you add or remove
files from it, you can simply run the ``flare/bin/gen-files-json.py`` utility script in the modules directory to
regenerate it.
