import json
from flare.button import Button
from flare.ignite import *
from flare.forms import boneSelector, conf



class BaseEditWidget( html5.Div ):
	"""
	Base class for a bone-compliant edit widget implementation using an input field.
	This widget defines the general interface of a bone edit control.
	"""
	style = [ "flr-value" ]

	def __init__( self, bone, **kwargs ):
		super().__init__()
		self.bone = bone
		self.widget = None

		widget = self._createWidget()
		if isinstance( widget, html5.Widget ):
			if not self.widget:
				self.widget = widget

			if not widget.parent():
				self.appendChild( widget )

			self._updateWidget()

	def _createWidget( self ):
		"""
		Function for creating the Widget or multiple Widgets that represent the bone.
		"""
		return Input()

	def _updateWidget( self ):
		"""
		Function for updating the Widget or multiple Widgets that represent the bone.
		"""
		self.widget[ "required" ] = self.bone.required
		self.widget[ "readonly" ] = self.bone.readonly

	def unserialize( self, value = None ):
		self.widget[ "value" ] = value or ""

	def serialize( self ):
		return self.widget[ "value" ]


class BaseViewWidget( html5.Div ):
	"""
	Base class for a bone-compliant view widget implementation using a div.
	"""
	style = [ "flr-value" ]

	def __init__( self, bone, **kwargs ):
		super().__init__()
		self.bone = bone
		self.value = None

	def unserialize( self, value = None ):
		self.value = value
		self.appendChild( html5.TextNode( value or conf[ "emptyValue" ] ), replace = True )

	def serialize( self ):
		return self.value


class BaseMultiEditWidgetEntry( html5.Div ):
	style = [ "flr-bone-widgets-item" ]
	"""
	Base class for an entry in a MultiBone container.
	"""

	def __init__( self, widget: html5.Widget ):
		super().__init__()
		self.widget = widget

		# Proxy some functions of the original widget
		for fct in [ "unserialize", "serialize", "focus" ]:
			setattr( self, fct, getattr( self.widget, fct ) )

		self.appendChild(
			"""<div [name]="dragArea" class="label flr-bone-dragger"><icon embedsvg="icon-drag-handle" ></icon></div>""",
			self.widget,
			"""<button [name]="removeBtn" class="btn--delete" text="Delete" icon="icon-cross" />"""
		)

		if widget.bone.boneStructure[ "readonly" ]:
			self.removeBtn.hide()
		else:
			# Proxy dragging event features of the dragArea to this widget!
			for event in [ "onDragStart", "onDragOver", "onDragLeave", "onDragEnd", "onDrop" ]:
				setattr( self.dragArea, event, getattr( self, event ) )
				self.dragArea.sinkEvent( event )  # sink has to be done behind setattr!

			self.dragArea[ "draggable" ] = True

	def onRemoveBtnClick( self ):
		self.parent().removeChild( self )

	def onDragStart( self, event ):
		if self.parent()[ "disabled" ]:
			return

		self.addClass( "is-dragging" )

		self.parent()._widgetToDrag = self
		event.dataTransfer.setData( "application/json", json.dumps( self.widget.serialize() ) )
		event.stopPropagation()

	def onDragOver( self, event ):
		if self.parent()[ "disabled" ]:
			return

		if self.parent()._widgetToDrag is not self:
			self.addClass( "is-dragging-over" )
			self.parent()._widgetIsOver = self

		event.preventDefault()

	def onDragLeave( self, event ):
		if self.parent()[ "disabled" ]:
			return

		self.removeClass( "is-dragging-over" )
		self.parent()._widgetIsOver = None

		event.preventDefault()

	def onDragEnd( self, event ):
		if self.parent()[ "disabled" ]:
			return

		self.removeClass( "is-dragging" )
		self.parent()._widgetToDrag = None

		if self.parent()._widgetIsOver:
			self.parent()._widgetIsOver.removeClass( "is-dragging-over" )
			self.parent()._widgetIsOver = None

		event.stopPropagation()

	def onDrop( self, event ):
		event.preventDefault()
		event.stopPropagation()

		widgetToDrop = self.parent()._widgetToDrag

		if widgetToDrop and widgetToDrop != self:
			if self.element.offsetTop > widgetToDrop.element.offsetTop:
				parentChildren = self.parent().children()

				if parentChildren[ -1 ] is self:
					self.parent().appendChild( widgetToDrop )
				else:
					self.parent().insertBefore(
						widgetToDrop,
						parentChildren[ parentChildren.index( self ) + 1 ]
					)
			else:
				self.parent().insertBefore( widgetToDrop, self )

		self.parent()._widgetToDrag = None


class BaseMultiEditWidget( html5.Div ):
	"""
	Class for encapsulating multiple bones inside a container
	"""
	entryFactory = BaseMultiEditWidgetEntry
	style = [ "flr-value-container" ]

	def __init__( self, bone, widgetFactory: callable, **kwargs ):
		super().__init__( """
			<div [name]="widgets" class="flr-bone-widgets"></div>
			<div [name]="actions" class="flr-bone-actions input-group">
				<button [name]="addBtn" class="btn--add" text="Add" icon="icon-add"></button>
			</div>
		""" )

		self.bone = bone
		self.widgetFactory = widgetFactory
		self.kwargs = kwargs

		self.widgets._widgetToDrag = None
		self.widgets._widgetIsOver = None  # "We have clearance, Clarence." - "Roger, Roger. What's our vector, Victor?"

		if self.bone.boneStructure[ "readonly" ]:
			self.addBtn.hide()

	def onAddBtnClick( self ):
		last = self.widgets.children( -1 )
		if last and not last.serialize():
			last.focus()
			return

		entry = self.addEntry()
		entry.focus()

	def addEntry( self, value = None ):
		entry = self.widgetFactory( self.bone, **self.kwargs )
		if self.entryFactory:
			entry = self.entryFactory( entry )

		if value:
			entry.unserialize( value )

		self.widgets.appendChild( entry )
		return entry

	def unserialize( self, value ):
		self.widgets.removeAllChildren()

		if not isinstance( value, list ):
			return

		for entry in value:
			self.addEntry( entry )

	def serialize( self ):
		ret = [ ]
		for widget in self.widgets:
			value = widget.serialize()
			if value:
				ret.append( value )

		return ret


class BaseMultiViewWidget( html5.Ul ):
	def __init__( self, bone, widgetFactory: callable, **kwargs ):
		super().__init__()
		self.bone = bone
		self.widgetFactory = widgetFactory
		self.kwargs = kwargs

	def unserialize( self, value ):
		self.removeAllChildren()

		if not isinstance( value, list ):
			return

		for entry in value:
			widget = self.widgetFactory( self.bone, **self.kwargs )
			widget.unserialize( entry )
			self.appendChild( widget )

	def serialize( self ):
		ret = [ ]
		for widget in self.widgets:
			value = widget.serialize()
			if value:
				ret.append( value )

		return ret


class BaseLanguageEditWidget( html5.Div ):
	"""
	Class for encapsulating a bone for each language inside a container
	"""

	def __init__( self, bone, widgetFactory: callable, **kwargs ):
		super().__init__( """
			<div [name]="widgets" class="flr-bone-widgets"></div>
			<div [name]="actions" class="flr-bone-actions input-group"></div>
		""" )

		languages = bone.skelStructure[ bone.boneName ][ "languages" ]
		assert languages, "This parameter must not be empty!"

		self.bone = bone
		self.languages = languages
		self._languageWidgets = { }

		# Create widget for every language
		for lang in self.languages:
			assert not any( [ ch in lang for ch in "<>\"'/" ] ), "This is not a valid language identifier!"

			langBtn = Button( lang, callback = self.onLangBtnClick )
			langBtn.addClass( "btn--lang", "btn--lang-" + lang )

			if lang == conf[ "defaultLanguage" ]:
				langBtn.addClass( "is-active" )

			self.actions.appendChild( langBtn )

			kwargs[ "language" ] = lang
			langWidget = widgetFactory(
				self.bone,
				**kwargs
			)

			if lang != conf[ "defaultLanguage" ]:
				langWidget.hide()

			self.widgets.appendChild( langWidget )

			self._languageWidgets[ lang ] = (langBtn, langWidget)

	def onLangBtnClick( self, sender ):
		for btn, widget in self._languageWidgets.values():
			if sender is btn:
				widget.show()
				btn.addClass( "is-active" )
			else:
				widget.hide()
				btn.removeClass( "is-active" )

	def unserialize( self, value ):
		if not isinstance( value, dict ):
			value = { }

		for lang, (_, widget) in self._languageWidgets.items():
			widget.unserialize( value.get( lang ) )

	def serialize( self ):
		ret = { }
		for lang, (_, widget) in self._languageWidgets.items():
			value = widget.serialize()
			if value:
				ret[ lang ] = value

		return ret


class BaseBone( object ):
	editWidgetFactory = BaseEditWidget
	viewWidgetFactory = BaseViewWidget
	multiEditWidgetFactory = BaseMultiEditWidget
	multiViewWidgetFactory = BaseMultiViewWidget
	languageEditWidgetFactory = BaseLanguageEditWidget
	languageViewWidgetFactory = BaseLanguageEditWidget  # use edit language widget also to view!

	"""
	Base "Catch-All" delegate for everything not handled separately.
	"""

	def __init__( self, moduleName, boneName, skelStructure ):
		super().__init__()

		self.moduleName = moduleName
		self.boneName = boneName
		self.skelStructure = skelStructure
		self.boneStructure = self.skelStructure[ self.boneName ]

		self.readonly = bool( self.boneStructure.get( "readonly" ) )
		self.required = bool( self.boneStructure.get( "required" ) )
		self.multiple = bool( self.boneStructure.get( "multiple" ) )
		self.languages = self.boneStructure.get( "languages" )

	def editWidget( self, value = None ) -> html5.Widget:
		widgetFactory = self.editWidgetFactory

		if self.multiEditWidgetFactory and self.multiple:
			multiWidgetFactory = widgetFactory  # have to make a separate "free" variable
			widgetFactory = lambda bone, **kwargs: self.multiEditWidgetFactory( bone, multiWidgetFactory, **kwargs )

		if self.languageEditWidgetFactory and self.languages:
			languageWidgetFactory = widgetFactory  # have to make a separate "free" variable
			widgetFactory = lambda bone, **kwargs: self.languageEditWidgetFactory( bone, languageWidgetFactory, **kwargs )

		widget = widgetFactory( self )
		widget.unserialize( value )
		return widget

	def viewWidget( self, value = None ):
		widgetFactory = self.viewWidgetFactory

		if self.multiViewWidgetFactory and self.boneStructure.get( "multiple" ):
			multiWidgetFactory = widgetFactory  # have to make a separate "free" variable
			widgetFactory = lambda bone, **kwargs: self.multiViewWidgetFactory( bone, multiWidgetFactory, **kwargs )

		if self.languageViewWidgetFactory and self.boneStructure.get( "languages" ):
			languageWidgetFactory = widgetFactory  # have to make a separate "free" variable
			widgetFactory = lambda bone, **kwargs: self.languageViewWidgetFactory( bone, languageWidgetFactory, **kwargs )

		widget = widgetFactory( self )
		widget.unserialize( value )
		return widget

	'''
	def toString(self, value):
		return value or conf["emptyValue"]

	def toJSON(self, value):
		if isinstance(value, list):
			return [str(i) for i in value]

		return value
	'''


boneSelector.insert( 0, lambda *args, **kwargs: True, BaseBone )
