========================================
Ignite
========================================
Ignite itself is a css framework written in less and serves as the basis for all components.
https://ignite.viur.dev/

In Flare, some simpler and more complex components are already implented with appropriate css classes.

Button
-------
The Button can be used with "flare-button" tag und provides the possibility to add an icon before the Button text.

Input
-------
The Input can be used with "flare-input" tag and provides the basis input element with ignite specific css classes.

Label
-------
The Label can be used with "flare-label" tag and provides the basis label element with ignite specific css classes.

Switch
-------
The switch is an on/off slidecontrol and can be used with "flare-switch" tag.
The component stores the current state internally in a checkbox input field.

Check
-------
The Check Component can be used with "flare-check" tag.
Like the switch, the internal state is stored in a checkbox input field.
Through this component the display of the checkbox can be customized via css.

Radio
-------
The Radio Component can be used with "flare-radio" tag.
The internal state is stored in a radio input field.
Through this component the display of the checkbox can be customized via css.

Select
----------
The Select can be used with "flare-select" tag and provides the basis select element with ignite specific css classes.
In addition it adds per default a unselectable default option.

Textarea
----------
The Textarea can be used with "flare-textarea" tag and provides the basis textarea element with ignite specific css classes.

Progress
----------
The Progress can be used with "flare-progess" tag and provides the basis progress element with ignite specific css classes.

Item
-------
The Item component can be used with the tag "flare-item" and provides a simple box component. It can contain an image as well as a title and a description

Table
-------
The Table component can be used with the "flare-table" tag and provides the basis table element with ignite specific css classes.
In additon this component provides the functions prepareRow and prepareCol to generate the table grid.

Popout
-------
The Popout component can be used with the "flare-popout" tag.
This component is a floating box and is often used as a tooltip or contextmenu.
With the css classes "popout--sw", "popout--nw".. you can change the direction.

Popup
-------
The are some diffenttypes of Popups. All Popuptypes are based on the base Popup Class.
It provides a close function a header, a body and a footer.
All Popups will be added to the body Tag.

Prompt
~~~~~~~
The Promt is a simple Input box with a cancel and ok button. Use this to get some user Input.

Alert
~~~~~~
The Alert is a simple Messagebox with an ok button. Use this for some Feedback.

Confirm
~~~~~~~~
The Confirm is a Messagebox with a yes / no selection. Each button has its own callback so you can bump different actions based on the selection that was made

Textarea Dialog
~~~~~~~~~~~~~~~~~
This Popup basically does the same as the Prompt, but it uses a textarea field instead of an input field.