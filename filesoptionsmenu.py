from singleton import Singleton

from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from editorutils import Dialog, AlertPopUp
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserIconView

from tilemapfiles import FilesManager
from os import getcwd
from os.path import isfile, join, sep as pathSeparator

@Singleton
class FilesOptionsMenu:
	
	def __newSceneFinish(self, notUsed = None):
		self.__newSceneMethodReference(notUsed)
		self.__newSceneDialog.dismiss()

	def __newScene(self, notUsed = None):
		self.__newSceneDialog.open()

	def __saveSceneFinish(self, notUsed = None):
		self.__saveSceneMethodReference(join(self.__fileChooser.path, self.__fileChooserInput.text))
		self.__fileChooserPopUp.dismiss()
		self.__saveSceneDialog.dismiss()
		self.__lastPath = self.__fileChooser.path

	def __validateSelectedOsf(self, entry, notUsed = None):
		if (isfile(entry[0]) == True):
			sepIndex = entry[0].rfind(pathSeparator)
			if (sepIndex != -1):
				self.__fileChooserInput.text = entry[0][sepIndex+1:]
			else:
				self.__fileChooserInput.text = entry[0]
		else:
			self.__errorPopUp.setText('Invalid file selected.')
			self.__errorPopUp.open()

	def __validateAndContinueToSave(self, notUsed = None):
		if (self.__fileChooserInput.text == ''):
			self.__errorPopUp.setText('No file selected.')
			self.__errorPopUp.open()
			return

		if (isfile(join(self.__fileChooser.path, self.__fileChooserInput.text)) == True):
			self.__saveSceneDialog.open()
		else:
			self.__saveSceneFinish()

	def __saveScene(self, notUsed = None):
		self.__fileChooser.path = self.__lastPath
		self.__fileChooser.filters = ['*.osf']
		self.__fileChooser.on_submit = self.__validateSelectedOsf
		self.__fileChooserOkButton.on_release = self.__validateAndContinueToSave
		self.__fileChooserPopUp.open()

	def __loadSceneFinish(self, notUsed = None):
		self.__loadSceneMethodReference(join(self.__fileChooser.path, self.__fileChooserInput.text))
		self.__fileChooserPopUp.dismiss()
		self.__lastPath = self.__fileChooser.path

	def __validateAndContinueToLoad(self, notUsed = None):
		if (self.__fileChooserInput.text == ''):
			self.__errorPopUp.setText('No file selected.')
			self.__errorPopUp.open()
			return

		if (isfile(join(self.__fileChooser.path, self.__fileChooserInput.text)) == True):
			self.__loadSceneFinish()
		else:
			self.__errorPopUp.setText("Selected file doesn't exist.")
			self.__errorPopUp.open()

	def __loadScene(self, notUsed = None):
		self.__fileChooser.path = self.__lastPath
		self.__fileChooser.filters = ['*.osf']
		self.__fileChooser.on_submit = self.__validateSelectedOsf
		self.__fileChooserOkButton.on_release = self.__validateAndContinueToLoad
		self.__fileChooserPopUp.open()

	def __exportScene(self, notUsed = None):
		#self.__fileChooser.path = self.__lastPath
		#self.__fileChooser.filters = ['*.ini']
		#self.__fileChooser.on_submit = self.__validateSelectedOsf
		#self.__fileChooserOkButton.on_release = self.__validateAndContinueToLoad
		#self.__fileChooserPopUp.open()
		FilesManager.Instance().exportScene('teste.ini')
	

	def __startBasicButtonsLayout(self):
		self.__layout = GridLayout(rows = 4, cols = 1, size_hint = (1.0, 1.0))
		self.__newButton = Button(text = 'New Scene', size_hint = (1.0, 0.25), on_release = self.__newScene)
		self.__loadButton = Button(text = 'Load Scene', size_hint = (1.0, 0.25), on_release = self.__loadScene)
		self.__saveButton = Button(text = 'Save Scene', size_hint = (1.0, 0.25), on_release = self.__saveScene)
		self.__exportButton = Button(text = 'Export Scene', size_hint = (1.0, 0.25), on_release = self.__exportScene)
		
		self.__layout.add_widget(self.__newButton)
		self.__layout.add_widget(self.__loadButton)
		self.__layout.add_widget(self.__saveButton)
		self.__layout.add_widget(self.__exportButton)

	def __startConfirmationPopUp(self):
		self.__newSceneDialog = Dialog(
			self.__newSceneFinish, 'Confirmation', 
			'Starting a new scene will remove all the\nnon saved changes.\nAre you sure?', 'Ok', 'Cancel'
		)
		self.__saveSceneDialog = Dialog(
			self.__saveSceneFinish, 'Confirmation',
			'This will override the selected file.\nContinue?', 'Ok', 'Cancel'
		)

	def __startFileChooser(self):
		
		self.__fileChooserLayout = BoxLayout(orientation = 'vertical')
		self.__fileChooserPopUp = Popup(auto_dismiss = False, title = 'Select the file:')
		self.__fileChooserInputLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		filenameLabel = Label(text = 'File:', size_hint = (0.3, 1.0))
		self.__fileChooserInput = TextInput(multiline = False, size_hint = (0.7, 1.0))
		self.__fileChooserInputLayout.add_widget(filenameLabel)
		self.__fileChooserInputLayout.add_widget(self.__fileChooserInput)
		self.__fileChooser = FileChooserIconView(size_hint = (1.0, 0.9))

		self.__fileChooserYesNoLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		self.__fileChooserOkButton = Button(text = 'Ok')
		self.__fileChooserCancelButton = Button(text = 'Cancel', on_release = self.__fileChooserPopUp.dismiss)
		self.__fileChooserYesNoLayout.add_widget(self.__fileChooserOkButton)
		self.__fileChooserYesNoLayout.add_widget(self.__fileChooserCancelButton)

		self.__fileChooserLayout.add_widget(self.__fileChooserInputLayout)
		self.__fileChooserLayout.add_widget(self.__fileChooser)
		self.__fileChooserLayout.add_widget(self.__fileChooserYesNoLayout)
		self.__fileChooserPopUp.content = self.__fileChooserLayout
		self.__lastPath = getcwd()


	def __init__(self, accordionItem, newSceneMethod, saveSceneMethod, loadSceneMethod):

		self.__newSceneMethodReference = newSceneMethod
		self.__saveSceneMethodReference = FilesManager.Instance().saveScene
		self.__loadSceneMethodReference = loadSceneMethod

		self.__startBasicButtonsLayout()	
		self.__startConfirmationPopUp()	
		self.__startFileChooser()
		self.__errorPopUp = AlertPopUp('Error', '', 'Ok')

		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)

	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False


