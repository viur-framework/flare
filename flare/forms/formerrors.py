from typing import List, Tuple
from flare.forms.bones.base import ReadFromClientErrorSeverity

def collectBoneErrors(errorList, currentKey):
	boneErrors = []
	for error in errorList:
		if error["fieldPath"] and error["fieldPath"][0] == currentKey:
			thisError = error.copy()
			thisError["fieldPath"] = error["fieldPath"][1:]
			boneErrors.append(thisError)
	return boneErrors

def checkErrors(bone) -> Tuple[bool, List[str]]:
	'''
		first return value is a shortcut to test if bone is valid or not
		second returns a list of fields which are invalid through this bone

	'''
	errors = bone["errors"]

	#no errors for this bone
	if not errors:
		return False, list()

	invalidatedFields = list()
	isInvalid = True

	for error in errors:
		if (
				(error["severity"] == ReadFromClientErrorSeverity.Empty and bone["required"]) or
				(error["severity"] == ReadFromClientErrorSeverity.InvalidatesOther)
		):
			if error["invalidatedFields"]:
				invalidatedFields.extend(error["invalidatedFields"])

	# We found only warnings
	if not invalidatedFields:
		return False, list()

	return isInvalid, invalidatedFields