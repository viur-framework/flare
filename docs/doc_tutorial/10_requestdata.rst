========================================
Request JSON data
========================================

In this tutorial, we will use flares API to load some JSON data from an API and process it.

Project setup
--------------------

Please refer to the "Hello World" tutorial on how to set up a basic project with flare.

Using HTTPRequest
--------------------

Flare comes with a high level API to request data. The ``flare.network`` module contains a class ``HTTPRequest``, whose
constructor takes six parameters:

1. ``method``: The HTTP method to use for the request (i.e. ``GET``, ``POST``, ...)
2. ``url``: The URL to request
3. ``callbackSuccess`` (optional): A reference to the function which is to be called when the request succeeds (takes a response parameter)
4. ``callbackFailure`` (optional): A reference to the function which is to be called when the request fails (take the parameters responseText and status)
5. ``payload`` (optional): The body of the request, if one is to be sent
6. ``content_type`` (optional): A value for a ``Content-Type`` header (e.g. ``application/json``)

Using this constructor immediately sends the request.

Handling the response
--------------------

In order to parse a JSON response in a success callback, simply use the default ``json`` functionality:

.. code:: python

    def successCallback(result):
        data = json.loads(result)

This will simply turn the response into the appropriate native structure, based on what kind of JSON has been returned:

* Objects will be turned into ``dict``
* Arrays will be turned into ``list``
* ``null`` will be turned into ``None``
* atomar values will be turned into their respective python counterpart

Example
--------------------

As an example, we will request the current time of the time zone ``Europe/Berlin`` from a public API, then display
it in a popup.

.. code:: html

    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Fetching data</title>
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
    import json
    import logging
    from flare import *
    from flare.network import HTTPRequest

    def _successCallback(result):
        data = json.loads(result)
        flare.popup.Alert(data["datetime"])

    def _failureCallback(responseText, status):
        logging.error("Failure: %s %d", responseText, status)

    HTTPRequest(
        "GET",
        "http://worldtimeapi.org/api/timezone/Europe/Berlin",
        _successCallback,
        _failureCallback
    )
    `
                });
            });
        </script>
    </head>
    <body class="is-loading">
    </body>
    </html>

