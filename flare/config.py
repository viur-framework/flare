"""
Flare configuration.
"""
from .html5.safeeval import SafeEval

from flare.views import conf as view_conf

conf = {
	"safeEvalInstance": SafeEval(),
	"saveEvalAllowedCallables": dict(),
	"basePathSvgs":"/static/svgs",
	"currentLanguage": "de",
}

conf.update(view_conf)

def updateConf(_conf):
	global conf
	conf.update(_conf)
	return conf



