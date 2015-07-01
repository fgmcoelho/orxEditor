from kivy.uix.boxlayout import BoxLayout
from editorutils import Dialog, Alert
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.checkbox import CheckBox

from editorutils import CancelableButton, NumberInput, AlignedLabel
from editorheritage import SeparatorLabel
from uisizes import optionsMenuSize, defaultLineSize, newSceneSize, defaultInputSize, defaultFontSize, \
		defaultSmallButtonSize, defaultLabelSize, exportSceneSize
from tilemapfiles import FilesManager
from keyboard import KeyboardAccess, KeyboardGuardian
from collisioninfo import CollisionGuardian
from scene import SceneAttributes
from modulesaccess import ModulesAccess

from os import getcwd
from os.path import isfile, join, abspath, sep as pathSeparator

class FileOptionsConfig(object):
	def __init__(self):
		super(FileOptionsConfig, self).__init__()
		self._fileOrDirectorySize = defaultInputSize.copy()
		self._fileOrDirectorySize['width'] = 40
		self._fileOrDirectorySize['size_hint'] = (None, None)

		self._checkboxSize = {
			'width' : 25,
			'height' : defaultFontSize,
			'size_hint' : (None, None)
		}

class NewScenePopup(KeyboardAccess, SeparatorLabel, FileOptionsConfig):
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
		ModulesAccess.get('SceneHandler').newScene(newSceneAttributes)

		self.close()
		ModulesAccess.get('FilesOptions').close()

	def __init__(self):
		super(NewScenePopup, self).__init__()
		inputSize = defaultInputSize.copy()
		inputSize['size_hint'] = (None, None)
		inputSize['width'] = 100

		labelInputSize = defaultInputSize.copy()

		self.__popup = Popup(title = 'New Scene Attributes', auto_dismiss = False, **newSceneSize)
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__tileSizeInput = NumberInput(module = 'NewScene', **inputSize)
		self.__xTilesInput = NumberInput(module = 'NewScene', **inputSize)
		self.__yTilesInput = NumberInput(module = 'NewScene', **inputSize)
		self.__keepCollisionFlags = CheckBox(**self._checkboxSize)
		self.__keepGroupsFlags = CheckBox(**self._checkboxSize)
		self.__okButton = CancelableButton(text = 'Ok', on_release = self.__confirm, **defaultSmallButtonSize)
		self.__cancelButton = CancelableButton(text = 'Cancel', on_release = self.close, **defaultSmallButtonSize)

		tilesSizeLine = BoxLayout(orientation = 'horizontal', **labelInputSize)
		tilesSizeLine.add_widget(AlignedLabel(text = 'Size of the tiles:', **labelInputSize))
		tilesSizeLine.add_widget(self.__tileSizeInput)

		xNumberOfTilesLine = BoxLayout(orientation = 'horizontal', **labelInputSize)
		xNumberOfTilesLine.add_widget(AlignedLabel(text = 'Number of tiles on X:', **labelInputSize))
		xNumberOfTilesLine.add_widget(self.__xTilesInput)

		yNumberOfTilesLine = BoxLayout(orientation = 'horizontal', **labelInputSize)
		yNumberOfTilesLine.add_widget(AlignedLabel(text = 'Number of tiles on Y:', **labelInputSize))
		yNumberOfTilesLine.add_widget(self.__yTilesInput)

		keepCollisionFlagsLine = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		keepCollisionFlagsLine.add_widget(self.__keepCollisionFlags)
		keepCollisionFlagsLine.add_widget(AlignedLabel(text = 'Keep collision flags.', **defaultLineSize))

		keepGroupsLine = BoxLayout (orientation = 'horizontal', **defaultLineSize)
		keepGroupsLine.add_widget(self.__keepGroupsFlags)
		keepGroupsLine.add_widget(AlignedLabel(text = 'Keep layer groups.', **defaultLineSize))

		confirmLine = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		confirmLine.add_widget(AlignedLabel(text = ''))
		confirmLine.add_widget(self.__okButton)
		confirmLine.add_widget(self.__cancelButton)

		self.__layout.add_widget(tilesSizeLine)
		self.__layout.add_widget(xNumberOfTilesLine)
		self.__layout.add_widget(yNumberOfTilesLine)
		self.__layout.add_widget(self._separator)
		self.__layout.add_widget(keepCollisionFlagsLine)
		self.__layout.add_widget(keepGroupsLine)
		self.__layout.add_widget(AlignedLabel(text = 'Any unsaved changes will be lost.', **defaultLineSize))
		self.__layout.add_widget(confirmLine)

		self.__popup.content = self.__layout
		self.__isShiftPressed = False

	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__popup.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()

class FileSelectorPopup(KeyboardAccess, FileOptionsConfig, SeparatorLabel):
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
		super(FileSelectorPopup, self).__init__()
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
		self.__fileChooserInputLayout = BoxLayout(orientation = 'horizontal', **defaultInputSize)
		self.__fileChooser = FileChooserIconView(size_hint = (1, 1))
		if (directoriesOnly == True):
			self.__fileChooserInput = TextInput(multiline = False, readonly = True, **defaultInputSize)
			self.__fileChooserInputLayout.add_widget(AlignedLabel(text = 'Directory:', **self._fileOrDirectorySize))
			self.__filters = [''] # we want to cut out all the files in this case
			self.__fileChooser.dirselect = True
			self.__fileChooser.bind(path = self.__setDirectory)
		else:
			self.__fileChooserInput = TextInput(multiline = False, **defaultInputSize)
			self.__fileChooserInputLayout.add_widget(AlignedLabel(text = 'File:', **self._fileOrDirectorySize))
			self.__fileChooser.on_submit = self.__submit
			self.__filters = filters

		self.__fileChooser.filters = self.__filters
		self.__fileChooserInputLayout.add_widget(self.__fileChooserInput)
		self.__finishMethod = finishMethod
		self.__fileChooserYesNoLayout = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		self.__fileChooserOkButton = CancelableButton(text = 'Ok', on_release = self.__validate,
			**defaultSmallButtonSize)
		self.__fileChooserCancelButton = CancelableButton(text = 'Cancel', on_release = self.close,
			**defaultSmallButtonSize)
		self.__fileChooserYesNoLayout.add_widget(self._separator)
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

class FileChooserUser(FileOptionsConfig, SeparatorLabel):
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
		super(FileChooserUser, self).__init__()
		self._fileChooserLayout = BoxLayout(orientation = 'vertical')
		self._fileChooserPopUp = Popup(auto_dismiss = False, title = 'Select the file:')
		self._fileChooserInputLayout = BoxLayout(orientation = 'horizontal', **defaultInputSize)
		self._fileChooserInput = TextInput(multiline = False, **defaultInputSize)
		self._fileChooserInputLayout.add_widget(AlignedLabel(text = 'File:', **self._fileOrDirectorySize))
		self._fileChooserInputLayout.add_widget(self._fileChooserInput)
		self._fileChooser = FileChooserIconView(size_hint = (1.0, 1.0))
		self._fileChooser.on_submit = self._submitMethod

		self._fileChooserYesNoLayout = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		# The Ok functionality is defined by the child class.
		self._fileChooserOkButton = CancelableButton(text = 'Ok', **defaultSmallButtonSize)
		self._fileChooserCancelButton = CancelableButton(text = 'Cancel', on_release = self.close,
			**defaultSmallButtonSize)

		self._fileChooserYesNoLayout.add_widget(self._separator)
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

class ExportScenePopup (KeyboardAccess, FileOptionsConfig, SeparatorLabel):
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
		super(ExportScenePopup, self).__init__()

		self.__filename = None
		self.__assetsPath = None

		self.__fileChooser = FileSelectorPopup(filters = ['*.ini'], finishMethod = self.__setFilename)
		self.__assetsChooser = FileSelectorPopup(finishMethod = self.__setAssetsPath, directoriesOnly = True)

		buttonOptions = defaultSmallButtonSize.copy()
		buttonOptions['height'] = defaultInputSize['height']

		self.__layout = BoxLayout(orientation = 'vertical')
		self.__filenameDescription = TextInput(text = '', readonly = True, multiline = False, **defaultInputSize)
		self.__chooseFilenameButton = CancelableButton(text = 'Choose', on_release = self.__fileChooser.open,
			**buttonOptions)
		self.__assetsPathDescription = TextInput(text = '', readonly = True, multiline = False, **defaultInputSize)
		self.__assetsPathButton = CancelableButton(text = 'Choose', on_release = self.__assetsChooser.open,
			**buttonOptions)
		self.__smoothCheckBox = CheckBox(active = True, **self._checkboxSize)
		self.__okButton = CancelableButton(text = 'Ok', on_release = self.__confirm, **defaultSmallButtonSize)
		self.__cancelButton = CancelableButton(text = 'Cancel', on_release = self.close, **defaultSmallButtonSize)

		self.__filenameLine = BoxLayout(orientation = 'horizontal', **defaultInputSize)
		self.__filenameLine.add_widget(self.__filenameDescription)
		self.__filenameLine.add_widget(self.__chooseFilenameButton)

		self.__assetsPathLine = BoxLayout(orientation = 'horizontal', **defaultInputSize)
		self.__assetsPathLine.add_widget(self.__assetsPathDescription)
		self.__assetsPathLine.add_widget(self.__assetsPathButton)

		self.__smoothLine = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		self.__smoothLine.add_widget(self.__smoothCheckBox)
		self.__smoothLine.add_widget(AlignedLabel(text = 'Turn on graphics smoothing', **defaultLabelSize))

		self.__confirmLine = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		self.__confirmLine.add_widget(AlignedLabel(text = '', height = defaultFontSize, size_hint = (1.0, None)))
		self.__confirmLine.add_widget(self.__okButton)
		self.__confirmLine.add_widget(self.__cancelButton)

		self.__layout.add_widget(AlignedLabel(text = 'Ini file to export the scene:', **defaultLabelSize))
		self.__layout.add_widget(self.__filenameLine)
		self.__layout.add_widget(AlignedLabel(text = 'Directory to save the assets:', **defaultLabelSize))
		self.__layout.add_widget(self.__assetsPathLine)
		self.__layout.add_widget(self._separator)
		self.__layout.add_widget(self.__smoothLine)
		self.__layout.add_widget(self.__confirmLine)

		self.__popup = Popup(auto_dismiss = False, title = 'Export Scene', content = self.__layout, **exportSceneSize)
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
		self.__newButton = CancelableButton(text = 'New Scene', on_release = self.__newScenePopup.open,
			**defaultLineSize)
		self.__loadButton = CancelableButton(text = 'Load Scene', on_release = self.__loadScenePopup.open,
			**defaultLineSize)
		self.__saveButton = CancelableButton(text = 'Save Scene', on_release = self.__saveScenePopup.open,
			**defaultLineSize)
		self.__exportButton = CancelableButton(text = 'Export Scene', on_release = self.__exportPopup.open,
			**defaultLineSize)
		self.__closeButton = CancelableButton(text = 'Close', on_release = self.close, **defaultLineSize)

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

