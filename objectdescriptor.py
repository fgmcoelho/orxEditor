from singleton import Singleton

from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

from os import getcwd
from editorobjects import ObjectTypes, BaseObject, RenderedObject
from collision import CollisionInformationPopup
from editorutils import CancelableButton, AlertPopUp, AlignedLabel
from communicationobjects import ObjectDescriptorToResourceLoarder
from layer import LayerInformationPopup
from modulesaccess import ModulesAccess
from editorheritage import LayoutGetter, SeparatorLabel
from uisizes import descriptorSize, descriptorLabelDefault, descriptorButtonDefault, descriptorButtonDoubleSize

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
		self.__pathLabel = Label(text = 'Path: ', size_hint = (1.0, 0.2), multiline=False, halign='left')
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

class DescriptorButtons(object):
	def __init__(self):
		super(DescriptorButtons, self).__init__()
		self._linesList = []
		self._copyLeftButton = CancelableButton(text = 'Copy left (a)', **descriptorButtonDoubleSize)
		self._copyRightButton = CancelableButton(text = 'Copy right (d)', **descriptorButtonDoubleSize)
		self._copyUpButton = CancelableButton(text = 'Copy up (w)', **descriptorButtonDoubleSize)
		self._copyDownButton = CancelableButton(text = 'Copy down (s)', **descriptorButtonDoubleSize)
		self._unselectButton = CancelableButton(text = 'Unselect (e)', **descriptorButtonDoubleSize)
		self._alignButton = CancelableButton(text = 'Align (q)', **descriptorButtonDefault)
		self._editCollisionButton = CancelableButton(text = 'Edit collision', **descriptorButtonDoubleSize)
		self._editGroupButton = CancelableButton(text = 'Edit Group', **descriptorButtonDefault)
		self._flipXButton = CancelableButton(text = 'Flip X (f)', **descriptorButtonDefault)
		self._flipYButton = CancelableButton(text = 'Flip Y (g)', **descriptorButtonDefault)
		self._undoButton = CancelableButton(text = 'Undo (z)', **descriptorButtonDefault)
		self._redoButton = CancelableButton(text = 'Redo (y)', **descriptorButtonDefault)

class CleanDescriptorLayoutGetter(object):
	def _getParentLayout(self):
		layout = ModulesAccess.get('ObjectDescriptor').getLayout()
		layout.clear_widgets()
		return layout

class ObjectDescriptGeneric(object):
	def _setValues(self, path = '', size = ''):
		self._pathLabel.text = 'Path: ' + str(path)
		self._sizeLabel.text = 'Size: ' + str(size)

	def __init__(self):
		super(ObjectDescriptGeneric, self).__init__()
		self._pathLabel = AlignedLabel(text = 'Path: ', **descriptorLabelDefault)
		self._describedObject = None

class NewMultipleSelectionDescriptor(CleanDescriptorLayoutGetter, SeparatorLabel):
	def __setValues(self, count = 0):
		self._selectedLabel.text = 'Selected: ' + str(count)

	def __init__(self):
		super(NewMultipleSelectionDescriptor, self).__init__()
		self._selectedLabel = AlignedLabel(text = 'Selected: 0', **descriptorLabelDefault)
		self._layerLabel = AlignedLabel(text = 'Group info:', **descriptorLabelDefault)
		self._layerButton = CancelableButton(text = 'Edit Group', size_hint = (0.3, 1.0),
			on_release = LayerInformationPopup.Instance().showPopUp)
		self._layerBox = BoxLayout(orientation = 'horizontal', height = descriptorLabelDefault['height'])
		self._layerBox.add_widget(self._layerLabel)
		self._layerBox.add_widget(self._layerButton)

		self._collisionBox = BoxLayout(orientation = 'horizontal', height = descriptorLabelDefault['height'])
		self._collisionInfoLabel = AlignedLabel(text = 'Collision info:', **descriptorLabelDefault)
		self._collisionHandler = CancelableButton(text = 'Edit Collision', size_hint = (0.3, 1.0),
			on_release = CollisionInformationPopup.Instance().showPopUp)
		self._collisionBox.add_widget(self.__collisionInfoLabel)
		self._collisionBox.add_widget(self.__collisionHandler)

	def set(self, objects = None):
		layout = self._getParentLayout()
		layout.add_widget(self._selectedLabel)
		layout.add_widget(self._separator)
		layout.add_widget(self._layerBox)
		layout.add_widget(self._collisionBox)
		if (objects is None):
			self._setValues()
		else:
			self._setValues(len(objects))

class NewRenderedObjectDescriptor(ObjectDescriptGeneric, CleanDescriptorLayoutGetter, SeparatorLabel,
		DescriptorButtons):
	def _setValues(self, path = '', size = '', scale = '', layer = '', name = '', flipX = '', flipY = '',
			collisionInfo = None):
		super(NewRenderedObjectDescriptor, self)._setValues(path, size)
		self._scaleLabel.text = 'Scale: ' + str(scale)
		self._layerLabel.text = 'Group: ' + str(layer)
		self._nameLabel.text = 'Name: ' + str(name)
		self._flipxLabel.text = 'Flipped on X: ' + str(flipX)
		self._flipyLabel.text = 'Flipped on Y: ' + str(flipY)
		if (collisionInfo is None):
			self._collisionInfoLabel.text = 'Has collision info: No'
		else:
			self._collisionInfoLabel.text = 'Has collision info: Yes'

	def __init__(self):
		super(NewRenderedObjectDescriptor, self).__init__()

		halfLineLabel = descriptorLabelDefault.copy()
		halfLineLabel['size_hint'] = (0.5, 1.0)
		halfLineLayout = {
			'orientation' : 'horizontal',
			'size_hint' : (1.0, None),
			'height' : descriptorLabelDefault['height'],
		}

		self._nameLabel = AlignedLabel(text = 'Name: ', **descriptorLabelDefault)

		self._flipBox = BoxLayout(**halfLineLayout)
		self._flipxLabel = AlignedLabel(text = 'Flipped on X: ', **halfLineLabel)
		self._flipyLabel = AlignedLabel(text = 'Flipped on Y: ', **halfLineLabel)
		self._flipBox.add_widget(self._flipxLabel)
		self._flipBox.add_widget(self._flipyLabel)

		self._sizeScaleBox = BoxLayout(**halfLineLayout)
		self._sizeLabel = AlignedLabel(text = 'Size: ', **halfLineLabel)
		self._scaleLabel = AlignedLabel(text = 'Scale: ', **halfLineLabel)

		self._sizeScaleBox.add_widget(self._sizeLabel)
		self._sizeScaleBox.add_widget(self._scaleLabel)

		self._layerScaleBox = BoxLayout(**halfLineLayout)
		self._layerLabel = AlignedLabel(text = 'Group: ', **halfLineLabel)
		self._collisionInfoLabel = AlignedLabel(text = 'Has collision info: ', **halfLineLabel)
		self._layerScaleBox.add_widget(self._layerLabel)
		self._layerScaleBox.add_widget(self._collisionInfoLabel)

		# Lines:
		self._linesList.append(BoxLayout(**halfLineLabel))
		self._linesList[-1].add_widget(self._copyLeftButton)
		self._linesList[-1].add_widget(self._copyRightButton)
		self._linesList[-1].add_widget(self._flipXButton)
		self._linesList.append(BoxLayout(**halfLineLabel))
		self._linesList[-1].add_widget(self._copyUpButton)
		self._linesList[-1].add_widget(self._copyDownButton)
		self._linesList[-1].add_widget(self._flipYButton)
		self._linesList.append(BoxLayout(**halfLineLabel))
		self._linesList[-1].add_widget(self._editCollisionButton)
		self._linesList[-1].add_widget(self._editGroupButton)
		self._linesList[-1].add_widget(self._alignButton)
		self._linesList.append(BoxLayout(**halfLineLabel))
		self._linesList[-1].add_widget(self._unselectButton)
		self._linesList[-1].add_widget(self._undoButton)
		self._linesList[-1].add_widget(self._redoButton)

	def set(self, obj = None):
		layout = self._getParentLayout()
		layout.add_widget(self._nameLabel)
		layout.add_widget(self._pathLabel)
		layout.add_widget(self._flipBox)
		layout.add_widget(self._sizeScaleBox)
		layout.add_widget(self._layerScaleBox)
		layout.add_widget(self._separator)
		for line in self._linesList:
			layout.add_widget(line)

		self._describedObject = obj
		if (self._describedObject is not None):
			self._setValues(obj.getPath(), obj.getSize(), obj.getScale(), obj.getLayer(), obj.getName(),
				obj.getFlipX(), obj.getFlipY(),	obj.getCollisionInfo())
		else:
			self._setValues()

class NewBaseObjectDescriptor(ObjectDescriptGeneric, CleanDescriptorLayoutGetter, SeparatorLabel):
	def _openResourceLoader(self, *args):
		if (self._describedObject is None or isinstance(self._describedObject, BaseObject) == False):
			AlertPopUp('Error', 'No compatible object selected.', 'Ok').open()
		else:
			# TODO: Add the modules access here
			#ObjectDescriptorToResourceLoarder.Instance().openPopUp(self._objRef.getPath())
			ModulesAccess.get('ResourceLoader').open(self._describedObject.getPath())

	def __draw(self, *args):
		if (self._describedObject is not None):
			ModulesAccess.get('SceneHandler').draw(self._describedObject)

	def __init__(self):
		super(NewBaseObjectDescriptor, self).__init__()
		self._sizeLabel = AlignedLabel(text = 'Size: ', **descriptorLabelDefault)
		self._loaderLine = BoxLayout(orientation = 'horizontal', height = descriptorLabelDefault['height'])
		self._loaderLine.add_widget(CancelableButton(text = 'Resource Loader', on_release = self._openResourceLoader,
			**descriptorButtonDoubleSize))
		self._loaderLine.add_widget(CancelableButton(text = 'Draw', on_release = self.__draw,
			**descriptorButtonDefault))

	def set(self, obj = None):
		layout = self._getParentLayout()
		layout.add_widget(self._pathLabel)
		layout.add_widget(self._sizeLabel)
		layout.add_widget(self._separator)
		layout.add_widget(self._loaderLine)
		self._describedObject = obj
		if (obj is not None):
			self._setValues(obj.getPath(), obj.getSize())
		else:
			self._setValues()

class NewObjectDescriptor(LayoutGetter):
	def __init__(self):
		ModulesAccess.add('ObjectDescriptor', self)
		self._layout = BoxLayout(orientation = 'vertical', height = descriptorSize['height'])

		self._baseObjectDescriptor = NewBaseObjectDescriptor()
		self._renderedObjectDescriptor = NewRenderedObjectDescriptor()

		self._baseObjectDescriptor.set()

	def set(self, objectOrList):
		if (type(objectOrList) is list):
			self._multipleObjectsDescritor.set(objectOrList)
		else:
			if (isinstance(objectOrList, BaseObject) ==True):
				self._baseObjectDescriptor.set(objectOrList)
			elif (isinstance(objectOrList, RenderedObject) == True):
				self._renderedObjectDescriptor.set(objectOrList)
			else:
				raise Exception('Unsuported object received.')

