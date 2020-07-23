from flare.i18n import translate
from flare.event import EventDispatcher

conf = {
	# Global holder to the currently logged-in user
	"currentUser": None,

	# A value displayed as "empty value"
	"emptyValue": translate("-"),

	# Language settings
	"currentLanguage": "de",
	# Vi version number
	"vi.version": (3, 0, 0),

	# Appendix to version
	"vi.version.appendix": "dev",

	# ViUR core name
	"vi.viur": "ViUR-core",

	# ViUR vi name
	"vi.name": "ViUR-vi",

	# Title delimiter
	"vi.title.delimiter": " - ",

	# Which access rights are required to open the Vi?
	"vi.access.rights": ["admin", "root"],

	# Context access variable prefix
	"vi.context.prefix": "",

	# Context action title fields
	"vi.context.title.bones": ["name"],

	# Global holder to main configuration taken from the server
	"mainConfig": None,

	# Global holder to main admin window
	"mainWindow": None,

	# Exposed server configuration
	"server": {},

	# ViUR server version number
	"core.version": None,

	# Modules list
	"modules": {"_tasks": {"handler": "singleton", "name": "Tasks"}},

	# Callable tasks
	"tasks": {"server": [], "client": []},

	# Language settings
	"defaultLanguage": "de",



	# Event dispatcher for initial startup Hash
	"initialHashEvent": EventDispatcher("initialHash"),

	# Actions in the top level bar
    "toplevelactions": ["log", "tasks", "userstate", "logout"],

	# Number of rows to fetch in list widgets
	"batchSize": 30,

	# Show bone names instead of description
	"showBoneNames": False,

	# Globally enable/disable dataset preview in lists
	"internalPreview": True,

	# Fallback default preview path template (if set None, adminInfo.preview only takes place)
	"defaultPreview": None,  # "/{{module}}/view/{{key}}"

	# Max number of entries to show in multiple Bones
	"maxMultiBoneEntries": 5,

	# Global ViUR Logics interpreter instance
	#"logics": Interpreter(),

	# Cached selector widgets on relationalBones for re-use
	"selectors": {},

	"updateParams": None,

	"cacheObj": {},
	"indexeddb":None
}