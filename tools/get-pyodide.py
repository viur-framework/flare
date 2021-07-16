#!/usr/bin/env python3
import os, sys, json, requests

VERSION = "0.17.0"
CDN = "https://cdn.jsdelivr.net/pyodide"
URL = "{CDN}/v{VERSION}/full/{file}"
DIR = "pyodide"
FILES = [
    "pyodide.asm.data",
    "pyodide.asm.data.js",
    "pyodide.asm.js",
    "pyodide.asm.wasm",
    "pyodide.js",
]

# Allow to install additional Pyodide pre-built packages by command-line arguments
PACKAGES = ["distlib", "micropip", "packaging", "pyparsing", "setuptools"] + sys.argv[
    1:
]
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

print(f"Installing Pyodide v{VERSION}:")

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

print(f"Done installing Pyodide v{VERSION}")

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

for part in ["dependencies", "import_name_to_package_name", "versions"]:
    for k in list(packages[part].keys()):
        if k not in PACKAGES:
            del packages[part][k]

with open(file, "w") as f:
    f.write(json.dumps(packages))

print("Done")
