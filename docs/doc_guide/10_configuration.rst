========================================
Configuration
========================================

Flare is divided into different components, which have different complexity.
In addition to a flare config, the forms and views components have their own config.

Flare config
------------------------

Here are some default values configured.

 - flare.icon.svg.embedding.path
	- defines the basepath for the used svg icons.
 - flare.icon.fallback.error
	- defines the fallback icon name
 - flare.language.current
	- sets the current active language

The views config will be merged on top.

Bind App
----------
An app that uses flare often has its own config object.
Flare provides a bindApp function that, in addition to setting the app instance in the configuation, also allows overriding the flare configuration.
For example, you can change the default language in your app configuration and all Flare components will use that value instead of the default flare settings.

