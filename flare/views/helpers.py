import os,site,importlib
from flare.config import conf
from flare.views.view import View

sitepackagespath = site.getsitepackages()[0]

def generateView(viewname):
	pass






def addView(view:View,name=None):
	'''
		add a View and make it available
	'''
	viewInst = view()

	if not name:
		name = viewInst.name

	conf["views_registered"].update({name:viewInst})

def registerViews(path):
	'''
		add all Views in a folder

	'''
	rootModule = path.replace(sitepackagespath,"").replace("/",".")[1:]

	for viewFile in os.listdir(path):

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

				if issubclass(_symbol,View) and _name != View.__name__:
					addView(_symbol)

		except:
			print( "Unable to import View from '%s'" % viewFile )
			raise

















