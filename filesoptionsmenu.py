from singleton import Singleton

from kivy.uix.boxlayout import BoxLayout
from editorutils import Dialog, Alert
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.checkbox import CheckBox

from editorutils import CancelableButton, NumberInput, AlignedLabel, inputDefault
from editorheritage import SeparatorLabel
from uisizes import optionsMenuSize, lineSize, newSceneSize
from tilemapfiles import FilesManager
from communicationobjects import FileOptionsMenuToScene
from keyboard import KeyboardAccess, KeyboardGuardian
from layerinfo import LayerGuardian
from collisioninfo import CollisionGuardian
from scene import SceneAttributes
from modulesaccess import ModulesAccess

from os import getcwd
from os.path import isfile, join, abspath, sep as pathSeparator

class NewScenePopup(KeyboardAccess, SeparatorLabel):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.close()

		elif (keycode[1] == 'shift'):
			self.__isShiftPressed = False

		elif (keycode[1] == 'tab'):
			if (self.__isShiftPressed == False):
				NumberInput.selectInputByFocus('NewScene')
			else:
				NumberInput.selectInputByFocus('NewScene', reverse = True)

	def _processKeyDown(self, keyboard, keycode, text, modifiers):
		if (keycode[1] == 'shift'):
			self.__isShiftPressed = True

	def __confirm(self, *args):
		try:
			tilesOnX = int(self.__xTilesInput.text)
			assert(tilesOnX > 0)
		except:
			alert = Alert('Error', 'Invalid entry for number of tiles on x.', 'Ok')
			return alert.open()

		try:
			tilesOnY = int(self.__yTilesInput.text)
			assert (tilesOnY > 0)
		except:
			alert = Alert('Error', 'Invalid entry for number of tiles on y.', 'Ok')
			return alert.open()

		try:
			tilesSize = int(self.__tileSizeInput.text)
			assert(tilesSize > 0)
		except:
			alert = Alert('Error', 'Invalid entry for the size of tiles.', 'Ok')
			return alert.open()

		if (tilesSize < 8):
			alert = Alert('Error', 'Minimum size tile supported is 8.', 'Ok')
			return alert.open()

		if (self.__keepCollisionFlags.active == False):
			CollisionGuardian.Instance().reset()

		if (self.__keepGroupsFlags.active == False):
			ModulesAccess.get('LayerGuardian').reset()

		newSceneAttributes = SceneAttributes(tilesSize, tilesOnX, tilesOnY)
		FileOptionsMenuToScene.Instance().newScene(newSceneAttributes)

		self.close()

	def __init__(self):
		super(NewScenePopup, self).__init__()
		self.__popup = Popup(title = 'New Scene Attributes', auto_dismiss = False, **newSceneSize)
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__tileSizeInput = NumberInput(module = 'NewScene', size_hint = (0.3, 1.0))
		self.__xTilesInput = NumberInput(module = 'NewScene', size_hint = (0.3, 1.0))
		self.__yTilesInput = NumberInput(module = 'NewScene', size_hint = (0.3, 1.0))
		self.__keepCollisionFlags = CheckBox(size_hint = (0.1, 1.0))
		self.__keepGroupsFlags = CheckBox(size_hint = (0.1, 1.0))
		self.__okButton = CancelableButton(text = 'Ok', on_release = self.__confirm, size_hint = (0.2, 1.0))
		self.__cancelButton = CancelableButton(text = 'Cancel', on_release = self.close, size_hint = (0.2, 1.0))

		tilesSizeLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		tilesSizeLine.add_widget(AlignedLabel(text = 'Size of the tiles:', size_hint = (0.7, 1.0)))
		tilesSizeLine.add_widget(self.__tileSizeInput)

		xNumberOfTilesLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		xNumberOfTilesLine.add_widget(AlignedLabel(text = 'Number of tiles on X:', size_hint = (0.7, 1.0)))
		xNumberOfTilesLine.add_widget(self.__xTilesInput)

		yNumberOfTilesLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		yNumberOfTilesLine.add_widget(AlignedLabel(text = 'Number of tiles on Y:', size_hint = (0.7, 1.0)))
		yNumberOfTilesLine.add_widget(self.__yTilesInput)

		keepCollisionFlagsLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		keepCollisionFlagsLine.add_widget(self.__keepCollisionFlags)
		keepCollisionFlagsLine.add_widget(AlignedLabel(text = 'Keep collision flags.'))

		keepGroupsLine = BoxLayout (orientation = 'horizontal', size_hint = (1.0, 0.1))
		keepGroupsLine.add_widget(self.__keepGroupsFlags)
		keepGroupsLine.add_widget(AlignedLabel(text = 'Keep layer groups.'))

		confirmLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		confirmLine.add_widget(AlignedLabel(text = '', size_hint = (0.6, 1.0)))
		confirmLine.add_widget(self.__okButton)
		confirmLine.add_widget(self.__cancelButton)

		self.__layout.add_widget(tilesSizeLine)
		self.__layout.add_widget(xNumberOfTilesLine)
		self.__layout.add_widget(yNumberOfTilesLine)
		self.__layout.add_widget(keepCollisionFlagsLine)
		self.__layout.add_widget(keepGroupsLine)
		self.__layout.add_widget(AlignedLabel(text = 'Any unsaved changes will be lost.', size_hint = (1.0, 0.1)))
		self.__layout.add_widget(confirmLine)

		self.__popup.content = self.__layout
		self.__isShiftPressed = False

	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__popup.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()

class FileSelectorPopup(KeyboardAccess):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.close()

	def __finish(self):
		if (self.__directoriesOnly == True):
			self.__selected = abspath(str(self.__fileChooser.path))
		else:
			self.__selected = join(self.__fileChooser.path, self.__fileChooserInput.text)

		if (self.__finishMethod is not None):
			self.__finishMethod()
		self.__lastPath = self.__fileChooser.path
		self.close()

	def __validate(self, *args):
		if (self.__validadeExists == True and self.__directoriesOnly == False):
			if (isfile(join(self.__fileChooser.path, self.__fileChooserInput.text)) == True):
				self.__warn.open()
		else:
			self.__finish()

	def __submit(self, selection, touch):
		if(len(selection) != 1):
			return

		if (self.__fileChooserInput.text == selection[0]):
			return self.__validate()
		else:
			self.__fileChooserInput.text = selection[0]

	def __setDirectory(self, chooser, newPath):
		self.__fileChooserInput.text = abspath(str(newPath))

	def __init__(self, validateExists = False, filters = ['*'], finishMethod = None, directoriesOnly = False):
		# control variables
		self.__validadeExists = validateExists
		if (validateExists == True):
			self.__warn = Dialog(self.__finish, 'Warning',
				'The selected file already exists.\nThis operation will override it,\n'\
				'are you sure you want to continue?', 'Ok', 'Cancel'
			)
		self.__lastPath = getcwd()
		self.__selected = None
		self.__directoriesOnly = directoriesOnly

		self.__fileChooserLayout = BoxLayout(orientation = 'vertical')
		self.__fileChooserPopUp = Popup(auto_dismiss = False, title = 'Select the file:')
		self.__fileChooserInputLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		self.__fileChooser = FileChooserIconView(size_hint = (1.0, 0.9))
		if (directoriesOnly == True):
			self.__fileChooserInput = TextInput(multiline = False, size_hint = (0.7, 1.0), readonly = True)
			self.__fileChooserInputLayout.add_widget(AlignedLabel(text = 'Directory:', size_hint = (0.3, 1.0)))
			self.__filters = [''] # we want to cut out all the files in this case
			self.__fileChooser.dirselect = True
			self.__fileChooser.bind(path = self.__setDirectory)
		else:
			self.__fileChooserInput = TextInput(multiline = False, size_hint = (0.7, 1.0))
			self.__fileChooserInputLayout.add_widget(AlignedLabel(text = 'File:', size_hint = (0.3, 1.0)))
			self.__fileChooser.on_submit = self.__submit
			self.__filters = filters

		self.__fileChooser.filters = self.__filters
		self.__fileChooserInputLayout.add_widget(self.__fileChooserInput)
		self.__finishMethod = finishMethod
		self.__fileChooserYesNoLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		self.__fileChooserOkButton = CancelableButton(text = 'Ok', on_release = self.__validate)
		self.__fileChooserCancelButton = CancelableButton(text = 'Cancel', on_release = self.close)
		self.__fileChooserYesNoLayout.add_widget(self.__fileChooserOkButton)
		self.__fileChooserYesNoLayout.add_widget(self.__fileChooserCancelButton)

		self.__fileChooserLayout.add_widget(self.__fileChooserInputLayout)
		self.__fileChooserLayout.add_widget(self.__fileChooser)
		self.__fileChooserLayout.add_widget(self.__fileChooserYesNoLayout)
		self.__fileChooserPopUp.content = self.__fileChooserLayout

	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__fileChooser.path = self.__lastPath
		self.__fileChooserPopUp.open()
		self.__selected = None
		self.__fileChooser.filters = [self.__filters[0] + 'aaaa'] # this forces the file list to reload
		self.__fileChooser.filters = self.__filters

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__fileChooserPopUp.dismiss()

	def getSelected(self):
		return self.__selected

class FileChooserUser(object):
	def _prepareOpen(self, filterToUse = ['*.osf']):
		assert(type(filterToUse) is list)
		self._fileChooser.path = self._lastPath
		self._fileChooser.filters = [''] # this forces the file chooser to reload the file list
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

	def _closePopUpsAndShowResult(self, method, arg, operation):
		try:
			method(arg)
			alertSuccess = True
			errorText = ''
		except Exception, e:
			alertSuccess = False
			errorText = str(e)

		self._lastPath = self._fileChooser.path
		self._fileChooserPopUp.dismiss()
		self.close()
		if (alertSuccess == True):
			self._successPopup.open()
		else:
			self._errorPopup.setText('Error ' + operation + ' the file:\n'+errorText)
			self._errorPopup.open()

	def __init__(self):
		self._fileChooserLayout = BoxLayout(orientation = 'vertical')
		self._fileChooserPopUp = Popup(auto_dismiss = False, title = 'Select the file:')
		self._fileChooserInputLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		self._fileChooserInput = TextInput(multiline = False, size_hint = (0.7, 1.0))
		self._fileChooserInputLayout.add_widget(AlignedLabel(text = 'File:', size_hint = (0.3, 1.0)))
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
		self._errorPopup = Alert('Error', '', 'Ok')
		self._successPopup = Alert('Success', '', 'Ok')


class SaveScenePopup(KeyboardAccess, FileChooserUser):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.close()

	def __saveSceneFinish(self, *args):
		filename = self._fileChooserInput.text
		if (filename[-4:] != '.osf'):
			filename += '.osf'

		self._closePopUpsAndShowResult(
			FilesManager.Instance().saveScene,
			join(self._fileChooser.path, filename),
			'saving'
		)

	def _validateAndContinue(self, *args):
		if (self._fileChooserInput.text == ''):
			self._errorPopup.setText('No file selected.')
			self._errorPopup.open()
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
		self._successPopup.setText("The file was successfully saved.")

	def open(self, *args):
		self._prepareOpen()
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self._fileChooserOkButton.on_release = self._validateAndContinue
		self._fileChooserPopUp.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self._fileChooserPopUp.dismiss()

class LoadScenePopup(KeyboardAccess, FileChooserUser):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.close()

	def _validateAndContinue(self, *args):
		if (self._fileChooserInput.text == ''):
			self._errorPopup.setText('No file selected.')
			self._errorPopup.open()
			return

		if (isfile(join(self._fileChooser.path, self._fileChooserInput.text)) == True):
			self.__loadSceneFinish()
		else:
			self._errorPopup.setText("Selected file doesn't exist.")
			self._errorPopup.open()

	def __loadSceneFinish(self, *args):
		self._closePopUpsAndShowResult(
			FilesManager.Instance().loadScene,
			join(self._fileChooser.path, self._fileChooserInput.text),
			'loading'
		)

	def __init__(self):
		super(LoadScenePopup, self).__init__()
		self._successPopup.setText('The file was successfully loaded.')

	def open(self, *args):
		self._prepareOpen()
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self._fileChooserOkButton.on_release = self._validateAndContinue
		self._fileChooserPopUp.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self._fileChooserPopUp.dismiss()

class ExportScenePopup (KeyboardAccess):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.close()

	def __confirm(self, *args):
		if (self.__filename is None):
			self.__errorPopup.setText('You need to select a file to export the scene.')
			return self.__errorPopup.open()

		if (self.__assetsPath is None):
			self.__errorPopup.setText('You need to select a directory to keep the assets.')
			return self.__errorPopup.open()

		alertSuccess = True
		try:
			FilesManager.Instance().exportScene(self.__filename, self.__assetsPath, bool(self.__smoothCheckBox.active))
		except Exception, e:
			errorText = str(e)
			alertSuccess = False

		self.close()

		if (alertSuccess == True):
			self.__successPopup.open()
		else:
			self.__errorPopup.setText('Error:\n' + errorText)
			self.__errorPopup.open()

	def __setFilename(self):
		self.__filename = self.__fileChooser.getSelected()
		if (self.__filename[-4:] != '.ini'):
			self.__filename += '.ini'
		self.__filenameDescription.text = self.__filename

	def __setAssetsPath(self):
		self.__assetsPath = self.__assetsChooser.getSelected()
		self.__assetsPathDescription.text = self.__assetsPath

	def __init__(self):
		self.__filename = None
		self.__assetsPath = None

		self.__fileChooser = FileSelectorPopup(filters = ['*.ini'], finishMethod = self.__setFilename)
		self.__assetsChooser = FileSelectorPopup(finishMethod = self.__setAssetsPath, directoriesOnly = True)

		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__filenameDescription = TextInput(text = '', readonly = True, multiline = False, size_hint = (0.7, 1.0))
		self.__chooseFilenameButton = CancelableButton(text = 'Choose', size_hint = (0.2, 1.0),
			on_release = self.__fileChooser.open)
		self.__assetsPathDescription = TextInput(text = '', readonly = True, multiline = False, size_hint = (0.7, 1.0))
		self.__assetsPathButton = CancelableButton(text = 'Choose', size_hint = (0.2, 1.0),
			on_release = self.__assetsChooser.open)
		self.__smoothCheckBox = CheckBox(active = True, size_hint = (0.2,  1.0))
		self.__okButton = CancelableButton(text = 'Ok', on_release = self.__confirm, size_hint = (0.2, 1.0))
		self.__cancelButton = CancelableButton(text = 'Cancel', on_release = self.close, size_hint = (0.2, 1.0))

		self.__filenameLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__filenameLine.add_widget(self.__filenameDescription)
		self.__filenameLine.add_widget(AlignedLabel(text = '', size_hint = (0.1, 1.0)))
		self.__filenameLine.add_widget(self.__chooseFilenameButton)

		self.__assetsPathLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__assetsPathLine.add_widget(self.__assetsPathDescription)
		self.__assetsPathLine.add_widget(AlignedLabel(size_hint = (0.1, 1.0), text = ''))
		self.__assetsPathLine.add_widget(self.__assetsPathButton)

		self.__smoothLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__smoothLine.add_widget(self.__smoothCheckBox)
		self.__smoothLine.add_widget(AlignedLabel(text = 'Turn on graphics smoothing', size_hint = (0.8, 1.0)))

		self.__confirmLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__confirmLine.add_widget(AlignedLabel(text = '', size_hint = (0.6, 0.2)))
		self.__confirmLine.add_widget(self.__okButton)
		self.__confirmLine.add_widget(self.__cancelButton)

		self.__layout.add_widget(AlignedLabel(text = 'Ini file to export the scene:', size_hint = (1.0, 0.1)))
		self.__layout.add_widget(self.__filenameLine)
		self.__layout.add_widget(AlignedLabel(text = 'Directory to save the assets:', size_hint = (1.0, 0.1)))
		self.__layout.add_widget(self.__assetsPathLine)
		self.__layout.add_widget(self.__smoothLine)
		self.__layout.add_widget(self.__confirmLine)

		self.__popup = Popup(size_hint = (0.5, 0.5), auto_dismiss = False, title = 'Export Scene',
			content = self.__layout)
		self.__errorPopup = Alert('Error', '', 'Ok')
		self.__successPopup = Alert('Success', 'The scene was successfully exported.', 'Ok')

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()

	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__filenameDescription.text = ''
		self.__assetsPathDescription.text = ''
		self.__filename = None
		self.__assetsPath = None
		self.__popup.open()

class FilesOptionsMenu(SeparatorLabel, KeyboardAccess):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.close()

	def __startBasicButtonsLayout(self):

		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__newButton = CancelableButton(text = 'New Scene', on_release = self.__newScenePopup.open, **lineSize)
		self.__loadButton = CancelableButton(text = 'Load Scene', on_release = self.__loadScenePopup.open, **lineSize)
		self.__saveButton = CancelableButton(text = 'Save Scene', on_release = self.__saveScenePopup.open, **lineSize)
		self.__exportButton = CancelableButton(text = 'Export Scene', on_release = self.__exportPopup.open, **lineSize)
		self.__closeButton = CancelableButton(text = 'Close', on_release = self.close, **lineSize)

		self.__layout.add_widget(self.__newButton)
		self.__layout.add_widget(self.__loadButton)
		self.__layout.add_widget(self.__saveButton)
		self.__layout.add_widget(self.__exportButton)
		self.__layout.add_widget(self._separator)
		self.__layout.add_widget(self.__closeButton)

		self.__popup = Popup(title = 'Scene Options', content = self.__layout, auto_dismiss = False, **optionsMenuSize)

	def __init__(self):
		super(FilesOptionsMenu, self).__init__()
		self.__newScenePopup = NewScenePopup()
		self.__saveScenePopup = SaveScenePopup()
		self.__loadScenePopup = LoadScenePopup()
		self.__exportPopup = ExportScenePopup()
		self.__startBasicButtonsLayout()
		ModulesAccess.add('FilesOptions', self)

	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__popup.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()

