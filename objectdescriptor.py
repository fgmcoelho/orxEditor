from kivy.uix.boxlayout import BoxLayout

from editorobjects import BaseObject, RenderedObject
from editorutils import CancelableButton, Alert, AlignedLabel
from modulesaccess import ModulesAccess
from editorheritage import LayoutGetter, SeparatorLabel
from uisizes import descriptorSize, defaultLabelSize, defaultSmallButtonSize, defaultLargeButtonSize

class DescriptorLinesConfigs(object):
	def __init__(self):
		super(DescriptorLinesConfigs, self).__init__()
		self._halfLineLabel = defaultLabelSize.copy()
		self._halfLineLabel['size_hint'] = (0.5, None)
		self._halfLineLayout = {
			'orientation' : 'horizontal',
			'size_hint' : (1.0, None),
			'height' : defaultLabelSize['height'],
		}

class DescriptorButtons(DescriptorLinesConfigs):
	def _call_increase_priority(self, *args):
		ModulesAccess.get('SceneHandler').processKeyDown((None, 'pageup'))

	def _call_decrease_priority(self, *args):
		ModulesAccess.get('SceneHandler').processKeyDown((None, 'pagedown'))

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
			**defaultLargeButtonSize)
		self._copyRightButton = CancelableButton(text = 'Copy right (d)', on_release = self._call_on_press,
			**defaultLargeButtonSize)
		self._copyUpButton = CancelableButton(text = 'Copy up (w)', on_release = self._call_on_press,
			**defaultLargeButtonSize)
		self._copyDownButton = CancelableButton(text = 'Copy down (s)', on_release = self._call_on_press,
			**defaultLargeButtonSize)
		self._unselectButton = CancelableButton(text = 'Unselect (e)', on_release = self._call_on_press,
			**defaultLargeButtonSize)
		self._alignButton = CancelableButton(text = 'Align (q)', on_release = self._call_on_press,
			**defaultSmallButtonSize)
		self._editCollisionButton = CancelableButton(
			text = 'Edit collision',
			on_release = ModulesAccess.get('CollisionEditor').open,
			**defaultLargeButtonSize)
		self._editGroupButton = CancelableButton(
			text = 'Edit Group',
			on_release = ModulesAccess.get('LayerInformation').open,
			**defaultSmallButtonSize
		)
		self._flipXButton = CancelableButton(text = 'Flip X (f)', on_release = self._call_on_press,
			**defaultSmallButtonSize)
		self._flipYButton = CancelableButton(text = 'Flip Y (g)', on_release = self._call_on_press,
			**defaultSmallButtonSize)
		self._undoButton = CancelableButton(text = 'Undo (z)', on_release = self._call_on_press,
			**defaultSmallButtonSize)
		self._redoButton = CancelableButton(text = 'Redo (y)', on_release = self._call_on_press,
			**defaultSmallButtonSize)
		self._increaseLayerButton = CancelableButton(text = 'Group up (PgUp)',
			on_release = self._call_increase_priority, **defaultLargeButtonSize)
		self._decreaseLayerButton = CancelableButton(text = 'Group down (PgDw)',
			on_release = self._call_decrease_priority, **defaultLargeButtonSize)

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
		self._linesList.append(BoxLayout(**self._halfLineLabel))
		self._linesList[-1].add_widget(self._increaseLayerButton)
		self._linesList[-1].add_widget(self._decreaseLayerButton)

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
		self._pathLabel = AlignedLabel(text = 'Path: ', **defaultLabelSize)
		self._describedObject = None

class MultipleSelectionDescriptor(CleanDescriptorLayoutGetter, SeparatorLabel, DescriptorButtons,
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
		super(MultipleSelectionDescriptor, self).__init__()
		self._selectedLabel = AlignedLabel(text = 'Selected: 0', **defaultLabelSize)

		self._mergeButton = CancelableButton(text = 'Merge (m)', on_release = self._call_on_press,
			**defaultSmallButtonSize)
		self._unmergeButton = CancelableButton(text = 'Break (n)', on_release = self._call_on_press,
			**defaultSmallButtonSize)

		self._linesList[2].add_widget(self._mergeButton)
		self._linesList[3].add_widget(self._unmergeButton)

	def set(self, objects = None):
		layout = self._getParentLayout()
		layout.add_widget(self._selectedLabel)
		layout.add_widget(self._layerCollisionBox)
		layout.add_widget(self.getSeparator())
		self._add_buttons(layout)
		if (objects is None):
			self.__setValues()
		else:
			self.__setValues(objects)

class RenderedObjectDescriptor(ObjectDescriptGeneric, CleanDescriptorLayoutGetter, SeparatorLabel,
		DescriptorButtons, GroupAndCollisionLabel):
	def _setValues(self, path = '', size = '', scale = '', layer = '', name = '', flipX = '', flipY = '',
			collisionInfo = None):
		super(RenderedObjectDescriptor, self)._setValues(path, size)
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
		super(RenderedObjectDescriptor, self).__init__()

		self._nameLabel = AlignedLabel(text = 'Name: ', **defaultLabelSize)

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
			**defaultSmallButtonSize)
		self._scaleDownButton = CancelableButton(text = 'Scale- (t)', on_release = self._call_on_press,
			**defaultSmallButtonSize)

		self._linesList[2].add_widget(self._scaleUpButton)
		self._linesList[3].add_widget(self._scaleDownButton)

	def set(self, obj = None):
		layout = self._getParentLayout()
		layout.add_widget(self._nameLabel)
		#layout.add_widget(self._pathLabel)
		layout.add_widget(self._flipBox)
		layout.add_widget(self._sizeScaleBox)
		layout.add_widget(self._layerCollisionBox)
		layout.add_widget(self.getSeparator())
		self._add_buttons(layout)

		self._describedObject = obj
		if (self._describedObject is not None):
			self._setValues(obj.getPath(), obj.getSize(), obj.getScale(), obj.getLayer(), obj.getName(),
				obj.getFlipX(), obj.getFlipY(),	obj.getCollisionInfo())
		else:
			self._setValues()

class NewBaseObjectDescriptor(ObjectDescriptGeneric, CleanDescriptorLayoutGetter, SeparatorLabel):
	def _openLoader(self, buttonPressed, touch):
		if (self._describedObject is None or isinstance(self._describedObject, BaseObject) == False):
			Alert('Error', 'No compatible object selected.', 'Ok').open()
		else:
			if (buttonPressed.id == 'resource'):
				ModulesAccess.get('ResourceLoader').open(self._describedObject.getPath())
			elif (buttonPressed.id == 'animation'):
				ModulesAccess.get('AnimationEditor').open(self._describedObject.getPath())
			else:
				raise Exception('Invalid button received!')

	def __draw(self, *args):
		if (self._describedObject is not None):
			ModulesAccess.get('SceneHandler').draw(self._describedObject)

	def __init__(self):
		super(NewBaseObjectDescriptor, self).__init__()
		self._sizeLabel = AlignedLabel(text = 'Size: ', **defaultLabelSize)
		self._loaderLine = BoxLayout(orientation = 'horizontal', height = defaultLabelSize['height'])
		self._loaderLine.add_widget(CancelableButton(text = 'Resource Loader', on_release = self._openLoader,
			id = 'resource', **defaultLargeButtonSize))
		self._loaderLine.add_widget(CancelableButton(text = 'Animation Editor', on_release = self._openLoader,
			id = 'animation', **defaultLargeButtonSize))
		self._loaderLine.add_widget(CancelableButton(text = 'Draw', on_release = self.__draw,
			**defaultSmallButtonSize))

	def set(self, obj = None):
		layout = self._getParentLayout()
		layout.add_widget(self._pathLabel)
		layout.add_widget(self._sizeLabel)
		layout.add_widget(self.getSeparator())
		layout.add_widget(self._loaderLine)
		self._describedObject = obj
		if (obj is not None):
			self._setValues(obj.getPath(), obj.getSize())
		else:
			self._setValues()

class ObjectDescriptor(LayoutGetter):
	def __init__(self):
		ModulesAccess.add('ObjectDescriptor', self)
		self._layout = BoxLayout(orientation = 'vertical', height = descriptorSize['height'])
		self._baseObjectDescriptor = NewBaseObjectDescriptor()
		self._renderedObjectDescriptor = RenderedObjectDescriptor()
		self._multipleObjectsDescritor = MultipleSelectionDescriptor()
		self._baseObjectDescriptor.set()
		self._currentSelected = None

	def set(self, objectOrList):
		if (type(objectOrList) is list):
			if (len(objectOrList) == 0):
				self._baseObjectDescriptor.set()
				self._currentSelected = objectOrList
				return
			elif (len(objectOrList) > 1):
				self._multipleObjectsDescritor.set(objectOrList)
				self._currentSelected = objectOrList
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

		self._currentSelected = objectOrList

	def getCurrentObject(self):
		return self._currentSelected

	def update(self):
		self.set(self._currentSelected)

