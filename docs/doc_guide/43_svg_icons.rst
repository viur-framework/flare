========================================
SVG Icons
========================================

Icons are dependent on css styling in flare. So icons in a text can have the same color as the surrounding text.
This is possible by embedding svg icons. If the tag flare-svg-icon is used, the parameter value can be used to specify a path or name to an icon.

.. code-block:: HTML

	<flare-svg-icon value="/static/icons/my-icon.svg">

To keep the code in flare clear, only the icon name can be specified.
If only the name is specified, the config variable conf["flare.icon.svg.embedding.path"] is used to compose the path of flare.

.. code-block:: HTML

	<flare-svg-icon value="my-icon">


It is also possible to define a fallback icon in case the icon cannot be loaded.
If the title is set it will be transferred to the svg and in case the fallback icon is not set the first character of the text will be used as placeholder.

.. code-block:: HTML

	<flare-svg-icon value="my-icon" fallbackIcon="error" title="My Icon">
	<!-- shows my-icon or on error the error icon -->

	<flare-svg-icon value="my-icon" title="My Icon">
	<!-- shows my-icon or the letter M -->

Icon
~~~~~~~~~~~~~~

In practice icons can come in different file types. flare-icon can also handle other images and even use filebones directly.
In case the icon is not an svg, it is not embedded, but included using img-tag.
flare-icon can use the following image types:

- *.svg, *.jpg, *.png, *.gif, *.bmp, *.webp, *..jpeg

.. code-block:: HTML

	<flare-icon value="{{skel['image']}}">
	<!--loads a filebone-->

The Svg-icon parameters fallbackIcon and title are also supported.
