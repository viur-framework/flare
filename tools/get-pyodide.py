#!/usr/bin/env python3
import os, sys, json, requests

VERSION = "dev"
VERSION = "v0.18.0"  # comment this line out to obtain latest dev version
CDN = "https://cdn.jsdelivr.net/pyodide"
URL = "{CDN}/{VERSION}/full/{file}"
DIR = "pyodide"
FILES = [
    "pyodide.asm.data",
    "pyodide.asm.data.js",
    "pyodide.asm.js",
    "pyodide.asm.wasm",
    "pyodide.js"
]

# Allow to install additional Pyodide pre-built packages by command-line arguments
PACKAGES = ["distlib", "distutils", "micropip", "packaging", "pyparsing", "setuptools"] + sys.argv[1:]

for package in PACKAGES:
    FILES.extend(
        [
            f"{package}.data",
            f"{package}.js",
        ]
    )

if not os.path.isdir(DIR):
    sys.stdout.write(f"Creating {DIR}/...")
    sys.stdout.flush()

    os.mkdir(DIR)
    print("Done")

print(f"Installing Pyodide {VERSION}:")

for file in FILES:
    url = URL.format(file=file, CDN=CDN, VERSION=VERSION)
    file = os.path.join(DIR, file)

    sys.stdout.write(f">>> {url}...")
    sys.stdout.flush()

    r = requests.get(url, stream=True)
    with open(file, "wb") as f:
        for chunk in r.iter_content(2 * 1024):
            f.write(chunk)

    print("Done")

print(f"Done installing Pyodide {VERSION}")

# Patch pyodide.js to only use "/pyodide/"
file = os.path.join(DIR, "pyodide.js")
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
file = os.path.join(DIR, "packages.json")
sys.stdout.write(f"Rewriting {file}...")
sys.stdout.flush()

packages = requests.get(
    URL.format(file="packages.json", CDN=CDN, VERSION=VERSION)
).json()

for k in list(packages["packages"].keys()):
    if k not in PACKAGES:
        del packages["packages"][k]

with open(file, "w") as f:
    f.write(json.dumps(packages))

print("Done")
