# -*- coding: utf-8 -*-

"""SVG abstraction layer integrations for HTML5."""

from . import core as html5


########################################################################################################################
# Attribute Collectors
########################################################################################################################


class _attrSvgViewBox(object):
    def _getViewbox(self):
        viewBox = self.element.viewBox
        try:
            return " ".join(
                [
                    str(x)
                    for x in [
                        viewBox.baseVal.x,
                        viewBox.baseVal.y,
                        viewBox.baseVal.width,
                        viewBox.baseVal.height,
                    ]
                ]
            )
        except:
            return ""

    def _setViewbox(self, val):
        self.element.setAttribute("viewBox", val)

    def _getPreserveaspectratio(self):
        return self.element.preserveAspectRatio

    def _setPreserveaspectratio(self, val):
        self.element.setAttribute("preserveAspectRatio", val)


class _attrSvgDimensions(object):
    def _getWidth(self):
        return self.element.width

    def _setWidth(self, val):
        self.element.setAttribute("width", val)

    def _getHeight(self):
        return self.element.height

    def _setHeight(self, val):
        self.element.setAttribute("height", val)

    def _getX(self):
        return self.element.x

    def _setX(self, val):
        self.element.setAttribute("x", val)

    def _getY(self):
        return self.element.y

    def _setY(self, val):
        self.element.setAttribute("y", val)

    def _getR(self):
        return self.element.r

    def _setR(self, val):
        self.element.setAttribute("r", val)

    def _getRx(self):
        return self.element.rx

    def _setRx(self, val):
        self.element.setAttribute("rx", val)

    def _getRy(self):
        return self.element.ry

    def _setRy(self, val):
        self.element.setAttribute("ry", val)

    def _getCx(self):
        return self.element.cx

    def _setCx(self, val):
        self.element.setAttribute("cx", val)

    def _getCy(self):
        return self.element.cy

    def _setCy(self, val):
        self.element.setAttribute("cy", val)


class _attrSvgPoints(object):
    """
    The SVGAnimatedPoints interface is used to reflect a ‘points’ attribute on a ‘polygon’ or ‘polyline’ element.
    It is mixed in to the SVGPolygonElement and SVGPolylineElement interfaces
    """

    def _getPoints(self):
        """
        returns SVGPointList object, see www.w3.org/TR/SVG2/shapes.html

        interface SVGPointList {

            readonly attribute unsigned long length;
            readonly attribute unsigned long numberOfItems;

            void clear();
            DOMPoint initialize(DOMPoint newItem);
            getter DOMPoint getItem(unsigned long index);
            DOMPoint insertItemBefore(DOMPoint newItem, unsigned long index);
            DOMPoint replaceItem(DOMPoint newItem, unsigned long index);
            DOMPoint removeItem(unsigned long index);
            DOMPoint appendItem(DOMPoint newItem);
            setter void (unsigned long index, DOMPoint newItem);
        };
        """
        return self.element.points

    def _setPoints(self, val):
        self.element.setAttribute("points", val)


class _attrSvgTwoPoints(object):

    def _getX1(self):
        return self.element.x1

    def _setX1(self, val):
        self.element.setAttribute("x1", val)

    def _getY1(self):
        return self.element.y1

    def _setY1(self, val):
        self.element.setAttribute("y1", val)

    def _getX2(self):
        return self.element.x2

    def _setX2(self, val):
        self.element.setAttribute("x2", val)

    def _getY2(self):
        return self.element.y2

    def _setY2(self, val):
        self.element.setAttribute("y2", val)


class _attrSvgTransform(object):
    def _getTransform(self):
        return self.element.transform

    def _setTransform(self, val):
        self.element.setAttribute("transform", val)


class _attrSvgXlink(object):
    def _getXlinkhref(self):
        return self.element.getAttribute("xlink:href")

    def _setXlinkhref(self, val):
        self.element.setAttribute("xlink:href", val)


class _attrSvgStyles(object):

    def __init__(self, *args, **kwargs):
        if 'fill' in kwargs:
            self._setFill(kwargs.pop('fill'))
        if 'fillopacity' in kwargs:
            self._setFillopacity(kwargs.pop('fillopacity'))
        if 'stroke' in kwargs:
            self._setStroke(kwargs.pop('stroke'))
        if 'strokeopacity' in kwargs:
            self._setStrokeopacity(kwargs.pop('strokeopacity'))
        if 'strokewidth' in kwargs:
            self._setStrokewidth(kwargs.pop('strokewidth'))
        if 'strokelinejoin' in kwargs:
            self._setStrokelinejoin(kwargs.pop('strokelinejoin'))
        if 'strokelinecap' in kwargs:
            self._setStrokelinecap(kwargs.pop('strokelinecap'))
        if 'strokedasharray' in kwargs:
            self._setStrokedasharray(kwargs.pop('strokedasharray'))
        super().__init__()

    def _getFill(self):
        return self.element.fill

    def _setFill(self, val):
        '''Set the fill color'''
        self.element.setAttribute("fill", val)

    def _getFillopacity(self):
        return self.element.getAttribute("fill-opacity")

    def _setFillopacity(self, val):
        self.element.setAttribute("fill-opacity", val)

    def _getStroke(self):
        return self.element.stroke

    def _setStroke(self, val):
        '''Set the stroke color'''
        self.element.setAttribute("stroke", val)

    def _getStrokeopacity(self):
        return self.element.getAttribute("stroke-opacity")

    def _setStrokeopacity(self, val):
        self.element.setAttribute("stroke-opacity", val)

    def _getStrokewidth(self):
        return self.element.getAttribute("stroke-width")

    def _setStrokewidth(self, val):
        self.element.setAttribute("stroke-width", val)

    def _getStrokelinecap(self):
        return self.element.getAttribute("stroke-linecap")

    def _setStrokelinecap(self, val):
        self.element.setAttribute("stroke-linecap", val)

    def _getStrokelinejoin(self):
        return self.element.getAttribute("stroke-linejoin")

    def _setStrokelinejoin(self, val):
        self.element.setAttribute("stroke-linejoin", val)

    def _getStrokedasharray(self):
        return self.element.getAttribute("stroke-dasharray")

    def _setStrokedasharray(self, val):
        self.element.setAttribute("stroke-dasharray", val)


########################################################################################################################
# SVG Widgets
########################################################################################################################


@html5.tag
class SvgWidget(html5.Widget):
    _namespace = "SVG"


@html5.tag
class Svg(SvgWidget, _attrSvgViewBox, _attrSvgDimensions, _attrSvgTransform):
    """
    From DOM's SvgSvgElement, following methods are inherited:
    - createSVGNumber
    - createSVGPoint
    - createSVGLength
    - createSVGAngle
    - createSVGMatrix
    - createSVGRect
    - createSVGTransform

    """
    _tagName = "svg"

    def _getVersion(self):
        return self.element.version

    def _setVersion(self, val):
        self.element.setAttribute("version", val)

    def _getXmlns(self):
        return self.element.xmlns

    def _setXmlns(self, val):
        self.element.setAttribute("xmlns", val)

    def createSVGNumber(self):
        return self.element.createSVGNumber()

    def createSVGPoint(self):
        return self.element.createSVGPoint()

    def createSVGLength(self):
        return self.element.createSVGLength()

    def createSVGAngle(self):
        return self.element.createSVGAngle()

    def createSVGMatrix(self):
        return self.element.createSVGMatrix()

    def createSVGRect(self):
        return self.element.createSVGRect()

    def createSVGTransform(self):
        return self.element.createSVGTransform()


@html5.tag
class SvgCircle(SvgWidget, _attrSvgTransform, _attrSvgDimensions, _attrSvgStyles):
    _tagName = "circle"

    def __init__(self, *args, **kwargs):
        SvgWidget.__init__(self, *args, **kwargs)
        _attrSvgStyles.__init__(self, *args, **kwargs)


@html5.tag
class SvgEllipse(SvgWidget, _attrSvgTransform, _attrSvgDimensions, _attrSvgStyles):
    _tagName = "ellipse"

    def __init__(self, *args, **kwargs):
        SvgWidget.__init__(self, *args, **kwargs)
        _attrSvgStyles.__init__(self, *args, **kwargs)


@html5.tag
class SvgG(SvgWidget, _attrSvgTransform, _attrSvgStyles):
    _tagName = "g"

    def __init__(self, *args, **kwargs):
        SvgWidget.__init__(self, *args, **kwargs)
        _attrSvgStyles.__init__(self, *args, **kwargs)

    def _getSvgTransform(self):
        return self.element.transform

    def _setSvgTransform(self, val):
        self.element.setAttribute("transform", val)


@html5.tag
class SvgImage(SvgWidget, _attrSvgViewBox, _attrSvgDimensions, _attrSvgTransform, _attrSvgXlink):
    _tagName = "image"


@html5.tag
class SvgLine(SvgWidget, _attrSvgTransform, _attrSvgTwoPoints, _attrSvgStyles):
    _tagName = "line"

    def __init__(self, *args, **kwargs):
        SvgWidget.__init__(self, *args, **kwargs)
        _attrSvgStyles.__init__(self, *args, **kwargs)


@html5.tag
class SvgPath(SvgWidget, _attrSvgTransform, _attrSvgStyles):
    _tagName = "path"

    def __init__(self, *args, **kwargs):
        SvgWidget.__init__(self, *args, **kwargs)
        _attrSvgStyles.__init__(self, *args, **kwargs)

    def _getD(self):
        return self.element.getAttribute("d")

    def _setD(self, val):
        self.element.setAttribute("d", val)

    def _getPathLength(self):
        return self.element.pathLength

    def _setPathLength(self, val):
        self.element.setAttribute("pathLength", val)


@html5.tag
class SvgPolygon(SvgWidget, _attrSvgTransform, _attrSvgPoints, _attrSvgStyles):
    """
    SvgWidget representing a "polygon" element in an SVG.
    """
    _tagName = "polygon"

    def __init__(self, *args, **kwargs):
        SvgWidget.__init__(self, *args, **kwargs)
        _attrSvgStyles.__init__(self, *args, **kwargs)


@html5.tag
class SvgPolyline(SvgWidget, _attrSvgTransform, _attrSvgPoints, _attrSvgStyles):
    _tagName = "polyline"

    def __init__(self, *args, **kwargs):
        SvgWidget.__init__(self, *args, **kwargs)
        _attrSvgStyles.__init__(self, *args, **kwargs)


@html5.tag
class SvgRect(SvgWidget, _attrSvgDimensions, _attrSvgTransform, _attrSvgStyles):
    _tagName = "rect"

    def __init__(self, *args, **kwargs):
        SvgWidget.__init__(self, *args, **kwargs)
        _attrSvgStyles.__init__(self, *args, **kwargs)


@html5.tag
class SvgText(SvgWidget, _attrSvgDimensions, _attrSvgTransform, _attrSvgStyles):
    _tagName = "text"

    def __init__(self, *args, **kwargs):
        txt = kwargs.pop('text', "")
        SvgWidget.__init__(self, *args, **kwargs)
        _attrSvgStyles.__init__(self, *args, **kwargs)
        self._setText(txt)

    def _getTextanchor(self):
        return self.element.getAttribute("text-anchor")

    def _setTextanchor(self, val):
        self.element.setAttribute("text-anchor", val)

    def _getFontfamily(self):
        return self.element.getAttribute("font-family")

    def _setFontfamily(self, val):
        self.element.setAttribute("font-family", val)

    def _getFontsize(self):
        return self.element.getAttribute("font-size")

    def _setFontsize(self, val):
        self.element.setAttribute("font-size", val)

    def _getText(self):
        return self.element.textContent

    def _setText(self, txt):
        self.element.textContent = txt

    def __str__(self):
        return self.element.textContent


""" later...

class SvgDefs(SvgWidget):
    _tagName = "defs"


class SvgClipPath(SvgWidget):
    _tagName = "clippath"


class SvgLinearGradient(SvgWidget, _attrSvgPoints):
    _tagName = "lineargradient"

    def _setGradientunits(self, value):
        self.element.gradientUnits = value

    def _getGradientunits(self):
        return self.element.gradientUnits

    def _setGradienttransform(self, value):
        self.element.gradientTransform = value

    def _getGradienttransform(self):
        return self.element.gradientTransform


class SvgStop(SvgWidget):
    _tagName = "stop"

    def _setOffset(self, value):
        self.element.offset = value

    def _getOffset(self):
        return self.element.offset

    def _setStopcolor(self, value):
        self.element.offset = value

    def _getStopcolor(self):
        return self.element.offset
"""
