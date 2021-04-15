========================================
Url handling
========================================

Flare Applications are SPA (Single Page Applications) the navigation is done via the #-hash part of the url.
This part is treated by Flare like a normal url. The hash should have a form like this.

.. code-block::

	#/path/pathPart2../pathEnd?param1=value&param2=value

The following functions split the hash into the corresponding url components or reassemble them.


getUrlHashAsString
~~~~~~~~~~~~~~~~~~~~~~~~~
This function takes the hash of the url and splits it into args and kwargs.
The return value is a tuple of the args string and the kwargs string.
In most cases you want to use getUrlHashAsObject instead.

getUrlHashAsObject
~~~~~~~~~~~~~~~~~~~~~~~
Uses the return value of getUrlHashAsString and also creates a tuple consisting of args and kwargs.
But now the first value is a list and the second is a dictionary.


setUrlHash
~~~~~~~~~~~~~~~
This function takes the objects from getUrlHashAsObject and reassembles them into a valid hash and finally sets the new url.

.. code-block:: Python

	urlHash, urlParams = getUrlHashAsObject() #read hash
	urlParams.update({"key":"newValue"}) #modify
	setUrlHash(urlHash,urlParams) #write back


example
~~~~~~~~~~~~~~~

.. code-block:: Python

	# current URL:
	#  http://localhost:8080/app/app.html#/user/list?amount=99&status=10
	urlHash, urlParams = getUrlHashAsObject() #read hash
	print(urlHash,urlParams)
	#['user','list'] {"amount":"99","status":"10"}
	urlParams.update({"status":"5"}) # change query
	setUrlHash(urlHash,urlParams) #write back to Url
	# new URL:
	#  http://localhost:8080/app/app.html#/user/list?amount=99&status=5

