# Flare
![Flare Logo](assets/img/flare-logo.webp)
[![Documentation Status](https://readthedocs.org/projects/viur-flare/badge/?version=latest)](https://viur-flare.readthedocs.io/en/latest/?badge=latest)

Flare is an application development framework for writing software frontends in pure Python.

## About
Flare is an app development framework for Python-based web-apps running on top of [Pyodide](https://github.com/pyodide/pyodide) in the browser.

It has integrations to concepts with [ViUR](https://www.viur.dev/), an MVC-framework for the Google App Engine platform, but can also be used stand-alone.

Fire up the tiny [Hello World](https://raw.githack.com/viur-framework/flare/main/hello.html) live demo. More information can be found [in the documentation](https://readthedocs.org/projects/viur-flare/badge/?version=latest).

## History
Flare is the result of a several years experience in writing web-apps in pure Python. Formerly compiled from Python to JavaScript using [PyJS](https://github.com/pyjs/pyjs), it now entirely settles up on Pyodide. Additionally, Flare serves as a toolbox for various projects and solutions developed at [Mausbrand Informationssysteme GmbH](https://www.mausbrand.de/en), a software-company from Dortmund, Germany.

## Pyodide
Pyodide is the [CPython](https://github.com/python/cpython/) reference implementation that is compiled using [emscripten](https://github.com/emscripten-core/emscripten) and runs natively inside modern browsers as WebAssembly (WASM). Pyodide itself comes with the full Python scientific-stack.

For better load-time optimization, we started to maintain our own fork of Pyodide called [pyodide-nano](https://github.com/mausbrand/pyodide).

## Related projects
- [html5](https://github.com/viur-framework/viur-html5) became an integrated part of Flare, but also exists stand-alone as a HTML5-DOM-object library. It is the core component of Flare and provides an HTML-parser for rapid DOM prototyping.
- [pyodide-html](https://github.com/xhlulu/pyodide-html) is another HTML object library for Pyodide which can be directly installed from within Pyodide.

## License
Copyright © 2021 by Mausbrand Informationssysteme GmbH.

Mausbrand and ViUR are registered trademarks of Mausbrand Informationssysteme GmbH.

You may use, modify and distribute this software under the terms and conditions of the MIT license. See the file LICENSE provided within this package for more information.
