"""WARNING! THIS SCRIPTS ARE USED IN A SANDBOX SO ALL DEPENDENCIES SHOULD BE HANDELED HERE!

	 THIS USES PYODIDE V0.17!
"""
from js import self as web_self


class weblog():
    @staticmethod
    def info( text ):
        if not isinstance( text, str ):
            text = str( text )
        web_self.postMessage( type = "info", text = text )

    @staticmethod
    def warn( text ):
        if not isinstance( text, str ):
            text = str( text )
        web_self.postMessage( type = "warn", text = text )

    @staticmethod
    def error( text ):
        if not isinstance( text, str ):
            text = str( text )
        web_self.postMessage( type = "error", text = text )


log = weblog()  # shortcut to use log.info ...
