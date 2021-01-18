"""
Flare configuration.
"""
from .html5 import core
from .safeeval import SafeEval

from typing import Dict

def updateConf(other: Dict):
	"""
	Merges other into conf
	"""

	global conf
	conf.update(other)
	return conf


# Main config
conf = {
	"basePathSvgs": "/static/svgs",
	"currentLanguage": "de",
}

# Assign SafeEval as htmlExpressionEvaluator
core.htmlExpressionEvaluator = SafeEval()

# Merge view_conf into main config
from flare.views import conf as view_conf
updateConf(view_conf)
