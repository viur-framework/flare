#!/usr/bin/env python3
import io, os, sys, json, shutil, argparse, pathlib, zipfile
from urllib.request import urlopen

SUPPORTED=[
    # Full Pyodide releases
    "v0.19.0",
    # Current development version of the Pyodide standard
    "dev",
    # Pyodide-nano is shipped as a zip-file
    #"v0.18.0-nano",
    #"v0.18.1-nano",
]

# Defaults
VERSION = SUPPORTED[0]
CDN = "https://cdn.jsdelivr.net/pyodide"
URL = "{CDN}/{VERSION}/full/{file}"
FILES = [
    "pyodide.asm.data",
    "pyodide.asm.js",
    "pyodide.asm.wasm",
    "pyodide.js",
    "pyodide_py.tar"
]
PACKAGES = [
    "distlib",
    "distutils",
    "micropip",
    "packaging",
    "pyparsing",
    "setuptools"
]

# Parse command line arguments
ap = argparse.ArgumentParser(
    description="Service program to obtain self-hosted, stripped copy of Pyodide from CDN"
)
ap.add_argument(
    "-v", "--pyodide", dest="version", default=VERSION, choices=SUPPORTED, help="Pyodide version to download"
)
ap.add_argument("-p", "--packages", nargs="*", help="Further packages to download")
ap.add_argument("-t", "--target", type=pathlib.Path, default="pyodide", help="Target folder")
args = ap.parse_args()

if is_nano := args.version.endswith("-nano"):
    PACKAGES = []

# Allow to install additional Pyodide pre-built packages by command-line arguments
PACKAGES += (args.packages or [])

if is_nano and PACKAGES:
    raise EnvironmentError("Pyodide-nano does not support additionaly packages currently!")

for package in PACKAGES:
    FILES.extend(
        [
            f"{package}.data",
            f"{package}.js",
        ]
    )

# Remove old target folder first
if os.path.dirname(args.target) not in [".", ".."] and os.path.isdir(args.target):
    sys.stdout.write(f"Removing {args.target}/...")
    sys.stdout.flush()

    shutil.rmtree(args.target)
    print("Done")

sys.stdout.write(f"Creating {args.target}/...")
sys.stdout.flush()

os.mkdir(args.target)

# Write version info
open(os.path.join(args.target, f"""{args.version}"""), "a").close()

print("Done")

print(f"Installing Pyodide {args.version}:")

if is_nano:
    # Pyodide Nano is just downloaded from a ZIP-File
    version = args.version.removeprefix("v").removesuffix("-nano")
    url = f"""https://github.com/phorward/pyodide/releases/download/{version}-nano/pyodide-nano-{version}.zip"""

    # Download ZIP-file into memory
    sys.stdout.write(f">>> {url}...")
    sys.stdout.flush()

    zip = urlopen(url).read()

    print("Done")

    # Unpack ZIP file from memory
    sys.stdout.write(f"Unpacking...")
    sys.stdout.flush()

    zip = zipfile.ZipFile(io.BytesIO(zip))
    zip.extractall(args.target)
    zip.close()

    print("Done")

    print(f"Done installing Pyodide {args.version}")
    sys.exit(0)

# Normal install of CDN version

for file in FILES:
    url = URL.format(file=file, CDN=CDN, VERSION=args.version)
    file = os.path.join(args.target, file)

    sys.stdout.write(f">>> {url}...")
    sys.stdout.flush()

    r = urlopen(url).read()

    with open(file, "wb") as f:
        f.write(r)

    print("Done")

# Patch pyodide.js to only use "/pyodide/"
file = os.path.join(args.target, "pyodide.js")
sys.stdout.write(f"Patching {file}...")
sys.stdout.flush()

with open(file, "r") as f:
    content = f.read()

with open(file, "w") as f:
    f.write(
        content.replace('config.indexURL || "./"', 'config.indexURL || "./pyodide/"')
    )

print("Done")

# Write a minimal packages.json with micropip, setuptools and distlibs pre-installed.
file = os.path.join(args.target, "packages.json")
sys.stdout.write(f"Rewriting {file}...")
sys.stdout.flush()

packages = json.loads(urlopen(URL.format(file="packages.json", CDN=CDN, VERSION=args.version)).read())

for k in list(packages["packages"].keys()):
    if k not in PACKAGES:
        del packages["packages"][k]

with open(file, "w") as f:
    f.write(json.dumps(packages))

print("Done")

print(f"Done installing Pyodide {args.version}")
