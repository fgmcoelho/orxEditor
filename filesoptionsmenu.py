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
from tilemapfiles import FilesManager

class NewScenePopup(KeyboardAccess):
	
	def __confirm(self, *args):
		try:
			tilesOnX = int(self.__xTilesInput.text)
			assert(tilesOnX > 0)
		except:
			alert = AlertPopUp('Error', 'Invalid entry for number of tiles on x.', 'Ok')
			return alert.open()

		try:
			tilesOnY = int(self.__yTilesInput.text)
			assert (tilesOnY > 0)
		except:
			alert = AlertPopUp('Error', 'Invalid entry for number of tiles on y.', 'Ok')
			return alert.open()
		
		try:
			tilesSize = int(self.__tileSizeInput.text)
			assert(tilesSize > 0)
		except:
			alert = AlertPopUp('Error', 'Invalid entry for the size of tiles.', 'Ok')
			return alert.open()

		if (tilesSize < 8):
			alert = AlertPopUp('Error', 'Minimum size tile supported is 8.', 'Ok')
			return alert.open()

		if (self.__keepCollisionFlags.active == False):
			CollisionGuardian.Instance().reset()

		if (self.__keepGroupsFlags.active == False):
			LayerGuardian.Instance().reset()

		newSceneAttributes = SceneAttributes(tilesSize, tilesOnX, tilesOnY)
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

class FileSelectorPopup(KeyboardAccess):
	
	def __finish(self):
		self.__selected = join(self.__fileChooser.path, self.__fileChooserInput.text)
		self.close()

	def __validateAndContinue(self):
		if (self.__validadeExists == True):
			if (isfile(join(self.__fileChooser.path, self.__fileChooserInput.text)) == True):
				self.__warn.open()
		else:
			self.__finish()

	def __init__(self, validateExists = False):
		self.__fileChooserLayout = BoxLayout(orientation = 'vertical')
		self.__fileChooserPopUp = Popup(auto_dismiss = False, title = 'Select the file:')
		self.__fileChooserInputLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		filenameLabel = Label(text = 'File:', size_hint = (0.3, 1.0))
		self.__fileChooserInput = TextInput(multiline = False, size_hint = (0.7, 1.0))
		self.__fileChooserInputLayout.add_widget(filenameLabel)
		self.__fileChooserInputLayout.add_widget(self.__fileChooserInput)
		self.__fileChooser = FileChooserIconView(size_hint = (1.0, 0.9))

		self.__fileChooserYesNoLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		self.__fileChooserOkButton = CancelableButton(text = 'Ok', on_release = self.__validate)
		self.__fileChooserCancelButton = CancelableButton(text = 'Cancel', on_release = self.close)
		self.__fileChooserYesNoLayout.add_widget(self.__fileChooserOkButton)
		self.__fileChooserYesNoLayout.add_widget(self.__fileChooserCancelButton)

		self.__fileChooserLayout.add_widget(self.__fileChooserInputLayout)
		self.__fileChooserLayout.add_widget(self.__fileChooser)
		self.__fileChooserLayout.add_widget(self.__fileChooserYesNoLayout)
		self.__fileChooserPopUp.content = self.__fileChooserLayout

		# control variables
		self.__validadeExists = validateExists
		if (validateExists == True):
			self.__warn = Dialog(self.__finish, 'Warning', 
				'The selected file already exists.\nThis operation will override it,\n'\
				'are you sure you want to continue?', 'Ok', 'Cancel'
			)
		self.__lastPath = getcwd()
		self.__selected = None

	def open(self):
		KeyboardGuardian.acquireKeyboard(self)
		self.__fileChooserPopUp.open()
		self.__selected = None

	def close(self):
		KeyboardGuardian.dropKeyboard(self)
		self.__fileChooserPopUp.dismiss()

	def getSelected(self):
		return self.__selected

class FileChooserUser(object):
	
	def _prepareOpen(self, filterToUse = ['*.osf']):
		assert(type(filterToUse) is list)
		self._fileChooser.path = self._lastPath
		self._fileChooser.filters = filterToUse

	def _submitMethod(self, selection, touch):
		if len(selection) == 0:
			return

		filename = selection[0].split(pathSeparator)[-1]
		if (filename[-4:] != '.osf'):
			return

		if (self._fileChooserInput.text == filename):
			return self._validateAndContinue()
		else:
			self._fileChooserInput.text = filename

	def __init__(self):
		self._fileChooserLayout = BoxLayout(orientation = 'vertical')
		self._fileChooserPopUp = Popup(auto_dismiss = False, title = 'Select the file:')
		self._fileChooserInputLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		filenameLabel = Label(text = 'File:', size_hint = (0.3, 1.0))
		self._fileChooserInput = TextInput(multiline = False, size_hint = (0.7, 1.0))
		self._fileChooserInputLayout.add_widget(filenameLabel)
		self._fileChooserInputLayout.add_widget(self._fileChooserInput)
		self._fileChooser = FileChooserIconView(size_hint = (1.0, 0.9))
		self._fileChooser.on_submit = self._submitMethod

		self._fileChooserYesNoLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		self._fileChooserOkButton = CancelableButton(text = 'Ok')
		self._fileChooserCancelButton = CancelableButton(text = 'Cancel', 
			on_release = self.close)
		self._fileChooserYesNoLayout.add_widget(self._fileChooserOkButton)
		self._fileChooserYesNoLayout.add_widget(self._fileChooserCancelButton)

		self._fileChooserLayout.add_widget(self._fileChooserInputLayout)
		self._fileChooserLayout.add_widget(self._fileChooser)
		self._fileChooserLayout.add_widget(self._fileChooserYesNoLayout)
		self._fileChooserPopUp.content = self._fileChooserLayout
		self._lastPath = getcwd()
		self._errorPopUp = AlertPopUp('Error', '', 'Ok')


class SaveScenePopup(KeyboardAccess, FileChooserUser):
	def __saveSceneFinish(self, *args):
		filename = self._fileChooserInput.text	
		if (filename[-4:] != '.osf'):
			filename += '.osf'

		FilesManager.Instance().saveScene(join(self._fileChooser.path, filename))
		self.__saveSceneDialog.dismiss()
		self._lastPath = self._fileChooser.path
		self.close()

	def _validateAndContinue(self, *args):
		if (self._fileChooserInput.text == ''):
			self._errorPopUp.setText('No file selected.')
			self._errorPopUp.open()
			return

		if (isfile(join(self._fileChooser.path, self._fileChooserInput.text)) == True):
			self.__saveSceneDialog.open()
		else:
			self.__saveSceneFinish()
	
	def __init__(self):
		super(SaveScenePopup, self).__init__()
		self.__saveSceneDialog = Dialog(
			self.__saveSceneFinish, 'Confirmation',
			'This will override the selected file.\nContinue?', 'Ok', 'Cancel'
		)
	
	def open(self, *args):
		self._prepareOpen()
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self._fileChooserOkButton.on_release = self._validateAndContinue
		self._fileChooserPopUp.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self._fileChooserPopUp.dismiss()

class LoadScenePopup(KeyboardAccess, FileChooserUser):
	def _validateAndContinue(self, *args):
		if (self._fileChooserInput.text == ''):
			self._errorPopUp.setText('No file selected.')
			self._errorPopUp.open()
			return

		if (isfile(join(self._fileChooser.path, self._fileChooserInput.text)) == True):
			self.__loadSceneFinish()
		else:
			self._errorPopUp.setText("Selected file doesn't exist.")
			self._errorPopUp.open()

	def __loadSceneFinish(self, *args):
		FilesManager.Instance().loadScene(join(self._fileChooser.path, self._fileChooserInput.text))
		self._fileChooserPopUp.dismiss()
		self._lastPath = self._fileChooser.path
		self.close()

	def __init__(self):
		super(LoadScenePopup, self).__init__()

	def open(self, *args):
		self._prepareOpen()
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self._fileChooserOkButton.on_release = self._validateAndContinue
		self._fileChooserPopUp.open()
	
	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self._fileChooserPopUp.dismiss()

@Singleton
class FilesOptionsMenu:

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
			on_release = self.__loadScenePopup.open)
		self.__saveButton = CancelableButton(text = 'Save Scene', size_hint = (1.0, 0.25), 
			on_release = self.__saveScenePopup.open)
		self.__exportButton = CancelableButton(text = 'Export Scene', size_hint = (1.0, 0.25), 
			on_release = self.__exportScene)
		
		self.__layout.add_widget(self.__newButton)
		self.__layout.add_widget(self.__loadButton)
		self.__layout.add_widget(self.__saveButton)
		self.__layout.add_widget(self.__exportButton)

	def __init__(self, accordionItem):
		self.__newScenePopup = NewScenePopup()
		self.__saveScenePopup = SaveScenePopup()
		self.__loadScenePopup = LoadScenePopup()

		self.__startBasicButtonsLayout()
		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)

	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False


