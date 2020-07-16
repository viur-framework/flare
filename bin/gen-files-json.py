#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, json

files = []

walkObj = os.walk(".")
for root, dirnames, filenames in walkObj:
	for f in filenames:
		if (f.endswith(".py")
			and not "(" in f
			and not any([f.startswith(i) for i in ["get-", "gen-", "test-"]])):

			f = os.path.join(root, f)[2:]
			files.append(f)
			print(f)

with open("files.json", "w") as f:
	json.dump(sorted(files), f, indent=2)

