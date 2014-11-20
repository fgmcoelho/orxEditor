from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label

from string import letters, digits
from singleton import Singleton

from editorutils import CancelableButton, AlertPopUp, Dialog
from keyboard import KeyboardAccess, KeyboardGuardian

class LayerRegister:
	def __init__(self, name, priority):
		self.__name = name
		self.__priority = priority

	def setPriority(self, newPriority):
		self.__priority = newPriority

	def getPriority(self):
		return self.__priority

	def getName(self):
		return self.__name

@Singleton
class LayerGuardian:
	def __init__(self):
		self.__defaultLayer = LayerRegister('default', 0)
		self.__layersDict = { 0 : self.__defaultLayer }
		for i in range(1, 16):
			self.__layersDict[i] = None

		self.__highestPriority = 0

	def __getIndex(self, layerName):
		for i in range(self.__highestPriority + 1):
			if(self.__layersDict[i].getName() == layerName):
				return i

		raise Exception('Fatal error on layer manager.')

	def addNewLayer(self, newLayer):
		self.__highestPriority += 1
		self.__layersDict[self.__highestPriority] = LayerRegister(newLayer, newLayer)

	def decreasePriority(self, layerName):
		i = self.__getIndex(layerName)
		if (i == 0):
			return
		else:
			swap = self.__layersDict[i-1]
			self.__layersDict[i-1] = self.__layersDict[i]
			self.__layersDict[i] = swap

	def increasePriority(self, layerName):
		i = self.__getIndex(layerName)
		if (i == self.__highestPriority):
			return
		else:
			swap = self.__layersDict[i+1]
			self.__layersDict[i+1] = self.__layersDict[i]
			self.__layersDict[i] = swap
	
	def deleteLayerByName(self, layerName):
		i = self.__getIndex(layerName)
		while (self.__layersDict[i] != None):
			self.__layersDict[i] = self.__layersDict[i + 1]
			i += 1

		self.__highestPriority -= 1

	def getLayerList(self):
		l = []
		formerKey = -1
		for key in self.__layersDict.keys():
			if (self.__layersDict[key] is not None):
				l.append(self.__layersDict[key])
				assert key == formerKey + 1
				formerKey = key

			else:
				break

		return l

class LayerEditorPopup(KeyboardAccess):

	# Overloaded method
	def _processKeyDown(self, keyboard, keycode, text, modifiers):

		if (keycode[1] == 'escape'):
			KeyboardGuardian.Instance().dropKeyboard(self)

	def __close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()

	def __updateLayers(self, *args):
		button = args[0]
		operation, layerName = button.id.split('#')
		if (operation == 'inc'):
			LayerGuardian.Instance().increasePriority(layerName)
		elif (operation == 'dec'):
			LayerGuardian.Instance().decreasePriority(layerName)
		else:
			LayerGuardian.Instance().deleteLayerByName(layerName)

		self.__render()

	def __processAddLayer(self, *args):
		newLayer = self.__layerNameInput.text.strip()
		if (newLayer == ''):
			error = AlertPopUp('Error', 'Layer name can\'t be empty.', 'Ok', self.__reaplyFocus)
			error.open()
			return

		layerList = LayerGuardian.Instance().getLayerList()
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

		LayerGuardian.Instance().addNewLayer(newLayer)
		self.__layerNameInput.text = ''
		self.__render()

	def __reaplyFocus(self):
		layerList = LayerGuardian.Instance().getLayerList()
		if (len(layerList) != self.__maxLayers):
			self.__inputBar.clear_widgets()
			oldText = self.__layerNameInput.text
			self.__layerNameInput = TextInput(text = oldText, multiline = False, size_hint = (0.9, 1.0),
				on_text_validate = self.__processAddLayer, focus = True)
			self.__inputBar.add_widget(self.__layerNameInput)
			self.__inputBar.add_widget(self.__layerAddButton)

	def __render(self):
		self.__layout.clear_widgets()
		layerList = LayerGuardian.Instance().getLayerList()
		for layer in layerList:
			name = layer.getName()
			line = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.05))
			line.add_widget(Label(text = name, size_hint = (0.85, 1.0)))
			line.add_widget(CancelableButton(text = '+', on_release = self.__updateLayers, id = 'inc#' + name,
				size_hint = (0.05, 1.0)))
			line.add_widget(CancelableButton(text = '-', on_release = self.__updateLayers, id = 'dec#' + name,
				size_hint = (0.05, 1.0)))
			if (name != 'default'):
				line.add_widget(CancelableButton(text = 'x', on_release = self.__updateLayers, id = 'rem#' + name,
					size_hint = (0.05, 1.0)))
			else:
				line.add_widget(Label(text='', size_hint = (0.05, 1.0)))


			self.__layout.add_widget(line)

		self.__layout.add_widget(Label(text = '', size_hint = (1.0, 0.85 - (len(layerList) * 0.05))))
		
		if (len(layerList) == self.__maxLayers):
			self.__layout.add_widget(Label(text = 'Maximum number of layers (%u) reached.' %
				(self.__maxLayers, ), size_hint = (1.0, 0.05)))
		else:
			self.__reaplyFocus()
			self.__layout.add_widget(self.__inputBar)

		self.__layout.add_widget(Label(text = '', size_hint = (1.0, 0.05)))
		self.__layout.add_widget(self.__closeLine)

	def __init__(self):
		super(LayerEditorPopup, self).__init__()
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__closeButton = CancelableButton(text = 'close', on_release = self.__close, size_hint = (0.1, 1.0))
		self.__closeLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.05))
		self.__closeLine.add_widget(Label(
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


		self.__popup = Popup(title = 'Groups Editor', content = self.__layout)
		self.__maxLayers = 16
		self.__validCharacters = letters + digits
		LayerGuardian.Instance()

	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__render()
		self.__popup.open()
