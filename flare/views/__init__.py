from ..observable import StateHandler

conf = {
    "app": None,
    "views_blacklist": [],  # filename without .py ["ignoreThisView"]
    "views_default": None,  # name of fallback view
    "views_registered": {},  # all Views
    "views_state": StateHandler(["activeView"]),  # current active View
}
