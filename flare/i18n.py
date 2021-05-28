"""Internationalization tools to easily implement multi-language applications."""
import logging
from . import html5

_currentLanguage = None

if html5.jseval:
    _currentLanguage = html5.jseval("navigator.language")

    if not _currentLanguage:
        _currentLanguage = html5.jseval("navigator.browserLanguage")

if not _currentLanguage:
    _currentLanguage = "en"

if len(_currentLanguage) > 2:
    _currentLanguage = _currentLanguage[:2]

logging.debug("Configured for language: %s", _currentLanguage)

_runtimeTranslations = {}
_lngMap = {}


def buildTranslations(pathToFolder):
    import importlib

    translations = importlib.import_module(pathToFolder + ".translations")

    # Populate the lng table
    for key in dir(translations):
        if key.startswith("lng"):
            lang = key[3:].lower()
            if lang not in _lngMap:
                _lngMap[lang] = {}

            _lngMap[lang].update(
                {k.lower(): v for k, v in getattr(translations, key).items()}
            )

    return _lngMap


def translate(key, fallback=None, **kwargs):
    """Tries to translate the given string in the currently selected language.

    Supports replacing markers (using {markerName} syntax).

    :param key: The string to translate
    :param fallback: Return string when no translation is found.
    :returns: The translated string
    """

    def processTr(inStr, **kwargs):
        for k, v in kwargs.items():
            inStr = inStr.replace("{{%s}}" % k, str(v))

        return inStr

    if _currentLanguage in _runtimeTranslations.keys():
        if key.lower() in _runtimeTranslations[_currentLanguage].keys():
            return processTr(
                _runtimeTranslations[_currentLanguage][key.lower()], **kwargs
            )

    if _currentLanguage in _lngMap.keys():
        if key.lower() in _lngMap[_currentLanguage].keys():
            return processTr(_lngMap[_currentLanguage][key.lower()], **kwargs)

    if fallback is not None:
        return fallback

    logging.error("Translation for %r not found", key)
    return processTr(key, **kwargs)


def addTranslation(lang, a, b=None):
    """Adds or updates new translations."""
    if not lang in _runtimeTranslations.keys():
        _runtimeTranslations[lang] = {}
    if isinstance(a, str) and b is not None:
        updateDict = {a.lower(): b}
    elif isinstance(a, dict):
        updateDict = {k.lower(): v for k, v in a.items()}
    else:
        raise ValueError("Invalid call to addTranslation")
    _runtimeTranslations[lang].update(updateDict)


def setLanguage(lang):
    """Sets the current language to lang."""
    global _currentLanguage
    _currentLanguage = lang


def getLanguage():
    """Returns the current language."""
    global _currentLanguage
    return _currentLanguage
