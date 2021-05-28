#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This script walks about our app directory hierarchy and collects all _wanted_ and _needed_ python files.

This should work for all of Linux, MacOS and Windows and uses posix compliant path structure.
"""

import json
import os
from pathlib import Path

files = []

walkObj = os.walk(".")
for root, dirnames, filenames in walkObj:
    for f in filenames:
        pathObject = Path(root).joinpath(f)
        pathParts = pathObject.parts
        if (f.endswith(".py") and
                "(" not in f and
                not any([f.startswith(i) for i in ["get-", "gen-", "test-"]]) and
                "docs" not in pathParts and  # dont want flare/docs in files
                "examples" not in pathParts and  # dont want flare/examples in files
                "scripts" not in pathParts and  # dont want flare/scripts in files
                "test" not in pathParts and  # dont want flare/test in files
                "bin" not in pathParts  # dont want flare/bin in files
        ):
            f = pathObject.as_posix().rstrip("./")
            print(f)
            files.append(f)

with open("files.json", "w") as outputFile:
    json.dump(sorted(files), outputFile, indent=2)
    print("", file=outputFile)  # append line break
