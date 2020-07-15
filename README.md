# flare
Web-App development framework for Python

## About
*flare* is an app development framework for Python-based web-apps running on top of [Pyodide](https://github.com/iodide-project/pyodide) in the browser.

It has integrations to concepts with [ViUR](https://www.viur.dev/), an MVC-framework for the Google App Engine platform, but can also be used stand-alone.

Fire up the tiny [Hello World](https://raw.githack.com/mausbrand/flare/master/hello.html) live demo. More information can be found [in the documentation](https://mausbrand.github.io/flare/).

## History
*flare* is the result of a several years experience in writing web-apps in pure Python. Formerly compiled from Python into JavaScript using PyJS, it now entirely settles up on Pyodide. Additionally, *flare* serves as a toolbox for various projects and solutions developed at [Mausbrand Informationssysteme GmbH](https://www.mausbrand.de/en). 

## Pyodide
*flare* is designed to be used with [Pyodide](https://github.com/iodide-project/pyodide).

Pyodide is described as "The Python scientific stack, compiled to WebAssembly". Precisely speaking, Pyodide is the Python reference implementation ([cpython](https://github.com/python/cpython/)) that is compiled using [emscripten](https://github.com/emscripten-core/emscripten) and runs natively inside modern browsers as WebAssembly (WASM).

Pyodide combines this WASM-compiled Python interpreter with well-known, natively compiled Python-libraries, mostly used in scientific computing. Pure Python packages can also be integrated using the tool `micropip`, which is served together with Pyodide.

In combination with *flare*, we use Pyodide to quickly build modern web-apps entirely in pure Python. 

## License
Copyright (C) 2020 by Mausbrand Informationssysteme GmbH.

Mausbrand and ViUR are registered trademarks of Mausbrand Informationssysteme GmbH.

You may use, modify and distribute this software under the terms and conditions of the MIT license. See the file LICENSE provided within this package for more information.
