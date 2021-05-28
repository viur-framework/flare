import os, sys, json, requests, getopt

VERSION = "0.16.1"
CDN = "https://pyodide-cdn2.iodide.io"
URL = "{CDN}/v{VERSION}/full/{file}"
DIR = "deploy/pyodide"


def downloadPyodide():
    print(DIR)

    if not os.path.isdir(DIR):
        sys.stdout.write(f"Creating {DIR}/...")
        sys.stdout.flush()

        os.makedirs(DIR)
        print("Done")

    print(f"Installing Pyodide v{VERSION}:")

    for file in [
        "console.html",
        "distlib.data",
        "distlib.js",
        "micropip.data",
        "micropip.js",
        "pyodide.asm.data",
        "pyodide.asm.data.js",
        "pyodide.asm.js",
        "pyodide.asm.wasm",
        "pyodide.js",
        "renderedhtml.css",
        "setuptools.data",
        "setuptools.js"
    ]:
        url = URL.format(file=file, CDN=CDN, VERSION=VERSION)
        file = os.path.join(DIR, file)

        sys.stdout.write(f">>> {url}...")
        sys.stdout.flush()

        r = requests.get(url, stream=True)
        with open(file, 'wb') as f:
            for chunk in r.iter_content(2 * 1024):
                f.write(chunk)

        print("Done")

    print(f"Done installing Pyodide v{VERSION}!")


def patchPyodideJs():
    # Patch pyodide.js to only use "/pyodide/"
    file = os.path.join(DIR, "pyodide.js")
    sys.stdout.write(f"Patching {file}...")
    sys.stdout.flush()

    with open(file, "r") as f:
        content = f.read()

    with open(file, "w") as f:
        f.write(content.replace(
            """var baseURL = self.languagePluginUrl """,
            """var baseURL = "/pyodide/" """
        ))

    print("Done")


def minimalPackageJson():
    # Write a minimal packages.json with micropip, setuptools and distlibs pre-installed.
    file = os.path.join(DIR, "packages.json")
    sys.stdout.write(f"Patching {file}...")
    sys.stdout.flush()

    with open(file, "w") as f:
        f.write(json.dumps({
            "dependencies": {
                "micropip": ["distlib"],
                "distlib": [],
                "setuptools": []
            },
            "import_name_to_package_name": {
                "distlib": "distlib",
                "setuptools": "setuptools",
                "micropip": "micropip"
            }
        }))

    print("Done")


def main(argv):
    global DIR, VERSION

    try:
        opts, args = getopt.getopt(argv, "hv:t:", ["version=", "target="])
    except getopt.GetoptError:
        print('get-pyodide.py -t /myfolder -v 0.16.1')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('get-pyodide.py -t /myfolder -v 0.16.1')
            sys.exit()
        elif opt in ("-v", "--version"):
            VERSION = arg
        elif opt in ("-t", "--target"):
            DIR = arg

    downloadPyodide()
    patchPyodideJs()
    minimalPackageJson()


if __name__ == "__main__":
    main(sys.argv[1:])
