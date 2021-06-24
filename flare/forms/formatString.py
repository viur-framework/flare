from flare.html5 import core

def formatString(format, data, structure=None, language=None):
    safeEval = core.htmlExpressionEvaluator
    try:
        ast = safeEval.compile(format)
    except:
        ast = safeEval.compile("value['name']")

    value = ""

    try:
        if isinstance(data, list):
            tmpList = []
            for v in data:
                try:
                    tmpList.append(safeEval.execute(ast, {
                        "value": v,
                        "structure": structure,
                        "language": language
                    }))
                except Exception as e:
                    tmpList.append("(invalid format string)")
            value = ", ".join(tmpList)

        elif isinstance(data, dict):
            try:
                value = safeEval.execute(ast, {
                    "value": data,
                    "structure": structure,
                    "language": language
                })
            except Exception as e:
                value = "(invalid format string)"

    except Exception as err:
        value = ""

    return value





