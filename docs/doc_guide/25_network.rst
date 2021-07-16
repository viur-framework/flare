========================================
Network
========================================

The `network`-module contains some classes and functions that allow to communicate or work with other services.

Requesting data
------------------
The following classes are used to request data from another service.

HTTPRequest
~~~~~~~~~~~~
HTTPRequest is a tiny wrapper around the Javascript object XMLHttpRequest.
Only the OPENED (1) and DONE (4) statuses are used. In case of OPENED the payload is sent.
If it is a post request, a possibly existing content type header is also set.
Depending on the status, the success callback or the failure callback specified during instantiation is called.

.. code-block:: Python

	HTTPRequest("GET", url, mySuccessFunction, myFailureFunction)

This tiny wrapper is used by the NetworkService, which encapsulates some ViUR-related request types

NetworkService
~~~~~~~~~~~~~~~~
This function can be passed the following parameters in addition to the callback functions for success, failure and finished:

 - module (str): Name of the target ViUR Module or None
 - url (str): Path (relative to Module)
 - params (dict): Dictionary of key-values paired url parameters
 - modifies (bool): previously registered classes can be notified with a onDataChanged event
 - secure (bool): for this ViUR request is an skey need, so fetch it before the request
 - kickoff (bool): by default this value is true, but you can use it to wait before to start a request
 - group (requestGroup): use this to bundle multiple requests and get at the end a final callback

This could be a simple request to test on a ViUR System if a user is logged in

.. code-block:: Python

	NetworkService.request( "user", "view/self",
	                    successHandler=iamAlreadyLoggedInFunction,
	                    failureHandler=loginFunction)

Sometimes you need to do a bunch of requests with a callback at the end

.. code-block:: Python

	agroup = requestGroup( allRequestsSuccessFunction )

	for aKey in dbKeyListToDelete:
		NetworkService.request( amodule, "delete", { "key": aKey },
				secure = True, #in case of deletion ViUR needs an skey
				modifies = False, #avoids the onDataChanged event
				group=agroup,
				successHandler = singleItemSuccessFunction,
				failureHandler = singleItemFailureFunction )

requestGroup
~~~~~~~~~~~~~~~~
This class is used to execute several requests of the NetworkService one by one and finally call the callback specified during instantiation.
In this case, be sure to set kickoff to False.


Other useful functions
----------------------------
The following functions were often used in connection with data queries and were therefore placed here.

DeferredCall
~~~~~~~~~~~~~~~~~~
This is a wrapper around the setTimeout JavascriptObject.
After a delay time (default:25ms) the given function is called with the given parameters.
This function is called outside the surrounding application flow!
Two hidden parameters can be specified during initialization and will not be passed to the function:

 - _delay: modifies the Timeout delay
 - _callback: will be called after handling the deferred Funktion

.. code-block:: Python

	DeferredCall(doSomeStuffLaterFunction,
		anArgumentForMyFunction,
		_delay=1000,
		_callback=sayHelloWennFinishedFunction)

