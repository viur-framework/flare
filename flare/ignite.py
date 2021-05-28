"""Flare-specific form Widgets with specialized classes and behavior."""

from . import html5


@html5.tag("flare-label")
class Label(html5.Label):
    def __init__(self, *args, **kwargs):
        super(Label, self).__init__(style="label flr-label", *args, **kwargs)


@html5.tag("flare-input")
class Input(html5.Input):
    def __init__(self, *args, **kwargs):
        super(Input, self).__init__(style="input flr-input", *args, **kwargs)


@html5.tag("flare-switch")
class Switch(html5.Div):
    def __init__(self, *args, **kwargs):
        super(Switch, self).__init__(style="switch flr-switch", *args, **kwargs)

        self.input = html5.Input(style="switch-input")
        self.appendChild(self.input)
        self.input["type"] = "checkbox"

        switchLabel = html5.Label(forElem=self.input)
        switchLabel.addClass("switch-label")
        self.appendChild(switchLabel)

    def _setChecked(self, value):
        self.input["checked"] = bool(value)

    def _getChecked(self):
        return self.input["checked"]


@html5.tag("flare-check")
class Check(html5.Input):
    def __init__(self, *args, **kwargs):
        super(Check, self).__init__(style="check flr-check", *args, **kwargs)

        checkInput = html5.Input()
        checkInput.addClass("check-input")
        checkInput["type"] = "checkbox"
        self.appendChild(checkInput)

        checkLabel = html5.Label(forElem=checkInput)
        checkLabel.addClass("check-label")
        self.appendChild(checkLabel)


@html5.tag("flare-radio")
class Radio(html5.Div):
    def __init__(self, *args, **kwargs):
        super(Radio, self).__init__(style="radio flr-radio", *args, **kwargs)

        radioInput = html5.Input()
        radioInput.addClass("radio-input")
        radioInput["type"] = "radio"
        self.appendChild(radioInput)

        radioLabel = html5.Label(forElem=radioInput)
        radioLabel.addClass("radio-label")
        self.appendChild(radioLabel)


@html5.tag("flare-select")
class Select(html5.Select):
    def __init__(self, *args, **kwargs):
        super(Select, self).__init__(style="select flr-select", *args, **kwargs)

        defaultOpt = html5.Option()
        defaultOpt["selected"] = True
        defaultOpt["disabled"] = True
        defaultOpt.element.innerHTML = ""
        self.appendChild(defaultOpt)


@html5.tag("flare-textarea")
class Textarea(html5.Textarea):
    def __init__(self, *args, **kwargs):
        super(Textarea, self).__init__(style="textarea flr-textarea", *args, **kwargs)


@html5.tag("flare-progress")
class Progress(html5.Progress):
    def __init__(self, *args, **kwargs):
        super(Progress, self).__init__(style="progress flr-progress", *args, **kwargs)


@html5.tag("flare-item")
class Item(html5.Div):
    def __init__(self, title=None, descr=None, className=None, *args, **kwargs):
        super(Item, self).__init__(style="item flr-item", *args, **kwargs)
        if className:
            self.addClass(className)

        self.fromHTML(
            """
			<div class="item-image flr-item-image" [name]="itemImage">
			</div>
			<div class="item-content flr-item-content" [name]="itemContent">
				<div class="item-headline flr-item-headline" [name]="itemHeadline">
				</div>
			</div>
		"""
        )

        if title:
            self.itemHeadline.appendChild(html5.TextNode(title))

        if descr:
            self.itemSubline = html5.Div()
            self.addClass("item-subline flr-item-subline")
            self.itemSubline.appendChild(html5.TextNode(descr))
            self.appendChild(self.itemSubline)


@html5.tag("flare-table")
class Table(html5.Table):
    def __init__(self, *args, **kwargs):
        super(Table, self).__init__(*args, **kwargs)
        self.head.addClass("ignt-table-head")
        self.body.addClass("ignt-table-body")

    def prepareRow(self, row):
        assert row >= 0, "Cannot create rows with negative index"

        for child in self.body._children:
            row -= child["rowspan"]
            if row < 0:
                return

        while row >= 0:
            tableRow = html5.Tr()
            tableRow.addClass("ignt-table-body-row")
            self.body.appendChild(tableRow)
            row -= 1

    def prepareCol(self, row, col):
        assert col >= 0, "Cannot create cols with negative index"
        self.prepareRow(row)

        for rowChild in self.body._children:
            row -= rowChild["rowspan"]

            if row < 0:
                for colChild in rowChild._children:
                    col -= colChild["colspan"]
                    if col < 0:
                        return

                while col >= 0:
                    tableCell = html5.Td()
                    tableCell.addClass("ignt-table-body-cell")
                    rowChild.appendChild(tableCell)
                    col -= 1

                return

    def fastGrid(self, rows, cols, createHidden=False):
        colsstr = "".join(
            ['<td class="ignt-table-body-cell"></td>' for _ in range(0, cols)]
        )
        tblstr = '<tbody [name]="body" class="ignt-table-body" >'

        for r in range(0, rows):
            tblstr += '<tr class="ignt-table-body-row %s">%s</tr>' % (
                "is-hidden" if createHidden else "",
                colsstr,
            )
        tblstr += "</tbody>"

        self.fromHTML(tblstr)
