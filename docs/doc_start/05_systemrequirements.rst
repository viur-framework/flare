============================
System requirements
============================

soon...


Serving own Pyodide
-------------------

The script ``bin/get-pyodide.py`` downloads a minimal Pyodide with only
``micropip`` and ``setuptools`` from the Pyodide CDN. Pyodide can also
be entirely built and configured on your own, for this check `the
documentation`_.

Depending on the location where you want to serve your app, some more
configuration might be necessary regarding the WASM mimetype.

Google App Engine
~~~~~~~~~~~~~~~~~

To serve your own Pyodide via Google App Engine, add the following lines
to your ``app.yaml`` file and modify them when needed, as Google App
Engine doesn’t recognize WASM files correctly.

.. code:: yaml

   handlers:
   - url: /pyodide/(.*\.wasm)$
     static_files: pyodide/\1
     upload: pyodide/.*\.wasm$
     mime_type: application/wasm
   - url: /pyodide
     static_dir: pyodide

Apache Webserver
~~~~~~~~~~~~~~~~

For apache web-server, this ``.htaccess`` configuration helped to serve
the app correctly.

::

   RewriteEngine off
   Options -ExecCGI +Indexes
   IndexOrderDefault Descending Date

   #Header always set Access-Control-Allow-Origin "*"
   #Header always set Access-Control-Allow-Methods GET

   <FilesMatch "\.py$">
       Options +Indexes -ExecCGI -Multiviews
       Order allow,deny
       Allow from all
       RemoveHandler .py
       AddType text/plain .py
   </FilesMatch>

   <FilesMatch "\.data$">
       Options +Indexes -ExecCGI -Multiviews
       Order allow,deny
       Allow from all
       RemoveHandler .data
       AddType application/octet-stream .data
   </FilesMatch>

   <FilesMatch "\.wasm$">
       Options +Indexes -ExecCGI -Multiviews
       Order allow,deny
       Allow from all
       RemoveHandler .wasm
       AddType application/wasm .wasm
   </FilesMatch>

.. _the documentation: https://pyodide.readthedocs.io/en/latest/building_from_sources.html
