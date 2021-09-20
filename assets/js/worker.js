// webworker.js

// THIS IS THE DEFAULT PYODIDE WEBWORKER
importScripts("https://cdn.jsdelivr.net/pyodide/v0.18.1/full/pyodide.js");

async function loadScripts(scriptPath="../../../webworker/",file="webworker_scripts.py") {
    let promises = [];
    let path = ("/lib/python3.9/site-packages/scripts/" + file).split("/")

    promises.push(
        new Promise((resolve, reject) => {
            fetch(scriptPath+file, {}).then((response) => {
                if (response.status === 200) {
                    response.text().then((code) => {
                        let lookup = "";
                        for (let i in path) {
                            if (!path[i]) {
                                continue;
                            }

                            lookup += (lookup ? "/" : "") + path[i];
                            if (parseInt(i) === path.length - 1) {
                                self.pyodide._module.FS.writeFile(lookup, code);
                            } else {
                                try {
                                    self.pyodide._module.FS.lookupPath(lookup);
                                } catch {
                                    self.pyodide._module.FS.mkdir(lookup);
                                }
                            }
                        }
                        resolve();
                    });
                } else {
                    reject();
                }
            })
        })
    )
    return Promise.all(promises);
}


async function loadPyodideAndPackages() {
    self.pyodide = await loadPyodide({indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.18.1/full/'});
}

let pyodideReadyPromise = loadPyodideAndPackages();

self.onmessage = async (event) => {
    await pyodideReadyPromise;

    const {python, ...context} = event.data;


    let scriptsPath = "../../../webworker/"
    if ("scriptPath" in context){
        scriptsPath = context["scriptPath"]
    }

    const isCompiled = await (await fetch(scriptsPath+"webworker_scripts.pyc"))
    console.log("---")
    console.log(isCompiled)
	console.log(scriptsPath)

    let scriptFile = "webworker_scripts.py"
    if (isCompiled.status === 200){
        scriptFile = "webworker_scripts.pyc"
    }

    await loadScripts(scriptsPath,scriptFile);

    for (const key of Object.keys(context)) {
        self[key] = context[key];
    }

    try {
        self.postMessage({
            results: await self.pyodide.runPythonAsync(python)
        });
    } catch (error) {
        console.log(error.message)
        self.postMessage(
            {error: error.message}
        );
    }
}
