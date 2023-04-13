from flare import html5, utils, conf
import logging, re, typing

# Choose your flavor; Because we don't have any real plan how to render values from RelationalBones and RecordBones
# correctly, you can choose from 3 technologies here... have fun.

def formatString(format: str, data: typing.Dict, structure=None, language=None):
    """Central entryPoint

    if string contains $( we use old formatstrings
    else we use evalStrings (core 3.0 draft)

    displayStrings actually only used in relations and records. This handler can be used with display param

    """
    if "$(" in format:
        if language is None:
            language = conf["flare.language.current"]

        return formatStringHandler(format, data, structure, language=language)

    return evalStringHandler(format, data, structure, language)


# formatString ---------------------------------------------------------------------------------------------------------
# This is a new handler for the old format-strings BUT in a reloaded version...

def formatStringHandler(
    format: str,
    value: typing.Dict,
    structure: typing.Dict,
    language: str = "de"
) -> str:

    # --- Helpers ---
    def listToDict(l):
        """Utility-function to convert an ordered dict-list into a dict"""
        if isinstance(l, list):
            return {k: v for k, v in l}

        assert isinstance(l, dict)
        return l

    # ---------------

    ret = ""
    start = 0
    for var in re.finditer(r"\$\(([^)]+)\)", format):
        # Create a text node from preding text
        if start < var.start():
            ret += format[start:var.start()]

        start = var.end()
        var = var.group(1)

        # Walk along the structure and value to find the bone
        parts = var.split(".")
        partStructure = listToDict(structure)
        partValue = value

        for bone in parts:
            # Handle empty part value and break
            if not partValue:
                ret += str(partValue)
                break

            partValue = partValue.get(bone)

            # Only for relationalbones...
            if bone in ["rel", "dest"]:
                if bone == "dest":
                    partStructure = listToDict(partStructure.get("relskel", {}))
                else:
                    partStructure = listToDict(partStructure.get("using", {}))

                continue

            partBone = listToDict(partStructure.get(bone, {}))
            if not partBone:
                raise ValueError(f"Access to unknown bone '{bone}' in variable '$({var})'")

            if bone is parts[-1]:
                # bone with further format setting
                if partFormat := partBone.get("format"):
                    if isinstance(partValue, list):
                        ret += ", ".join([
                            formatStringHandler(partFormat, v, partStructure.get(bone)) for v in partValue
                        ])
                    else:
                        ret += formatStringHandler(partFormat, partValue, partStructure.get(bone))

                # bone with language setting
                elif (partLanguages := partBone.get("languages")) and language in partLanguages:
                    # bone is a list
                    if isinstance(partValue, list):
                        ret += ", ".join([str(v.get(language, conf["emptyValue"])) for v in partValue])

                    # just the value
                    else:
                        ret += str(partValue.get(language, conf["emptyValue"]))

                # bone is a list
                elif isinstance(partValue, list):
                    ret += ", ".join([str(v) for v in partValue])

                # just the value
                else:
                    ret += str(partValue)
            else:
                partStructure = partBone

    if rest := format[start:]:
        ret += rest

    return ret


# displayString --------------------------------------------------------------------------------------------------------
# Display string is a new attempt for rendering format string values. It is a drop-in replacement.

def displayStringHandler(
    display: str,
    value: typing.Dict,
    structure: typing.Dict,
    language: str = "de"  # fixme: language not supported yet.
) -> [html5.Widget]:
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


# evalString -----------------------------------------------------------------------------------------------------------

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
