# Changelog

This file documents any relevant changes.

## [1.0.7] - 2021-09-30
- Fix: interalEdit Forms no longer lose data 

## [1.0.6] - 2021-09-29
- Feat: listhandler now can emit finished status and locks running requests
- Feat: Forms - allow dict as BoneStructure
- Feat: Forms - relationalBone listhandler can now be filtered if the tag is used

## [1.0.5] - 2021-09-21
- Feat: added Icon Caching
- Feat: added SyncHandler
- Feat: hash getter und setter can now accept parameters
- Feat: direct FileUpload is now possible, use `"widget":"direct"` as parameter
- Feat: Update get-pyodide.py with configurable Version
- Fix: File and Folder names are displayed again
- Fix: Multiple SelectBones can be set to ReadOnly again

## [1.0.4] - 2021-09-20
- Feat: Update get-pyodide.py command-line parameters and version string check

## [1.0.3] - 2021-08-20
- Fix: updated relational style

## [1.0.2] - 2021-08-20
- Fix: edit widget for relational bone didn't work properly due unclosed <div>-tag

## [1.0.1] - 2021-08-19
- Fix: webworker now can be used with zipped application

## [1.0.0] - 2021-08-13
- Feat(**BREAKING**): unified buildscripts
- Feat: added alternative displayStrings for relations
- Feat: updated to Pyodide 0.18
- Feat: added debug popup (wip)
- Feat: pyodide webworker

## [development]
- Feat: html5 library
- Feat: ignite components
- Feat: views
- Feat: forms
- Feat: translations
- Feat: build scripts
- Feat: dockerfile
