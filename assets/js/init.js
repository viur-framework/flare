class init {

	constructor(config) {
		this.config = config
		window.languagePluginLoader.then(() => {
			let kickoff = config.kickoff || "";

			// Run prelude first
			window.pyodide.runPythonAsync(config.prelude || "").then(() => {

				// Then fetch sources and import modules
				this.fetchSources(config.fetch || {}).then(() => {
					for(let module of Object.keys(config.fetch || {}))
					{
						if(config.fetch[module].optional === true)  {
							kickoff = `try:\n\timport ${module}\nexcept:\n\tpass\n` + kickoff
						}
						else {
							kickoff = `import ${module}\n` + kickoff
						}
					}

					// Then, run kickoff code
					window.pyodide.runPythonAsync(kickoff).then(
						() => this.initializingComplete());
				});
			});
		});
	}

	loadSources(module, baseURL, files) {
		let promises = [];
		let bar = null;
		let info = null;
		try{
			bar = document.getElementById("loadingbar")
			info = document.getElementById("fileinfo")
			bar.max += files.length
		}catch (e) {}

		for (let f in files) {

			promises.push(
				new Promise((resolve, reject) => {
					let file = files[f];
					let url = (baseURL ? baseURL + "/" : "") + file;

					fetch(url, {}).then((response) => {
						if (response.status === 200)
							return response.text().then((code) => {
								let path = ("/lib/python3.7/site-packages/" + module + "/" + file).split("/");
								let lookup = "";

								if (bar){
									bar.value +=1
									info.innerHTML = files[f]
								}

								for (let i in path) {
									if (!path[i]) {
										continue;
									}

									lookup += (lookup ? "/" : "") + path[i];
									if (parseInt(i) === path.length - 1) {
										window.pyodide._module.FS.writeFile(lookup, code);
										console.debug(`fetched ${lookup}`);
									} else {
										try {
											window.pyodide._module.FS.lookupPath(lookup);
										} catch {
											window.pyodide._module.FS.mkdir(lookup);
											console.debug(`created ${lookup}`);
										}
									}
								}

								resolve();
							});
						else
							reject();
					});
				})
			);
		}

		return Promise.all(promises);
	}

	fetchSources(modules) {
		let promises = [];

		for( let module of Object.keys(modules) )
		{
			promises.push(
				new Promise((resolve, reject) => {
					let mapfile = `${modules[module]["path"]}/files.json`;
					fetch(mapfile, {}).then((response) => {
						if (response.status === 200) {
							response.text().then((list) => {
								let files = [];

								try {
									files = JSON.parse(list);
								}
								catch (e) {
									if( modules[module]["optional"] ) {
										console.info(`Optional module ${module} wasn't found`);
										return resolve();
									}
									else {
										console.error(`Unable to parse ${mapfile} properly, check for correct config of ${module}`);
										return reject();
									}
								}

								this.loadSources(module, modules[module]["path"], files).then(() => {
									resolve();
								})
							})
						} else {
							if( modules[module]["optional"] ) {
								console.info(`Optional module ${module} wasn't found`);
								return resolve();
							}

							reject();
						}
					})
				}));
		}

		return Promise.all(promises).then(() => {
			try{
				let bar = document.getElementById("loadingbar")
				bar.max -= 1 //progressbar starts at 1
			}catch (e) {}

			for( let module of Object.keys(modules) ) {
				window.pyodide.loadedPackages[module] = "default channel";
			}

			window.pyodide.runPython(
				'import importlib as _importlib\n' +
				'_importlib.invalidate_caches()\n'
			);

			//wrapper
			let wrapper = document.getElementById("wrapper")
			wrapper.style.display="none"
			document.body.classList.add("is-loading")

		});
	}

	initializingComplete() {
		document.body.classList.remove("is-loading")
	}
}
