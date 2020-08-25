"""
Flare configuration.
"""
from .html5.safeeval import SafeEval
from .cache import Cache

conf = {
	"cache": Cache(),
	#"icons.pool": {},
	"safeEvalInstance": SafeEval(),
	"saveEvalAllowedCallables": dict()
}
