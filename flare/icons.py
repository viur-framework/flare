"""Components for displaying icons."""

from . import html5
from .network import HTTPRequest
from flare.config import conf
import logging, string


@html5.tag("flare-svg-icon")
class SvgIcon(html5.svg.Svg):
    """A raw, embedded SVG icon-component."""

    _leafTag = True

    def __init__(self, value=None, fallbackIcon=None, title=""):
        super().__init__()
        self.value = value
        self.url = self.value
        self.title = title
        self.fallbackIcon = fallbackIcon

        self["xmlns"] = "http://www.w3.org/2000/svg"
        self["class"] = ["icon"]  # mostly used

        if title:
            self["title"] = title

        if value:
            self.getIcon()

    def _setValue(self, value):
        self.value = value
        self.getIcon()

    def _setTitle(self, val):
        self.title = val
        self.element.title = val

    def getIcon(self):
        if self.value == "icons/modules/users.svg":
            logging.warning("Please use 'icon-users' or a project specific svg path")
            self.value = "icon-users"
        if self.value and self.value.endswith(".svg"):
            self.url = self.value
        else:
            self.url = conf["flare.icon.svg.embedding.path"] + "/%s.svg" % self.value

        if self.url in conf["flare.icon.cache"]:
            try:
                self.replaceSVG(conf["flare.icon.cache"][self.url])
            except:
                HTTPRequest(
                    "GET",
                    self.url,
                    callbackSuccess=self.replaceSVG,
                    callbackFailure=self.requestFallBack,
                )
        else:
            HTTPRequest(
                "GET",
                self.url,
                callbackSuccess=self.replaceSVG,
                callbackFailure=self.requestFallBack,
            )

    def replaceSVG(self, icondata):
        conf["flare.icon.cache"].update({self.url:icondata})
        self.removeAllChildren()

        for node in html5.fromHTML(icondata):
            if isinstance(node, html5.svg.Svg):
                self["viewbox"] = node["viewbox"]
                self.addClass(node["class"])
                self.appendChild(node._children)
                break

    def requestFallBack(self, data, status):
        url = None
        if self.fallbackIcon:
            url = conf["flare.icon.svg.embedding.path"] + "/%s.svg" % self.fallbackIcon
        elif self.title:
            # language=HTML
            self["viewbox"] = "-10 -10 20 20"
            self.appendChild(
                """<text style="text-anchor: middle" y="6.5">%s</text>"""
                % self.title[0].upper()
            )
        else:
            url = (
                conf["flare.icon.svg.embedding.path"]
                + "/%s.svg" % conf["flare.icon.fallback.error"]
            )  # fallback

        if url:
            HTTPRequest("GET", url, callbackSuccess=self.replaceSVG)


@html5.tag("flare-icon")
class Icon(html5.I):
    """Icon component with first-letter fallback, normally shown as embedded SVG."""

    _leafTag = True

    def __init__(self, value=None, fallbackIcon=None, title="", classes=[]):
        super().__init__()
        self["class"] = ["i"] + classes
        self.title = title
        self.fallbackIcon = fallbackIcon
        self.value = value

        # Widget reference variables
        self.imgWidget = None
        self.svgWidget = None
        self.txtWidget = None

        if value:
            self["value"] = value

    def _setValue(self, value):
        if isinstance(value, dict):
            self.value = value.get("dest", {}).get("downloadUrl")
        else:
            self.value = value

        # sig= test is really ugly we need a better solution
        if self.value:
            if self.txtWidget:
                self.removeChild(self.txtWidget)
                self.txtWidget = None

            if "sig=" in self.value or any(
                [
                    self.value.lower().endswith(ext)
                    for ext in [
                        ".jpg",
                        ".png",
                        ".gif",
                        ".bmp",
                        ".webp",
                        ".heic",
                        ".jpeg",
                    ]
                ]
            ):
                if not self.imgWidget:
                    self.imgWidget = html5.Img()
                    self.imgWidget.addEventListener("error", self.onError)

                self.imgWidget["src"] = self.value
                self.appendChild(self.imgWidget)
                return
            elif self.value.endswith(".svg"):
                url = self.value
            else:
                url = conf["flare.icon.svg.embedding.path"] + "/%s.svg" % self.value

            if self.svgWidget:
                self.removeChild(self.svgWidget)
                self.svgWidget = None

            self.svgWidget = SvgIcon(url, self.fallbackIcon, self.title)
            self.appendChild(self.svgWidget)
        else:
            self.onError()

    def _setTitle(self, val):
        self.title = val
        self.element.title = val

        if not self.value:
            self.onError()

    def _setFallback(self, val):
        self.fallbackIcon = val
        if not self.value:
            self.onError()

    def onError(self):
        if self.imgWidget:
            self.removeChild(self.imgWidget)
            self.imgWidget = None

        if self.svgWidget:
            self.removeChild(self.svgWidget)
            self.svgWidget = None

        if self.txtWidget:
            self.removeChild(self.txtWidget)
            self.txtWidget = None

        if self.fallbackIcon:
            self.svgWidget = SvgIcon(
                conf["flare.icon.svg.embedding.path"] + "/%s.svg" % self.fallbackIcon,
                title=self.title,
            )
            self.appendChild(self.svgWidget)

        elif self.title:
            initials = self.title.replace("-", " ")  # replace dashes by spaces
            initials = initials.translate(
                {ord(c): None for c in string.punctuation}
            )  # remove all punctuations

            self.txtWidget = html5.TextNode(
                "".join([tag[0] for tag in initials.split(maxsplit=1)])
            )  # Only allow first two words
            self.appendChild(self.txtWidget)
        else:
            self.svgWidget = SvgIcon(
                conf["flare.icon.svg.embedding.path"]
                + "/%s.svg" % conf["flare.icon.fallback.error"],
                title=self.title,
            )

            self.appendChild(self.svgWidget)


@html5.tag("flare-badge-icon")
class BadgeIcon(Icon):
    """A badge icon is an icon-component with a little badge, e.g. a number of new messages or items in the cart or so."""

    def __init__(self, title="", value=None, fallbackIcon=None, badge=None):
        super().__init__(title, value, fallbackIcon)
        self._badge = None

        # language=HTML
        self.appendChild(
            """
            <span class="badge" [name]="badgeWidget" hidden></span>
            """
        )

        if badge:
            self["badge"] = badge

    def _setBadge(self, badge):
        self._badge = badge

        if badge is None:
            self.badgeWidget.hide()
        else:
            self.badgeWidget.replaceChild(badge)
            self.badgeWidget.show()

    def _getBadge(self):
        return self._badge
