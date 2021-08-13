// webworker.js

// THIS IS THE DEFAULT PYODIDE WEBWORKER
importScripts("https://cdn.jsdelivr.net/pyodide/v0.18.0/full/pyodide.js");

async function loadScripts(scriptPath="../../../flare/flare/") {
    let promises = [];
    let url = "webworker_scripts.py"

    let path = ("/lib/python3.9/site-packages/scripts/" + url).split("/")

    promises.push(
        new Promise((resolve, reject) => {
            //default workerScriptPath = "/app/s/flare/flare"
            fetch(scriptPath+url, {}).then((response) => {
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
    self.pyodide = await loadPyodide({indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.18.0/full/'});
}

let pyodideReadyPromise = loadPyodideAndPackages();

self.onmessage = async (event) => {
    await pyodideReadyPromise;

    const {python, ...context} = event.data;
    if ("scriptPath" in context){
        await loadScripts(context["scriptPath"]);
    }else{
        await loadScripts();
    }

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
