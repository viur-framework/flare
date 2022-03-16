from flare.icons import SvgIcon
from flare.i18n import translate
from flare import html5


def collectBoneErrors(errorList, currentKey, boneStructure):
    """Collect Errors from given errorList.

    severity:
        NotSet = 0
        InvalidatesOther = 1
        Empty = 2
        Invalid = 3
    """
    boneErrors = []

    for error in errorList or []:
        if error["fieldPath"] and error["fieldPath"][0] == currentKey:
            isError = False
            if (error["severity"] == 0 or error["severity"] == 2) and boneStructure["required"]:
                isError = True
            elif error["severity"] == 3:
                isError = True
            # ToDO Field dependency!

            if isError:
                thisError = error.copy()
                thisError["fieldPath"] = error["fieldPath"][1:]
                boneErrors.append(thisError)

    return boneErrors
