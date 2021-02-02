import logging
import os,site,importlib, inspect
from flare.config import conf
from flare.views.view import View

sitepackagespath = site.getsitepackages()[0]

def generateView( view:View, moduleName, actionName, name = None, data = () ):
	instView = view()
	instView.params = {
		"moduleName":moduleName,
		"actionName":actionName,
		"data":data
	}

	if name:
		instView.name = name
	else:
		instView.name = moduleName + actionName

	return instView

def addView(view:View,name=None):
	'''
		add a View and make it available
	'''
	logging.debug("addView: %r, %r", view, name)
	instView = view()

	if not name:
		name = instView.name

	conf["views_registered"].update({name:instView})

def updateDefaultView(name):
	conf[ "views_default" ] = name

def removeView(name,targetView=None):
	#try:
	del conf[ "views_registered" ][name]
	if not targetView:
		targetView = conf["views_default"]

	conf[ "views_state" ].updateState( "activeView", targetView ) #switch to default View
	#except:pass


def registerViews(path):
	'''
		add all Views in a folder

	'''
	rootModule = path.replace(sitepackagespath,"").replace("/",".")[1:]

	for viewFile in os.listdir(path):
		logging.debug("found  view_ %r", viewFile)

		if viewFile == "__init__.py" or not viewFile.endswith( ".py" ):
			continue

		viewFile = viewFile[:-3]

		if viewFile in conf["views_blacklist"]:
			continue

		try:
			_import = importlib.import_module("%s.%s"%(rootModule,viewFile))
			for _name in dir( _import ):
				if _name.startswith( "_" ):
					continue

				_symbol = getattr( _import, _name )
				if inspect.isclass(_symbol) and issubclass(_symbol,View) and _name != View.__name__:
					addView(_symbol)

		except Exception as err:
			logging.error( "Unable to import View from '%s'" % viewFile )
			logging.exception(err)
			raise

















