from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

from editorutils import CancelableButton, Alert, Dialog, AlignedLabel, AlignedToggleButton
from editorheritage import SeparatorLabel, AutoFocusInputUser
from keyboard import KeyboardAccess, KeyboardGuardian
from uisizes import defaultLabelSize, defaultLineSize, defaultSmallButtonSize, defaultInputSize, defaultFontSize,\
	defaultDoubleLineSize
from modulesaccess import ModulesAccess

class LayerEditorPopup(AutoFocusInputUser, SeparatorLabel, KeyboardAccess):
	def __doDeleteLayer(self):
		if (self.__layerToRemoveName is not None):
			ModulesAccess.get('LayerGuardian').deleteLayerByName(self.__layerToRemoveName)
			allObjList = ModulesAccess.get('SceneHandler').getAllObjects()
			for obj in allObjList:
				if (obj.getLayer() == self.__layerToRemoveName):
					obj.setLayer('default')

			self.__layerToRemoveName = None
			self.__render()

	def __updateLayers(self, *args):
		button = args[0]
		operation, layerName = button.id.split('#')
		if (operation == 'inc'):
			ModulesAccess.get('LayerGuardian').increasePriority(layerName)
			self.__render()
		elif (operation == 'dec'):
			ModulesAccess.get('LayerGuardian').decreasePriority(layerName)
			self.__render()
		else:
			allObjList = ModulesAccess.get('SceneHandler').getAllObjects()
			count = 0
			self.__layerToRemoveName = layerName
			for obj in allObjList:
				if (obj.getLayer() == layerName):
					count += 1

			if (count != 0):
				warn = Dialog(
					self.__doDeleteLayer,
					'Warning',
					'Removing this group will set %d object%s to the\n\'default\' group.\n'\
					'This operation can not be reverted.' % (count, 's' if count > 1 else ''),
					'Ok',
					'Cancel', None, None
				)
				warn.open()

			else:
				warn = Dialog(
					self.__doDeleteLayer,
					'Warning',
					'If you continue, this group will be removed.\nThis operation can not be reverted.',
					'Ok',
					'Cancel',
				)
				warn.open()

	def __processAddLayer(self, *args):
		newLayer = self._autoFocusInput.text.strip()
		if (newLayer == ''):
			error = Alert('Error', 'Layer name can\'t be empty.', 'Ok', self.__reaplyFocus)
			error.open()
			return

		layerList = ModulesAccess.get('LayerGuardian').getLayerList()
		for layer in layerList:
			if (newLayer == layer.getName()):
				error = Alert('Error', 'This name has already been used.', 'Ok', self.__reaplyFocus)
				error.open()
				return

		invalidSet = []
		for char in newLayer:
			if (char not in self._validCharacters):
				invalidSet.append(char)

		if (invalidSet != []):
			error = Alert('Error', 'Found invalid characters in the name:\n ' + ''.join(invalidSet), 'Ok',
				self.__reaplyFocus)
			error.open()
			return

		ModulesAccess.get('LayerGuardian').addNewLayer(newLayer)
		self._autoFocusInput.text = ''
		self.__render()

	def __reaplyFocus(self):
		layerList = ModulesAccess.get('LayerGuardian').getLayerList()
		if (len(layerList) != self.__maxLayers):
			self.__inputBar.clear_widgets()
			self.__inputBar.add_widget(self._autoFocusInput)
			self.__inputBar.add_widget(self.__layerAddButton)
			Clock.schedule_once(self._delayedFocus, 0)

	def __render(self):
		self.__layout.clear_widgets()
		layerList = ModulesAccess.get('LayerGuardian').getLayerList()
		for layer in layerList:
			name = layer.getName()
			line = BoxLayout(orientation = 'horizontal', id = 'line_' + name, **defaultLineSize)
			line.add_widget(AlignedLabel(text = name, **defaultLabelSize))
			line.add_widget(CancelableButton(text = '+Priority', on_release = self.__updateLayers, id = 'inc#' + name,
				**defaultSmallButtonSize))
			line.add_widget(CancelableButton(text = '-Priority', on_release = self.__updateLayers, id = 'dec#' + name,
				**defaultSmallButtonSize))
			if (name != 'default'):
				line.add_widget(CancelableButton(text = 'Remove', on_release = self.__updateLayers, id = 'rem#' + name,
					**defaultSmallButtonSize))
			else:
				line.add_widget(AlignedLabel(text='', **defaultSmallButtonSize))
			self.__layout.add_widget(line)

		self.__layout.add_widget(self.getSeparator())

		if (len(layerList) == self.__maxLayers):
			self.__layout.add_widget(AlignedLabel(text = 'Maximum number of layers (%u) reached.' %
				(self.__maxLayers, ), **defaultLabelSize))
		else:
			self.__reaplyFocus()
			self.__layout.add_widget(self.__inputBar)

		self.__layout.add_widget(AlignedLabel(text = '', **defaultLineSize))
		self.__layout.add_widget(self.__closeLine)

	def __init__(self):
		super(LayerEditorPopup, self).__init__()
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))

		self.__closeButton = CancelableButton(text = 'Done', on_release = self.close, **defaultSmallButtonSize)
		self.__closeLine = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		self.__closeLine.add_widget(
			AlignedLabel(
				text =  'Hint: Lower priority (closer to the top of the window) are drawn\n'\
				'first, hence they will be drawn under the ones with higher priority.',
				**defaultDoubleLineSize
			)
		)
		self.__closeLine.add_widget(self.__closeButton)

		self.__inputBar = BoxLayout(orientation = 'horizontal', **defaultInputSize)
		self._autoFocusInput.bind(on_text_validate = self.__processAddLayer)
		self.__layerAddButton = CancelableButton(text = 'Add', on_release = self.__processAddLayer,
			**self._addButtonSize)

		self.__popup = Popup(title = 'Groups Editor', content = self.__layout, auto_dismiss = False)
		self.__maxLayers = 16
		self.__layerToRemoveName = None

	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__render()
		self.__popup.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		ModulesAccess.get('LayerInformation').update()
		self.__popup.dismiss()


class LayerInformationPopup(KeyboardAccess, SeparatorLabel):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.close()

		elif (len(self.__buttonList) != 1 and keycode[1] in ['up', 'down']):
			index = self.__getSelectedButtonIndex()
			if (index == -1):
				self.__buttonList[0].state = 'down'
				return

			if (keycode[1] == 'up'):
				newIndex = (index + 1) % len(self.__buttonList)
			else:
				newIndex = (index - 1) % len(self.__buttonList)

			self.__buttonList[index].state = 'normal'
			self.__buttonList[newIndex].state = 'down'

		elif (keycode[1] == 'enter'):
			self.__save()

	def __getSelectedButtonIndex(self):
		for i in range(len(self.__buttonList)):
			if (self.__buttonList[i].state == 'down'):
				return i
		return -1

	def __save(self, *args):
		newLayer = None
		for button in self.__buttonList:
			if (button.state == 'down'):
				assert(newLayer is None)
				newLayer = button.text

		if (newLayer is None):
			errorAlert = Alert(
				'Error',
				'No layer selected!\nYou must select a new layer.',
				'Ok'
			)
			errorAlert.open()
		else:
			for obj in self.__objectsList:
				obj.setLayer(newLayer)

			ModulesAccess.get('SceneHandler').redraw()
			ModulesAccess.get('ObjectDescriptor').update()
			self.close()

	def __getLayerNameIfAllEqual(self):
		firstLayer = self.__objectsList[0].getLayer()
		for obj in self.__objectsList[1:]:
			if (obj.getLayer() != firstLayer):
				return None

		return firstLayer

	def __render(self):
		self.__layout.clear_widgets()
		if (len(self.__objectsList) == 1):
			self.__layout.add_widget(AlignedLabel(text = 'Select the new group for the object:',
				**defaultLabelSize))
		else:
			self.__layout.add_widget(AlignedLabel(text = 'Select the new group for the objects:',
				**defaultLabelSize))

		self.__buttonList = []
		layerToMark = self.__getLayerNameIfAllEqual()
		layerList = ModulesAccess.get('LayerGuardian').getLayerList()
		for layer in layerList:
			if (layerToMark is not None and layerToMark == layer.getName()):
				state = 'down'
			else:
				state = 'normal'
			layerButton = AlignedToggleButton(text = layer.getName(), group = 'layers', state = state,
					**defaultLabelSize)
			self.__layout.add_widget(layerButton)
			self.__buttonList.append(layerButton)

		self.__layout.add_widget(self.getSeparator())
		self.__layout.add_widget(self.__bottomLine)

	def __init__(self):
		super(self.__class__, self).__init__()
		self.__editFlagsPopup = LayerEditorPopup()
		self.__popup = Popup(title = 'Group Selector', auto_dismiss = False)
		self.__layout = BoxLayout(orientation = 'vertical')
		self.__objectsList = None

		self.__bottomLine = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		self.__cancelButton = CancelableButton(text = 'Cancel', on_release = self.close, **defaultSmallButtonSize)
		self.__doneButton = CancelableButton(text = 'Done', on_release = self.__save, **defaultSmallButtonSize)
		self.__editLayersButton = CancelableButton(text = 'Edit groups', on_release = self.__editFlagsPopup.open,
			**defaultSmallButtonSize)
		self.__bottomLine.add_widget(self.__editLayersButton)
		self.__bottomLine.add_widget(AlignedLabel(text = '', **defaultLineSize))
		self.__bottomLine.add_widget(self.__cancelButton)
		self.__bottomLine.add_widget(self.__doneButton)
		self.__popup.content = self.__layout
		ModulesAccess.add('LayerInformation', self)

	def update(self):
		self.__render()

	def open(self, *args):
		objList = ModulesAccess.get('SceneHandler').getCurrentSelection()
		if (objList == []):
			errorAlert = Alert(
				'Error',
				'No object is selected!\nYou need to select at least one object from the scene.',
				'Ok'
			)
			errorAlert.open()
		else:
			self.__objectsList = objList
			self.__render()
			KeyboardGuardian.Instance().acquireKeyboard(self)
			self.__popup.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()

