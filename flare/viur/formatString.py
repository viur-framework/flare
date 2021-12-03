from flare import html5, utils
import logging, re, typing


def formatString(format: str, data: typing.Dict, structure=None, language=None):
    """Central entryPoint

    if string contains $( we use old formatstrings
    else we use evalStrings (core 3.0 draft)

    displayStrings actually only used in relations and records. This handler can be used with display param

    """
    if "$(" in format:
        return formatStringHandler(format, data, structure, language=language)
    return evalStringHandler(format, data, structure, language)


# formatString ---------------------------------------------------------------------------------------------------------
def formatOneEntry(key, format, data, structure=None, prefix=None, language=None, context=None, _rec=0):
    res = format
    val = data[key]

    # Get structure if available
    struct = structure.get(key) if structure else None
    if isinstance(struct, list):
        struct = {k: v for k, v in struct}

    if isinstance(val, dict):  # if bone is multilang, only render current lang
        if struct and ("$(%s)" % ".".join(prefix + [key])) in res:
            langs = struct.get("languages")
            if langs:
                if language and language in langs:
                    val = val.get(language, "")
                else:
                    val = ", ".join([str(value) for value in val.values()])

            else:
                return ""

        else:
            res = formatStringHandler(
                res, val, structure, prefix + [key], language, _rec=_rec + 1
            )

    elif isinstance(val, list) and len(val) > 0 and isinstance(val[0],
                                                               dict):  # if bone is relationalbone with rel and dest
        if struct and "dest" in val[0] and "rel" in val[0]:
            if "relskel" in struct and "format" in struct:
                format = struct["format"]
                struct = struct["relskel"]

            res = res.replace(
                "$(%s)" % ".".join(prefix + [key]),
                ", ".join(
                    [
                        formatStringHandler(format, v, struct, [], language, _rec=_rec + 1)
                        for v in val
                    ]
                ),
            )
        else:
            res = formatStringHandler(
                res, val[0], struct, prefix + [key], language, _rec=_rec + 1
            )

    elif isinstance(val, list):  # list values like multistr
        val = ", ".join(map(str, val))

    # Check for select-bones
    if (
            isinstance(struct, dict) and "values" in struct and struct["values"]
    ):  # if selectbone translate key to value
        vals = struct["values"]

        if isinstance(vals, list):
            vals = {k: v for k, v in vals}

        # NO elif!
        if isinstance(vals, dict):
            if val in vals:
                val = vals[val]

    res = res.replace("$(%s)" % (".".join(prefix + [key])), str(val))
    return res


def formatStringHandler(format, data, structure=None, prefix=None, language=None, context=None, _rec=0):
    """Parses a string given by format and substitutes placeholders using values specified by data.
    The syntax for the placeholders is $(%s).
    Its possible to traverse to sub-dictionarys by using a dot as seperator.
    If data is a list, the result each element from this list applied to the given string; joined by ", ".
    Example:
    -------
        data = {"name": "Test","subdict": {"a":"1","b":"2"}}
        formatString = "Name: $(name), subdict.a: $(subdict.a)"
    Result:
    ------
    "Name: Test, subdict.a: 1"
    :param format: String containing the format.
    :type format: str
    :param data: Data applied to the format String
    :type data: list | dict
    :param structure: Parses along the structure of the given skeleton.
    :type structure: dict
    :return: The traversed string with the replaced values.
    :rtype: str
    """
    # print("FORMAT STRING", format, data, structure, prefix)
    if structure and isinstance(structure, list):
        structure = {k: v for k, v in structure}

    prefix = prefix or []
    res = format

    if isinstance(data, list):
        return ", ".join(
            [
                formatString(format, x, structure, prefix, language, _rec=_rec + 1)
                for x in data
            ]
        )

    elif isinstance(data, str):
        return data

    elif not data:
        return res

    for key in data.keys():
        res = formatOneEntry(key, res, data, structure, prefix, language, context, _rec)

    return res


# displayString ---------------------------------------------------------------------------------------------------------
def displayStringHandler(
        display: str,
        value: typing.Dict,
        structure: typing.Dict,
        language: str = "de") -> [html5.Widget]:
    from flare.viur import BoneSelector

    # --- Helpers ---
    def listToDict(l):
        """Utility-function to convert an ordered dict-list into a dict"""
        if isinstance(l, list):
            return {k: v for k, v in l}

        assert isinstance(l, dict)
        return l

    # ---------------

    widgets = []
    start = 0
    for var in re.finditer(r"\$\(([^)]+)\)", display):
        # Create a text node from preding text
        if start < var.start():
            widgets.append(html5.TextNode(display[start:var.start()]))

        start = var.end()
        var = var.group(1)

        # Walk along the structure and value to find the bone
        parts = var.split(".")
        partStructure = listToDict(structure)
        partValue = value

        for bone in parts:
            partValue = partValue.get(bone)

            # Only or relationalbones...
            if bone in ["rel", "dest"]:
                if bone == "dest":
                    partStructure = listToDict(partStructure.get("relskel", {}))
                else:
                    partStructure = listToDict(partStructure["using"])

                continue

            partBone = listToDict(partStructure.get(bone, {}))
            if not partBone:
                raise ValueError(f"Access to unknown bone '{bone}' in variable '$({var})'")

            if bone is parts[-1]:
                boneFactory = BoneSelector.select(None, bone, partStructure)
                assert boneFactory, f"Couldn't find matching bone factory for bone '{bone}' in variable '$({var})'"

                widgets.append(boneFactory(None, bone, partStructure).viewWidget(partValue))
            else:
                partStructure = partBone

    if rest := display[start:]:
        widgets.append(html5.TextNode(rest))

    return widgets


# evalString ---------------------------------------------------------------------------------------------------------
def evalStringHandler(format, data, structure, language):
    if not html5.core.htmlExpressionEvaluator:
        return format

    try:
        value = html5.core.htmlExpressionEvaluator.execute(
            format, {
                "value": data,
                "structure": structure,
                "language": language
            }
        )
    except Exception as e:
        logging.exception(e)
        value = "(invalid format string)"

    return value
