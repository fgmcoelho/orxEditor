from singleton import Singleton

from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

from os import getcwd
from editorobjects import ObjectTypes
from collision import CollisionInformationPopup
from editorutils import CancelableButton, AlertPopUp
from communicationobjects import ObjectDescriptorToResourceLoarder
from layer import LayerInformationPopup

@Singleton
class BaseObjectDescriptor:
	def __setValues(self, path, size, obj):
		self.__pathLabel.text = 'Path: ' + str(path)
		self.__sizeLabel.text = 'Size: ' + str(size)
		self.__objRef = obj

	def __openResourceLoader(self, *args):
		if (self.__objRef is None or self.__objRef.getType() != ObjectTypes.baseObject):
			errorWarn = AlertPopUp('Error', 'No compatible object selected.', 'Ok')
			errorWarn.open()
		else:
			ObjectDescriptorToResourceLoarder.Instance().openPopUp(self.__objRef.getPath())

	def __init__(self, accordionItem):
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__pathLabel = Label(text = 'Path: ', size_hint = (1.0, 0.2), multiline=False)
		self.__pathLabel.text_size = (self.__pathLabel.width, None)
		self.__sizeLabel = Label(text = 'Size: ', size_hint = (1.0, 0.2))
		self.__layout.add_widget(self.__pathLabel)
		self.__layout.add_widget(self.__sizeLabel)
		self.__layout.add_widget(Label(text = '', size_hint = (1.0, 0.4)))
		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)
		self.__objRef = None
		loaderLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		loaderLine.add_widget(Label(text = 'Resource loader:', size_hint = (0.8, 1.0)))
		loaderLine.add_widget(CancelableButton(text = 'Load', on_release = self.__openResourceLoader,
			size_hint = (0.2, 1.0)))
		self.__layout.add_widget(loaderLine)

	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False

	def setValues(self, path = '', size='', obj = None):
		self.__setValues(path, size, obj)
		self.setActive()

	def setValuesNoActive(self, path = '', size = ''):
		self.__setValues(path, size)

@Singleton
class MultipleSelectionDescriptor:
	def __init__(self, accordionItem):
		self.__layout = BoxLayout (orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__selectedLabel = Label(text = 'Selected: 0', size_hint = (1.0, 0.1))
		
		self.__layerLabel = Label(text = 'Group info:', size_hint = (0.7, 1.0))
		self.__layerButton = CancelableButton(text = 'Edit Group', size_hint = (0.3, 1.0), 
			on_release = LayerInformationPopup.Instance().showPopUp)
		self.__layerBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__layerBox.add_widget(self.__layerLabel)
		self.__layerBox.add_widget(self.__layerButton)

		self.__collisionBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__collisionInfoLabel = Label(text = 'Collision info:', size_hint = (0.7, 1.0))
		self.__collisionHandler = CancelableButton(text = 'Edit Collision', size_hint = (0.3, 1.0), 
			on_release = CollisionInformationPopup.Instance().showPopUp)
		self.__collisionBox.add_widget(self.__collisionInfoLabel)
		self.__collisionBox.add_widget(self.__collisionHandler)

		self.__layout.add_widget(self.__selectedLabel)
		self.__layout.add_widget(Label(text = '', size_hint = (1.0, 0.5)))
		self.__layout.add_widget(self.__layerBox)
		self.__layout.add_widget(self.__collisionBox)

		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)

	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False

	def __setValues(self, count = 0):
		self.__selectedLabel.text = 'Selected: ' + str(count)

	def setValuesNoActive(self, count = 0):
		self.__setValues(count)

	def setValues(self, count = 0):
		self.__setValues(count)
		self.setActive()

@Singleton
class RenderedObjectDescriptor:
	def __init__(self, accordionItem, collisionPopUpMethod, layerPopUpMethod):
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__pathLabel = Label(text = 'Path: ', size_hint = (1.0, 0.1))
		self.__nameLabel = Label(text = 'Name: ', size_hint = (1.0, 0.1))

		self.__flipBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__flipxLabel = Label(text = 'Flipped on X: ', size_hint = (0.5, 1.0))
		self.__flipyLabel = Label(text = 'Flipped on Y: ', size_hint = (0.5, 1.0))
		self.__flipBox.add_widget(self.__flipxLabel)
		self.__flipBox.add_widget(self.__flipyLabel)

		self.__sizeScaleBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__sizeLabel = Label(text = 'Size: ', size_hint = (0.5, 1.0))
		self.__scaleLabel = Label(text = 'Scale: ', size_hint = (0.5, 1.0))

		self.__sizeScaleBox.add_widget(self.__sizeLabel)
		self.__sizeScaleBox.add_widget(self.__scaleLabel)
		
		self.__layerBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__layerLabel = Label(text = 'Group: ', size_hint = (0.7, 1.0))
		self.__layerButton = CancelableButton(text = 'Edit Group', size_hint = (0.3, 1.0), 
			on_release = layerPopUpMethod)
		
		self.__layerBox.add_widget(self.__layerLabel)
		self.__layerBox.add_widget(self.__layerButton)
		

		self.__collisionBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__collisionInfoLabel = Label(text = 'Has collision info: ', size_hint = (0.7, 1.0))
		self.__collisionHandler = CancelableButton(text = 'Edit Collision', size_hint = (0.3, 1.0), 
			on_release = collisionPopUpMethod)

		self.__collisionBox.add_widget(self.__collisionInfoLabel)
		self.__collisionBox.add_widget(self.__collisionHandler)

		self.__layout.add_widget(self.__pathLabel)
		self.__layout.add_widget(self.__nameLabel)
		self.__layout.add_widget(self.__flipBox)
		self.__layout.add_widget(self.__sizeScaleBox)
		self.__layout.add_widget(self.__layerBox)
		self.__layout.add_widget(self.__collisionBox)

		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)

	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False

	def setValues(self, path = '', size = '', scale = '', layer = '', name = '', flipX = '', flipY = '',
			collisionInfo = None):
		self.__setValues(path, size, scale, layer, name, flipX, flipY, collisionInfo)
		self.setActive()

	def setValuesNoActive(self, path = '', size = '', scale = '', layer = '', name = '', flipX = '', flipY = '',
			collisionInfo = None):
		self.__setValues(path, size, scale, layer, name, flipX, flipY, collisionInfo)

	def __setValues(self, path, size, scale, layer, name, flipX, flipY, collisionInfo):
		self.__pathLabel.text = 'Path: ' + str(path)
		self.__sizeLabel.text = 'Size: ' + str(size)
		self.__scaleLabel.text = 'Scale: ' + str(scale)
		self.__layerLabel.text = 'Group: ' + str(layer)
		self.__nameLabel.text = 'Name: ' + str(name)
		self.__flipxLabel.text = 'Flipped on X: ' + str(flipX)
		self.__flipyLabel.text = 'Flipped on Y: ' + str(flipY)
		if (collisionInfo is None):
			self.__collisionInfoLabel.text = 'Has collision info: None'
		else:
			self.__collisionInfoLabel.text = 'Has collision info: Available'

@Singleton
class ObjectDescriptor:
	def updateObjectDescriptors(self):
		self.setObject(self.__currentObject)

	def openCollisionPopUp(self, *args):
		CollisionInformationPopup.Instance().showPopUp()
		if (self.__currentObject is not None):
			self.setObject(self.__currentObject)
	
	def openLayerPopUp(self, *args):
		LayerInformationPopup.Instance().showPopUp()
		if (self.__currentObject is not None):
			self.setObject(self.__currentObject)

	def __init__(self, baseObjectAccordion, renderedObjectAccordion):
		self.__currentObject = None
		self.__baseObjectDescriptor = BaseObjectDescriptor.Instance(baseObjectAccordion)
		self.__renderedObjectDescriptor = RenderedObjectDescriptor.Instance(renderedObjectAccordion,
			self.openCollisionPopUp, self.openLayerPopUp)
		self.__baseObjectDescriptor.setActive()

	def resetAllWidgets(self):
		self.__baseObjectDescriptor.setValues()
		self.__renderedObjectDescriptor.setValuesNoActive()

	def setObject(self, obj):
		path = obj.getPath()
		size = obj.getSize()
		cwd = getcwd() + '/'
		if (cwd == path[:len(cwd)]):
			path = path[len(cwd):]

		if (obj.getType() == ObjectTypes.renderedObject):
			self.__renderedObjectDescriptor.setValues(path, size, obj.getScale(), obj.getLayer(), obj.getName(),
				obj.getFlipX(), obj.getFlipY(), obj.getCollisionInfo())

		else:
			self.__baseObjectDescriptor.setValues(path, size, obj)

		self.__currentObject = obj

	def getCurrentObject(self):
		return self.__currentObject

	def clearCurrentObject(self):
		if (self.__currentObject is None):
			return

		if (self.__currentObject.getType() == ObjectTypes.renderedObject):
			MultipleSelectionDescriptor.Instance().setValuesNoActive()
			self.__renderedObjectDescriptor.setValuesNoActive()
			self.__baseObjectDescriptor.setValues()
		else:
			MultipleSelectionDescriptor.Instance().setValuesNoActive()
			self.__renderedObjectDescriptor.setValuesNoActive()
			self.__baseObjectDescriptor.setValues()

		self.__currentObject = None

