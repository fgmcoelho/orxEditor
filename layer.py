from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label

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

	def __close(self, *args):
		self.__popup.dismiss()

	def __updateLayers(self, *args):
		pass

	def __render(self):
		self.__layout.clear_widgets()
		layerList = LayerGuardian.Instance().getLayerList()
		for layer in layerList:
			name = layer.getName()
			line = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.05))
			line.add_widget(Label(text = name, size_hint = (0.7, 1.0)))
			line.add_widget(CancelableButton(text = '+', on_release = self.__updateLayers, id = 'inc#' + name,
				size_hint = (0.1, 1.0)))
			line.add_widget(CancelableButton(text = '-', on_release = self.__updateLayers, id = 'dec#' + name,
				size_hint = (0.1, 1.0)))
			line.add_widget(CancelableButton(text = 'x', on_release = self.__updateLayers, id = 'rem#' + name,
				size_hint = (0.1, 1.0)))

			self.__layout.add_widget(line)

		self.__layout.add_widget(Label(text = '', size_hint = (1.0, 0.95 - (len(layerList) * 0.05))))
		self.__layout.add_widget(self.__closeLine)

	def __init__(self):
		super(LayerEditorPopup, self).__init__()
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__closeButton = CancelableButton(text = 'close', on_release = self.__close, size_hint = (0.3, 1.0))
		self.__closeLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.05))
		self.__closeLine.add_widget(Label(text = 'Hint:', size_hint = (0.7, 1.0)))
		self.__closeLine.add_widget(self.__closeButton)
		self.__popup = Popup(title = 'Groups Editor', content = self.__layout)
		LayerGuardian.Instance()


	def open(self, *args):
		self.__render()
		self.__popup.open()
