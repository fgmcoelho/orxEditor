from singleton import Singleton

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from editorutils import CancelableButton, AlertPopUp, Dialog, AlignedLabel, AlignedToggleButton
from keyboard import KeyboardAccess, KeyboardGuardian
from modulesaccess import ModulesAccess

from string import letters, digits

class LayerEditorPopup(KeyboardAccess):
	# Overloaded method
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.__close()

	def __close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		ModulesAccess.get('LayerInformation').update()
		self.__popup.dismiss()

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
		newLayer = self.__layerNameInput.text.strip()
		if (newLayer == ''):
			error = AlertPopUp('Error', 'Layer name can\'t be empty.', 'Ok', self.__reaplyFocus)
			error.open()
			return

		layerList = ModulesAccess.get('LayerGuardian').getLayerList()
		for layer in layerList:
			if (newLayer == layer.getName()):
				error = AlertPopUp('Error', 'This name has already been used.', 'Ok', self.__reaplyFocus)
				error.open()
				return

		invalidSet = []
		for char in newLayer:
			if (char not in self.__validCharacters):
				invalidSet.append(char)

		if (invalidSet != []):
			error = AlertPopUp('Error', 'Found invalid characters in the name:\n ' + ''.join(invalidSet), 'Ok',
				self.__reaplyFocus)
			error.open()
			return

		ModulesAccess.get('LayerGuardian').addNewLayer(newLayer)
		self.__layerNameInput.text = ''
		self.__render()

	def __reaplyFocus(self):
		layerList = ModulesAccess.get('LayerGuardian').getLayerList()
		if (len(layerList) != self.__maxLayers):
			self.__inputBar.clear_widgets()
			oldText = self.__layerNameInput.text
			self.__layerNameInput = TextInput(text = oldText, multiline = False, size_hint = (0.9, 1.0),
				on_text_validate = self.__processAddLayer, focus = True)
			self.__inputBar.add_widget(self.__layerNameInput)
			self.__inputBar.add_widget(self.__layerAddButton)

	def __render(self):
		self.__layout.clear_widgets()
		layerList = ModulesAccess.get('LayerGuardian').getLayerList()
		for layer in layerList:
			name = layer.getName()
			line = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.05))
			line.add_widget(AlignedLabel(text = name, size_hint = (0.85, 1.0)))
			line.add_widget(CancelableButton(text = '+', on_release = self.__updateLayers, id = 'inc#' + name,
				size_hint = (0.05, 1.0)))
			line.add_widget(CancelableButton(text = '-', on_release = self.__updateLayers, id = 'dec#' + name,
				size_hint = (0.05, 1.0)))
			if (name != 'default'):
				line.add_widget(CancelableButton(text = 'x', on_release = self.__updateLayers, id = 'rem#' + name,
					size_hint = (0.05, 1.0)))
			else:
				line.add_widget(AlignedLabel(text='', size_hint = (0.05, 1.0)))
			self.__layout.add_widget(line)

		self.__layout.add_widget(AlignedLabel(text = '', size_hint = (1.0, 0.85 - (len(layerList) * 0.05))))

		if (len(layerList) == self.__maxLayers):
			self.__layout.add_widget(AlignedLabel(text = 'Maximum number of layers (%u) reached.' %
				(self.__maxLayers, ), size_hint = (1.0, 0.05)))
		else:
			self.__reaplyFocus()
			self.__layout.add_widget(self.__inputBar)

		self.__layout.add_widget(AlignedLabel(text = '', size_hint = (1.0, 0.05)))
		self.__layout.add_widget(self.__closeLine)

	def __init__(self):
		super(LayerEditorPopup, self).__init__()
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__closeButton = CancelableButton(text = 'close', on_release = self.__close, size_hint = (0.1, 1.0))
		self.__closeLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.05))
		self.__closeLine.add_widget(AlignedLabel(
			text =  'Hint: Lower priority (closer to the top of the window) are drawn\n'\
			'first, hence they will be drawn under the ones with higher priority.',
			size_hint = (0.9, 1.0))
		)
		self.__closeLine.add_widget(self.__closeButton)

		self.__inputBar = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.05))
		self.__layerNameInput = TextInput(multiline = False, size_hint = (0.9, 1.0),
			on_text_validate = self.__processAddLayer, focus = False)
		self.__layerAddButton = CancelableButton(text = 'Add', size_hint = (0.1, 1.0),
			on_release = self.__processAddLayer)


		self.__popup = Popup(title = 'Groups Editor', content = self.__layout, auto_dismiss = False)
		self.__maxLayers = 16
		self.__validCharacters = letters + digits
		self.__layerToRemoveName = None

	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__render()
		self.__popup.open()

class LayerInformationPopup(KeyboardAccess):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.close()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()

	def __save(self, *args):
		newLayer = None
		for button in self.__buttonList:
			if (button.state == 'down'):
				assert(newLayer is None)
				newLayer = button.text

		if (newLayer is None):
			errorAlert = AlertPopUp(
				'Error',
				'No layer selected!\nYou must select a new layer.',
				'Ok'
			)
			errorAlert.open()
		else:
			for obj in self.__objectsList:
				obj.setLayer(newLayer)

			ModulesAccess.get('SceneHandler').redraw()
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
			self.__layout.add_widget(AlignedLabel(text = 'Select the new group for the object:', size_hint = (1.0, 0.05)))
		else:
			self.__layout.add_widget(AlignedLabel(text = 'Select the new group for the objects:', size_hint = (1.0, 0.05)))

		self.__buttonList = []
		layerToMark = self.__getLayerNameIfAllEqual()
		layerList = ModulesAccess.get('LayerGuardian').getLayerList()
		for layer in layerList:
			if (layerToMark is not None and layerToMark == layer.getName()):
				state = 'down'
			else:
				state = 'normal'
			layerButton = AlignedToggleButton(text = layer.getName(), group = 'layers', state = state,
					size_hint = (1.0, 0.05), height = 20, shorten = True, shorten_from = 'left')
			self.__layout.add_widget(layerButton)
			self.__buttonList.append(layerButton)

		self.__layout.add_widget(AlignedLabel(text = '', size_hint = (1.0, 0.05 * (18 - len(layerList)))))
		self.__layout.add_widget(self.__bottomLine)

	def __init__(self):
		super(self.__class__, self).__init__()
		self.__editFlagsPopup = LayerEditorPopup()
		self.__popup = Popup(title = 'Group Selector', auto_dismiss = False)
		self.__layout = BoxLayout(orientation = 'vertical')
		self.__objectsList = None

		self.__bottomLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.05))
		self.__cancelButton = CancelableButton(text = 'Cancel', size_hint = (0.1, 1.0), on_release = self.close)
		self.__doneButton = CancelableButton(text = 'Done', size_hint = (0.1, 1.0), on_release = self.__save)
		self.__editLayersButton = CancelableButton(text = 'Edit groups', size_hint = (0.2, 1.0),
			on_release = self.__editFlagsPopup.open)
		self.__bottomLine.add_widget(self.__editLayersButton)
		self.__bottomLine.add_widget(AlignedLabel(text = '', size_hint = (0.6, 1.0)))
		self.__bottomLine.add_widget(self.__cancelButton)
		self.__bottomLine.add_widget(self.__doneButton)
		self.__popup.content = self.__layout
		ModulesAccess.add('LayerInformation', self)

	def update(self):
		self.__render()

	def open(self, *args):
		objList = ModulesAccess.get('SceneHandler').getCurrentSelection()
		if (objList == []):
			errorAlert = AlertPopUp(
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

