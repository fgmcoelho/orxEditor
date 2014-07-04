from singleton import Singleton

from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

from os import getcwd
from editorobjects import ObjectTypes
from collision import CollisionInformationPopup

@Singleton
class BaseObjectDescriptor:
	
	def __init__(self, accordionItem):
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__pathLabel = Label(text = 'Path: ', size_hint = (1.0, 0.5))
		self.__sizeLabel = Label(text = 'Size: ', size_hint = (1.0, 0.5))
		self.__layout.add_widget(self.__pathLabel)
		self.__layout.add_widget(self.__sizeLabel)
		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)

	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False

	def __setValues(self, path, size):
		self.__pathLabel.text = 'Path: ' + str(path)
		self.__sizeLabel.text = 'Size: ' + str(size)

	def setValues(self, path = '', size=''):
		self.__setValues(path, size)
		self.setActive()

	def setValuesNoActive(self, path = '', size = ''):
		self.__setValues(path, size)

@Singleton
class MultipleSelectionDescriptor:

	def __init__(self, accordionItem):
		self.__layout = BoxLayout (orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__selectedLabel = Label(text = 'Selected: 0')
		
		self.__layout.add_widget(self.__selectedLabel)
		
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
	def __init__(self, accordionItem, popUpMethod):
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__pathLabel = Label(text = 'Path: ', size_hint = (1.0, 0.2))

		self.__nameLabel = Label(text = 'Name: ', size_hint = (1.0, 0.2))

		self.__flipBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__flipxLabel = Label(text = 'Flipped on X: ', size_hint = (0.5, 1.0))
		self.__flipyLabel = Label(text = 'Flipped on Y: ', size_hint = (0.5, 1.0))
		self.__flipBox.add_widget(self.__flipxLabel)
		self.__flipBox.add_widget(self.__flipyLabel)

		self.__sizeScaleLayerBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__sizeLabel = Label(text = 'Size: ', size_hint = (0.333, 1.0))
		self.__scaleLabel = Label(text = 'Scale: ', size_hint = (0.333, 1.0))
		self.__layerLabel = Label(text = 'Layer: ', size_hint = (0.3334, 1.0))
		
		self.__sizeScaleLayerBox.add_widget(self.__sizeLabel)
		self.__sizeScaleLayerBox.add_widget(self.__scaleLabel)
		self.__sizeScaleLayerBox.add_widget(self.__layerLabel)

		self.__collisionBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__collisionInfoLabel = Label(text = 'Has collision info: ')
		self.__collisionHandler = Button(text = 'Edit Collision', size_hint = (0.3, 1.0))
		self.__collisionHandler.bind(on_release=popUpMethod)
		
		self.__collisionBox.add_widget(self.__collisionInfoLabel)
		self.__collisionBox.add_widget(self.__collisionHandler)

		self.__layout.add_widget(self.__pathLabel)
		self.__layout.add_widget(self.__nameLabel)
		self.__layout.add_widget(self.__flipBox)
		self.__layout.add_widget(self.__sizeScaleLayerBox)
		self.__layout.add_widget(self.__collisionBox)

		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)
	
	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False

	def setValues(self, path = '', size = '', scale = '', layer = '', name = '', flipX = '', flipY = '', collisionInfo = None):
		self.__setValues(path, size, scale, layer, name, flipX, flipY, collisionInfo)
		self.setActive()

	def setValuesNoActive(self, path = '', size = '', scale = '', layer = '', name = '', flipX = '', flipY = '', 
			collisionInfo = None):
		self.__setValues(path, size, scale, layer, name, flipX, flipY, collisionInfo)

	def __setValues(self, path, size, scale, layer, name, flipX, flipY, collisionInfo):
		self.__pathLabel.text = 'Path: ' + str(path)
		self.__sizeLabel.text = 'Size: ' + str(size)
		self.__scaleLabel.text = 'Scale: ' + str(scale)
		self.__layerLabel.text = 'Layer: ' + str(layer)
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

	def openCollisionPopUp(self, ignore):
		
		CollisionInformationPopup.Instance().showPopUp()
		if (self.__currentObject is not None):
			self.setObject(self.__currentObject)

	def __init__(self, baseObjectAccordion, renderedObjectAccordion):
		
		self.__currentObject = None

		self.__baseObjectDescriptor = BaseObjectDescriptor.Instance(baseObjectAccordion)
		self.__renderedObjectDescriptor = RenderedObjectDescriptor.Instance(renderedObjectAccordion, self.openCollisionPopUp)

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
			self.__renderedObjectDescriptor.setValues(path, size, obj.getScale(), obj.getLayer(), obj.getName(), obj.getFlipX(),
				obj.getFlipY(), obj.getCollisionInfo())
		
		else:
			self.__baseObjectDescriptor.setValues(path, size)

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

