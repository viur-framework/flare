""" still WIP """
import inspect
from . import html5, popup
from flare.config import conf


def debug( element = None ):
    """Debug popup"""
    if not element:
        element = conf[ "app" ]

    elementEntry = debugElement( element )
    debugPopup = popup.Popup( "Debug" )
    debugPopup[ "style" ][ "width" ] = "90%"
    debugPopup.popupBody.appendChild( elementEntry )


def debugElement( element ):
    """recursive debug tree"""
    default = [ i for i in dir( html5.Div ) if not i.startswith( "_" ) ] + [ "element" ]
    aapp = [ i for i in dir( element ) if not i.startswith( "_" ) ]
    res = list( set( aapp ) ^ set( default ) )
    res.sort()

    ares = { }
    for i in res:
        obj = getattr( element, i )
        t = type( obj ).__name__
        itemRes = { "type": t }

        if t == "method":
            itemRes.update( { "params": inspect.getfullargspec( obj ) } )
        else:
            itemRes.update( { "value": obj } )
        ares.update( { i: itemRes } )

    elementPanel = html5.Div()
    tree = html5.Ul()
    tree.addClass( "is-list" )
    elementPanel.appendChild( tree )

    def loadChildAttribures( e, w ):
        optlist = html5.Ul()
        optlist.addClass( "is-list" )

        w.parent().insertAfter( optlist, w )
        for attrname, optdict in ares.items():
            if optdict[ "type" ] == "method":
                optlist.appendChild( f'''<li>{attrname}:{optdict[ "type" ]}({optdict[ "params" ]})</li>''' )
            else:
                optlist.appendChild( f'''<li>{attrname}:{optdict[ "type" ]}={optdict[ "value" ]}</li>''' )

    elementPanel.getAttrs = loadChildAttribures
    tree.appendChild( f'''<li ["name"]="currentObject"><a class="link" @click="getAttrs"><h2 class="headline">{element.__class__.__name__}</h2></a></li>''', bindTo = elementPanel )

    if element._children:
        elementPanel.childs = element._children

        def loadChildElements( e, w ):
            for c in elementPanel.childs:
                w.parent().appendChild( debugElement( c ) )

        elementPanel.getChilds = loadChildElements
        tree.appendChild( f'''<li><a class="link" @click="getChilds">childs</a></li>''', bindTo = elementPanel )
    return elementPanel
