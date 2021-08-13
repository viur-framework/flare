from flare import html5, utils
import logging, re, typing


def displayString(display: str, value: typing.Dict, structure: typing.Dict, language: str = "de") -> [html5.Widget]:
    from flare.forms import boneSelector

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
                boneFactory = boneSelector.select(None, bone, partStructure)
                assert boneFactory, f"Couldn't find matching bone factory for bone '{bone}' in variable '$({var})'"

                widgets.append(boneFactory(None, bone, partStructure).viewWidget(partValue))
            else:
                partStructure = partBone

    if rest := display[start:]:
        widgets.append(html5.TextNode(rest))

    return widgets


def formatString(format: str, data: typing.Dict, structure=None, language=None):
    if "$(" in format:
        # Create a proposal for a new format string
        proposal = " + ".join([part for parts in map(
            lambda part: (f"'{part.group(1)}'", part.group(2), f"'{part.group(3)}'"),
            re.finditer(r"([^$()]*)\$\(([^)]+)\)([^$()]*)", format)) for part in parts if part != "''"]
        )

        format = format.replace("\"", "\\\"")
        proposal = proposal.replace("\"", "\\\"")

        raise ValueError(
            f"The formatString \"{format}\" is invalid in ViUR3 now. "
            f"Please change it to a Python-expression, like \"{proposal}\""
        )

    if not html5.core.htmlExpressionEvaluator:
        return format

    try:
        value = html5.core.htmlExpressionEvaluator.execute(format, data)
    except Exception as e:
        logging.exception(e)
        value = "(invalid format string)"

    return value
