from singleton import Singleton

from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from editorutils import Dialog, AlertPopUp
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.checkbox import CheckBox

from editorutils import CancelableButton, NumberInput
from tilemapfiles import FilesManager
from os import getcwd
from os.path import isfile, join, sep as pathSeparator
from communicationobjects import FileOptionsMenuToScene
from keyboard import KeyboardAccess, KeyboardGuardian
from layerinfo import LayerGuardian
from collisioninfo import CollisionGuardian
from scene import SceneAttributes

class NewScenePopup(KeyboardAccess):
	
	def __confirm(self, *args):
		try:
			x = int(self.__xTilesInput.text)
			assert(x > 0)
		except:
			alert = AlertPopUp('Error', 'Invalid entry for number of tiles in x.', 'Ok')
			return alert.open()

		try:
			y = int(self.__yTilesInput.text)
			assert (y > 0)
		except:
			alert = AlertPopUp('Error', 'Invalid entry for number of tiles in y.', 'Ok')
			return alert.open()
		
		try:
			s = int(self.__tileSizeInput.text)
			assert(s > 0)
		except:
			alert = AlertPopUp('Error', 'Invalid entry for the size of tiles.', 'Ok')
			return alert.open()

		if (s < 8):
			alert = AlertPopUp('Error', 'Minimum size tile supported is 8.', 'Ok')
			return alert.open()

		if (self.__keepCollisionFlags.active == False):
			CollisionGuardian.Instance().reset()

		if (self.__keepGroupsFlags.active == False):
			LayerGuardian.Instance().reset()

		newSceneAttributes = SceneAttributes(s, x, y)
		FileOptionsMenuToScene.Instance().newScene(newSceneAttributes)

		self.close()

	def __init__(self):
		self.__popup = Popup(title = 'New Scene Attributes', size_hint = (0.5, 0.5), auto_dismiss = False)
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__tileSizeInput = NumberInput(module = 'NewScene', size_hint = (0.3, 1.0))
		self.__xTilesInput = NumberInput(module = 'NewScene', size_hint = (0.3, 1.0))
		self.__yTilesInput = NumberInput(module = 'NewScene', size_hint = (0.3, 1.0))
		self.__keepCollisionFlags = CheckBox(size_hint = (0.1, 1.0))
		self.__keepGroupsFlags = CheckBox(size_hint = (0.1, 1.0))
		self.__okButton = CancelableButton(text = 'Ok', on_release = self.__confirm, size_hint = (0.2, 1.0))
		self.__cancelButton = CancelableButton(text = 'Cancel', on_release = self.close, size_hint = (0.2, 1.0))
		
		tilesSizeLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		tilesSizeLine.add_widget(Label(text = 'Size of the tiles:', size_hint = (0.7, 1.0)))
		tilesSizeLine.add_widget(self.__tileSizeInput)
		
		xNumberOfTilesLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		xNumberOfTilesLine.add_widget(Label(text = 'Number of tiles on X:', size_hint = (0.7, 1.0)))
		xNumberOfTilesLine.add_widget(self.__xTilesInput)

		yNumberOfTilesLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		yNumberOfTilesLine.add_widget(Label(text = 'Number of tiles on Y:', size_hint = (0.7, 1.0)))
		yNumberOfTilesLine.add_widget(self.__yTilesInput)

		keepCollisionFlagsLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		keepCollisionFlagsLine.add_widget(self.__keepCollisionFlags)
		keepCollisionFlagsLine.add_widget(Label(text = 'Keep collision flags.'))

		keepGroupsLine = BoxLayout (orientation = 'horizontal', size_hint = (1.0, 0.1))
		keepGroupsLine.add_widget(self.__keepGroupsFlags)
		keepGroupsLine.add_widget(Label(text = 'Keep layer groups.'))

		confirmLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		confirmLine.add_widget(Label(text = '', size_hint = (0.6, 1.0)))
		confirmLine.add_widget(self.__okButton)
		confirmLine.add_widget(self.__cancelButton)

		self.__layout.add_widget(tilesSizeLine)
		self.__layout.add_widget(xNumberOfTilesLine)
		self.__layout.add_widget(yNumberOfTilesLine)
		self.__layout.add_widget(keepCollisionFlagsLine)
		self.__layout.add_widget(keepGroupsLine)
		self.__layout.add_widget(Label(text = 'Any unsaved changes will be lost.', size_hint = (1.0, 0.1)))
		self.__layout.add_widget(confirmLine)

		self.__popup.content = self.__layout
			
	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)	
		self.__popup.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()

@Singleton
class FilesOptionsMenu:
	
	def __newSceneFinish(self, *args):
		self.__newSceneMethodReference()
		self.__newSceneDialog.dismiss()

	def __newScene(self, *args):
		self.__newSceneDialog.open()

	def __saveSceneFinish(self, *args):
		self.__saveSceneMethodReference(join(self.__fileChooser.path, self.__fileChooserInput.text))
		self.__fileChooserPopUp.dismiss()
		self.__saveSceneDialog.dismiss()
		self.__lastPath = self.__fileChooser.path

	def __validateSelectedOsf(self, entry, *args):
		if (isfile(entry[0]) == True):
			sepIndex = entry[0].rfind(pathSeparator)
			if (sepIndex != -1):
				self.__fileChooserInput.text = entry[0][sepIndex+1:]
			else:
				self.__fileChooserInput.text = entry[0]
		else:
			self.__errorPopUp.setText('Invalid file selected.')
			self.__errorPopUp.open()

	def __validateAndContinueToSave(self, *args):
		if (self.__fileChooserInput.text == ''):
			self.__errorPopUp.setText('No file selected.')
			self.__errorPopUp.open()
			return

		if (isfile(join(self.__fileChooser.path, self.__fileChooserInput.text)) == True):
			self.__saveSceneDialog.open()
		else:
			self.__saveSceneFinish()

	def __saveScene(self, *args):
		self.__fileChooser.path = self.__lastPath
		self.__fileChooser.filters = ['*.osf']
		self.__fileChooser.on_submit = self.__validateSelectedOsf
		self.__fileChooserOkButton.on_release = self.__validateAndContinueToSave
		self.__fileChooserPopUp.open()

	def __loadSceneFinish(self, *args):
		self.__loadSceneMethodReference(join(self.__fileChooser.path, self.__fileChooserInput.text))
		self.__fileChooserPopUp.dismiss()
		self.__lastPath = self.__fileChooser.path

	def __validateAndContinueToLoad(self, *args):
		if (self.__fileChooserInput.text == ''):
			self.__errorPopUp.setText('No file selected.')
			self.__errorPopUp.open()
			return

		if (isfile(join(self.__fileChooser.path, self.__fileChooserInput.text)) == True):
			self.__loadSceneFinish()
		else:
			self.__errorPopUp.setText("Selected file doesn't exist.")
			self.__errorPopUp.open()

	def __loadScene(self, *args):
		self.__fileChooser.path = self.__lastPath
		self.__fileChooser.filters = ['*.osf']
		self.__fileChooser.on_submit = self.__validateSelectedOsf
		self.__fileChooserOkButton.on_release = self.__validateAndContinueToLoad
		self.__fileChooserPopUp.open()

	def __exportScene(self, *args):
		#self.__fileChooser.path = self.__lastPath
		#self.__fileChooser.filters = ['*.ini']
		#self.__fileChooser.on_submit = self.__validateSelectedOsf
		#self.__fileChooserOkButton.on_release = self.__validateAndContinueToLoad
		#self.__fileChooserPopUp.open()
		FilesManager.Instance().exportScene('teste.ini')
	

	def __startBasicButtonsLayout(self):
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__newButton = CancelableButton(text = 'New Scene', size_hint = (1.0, 0.25), 
			on_release = self.__newScenePopup.open)
		self.__loadButton = CancelableButton(text = 'Load Scene', size_hint = (1.0, 0.25), 
			on_release = self.__loadScene)
		self.__saveButton = CancelableButton(text = 'Save Scene', size_hint = (1.0, 0.25), 
			on_release = self.__saveScene)
		self.__exportButton = CancelableButton(text = 'Export Scene', size_hint = (1.0, 0.25), 
			on_release = self.__exportScene)
		
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
		self.__fileChooserOkButton = CancelableButton(text = 'Ok')
		self.__fileChooserCancelButton = CancelableButton(text = 'Cancel', 
			on_release = self.__fileChooserPopUp.dismiss)
		self.__fileChooserYesNoLayout.add_widget(self.__fileChooserOkButton)
		self.__fileChooserYesNoLayout.add_widget(self.__fileChooserCancelButton)

		self.__fileChooserLayout.add_widget(self.__fileChooserInputLayout)
		self.__fileChooserLayout.add_widget(self.__fileChooser)
		self.__fileChooserLayout.add_widget(self.__fileChooserYesNoLayout)
		self.__fileChooserPopUp.content = self.__fileChooserLayout
		self.__lastPath = getcwd()


	def __init__(self, accordionItem):
		self.__newScenePopup = NewScenePopup()

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


