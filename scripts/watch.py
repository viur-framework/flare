import os, sys, pathlib, shutil, argparse
try:
	from watchgod import watch, PythonWatcher
	from watchgod.watcher import Change
except:
	print("To use this watcher, watchgod musst be installed. use E.g. pip install watchgod")
	sys.exit()


PATHBLACKLIST = ["/docs/","/examples/","/bin/","/scripts/","/test/", "/assets/"]

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='watch a flare application and update py files on change')
	parser.add_argument('source', help='source path relativ to projectpath')
	parser.add_argument('target', help='target path relativ to projectpath')
	parser.add_argument("-n", "--name", help='application name', default="vi")
	args = parser.parse_args()

	sourcePath = args.source.strip("/") #'sources/viur-vi/vi'
	targetPath = args.target.strip("/") #'deploy/vi'
	applicationName = args.name


	PROJECT_WORKSPACE = os.environ.get("PROJECT_WORKSPACE", ".")
	os.chdir(PROJECT_WORKSPACE)

	# build on start with assets
	print("initial build... please wait")
	flareFolder = str(pathlib.Path(__file__).absolute()).split("/scripts")[0]
	os.system(f'python3 {flareFolder}/scripts/flare.py -t {PROJECT_WORKSPACE}/{targetPath} -s {PROJECT_WORKSPACE}/{sourcePath} -n {applicationName}')

	# only watch py files
	print(f"../watching")
	for changes in watch(os.path.join(PROJECT_WORKSPACE,sourcePath), watcher_cls=PythonWatcher):
		changes = list(changes)

		#dont copy py files from blacklisten folders
		if any(map(changes[0][1].__contains__,PATHBLACKLIST)):
			continue

		if changes[0][0] in [Change.added, Change.deleted]:
			print("remember to update files.json")
		else:
			print(f"update {changes[0][1]}")

		filepath = changes[0][1].replace(str(os.path.join(PROJECT_WORKSPACE,sourcePath)+"/"),"")

		if changes[0][0] == Change.deleted:
			os.remove(os.path.join(PROJECT_WORKSPACE,targetPath,filepath))
		else:
			#copy changed or added file
			shutil.copy(changes[0][1], os.path.join(PROJECT_WORKSPACE,targetPath,filepath))

