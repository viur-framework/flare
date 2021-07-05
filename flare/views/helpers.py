import logging
import os, site, importlib, inspect
from flare.config import conf
from flare.views.view import View

sitepackagespath = site.getsitepackages()[0]


def generateView(view: View, moduleName, actionName, name=None, data=()):
    instView = view()
    instView.params = {"moduleName": moduleName, "actionName": actionName, "data": data}

    if name:
        instView.name = name
    else:
        instView.name = moduleName + actionName

    return instView


def addView(view: View, name=None):
    """Add a View and make it available."""
    logging.debug("addView: %r, %r", view, name)
    instView = view()

    if not name:
        name = instView.name
    else:
        instView.name = name

    conf["views_registered"].update({name: instView})


def updateDefaultView(name):
    conf["views_default"] = name


def removeView(name, targetView=None):
    # try:
    del conf["views_registered"][name]
    if not targetView:
        targetView = conf["views_default"]

    conf["views_state"].updateState("activeView", targetView)  # switch to default View


# except:pass


def registerViews(root, path):
    """Add all Views in a folder."""
    rootpath = os.path.join(root, path)

    if root[1:].split("/")[0].endswith(".zip"):
        ### we need some rework here
        _paths = root[1:].split("/")
        if len(_paths) > 1:
            apath = os.path.join(*_paths[1:], path)
        else:
            apath = path

        import zipfile

        aZipfile = zipfile.ZipFile(_paths[0])

        viewList = zip_listdir(aZipfile, apath)

        rootModule = (
            rootpath[1:].replace(root[1:].split("/")[0], "").replace("/", ".")[1:]
        )
    else:
        viewList = os.listdir(rootpath)
        rootModule = rootpath.replace(sitepackagespath, "").replace("/", ".")[1:]

    for viewFile in viewList:
        logging.debug("found  view_ %r", viewFile)

        if viewFile == "__init__.py" or not (
            viewFile.endswith(".py") or viewFile.endswith(".pyc")
        ):
            continue

        viewFile = viewFile[:-3]
        if viewFile.endswith("."):
            viewFile = viewFile[:-1]

        if viewFile in conf["views_blacklist"]:
            continue

        try:
            _import = importlib.import_module("%s.%s" % (rootModule, viewFile))
            for _name in dir(_import):
                if _name.startswith("_"):
                    continue

                _symbol = getattr(_import, _name)
                if (
                    inspect.isclass(_symbol)
                    and issubclass(_symbol, View)
                    and _name != View.__name__
                ):
                    addView(_symbol)

        except Exception as err:
            logging.error("Unable to import View from '%s'" % viewFile)
            logging.exception(err)
            raise


def zip_listdir(zip_file, target_dir):
    file_names = zip_file.namelist()

    if not target_dir.endswith("/"):
        target_dir += "/"

    if target_dir == "/":
        target_dir = ""

    result = [
        file_name
        for file_name in file_names
        if file_name.startswith(target_dir) and not "/" in file_name[len(target_dir) :]
    ]
    result = [x.split("/")[-1] for x in result]
    result = filter(None, result)
    return result
