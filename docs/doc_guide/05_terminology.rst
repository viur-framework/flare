========================================
Terminology
========================================
Originally, Flare was developed for ViUR. Because of these roots, some terms or objects may cause confusion without further explanation.

Lets start with a quick overview of some main components.

config.py
	This is a central location where you can store data or information that needs to be shared by the entire application.
	Some Examples are

		- paths
		- caches
		- configurations
		- versions

network.py
	The default format used for data exchange is json. Each query is made via the NetworkService class in network.py.

views
	Views are used to divide content within the application. There is always one view that is active.
	They are saved after their instantiation in a object and are only hooked into the DOM when this view is activated.
	A view can contain multiple widgets that replace the existing content when activated.

safeeval
	Executes a string containing Python code. The possible operations are strongly limited for security reasons.
	With safeeval `flare-if` can show and hide content without the need of coding, and `{{ expressions }}` can directly be interpreted inside of HTML-code.

icons
	The icon class can use any of the common image types.
	In most cases, you want to have icons that match the font color. In this case flare requires svg icons.

priorityqueues
	PriorityQueues are used to provide a plugin capability.
	For each type there is somewhere centrally an instance of such a PriorityQueue.
	In this the options are added with the insert function and prioritized with a numerical value and validation function.
	If now a suitable option is searched, the select function is called with parameters which are passed to the validation function.
	The first matching option in the prioritized list is then returned.


Only relevant if used with ViUR
--------------------------------------
bones
	Bones are in the ViUR ecosystem data field definitions.
	There are different types and hold besides the type information also display information like a description and tooltips.

moduleInfo
	Modules are the controllers of a ViUR application, and implement the application logic.
	In the case of relations, information about the target module may be required, which can be found in the module info.

