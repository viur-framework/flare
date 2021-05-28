import os, sys, json, getopt, shutil


def cleanString(str):
    '''
     replace characters from string which could brake the commands.
     actual used to clean the environment workspace variable
    '''

    return str.replace('"', "").replace("'", "")


def copySourcePy(source, target):
    '''
        copy python source files to destination respecting the folder structure
    '''

    cwd = os.getcwd()
    os.chdir(os.path.join(cwd, source))
    absTarget = os.path.join(cwd, target)

    os.system(f'find "." -name "*.py" -exec cp --parents \\{{\\}} "{absTarget}" \;')
    os.chdir(cwd)

    cleanSources(target)
    copyflareAssets(source, target)


def cleanSources(target):
    cwd = os.getcwd()
    absTarget = os.path.join(cwd, target)

    for folder in ["bin", "docs", "examples", "scripts", "test"]:
        target = os.path.join(absTarget, "flare", folder)
        os.system(f'rm -rf {target}')


def minifyPy(target):
    '''
        minifies oll py files and strips comments and documentation
    '''
    os.system(
        f'for py in `find {target} -name "*.py"`; do echo "Minifying ${{py}}..."; pyminify --remove-literal-statements ${{py}} > ${{py}}.min; mv ${{py}}.min ${{py}}; done')


def compilePy(target):
    '''
        compiles py files to pyc and removes all py files at the end

    '''
    import compileall
    compileall.compile_dir(target, force=True, legacy=True)
    os.system(f'find "{target}" -name "*.py" -type f -delete')


def movingFlareBeforeZip(target, packagename):
    '''
        If we deliver this app as zip and a flare submodule exists
        move it to the root directory

    '''
    cwd = os.getcwd()
    flareFolder = os.path.join(cwd, packagename, "flare")
    if os.path.exists(flareFolder):
        os.rename(flareFolder, flareFolder + "_")
        shutil.copytree(os.path.join(flareFolder + "_", "flare"), os.path.join(cwd, "flare"))
        shutil.rmtree(flareFolder + "_")


def zipPy(target, packagename):
    '''
    zips all files in target folder
    '''
    cwd = os.getcwd()
    targetpath = os.path.join(cwd, target)
    packagepath = os.path.join(targetpath, packagename)

    if not os.path.exists(packagepath):
        os.makedirs(packagepath)

    os.system(f'find {targetpath} -maxdepth 1 -not -name {packagename} -exec mv -t {packagepath} {{}} +')

    os.chdir(targetpath)  # switch to root folder

    movingFlareBeforeZip(target, packagename)

    os.system("rm -f files.zip")  # remove old zip if exists
    os.system(f'zip files.zip -r ./*')  # zip this folder

    # remove everything thats not files.zip
    _ = [os.system(f'rm -rf {i}') for i in os.listdir(os.path.join(cwd, target)) if i != "files.zip"]

    os.chdir(cwd)  # switch back


def copyAssets(source, target):
    '''
        Copy assets to targetfolder
        if flare exists copy assets first, so that they can be replaced by project

    '''
    flarefolder = os.path.join(source, "flare", "assets")
    if os.path.exists(flarefolder):
        shutil.copytree(flarefolder, os.path.join(target, "public", "flare"), dirs_exist_ok=True)

    assetfolder = os.path.join(source, "public")
    if os.path.exists(assetfolder):
        shutil.copytree(assetfolder, os.path.join(target, "public"), dirs_exist_ok=True)

    toplevelFiles = (".html", ".js", ".webmanifest", ".json")

    _ = [shutil.copyfile(os.path.join(source, i), os.path.join(target, i)) for i in os.listdir(source) if
         i.endswith(toplevelFiles)]


def copyflareAssets(source, target):
    flarefolder = os.path.join(source, "flare")
    if os.path.exists(flarefolder):
        shutil.copy(os.path.join(flarefolder, "flare", "files.json"),
                    os.path.join(target, "flare", "flare", "files.json"))


def clearTarget(target):
    '''
        clear target folder
    '''
    if not os.path.exists(target):
        os.makedirs(target)
    os.system(f'rm -rf {target}/*')


def main(argv):
    packagename = "app"
    target = "/deploy/app"
    source = "/sources/app"
    minify = False
    compile = False
    zip = False

    projectWorkspace = cleanString(os.environ.get("PROJECT_WORKSPACE", "."))
    os.chdir(projectWorkspace)

    try:
        opts, args = getopt.getopt(argv, "ht:s:m:c:z:n:",
                                   ["target=", "source=", "minify=", "compile=", "zip=", "name="])
    except getopt.GetoptError:
        print('gulp.py -t taskname -s ./sources')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('gulp.py -t taskname -s ./sources')
            sys.exit()
        elif opt in ("-s", "--source"):
            source = os.path.realpath(arg)
        elif opt in ("-t", "--target"):
            target = os.path.realpath(arg)
        elif opt in ("-m", "--minify"):
            minify = False if arg == "false" else True
        elif opt in ("-c", "--compile"):
            compile = False if arg == "false" else True
        elif opt in ("-z", "--zip"):
            zip = False if arg == "false" else True
        elif opt in ("-n", "--name"):
            packagename = arg

    clearTarget(target)

    copySourcePy(source, target)

    if minify:
        minifyPy(target)

    if compile:
        compilePy(target)

    if zip:
        zipPy(target, packagename)

    copyAssets(source, target)


if __name__ == "__main__":
    main(sys.argv[1:])
