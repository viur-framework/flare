import logging
from flare import html5
from flare.forms import boneSelector, InvalidBoneValueException
from flare.network import NetworkService
from flare.button import Button
from flare.event import EventDispatcher

@html5.tag
class viurForm(html5.Form):

	def __init__(self,formName = None, moduleName = None, actionName="add", skel=None, structure=None, ignore=(),hide=()):
		super().__init__()
		self.formName = formName
		self.moduleName = moduleName
		self.actionName = actionName
		self.bones = {}
		self.skel = skel
		self.errors = []
		self.ignore = ignore
		self.hide = hide

		if structure:
			self.structure = {k: v for k, v in structure}
		self.formSuccess = EventDispatcher( "formSuccess" )
		self.formSuccess.register(self)

		self.addClass("form")

	def _setModulename( self, val ):
		self.moduleName = val

	def _setActionname( self, val ):
		self.actionName = val

	def _setFormname( self,val ):
		self.formName = val

	def buildForm( self ):
		for key, bone in self.structure.items():
			if key in self.ignore:
				continue
			bonefield = boneField(key,self)
			self.appendChild( bonefield )

		submitbtn = sendForm(text = "speichern",form = self)
		self.appendChild(submitbtn)

	def buildInternalForm( self ):
		for key, bone in self.structure.items():
			if key in self.ignore:
				continue

			bonefield = boneField(key,self)
			bonefield.onAttach() #we need a better solution
			self.appendChild( bonefield )

	def registerField( self,key,widget ):
		if key in self.ignore:
			return 0

		if key in self.bones:
			logging.debug("Double field definition in {}!, only first field will be used", self)
			return 0

		self.bones.update({key:widget})

	def submitForm( self ):
		res = { }
		if "key" in self.skel and self.skel["key"]:
			res["key"] = self.skel["key"]

		for key, boneField in self.bones.items():
			widget = boneField.bonewidget
			# ignore the key, it is stored in self.key, and read-only bones
			if key == "key" or widget.bone.readonly:
				continue

			try:
				res[ key ] = widget.serialize()
				if res[ key ] is None:
					res[ key ] = ""

			except InvalidBoneValueException:
				pass
				#if validityCheck:
				#	return None

		NetworkService.request( self.moduleName, self.actionName, res,
								secure = True, #always with fresh skey
								successHandler = self.actionSuccess,
								failureHandler = self.actionFailed )

		return res

	def actionSuccess( self, req ):
		resp = NetworkService.decode(req)
		logging.debug("actionSuccess: %r", resp)
		'''
		severity cases:
			NotSet = 0
			InvalidatesOther = 1 <-- relevant
			Empty = 2
			Invalid = 3			 <-- relevant
		'''
		if "action" in resp and resp["action"].endswith("Success"):
			self.formSuccess.fire(self)

		else:
			pass #form rejected
			self.errors = resp["errors"]

			for error in self.errors:
				if error[ "fieldPath" ] in self.bones:
					boneField = self.bones[ error[ "fieldPath" ] ]  # todo dependency errors
					if (error["severity"]%2 == 0 and boneField["required"]) or\
						(error["severity"]%2 == 1): #invalid

						boneField.setInvalid()
					else:
						boneField.setValid()

			self.createFormErrorMessage()

	def createFormSuccessMessage( self ):
		try:
			self.removeChild( self.errorhint )
		except:
			pass

		if "successhint" not in dir(self):
			# language=HTML
			self.prependChild( '''
						<div [name]="successhint" class="msg is-active msg--success ">Erfolgreich gespeichert!</div>
					''' )


	def createFormErrorMessage( self ):
		try:
			self.removeChild(self.successhint)
		except: pass

		if "errorhint" not in dir(self):
			#language=HTML
			self.prependChild('''
				<div [name]="errorhint" class="msg is-active msg--error "></div>
			''')

		self.errorhint.removeAllChildren()
		for error in self.errors:
			if error[ "fieldPath" ] in self.bones:
				boneField = self.bones[ error[ "fieldPath" ] ]  # todo dependency errors
				if error[ "severity" ] == 1 or error[ "severity" ] == 3:  # invalid
					#language=HTML
					self.errorhint.appendChild('''<span class="flr-bone--error">{{boneDescr}}: {{error}} </span>''',
											   boneDescr = boneField.structure[ boneField.boneName].get("descr", boneField.boneName),
											   error=error["errorMessage"])

	def actionFailed( self, req, *args, **kwargs ):
		logging.debug("FAILED: %r", req)


	def onFormSuccess( self,event ):
		self.createFormSuccessMessage()



@html5.tag
class boneField(html5.Div):

	def __init__(self, boneName=None, form=None):
		super().__init__()
		self.boneName = boneName
		self.form = form
		self.label = True
		self.hidden = False
		self.placeholder = False
		self.defaultvalue = None

		self.formloaded = False

	def onAttach(self):

		if not self.formloaded:
			if "boneName" not in dir(self):
				logging.debug("Please add boneName attribute to {}", self)

			if "form" not in dir(self) or not self.form:
				logging.debug("Please add :form attribute with a named form widget to {}.", self)

			if "skel" not in dir(self.form) or "structure" not in dir(self.form):
				logging.debug( "Missing :skel and :structure databinding on referenced form", self.form)

			if "moduleName" not in dir(self.form):
				logging.debug( "Missing moduleName attribute on referenced form", self.form)

			#self.form existiert und form hat skel und structure
			if  isinstance(self.form.structure, list):
				self.structure = {k: v for k, v in self.form.structure}
			else:
				self.structure = self.form.structure

			self.skel = self.form.skel
			self.moduleName = self.form.moduleName

			formparam = {"formName":self.form.formName}
			try:
				boneFactory = boneSelector.select( self.moduleName, self.boneName, self.structure, **formparam )( self.moduleName, self.boneName, self.structure )
				self.bonewidget = boneFactory.editWidget()
			except Exception as e:
				logging.exception(e)
				self.bonewidget = html5.Div("Bone not Found %s"%self.boneName)
				self.appendChild( self.bonewidget )
				return 0

			bonestructure = self.structure.get(self.boneName,{})
			#label and bone wrapper
			self.addClass(["input-group",
						   "flr-bone",
						   "flr-bone--%s"%bonestructure.get("type").replace( ".", "-" ),
						   "flr-bone--%s"%self.boneName.replace( "_", "-" )])

			if self.boneName in self.form.hide or self.hidden:
				self._setHidden(True)
			else:
				self._setHidden( False )

			self.form.registerField(self.boneName,self)

			if self.label: #label optional
				self.appendChild(self.labelTemplate(),
								 descr = bonestructure.get("descr", self.boneName),
								 type = bonestructure.get("type"),
								 boneName = self.boneName)

			self.appendChild(self.bonewidget)

			if self.defaultvalue:
				self.skel[self.boneName] = self.defaultvalue # warning overrides server default


			self.unserialize(self.skel)
			self.formloaded = True

	def unserialize(self, data = None):
		for key, bone in self.form.bones.items():
			if data is not None:
				bone.bonewidget.unserialize(data.get(key))

	def _setBonename( self,val ):
		self.boneName = val

	def _setLabel( self,val ):
		if val=="True":
			self.label = True
		else:
			self.label = False

	def _setPlaceholder( self,val ):
		if val:
			self.placeholder = val
		else:
			self.placeholder = False

	def _setHide( self,val ):
		if val == "True":
			self.hidden = True
		else:
			self.hidden = False

	def _setValue( self,val ):
		self.defaultvalue = val

	def labelTemplate( self):
		'''
			Default label
		'''
		# language=HTML
		return '''<label [name]="bonelabel" class="input-group-item--first label flr-label flr-label--{{type}} flr-label--{{boneName}}">{{descr}}</label>'''

	def setInvalid( self ):
		self.toggleClass("is-invalid","is-valid") #wrapper
		if self.bonelabel:
			self.bonelabel.toggleClass( "is-invalid", "is-valid" ) #label
		self.bonewidget.toggleClass( "is-invalid", "is-valid" ) #bone

	def setValid( self ):
		self.toggleClass("is-valid","is-invalid")
		if self.bonelabel:
			self.bonelabel.toggleClass("is-valid","is-invalid")
		self.bonewidget.toggleClass("is-valid","is-invalid")

@html5.tag
class sendForm(Button):

	def __init__( self, text = None, callback = None, className = "btn--submit btn--primary", icon = None, badge = None,form=None ):
		super().__init__(text,callback,className,icon)
		self.form = form


	def onAttach(self):
		if "form" not in dir(self) or not self.form:
			logging.debug("Please add :form attribute with a named form widget to {}.", self)
			self.element.innerHTML = "ERROR"
			self.disable()

		self.callback = self.sendViurForm

	def sendViurForm( self,widget ):
		self.form.submitForm()
