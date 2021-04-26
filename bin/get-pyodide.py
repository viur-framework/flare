#!/usr/bin/env python3
import os, sys, json, requests

VERSION = "0.17.0"
CDN = "https://cdn.jsdelivr.net/pyodide"
URL = "{CDN}/v{VERSION}/full/{file}"
DIR = "pyodide"
DISTFILES = [
	"distlib.data",
	"distlib.js",
	"micropip.data",
	"micropip.js",
	"pyodide.asm.data",
	"pyodide.asm.data.js",
	"pyodide.asm.js",
	"pyodide.asm.wasm",
	"pyodide.js",
	"setuptools.data",
	"setuptools.js"
]

# Allow to install additional Pyodide pre-built packages by command-line arguments
for additional in sys.argv[1:]:
	DISTFILES.extend([
		f"{additional}.data",
		f"{additional}.js",
	])

if not os.path.isdir(DIR):
	sys.stdout.write(f"Creating {DIR}/...")
	sys.stdout.flush()

	os.mkdir(DIR)
	print("Done")

print(f"Installing Pyodide v{VERSION}:")

for file in DISTFILES:
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

# Patch pyodide.js to only use "/pyodide/"
file = os.path.join(DIR, "pyodide.js")
sys.stdout.write(f"Patching {file}...")
sys.stdout.flush()

with open(file, "r") as f:
	content = f.read()

with open(file, "w") as f:
	f.write(content.replace(
		"config.indexURL || \"./\"",
		"config.indexURL || \"./pyodide/\""
	))

print("Done")

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
			"setuptools":"setuptools",
			"micropip": "micropip"
		}
	}))

print("Done")
