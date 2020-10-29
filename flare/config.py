"""
Flare configuration.
"""
from .html5.safeeval import SafeEval
from .cache import Cache
from flare.views import conf as view_conf

conf = {
	"cache": Cache(),
	#"icons.pool": {},
	"safeEvalInstance": SafeEval(),
	"saveEvalAllowedCallables": dict()
}

conf.update(view_conf)