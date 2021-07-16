#!/usr/bin/env python3
"""
This helper script is used to simplify gulp build chains together with flare applications.
"""


import os, sys, json, getopt


def cleanString(str):
    return str.replace('"', "")


def setup(sourcefolder):
    projectWorkspace = cleanString(os.environ["PROJECT_WORKSPACE"])
    status = os.system(f'cd "{projectWorkspace}" && cd "{sourcefolder}" && npm install')
    if status > 0:
        sys.exit(3)


def runGulp(sourcefolder, taskname):
    projectWorkspace = cleanString(os.environ["PROJECT_WORKSPACE"])
    status = os.system(
        f'cd "{projectWorkspace}" && cd "{sourcefolder}" && npx gulp "{taskname}"'
    )
    if status > 0:
        sys.exit(3)


def main(argv):
    taskname = ""  # run default
    sourcefolder = "sources"

    try:
        opts, args = getopt.getopt(argv, "ht:s:", ["task=", "source="])
    except getopt.GetoptError:
        print("gulp.py -t taskname -s ./sources")
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("gulp.py -t taskname -s ./sources")
            sys.exit()
        elif opt in ("-s", "--source"):
            sourcefolder = arg
        elif opt in ("-t", "--task"):
            taskname = arg

    setup(sourcefolder)
    runGulp(sourcefolder, taskname)


if __name__ == "__main__":
    main(sys.argv[1:])
