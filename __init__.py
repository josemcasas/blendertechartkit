from . import prefs
from . import properties
from . import operators
from . import panels


def register():
    prefs.register()
    properties.register()
    operators.register()
    panels.register()


def unregister():
    panels.unregister()
    operators.unregister()
    properties.unregister()
    prefs.unregister()
