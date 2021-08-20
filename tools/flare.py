#!/usr/bin/env python3
"""
flare application packager and build tool
"""

import os, shutil, json, argparse, pathlib

PATHBLACKLIST = ["assets", "docs", "examples", "test", "tools"]


def cleanString(str):
    """Replace characters from string which could brake the commands.

    actual used to clean the environment workspace variable
    """
    return str.replace('"', "").replace("'", "")


def copySourcePy(source, target):
    """Copy python source files to destination respecting the folder structure."""
    cwd = os.getcwd()
    os.chdir(os.path.join(cwd, source))
    absTarget = os.path.join(cwd, target)

    os.system(f'find "." -name "*.py" -exec rsync -Rq \\{{\\}} "{absTarget}" \;')
    os.chdir(cwd)

    cleanSources(target)
    copyflareAssets(source, target)
    copypackageAssets(source, target)


def cleanSources(target):
    cwd = os.getcwd()
    absTarget = os.path.join(cwd, target)

    for folder in ["bin", "docs", "examples", "scripts", "test"]:
        target = os.path.join(absTarget, "flare", folder)
        os.system(f"rm -rf {target}")


def minifyPy(target):
    """Minifies oll py files and strips comments and documentation."""
    os.system(
        f'for py in `find {target} -name "*.py"`; do echo "Minifying ${{py}}..."; pyminify --remove-literal-statements ${{py}} > ${{py}}.min; mv ${{py}}.min ${{py}}; done'
    )


def compilePy(target):
    """Compiles py files to pyc and removes all py files at the end."""
    import compileall

    compileall.compile_dir(target, force=True, legacy=True)
    os.system(f'find "{target}" -name "*.py" -type f -delete')


def movingFlareBeforeZip(target, packagename):
    """If we deliver this app as zip and a flare submodule exists move it to the root directory."""
    cwd = os.getcwd()
    flareFolder = os.path.join(cwd, packagename, "flare")
    if os.path.exists(flareFolder):
        os.rename(flareFolder, flareFolder + "_")
        shutil.copytree(
            os.path.join(flareFolder + "_", "flare"), os.path.join(cwd, "flare")
        )
        shutil.rmtree(flareFolder + "_")


def movingPackagesBeforeZip(target, packagename):
    """If we deliver this app as zip and all files of the packages foldermusst be moved to the root directory."""
    cwd = os.getcwd()
    packagesFolder = os.path.join(cwd, packagename, "packages")
    if os.path.exists(packagesFolder):
        shutil.copytree(packagesFolder, cwd, dirs_exist_ok=True)
        shutil.rmtree(packagesFolder)


def zipPy(target, packagename):
    """Zips all files in target folder."""
    cwd = os.getcwd()
    targetpath = os.path.join(cwd, target)
    packagepath = os.path.join(targetpath, packagename)

    if not os.path.exists(packagepath):
        os.makedirs(packagepath)

    os.system(
        f'find {targetpath} -maxdepth 1 -not -name {packagename} -exec mv \\{{\\}} "{packagepath}" \;'
    )

    os.chdir(targetpath)  # switch to root folder

    movingFlareBeforeZip(target, packagename)
    movingPackagesBeforeZip(target, packagename)
    os.system("rm -f files.zip")  # remove old zip if exists
    os.system(f"zip files.zip -r ./*")  # zip this folder

    # remove everything thats not files.zip
    _ = [
        os.system(f"rm -rf {i}")
        for i in os.listdir(os.path.join(cwd, target))
        if i != "files.zip"
    ]

    os.chdir(cwd)  # switch back


def copyAssets(source, target):
    """Copy assets to targetfolder.

    if flare exists copy assets first, so that they can be replaced by project
    """
    flarefolder = os.path.join(source, "flare", "assets")
    if os.path.exists(flarefolder):
        shutil.copytree(
            flarefolder, os.path.join(target, "public", "flare"), dirs_exist_ok=True
        )

    assetfolder = os.path.join(source, "public")
    if os.path.exists(assetfolder):
        shutil.copytree(assetfolder, os.path.join(target, "public"), dirs_exist_ok=True)

    toplevelFiles = (".html", ".js", ".webmanifest", ".json")

    _ = [
        shutil.copyfile(os.path.join(source, i), os.path.join(target, i))
        for i in os.listdir(source)
        if i.endswith(toplevelFiles)
    ]


def copyflareAssets(source, target):
    flarefolder = os.path.join(source, "flare")
    if os.path.exists(flarefolder):
        shutil.copy(
            os.path.join(flarefolder, "flare", "files.json"),
            os.path.join(target, "flare", "flare", "files.json"),
        )

def copyWebworkerScripts(source, target):
    flarefolder = os.path.join( source, "flare", "flare", "webworker")
    if os.path.exists( flarefolder ):
        shutil.copytree(
            flarefolder, os.path.join( target, "webworker" ), dirs_exist_ok = True
        )

    appfolder = os.path.join(source, "webworker")
    if os.path.exists( appfolder ):
        shutil.copytree(
            appfolder, os.path.join( target, "webworker" ), dirs_exist_ok = True
        )



def copypackageAssets(source, target):
    packagesFolder = os.path.join(source, "packages")
    if os.path.exists(packagesFolder):
        shutil.copy(
            os.path.join(packagesFolder, "files.json"),
            os.path.join(target, "packages", "files.json"),
        )


def clearTarget(target):
    """Clear target folder."""
    if not os.path.exists(target):
        os.makedirs(target)
    os.system(f"rm -rf {target}/*")


def generateFilesJson(source):
    """Walks over the source app directory hierarchy and collects all _wanted_ and _needed_ python files.
    This should work for all of Linux, MacOS and Windows and uses posix compliant path structure.
    """
    files = []

    walkObj = os.walk(source)
    for root, dirnames, filenames in walkObj:
        for f in filenames:
            pathObject = pathlib.Path(root).joinpath(f)
            pathParts = pathObject.parts
            if (
                f.endswith(".py")
                and "(" not in f
                and not any([f.startswith(i) for i in ["get-", "gen-", "test-"]])  # this might be unnecessary...
                and not any([p in PATHBLACKLIST for p in pathParts])  # ignore folders from blacklist
            ):
                f = pathObject.as_posix().rstrip("./")
                #print(f)
                files.append(f)

    with open("files.json", "w") as outputFile:
        json.dump(sorted(files), outputFile, indent=2)
        print("", file=outputFile)  # append line break


def main():
    # parse command-line arguments
    ap = argparse.ArgumentParser(
        description="Flare application packager and build tool"
    )

    ap.add_argument("-s", "--source", required=True, type=pathlib.Path,
                    help="Path to source folder of the flare application")
    ap.add_argument("-t", "--target", required=True, type=pathlib.Path,
                    help="Path to output folder of the packaged flare application")

    ap.add_argument("-n", "--name", type=str, help="Name of the target package", default="app")
    ap.add_argument("-m", "--minify", help="Minify source by removing docstrings", action="store_true", default=False)
    ap.add_argument("-c", "--compile", help="Compile into pre-compiled .PYC-files", action="store_true", default=False)
    ap.add_argument("-z", "--zip", help="Create zipped package to decreased number of download requests",
                    action="store_true", default=False)
    ap.add_argument("-w", "--watch", help="Run in watch mode, re-compile target on any changes in source",
                    action="store_true", default=False)

    args = ap.parse_args()

    if args.source == args.target:
        raise ValueError("You may not set source and target to the same directories")

    if args.watch:
        print("starting initial build")

    os.chdir(cleanString(os.environ.get("PROJECT_WORKSPACE", ".")))

    clearTarget(args.target)
    copySourcePy(args.source, args.target)

    if args.minify:
        minifyPy(args.target)

    if args.compile:
        compilePy(args.target)

    if args.zip:
        zipPy(args.target, args.name)

    copyWebworkerScripts(args.source, args.target)
    if args.minify:
        minifyPy(os.path.join(args.target,"webworker"))
    #if args.compile:
    #    compilePy(os.path.join(args.target,"webworker"))

    copyAssets(args.source, args.target)

    if args.watch:
        print("watching for changes...")

        from watchgod import watch, PythonWatcher
        from watchgod.watcher import Change

        for changes in watch(args.source, watcher_cls=PythonWatcher):
            changes = list(changes)

            # dont copy py files from blacklisted folders
            if any(map(changes[0][1].__contains__, [f"/{p}/" for p in PATHBLACKLIST])):
                continue

            recreateFilesJson = False

            if changes[0][0] == Change.added:
                print(f"{changes[0][1]} added")
                recreateFilesJson = True
            elif changes[0][0] == Change.deleted:
                print(f"{changes[0][1]} deleted")
                recreateFilesJson = True
            else:
                print(f"{changes[0][1]} modified")

            if recreateFilesJson:
                print("regenerating files.json")
                generateFilesJson(args.source)

            filepath = changes[0][1].replace(str(args.source) + "/", "")

            if not args.zip:
                if changes[0][0] == Change.deleted:
                    os.remove(os.path.join(args.target, filepath))
                else:
                    # copy changed or added file
                    shutil.copy(changes[0][1], os.path.join(args.target, filepath))

                if recreateFilesJson:
                    shutil.copy(os.path.join(args.source, "files.json"), os.path.join(args.target, "files.json"))

            else:
                clearTarget(args.target)
                copySourcePy(args.source, args.target)

            if args.minify:
                minifyPy(args.target)

            if args.compile:
                compilePy(args.target)

            if args.zip:
                zipPy(args.target, args.name)
                copyAssets(args.source, args.target)


if __name__ == "__main__":
    main()
