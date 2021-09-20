#!/usr/bin/env python3
import os, sys, json, requests, argparse, pathlib

# Defaults
VERSION = "v0.18.1"
CDN = "https://cdn.jsdelivr.net/pyodide"
URL = "{CDN}/{VERSION}/full/{file}"
FILES = [
    "pyodide.asm.data",
    "pyodide.asm.js",
    "pyodide.asm.wasm",
    "pyodide.js"
]
PACKAGES = ["distlib", "distutils", "micropip", "packaging", "pyparsing", "setuptools"]

# Parse command line arguments
ap = argparse.ArgumentParser(description="Service program to obtain self-hosted, stripped copy of Pyodide from CDN")
ap.add_argument(
    "-v", "--pyodide", dest="version", default=VERSION, help="Pyodide version to download"
)
ap.add_argument("-p", "--packages", nargs="*", help="Further packages to download")
ap.add_argument("-t", "--target", type=pathlib.Path, default="pyodide", help="Target folder")
args = ap.parse_args()

assert any([args.version.startswith(accept) for accept in ["v0.18", "dev"]]), "Invalid version provided"

# Allow to install additional Pyodide pre-built packages by command-line arguments
packages = PACKAGES + (args.packages or [])

for package in packages:
    FILES.extend(
        [
            f"{package}.data",
            f"{package}.js",
        ]
    )

if not os.path.isdir(args.target):
    sys.stdout.write(f"Creating {args.target}/...")
    sys.stdout.flush()

    os.mkdir(args.target)
    print("Done")

print(f"Installing Pyodide {args.version}:")

for file in FILES:
    url = URL.format(file=file, CDN=CDN, VERSION=args.version)
    file = os.path.join(args.target, file)

    sys.stdout.write(f">>> {url}...")
    sys.stdout.flush()

    r = requests.get(url, stream=True)
    assert r.status_code == 200, f"Error retrieving {url}"

    with open(file, "wb") as f:
        for chunk in r.iter_content(2 * 1024):
            f.write(chunk)

    print("Done")

print(f"Done installing Pyodide {args.version}")

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

packages = requests.get(
    URL.format(file="packages.json", CDN=CDN, VERSION=args.version)
).json()

for k in list(packages["packages"].keys()):
    if k not in PACKAGES:
        del packages["packages"][k]

with open(file, "w") as f:
    f.write(json.dumps(packages))

print("Done")
