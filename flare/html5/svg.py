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
    def _getPoints(self):
        return self.element.points

    def _setPoints(self, val):
        self.element.setAttribute("points", val)

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
    def _getFill(self):
        return self.element.fill

    def _setFill(self, val):
        self.element.setAttribute("fill", val)

    def _getStroke(self):
        return self.element.stroke

    def _setStroke(self, val):
        self.element.setAttribute("stroke", val)


########################################################################################################################
# SVG Widgets
########################################################################################################################


@html5.tag
class SvgWidget(html5.Widget):
    _namespace = "SVG"


@html5.tag
class Svg(SvgWidget, _attrSvgViewBox, _attrSvgDimensions, _attrSvgTransform):
    _tagName = "svg"

    def _getVersion(self):
        return self.element.version

    def _setVersion(self, val):
        self.element.setAttribute("version", val)

    def _getXmlns(self):
        return self.element.xmlns

    def _setXmlns(self, val):
        self.element.setAttribute("xmlns", val)


@html5.tag
class SvgCircle(SvgWidget, _attrSvgTransform, _attrSvgDimensions):
    _tagName = "circle"


@html5.tag
class SvgEllipse(SvgWidget, _attrSvgTransform, _attrSvgDimensions):
    _tagName = "ellipse"


@html5.tag
class SvgG(SvgWidget, _attrSvgTransform, _attrSvgStyles):
    _tagName = "g"

    def _getSvgTransform(self):
        return self.element.transform

    def _setSvgTransform(self, val):
        self.element.setAttribute("transform", val)


@html5.tag
class SvgImage(
    SvgWidget, _attrSvgViewBox, _attrSvgDimensions, _attrSvgTransform, _attrSvgXlink
):
    _tagName = "image"


@html5.tag
class SvgLine(SvgWidget, _attrSvgTransform, _attrSvgPoints):
    _tagName = "line"


@html5.tag
class SvgPath(SvgWidget, _attrSvgTransform):
    _tagName = "path"

    def _getD(self):
        return self.element.d

    def _setD(self, val):
        self.element.setAttribute("d", val)

    def _getPathLength(self):
        return self.element.pathLength

    def _setPathLength(self, val):
        self.element.setAttribute("pathLength", val)


@html5.tag
class SvgPolygon(SvgWidget, _attrSvgTransform, _attrSvgPoints):
    _tagName = "polygon"


@html5.tag
class SvgPolyline(SvgWidget, _attrSvgTransform, _attrSvgPoints):
    _tagName = "polyline"


@html5.tag
class SvgRect(SvgWidget, _attrSvgDimensions, _attrSvgTransform, _attrSvgStyles):
    _tagName = "rect"


@html5.tag
class SvgText(SvgWidget, _attrSvgDimensions, _attrSvgTransform, _attrSvgStyles):
    _tagName = "text"


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
