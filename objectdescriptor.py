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

class DescriptorLinesConfigs(object):
	def __init__(self):
		super(DescriptorLinesConfigs, self).__init__()
		self._halfLineLabel = descriptorLabelDefault.copy()
		self._halfLineLabel['size_hint'] = (0.5, 1.0)
		self._halfLineLayout = {
			'orientation' : 'horizontal',
			'size_hint' : (1.0, None),
			'height' : descriptorLabelDefault['height'],
		}

class DescriptorButtons(DescriptorLinesConfigs):
	def _call_on_press(self, button, touch):
		k = button.text.split('(')[1].split(')')[0]
		ModulesAccess.get('SceneHandler').processKeyDown((None, k))

	def _add_buttons(self, layout):
		for line in self._linesList:
			layout.add_widget(line)

	def __init__(self):
		super(DescriptorButtons, self).__init__()

		self._linesList = []
		self._copyLeftButton = CancelableButton(text = 'Copy left (a)', on_release = self._call_on_press,
			**descriptorButtonDoubleSize)
		self._copyRightButton = CancelableButton(text = 'Copy right (d)', on_release = self._call_on_press,
			**descriptorButtonDoubleSize)
		self._copyUpButton = CancelableButton(text = 'Copy up (w)', on_release = self._call_on_press,
			**descriptorButtonDoubleSize)
		self._copyDownButton = CancelableButton(text = 'Copy down (s)', on_release = self._call_on_press,
			**descriptorButtonDoubleSize)
		self._unselectButton = CancelableButton(text = 'Unselect (e)', on_release = self._call_on_press,
			**descriptorButtonDoubleSize)
		self._alignButton = CancelableButton(text = 'Align (q)', on_release = self._call_on_press,
			**descriptorButtonDefault)
		self._editCollisionButton = CancelableButton(text = 'Edit collision', on_release = self._call_on_press,
			**descriptorButtonDoubleSize)
		self._editGroupButton = CancelableButton(text = 'Edit Group', on_release = self._call_on_press,
			**descriptorButtonDefault)
		self._flipXButton = CancelableButton(text = 'Flip X (f)', on_release = self._call_on_press,
			**descriptorButtonDefault)
		self._flipYButton = CancelableButton(text = 'Flip Y (g)', on_release = self._call_on_press,
			**descriptorButtonDefault)
		self._undoButton = CancelableButton(text = 'Undo (z)', on_release = self._call_on_press,
			**descriptorButtonDefault)
		self._redoButton = CancelableButton(text = 'Redo (y)', on_release = self._call_on_press,
			**descriptorButtonDefault)

		# Lines:
		self._linesList.append(BoxLayout(**self._halfLineLabel))
		self._linesList[-1].add_widget(self._copyLeftButton)
		self._linesList[-1].add_widget(self._copyRightButton)
		self._linesList[-1].add_widget(self._flipXButton)
		self._linesList.append(BoxLayout(**self._halfLineLabel))
		self._linesList[-1].add_widget(self._copyUpButton)
		self._linesList[-1].add_widget(self._copyDownButton)
		self._linesList[-1].add_widget(self._flipYButton)
		self._linesList.append(BoxLayout(**self._halfLineLabel))
		self._linesList[-1].add_widget(self._editCollisionButton)
		self._linesList[-1].add_widget(self._editGroupButton)
		self._linesList[-1].add_widget(self._alignButton)
		self._linesList.append(BoxLayout(**self._halfLineLabel))
		self._linesList[-1].add_widget(self._unselectButton)
		self._linesList[-1].add_widget(self._undoButton)
		self._linesList[-1].add_widget(self._redoButton)

class GroupAndCollisionLabel(DescriptorLinesConfigs):
	def __init__(self):
		super(GroupAndCollisionLabel, self).__init__()
		self._layerCollisionBox = BoxLayout(**self._halfLineLayout)
		self._layerLabel = AlignedLabel(text = 'Group: ', **self._halfLineLabel)
		self._collisionInfoLabel = AlignedLabel(text = 'Has collision info: ', **self._halfLineLabel)
		self._layerCollisionBox.add_widget(self._layerLabel)
		self._layerCollisionBox.add_widget(self._collisionInfoLabel)

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

class NewMultipleSelectionDescriptor(CleanDescriptorLayoutGetter, SeparatorLabel, DescriptorButtons,
		GroupAndCollisionLabel):

	def __setValues(self, objects):
		self._selectedLabel.text = 'Selected: ' + str(len(objects))
		s = set()
		collisionCount = 0
		for obj in objects:
			s.add(obj.getLayer())
			if (obj.getCollisionInfo() is not None):
				collisionCount += 1

		if (len(s) == 1):
			self._layerLabel.text = 'Group: ' + objects[0].getLayer()
		else:
			self._layerLabel.text = 'Group: Varies'

		if (collisionCount == 0):
			self._collisionInfoLabel.text = 'Has collision info: No'
		else:
			self._collisionInfoLabel.text = 'Has collision info: Yes'

	def __init__(self):
		super(NewMultipleSelectionDescriptor, self).__init__()
		self._selectedLabel = AlignedLabel(text = 'Selected: 0', **descriptorLabelDefault)

	def set(self, objects = None):
		layout = self._getParentLayout()
		layout.add_widget(self._selectedLabel)
		layout.add_widget(self._layerCollisionBox)
		layout.add_widget(self._separator)
		self._add_buttons(layout)
		if (objects is None):
			self.__setValues()
		else:
			self.__setValues(objects)

class NewRenderedObjectDescriptor(ObjectDescriptGeneric, CleanDescriptorLayoutGetter, SeparatorLabel,
		DescriptorButtons, GroupAndCollisionLabel):
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

		self._nameLabel = AlignedLabel(text = 'Name: ', **descriptorLabelDefault)

		self._flipBox = BoxLayout(**self._halfLineLayout)
		self._flipxLabel = AlignedLabel(text = 'Flipped on X: ', **self._halfLineLabel)
		self._flipyLabel = AlignedLabel(text = 'Flipped on Y: ', **self._halfLineLabel)
		self._flipBox.add_widget(self._flipxLabel)
		self._flipBox.add_widget(self._flipyLabel)

		self._sizeScaleBox = BoxLayout(**self._halfLineLayout)
		self._sizeLabel = AlignedLabel(text = 'Size: ', **self._halfLineLabel)
		self._scaleLabel = AlignedLabel(text = 'Scale: ', **self._halfLineLabel)

		self._sizeScaleBox.add_widget(self._sizeLabel)
		self._sizeScaleBox.add_widget(self._scaleLabel)

		self._scaleUpButton = CancelableButton(text = 'Scale+ (r)', on_release = self._call_on_press,
			**descriptorButtonDefault)
		self._scaleDownButton = CancelableButton(text = 'Scale- (t)', on_release = self._call_on_press,
			**descriptorButtonDefault)

		self._linesList[2].add_widget(self._scaleUpButton)
		self._linesList[3].add_widget(self._scaleDownButton)

	def set(self, obj = None):
		layout = self._getParentLayout()
		layout.add_widget(self._nameLabel)
		layout.add_widget(self._pathLabel)
		layout.add_widget(self._flipBox)
		layout.add_widget(self._sizeScaleBox)
		layout.add_widget(self._layerCollisionBox)
		layout.add_widget(self._separator)
		self._add_buttons(layout)

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
		self._multipleObjectsDescritor = NewMultipleSelectionDescriptor()
		self._baseObjectDescriptor.set()

	def set(self, objectOrList):
		if (type(objectOrList) is list):
			if (len(objectOrList) == 0):
				self._baseObjectDescriptor.set()
				return
			elif (len(objectOrList) > 1):
				self._multipleObjectsDescritor.set(objectOrList)
				return
			else:
				objectOrList = objectOrList[0]

		if (objectOrList is None):
			self._baseObjectDescriptor.set()
		elif (isinstance(objectOrList, BaseObject) ==True):
			self._baseObjectDescriptor.set(objectOrList)
		elif (isinstance(objectOrList, RenderedObject) == True):
			self._renderedObjectDescriptor.set(objectOrList)
		else:
			raise Exception('Unsuported object received: ' + str(objectOrList))

