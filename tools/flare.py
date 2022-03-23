#!/usr/bin/env python3
"""
flare application packager and build tool
"""

import os, shutil, json, argparse, pathlib, fnmatch, watchgod, python_minifier, compileall, tempfile

ignore_patterns = [
    "flare/assets/*",
    "flare/docs/*",
    "flare/examples/*",
    "flare/test/*",
    "flare/tools/*",
    "gen-*"
]


def copySourcePy(source, target):
    """Copy python source files to destination respecting the folder structure."""
    shutil.copytree(source, target, dirs_exist_ok=True)
    cleanSources(target)
    copyflareAssets(source, target)
    copypackageAssets(source, target)


def cleanSources(target):
    cwd = os.getcwd()
    absTarget = os.path.join(cwd, target)

    for folder in ["bin", "docs", "examples", "scripts", "test"]:
        target = os.path.join(absTarget, "flare", folder)
        if os.path.exists(target):
            shutil.rmtree(target)


def minifyPy(target):
    """Minifies all .py-files and strips comments and documentation."""
    for root, _, filenames in os.walk(target):
        for filename in filenames:
            filename = os.path.join(root, filename)

            if filename.endswith(".py"):
                with open(filename, "r+") as f:
                    code = f.read()
                    f.seek(0)
                    f.truncate()
                    f.write(python_minifier.minify(code, remove_literal_statements=True))

def compilePy(target):
    """Compiles py files to pyc and removes all py files at the end."""
    compileall.compile_dir(target, force=True, legacy=True, quiet=1)  # fixme: This does not work when local Python is 3.9.7 but Pyodide is 3.9.5...

    # Remove all source files from target folder
    for root, _, filenames in os.walk(target):
        for filename in filenames:
            filename = os.path.join(root, filename)

            if filename.endswith(".py"):
                os.remove(filename)

    # Update files.json
    generateFilesJson(target, ".pyc")


def zipPy(target, packagename):
    """Zips all files in target folder."""
    tmp = tempfile.mkdtemp()

    to_drop = [packagename]

    for entry in os.scandir(target):
        if entry.name == "flare":
            # special case... move flare/flare to just flare
            flare_tmp = tempfile.mkdtemp()
            shutil.move(os.path.join(target, "flare", "flare"), flare_tmp)
            shutil.rmtree(os.path.join(target, "flare"))
            shutil.move(os.path.join(flare_tmp, "flare"), target)
            to_drop.append("flare")
            continue
        elif entry.name == "packages":
            to_drop.append(entry.name)
            continue

        srcname = os.path.join(target, entry.name)
        dstname = os.path.join(tmp, entry.name)
        shutil.move(srcname, dstname)

    shutil.move(tmp, os.path.join(target, packagename))
    shutil.make_archive(os.path.join(target, "files"), "zip", target, verbose=True)

    for drop in to_drop:
        shutil.rmtree(os.path.join(target, drop))


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

    for i in os.listdir(source):
        if i.endswith((".html", ".js", ".webmanifest")):
            shutil.copyfile(os.path.join(source, i), os.path.join(target, i))


def copyflareAssets(source, target):
    flarefolder = os.path.join(source, "flare")
    if os.path.exists(flarefolder):
        shutil.copy(
            os.path.join(flarefolder, "flare", "files.json"),
            os.path.join(target, "flare", "flare", "files.json"),
        )

def copyWebworkerScripts(source, target):
    flarefolder = os.path.join( source, "flare", "flare", "webworker")
    if os.path.exists(flarefolder):
        shutil.copytree(
            flarefolder, os.path.join(target, "webworker"), dirs_exist_ok=True
        )

    appfolder = os.path.join(source, "webworker")
    if os.path.exists(appfolder):
        shutil.copytree(
            appfolder, os.path.join(target, "webworker"), dirs_exist_ok=True
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
    else:
        shutil.rmtree(target)


def generateFilesJson(source, ext=".py"):
    """Walks over the source app directory hierarchy and collects all _wanted_ and _needed_ python files.
    This should work for all of Linux, MacOS and Windows and uses posix compliant path structure.
    """
    files = []

    for root, _, filenames in os.walk(source):
        root = os.path.relpath(root, source)

        for filename in filenames:
            filename = str(os.path.join(root, filename)).removeprefix("./")

            if filename.endswith(ext) and not any([fnmatch.fnmatch(filename, pat) for pat in ignore_patterns]):
                files.append(filename)
                #print(files[-1])

    with open(os.path.join(source, "files.json"), "w") as outputFile:
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

    os.chdir(os.environ.get("PROJECT_WORKSPACE", "."))

    # Clear target first
    clearTarget(args.target)

    # Copy sources
    copySourcePy(args.source, args.target)

    if args.minify:
        # Minify copied sources
        minifyPy(args.target)

    if args.compile:
        # Turn PY into pre-compiled PYC files
        compilePy(args.target)
    else:
        # If this is not wanted, generate ordinary files.json
        generateFilesJson(args.target)

    if args.zip:
        # Compress target into zip archive
        zipPy(args.target, args.name)

    # Copy and handle webworker scripts separately
    copyWebworkerScripts(args.source, args.target)

    if args.minify:
        minifyPy(os.path.join(args.target, "webworker"))
    #if args.compile:
    #    compilePy(os.path.join(args.target,"webworker"))

    # Copy further assets
    copyAssets(args.source, args.target)

    if args.watch:
        print("watching for changes...")

        for changes in watchgod.watch(args.source, watcher_cls=watchgod.PythonWatcher):
            changes = list(changes)
            filename = os.path.relpath(changes[0][1], args.source)

            if any([fnmatch.fnmatch(filename, pat) for pat in ignore_patterns]):
                continue

            recreateFilesJson = False

            if changes[0][0] == watchgod.watcher.Change.added:
                print(f"{filename} added")
                recreateFilesJson = True
            elif changes[0][0] == watchgod.watcher.Change.deleted:
                print(f"{filename} deleted")
                recreateFilesJson = True
            else:
                print(f"{filename} modified")

            filepath = changes[0][1].replace(str(args.source) + "/", "")

            if not args.zip:
                if changes[0][0] == watchgod.watcher.Change.deleted:
                    os.remove(os.path.join(args.target, filepath))
                else:
                    # copy changed or added file
                    shutil.copy(changes[0][1], os.path.join(args.target, filepath))

                if recreateFilesJson:
                    shutil.copy(os.path.join(args.source, "files.json"), os.path.join(args.target, "files.json"))

            else:
                clearTarget(args.target)
                copySourcePy(args.source, args.target)

            if recreateFilesJson:
                print("regenerating files.json")
                generateFilesJson(args.target)

            if args.minify:
                minifyPy(args.target)

            if args.compile:
                compilePy(args.target)

            if args.zip:
                zipPy(args.target, args.name)
                copyAssets(args.source, args.target)


if __name__ == "__main__":
    main()
