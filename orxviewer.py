from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.checkbox import CheckBox
from kivy.network.urlrequest import UrlRequest

from editorheritage import SeparatorLabel
from editorutils import AlignedLabel, CancelableButton, NumberInput, boolToStr
from uisizes import defaultLineSize, defaultLabelSize, defaultSmallButtonSize, orxViewerSize, defaultInputSize, \
	defaultCheckboxSize
from keyboard import KeyboardAccess, KeyboardGuardian

from platform import system, machine
from os import environ, chdir, mkdir, unlink, chmod, spawnve, P_NOWAITO
from os.path import join, isfile, exists, abspath, dirname
from sys import argv
from modulesaccess import ModulesAccess
from zipfile import ZipFile


class ViewerConfigs(object):
	def __init__(self):
		super(ViewerConfigs, self).__init__()
		self._defaults = {
			"Display": {
				"ScreenWidth":  "800",
				"ScreenHeight": "600",
				"Title":        "OrxViewer",
				"RefreshRate":  "60",
				"VSync" :       "true",
			},

			"Viewport": {
				"Camera":          "Camera",
				"BackgroundColor": "(0x00, 0x11, 0x2B)",
			},

			"Resource": {
				"Texture": "../tiles/",
			},

			"Mouse": {
				"ShowCursor": "true",
			},

			"Camera": {
				"Position":      "(400, 300, 0)",
				"GroupList":     "@General.GroupList",
				"FrustumWidth":  "@Display.ScreenWidth",
				"FrustumHeight": "@Display.ScreenHeight",
				"FrustumFar":    "2.0",
				"Zoom":          "1.0",
			},

			"Input": {
				"SetList": "MainInput",
			},

			"Physics" : {
				"ShowDebug": "true",
			},

			"MainInput": {
				"KEY_ESCAPE": "Quit",
				"KEY_UP":     "MoveUp",
				"KEY_DOWN":   "MoveDown",
				"KEY_LEFT":   "MoveLeft",
				"KEY_RIGHT":  "MoveRight",
			},
		}

class OrxViewer(ViewerConfigs, SeparatorLabel, KeyboardAccess):
	# overloaded method:
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.close()

		elif (keycode[1] == 'tab'):
			NumberInput.selectInputByFocus("OrxViewer")

	def _hasViewer(self):
		path = join(self.__currentPath, "bin", self.__filename)
		if (exists(path) == True and isfile(path) == True):
			return True
		else:
			return False

	def _download_finish(self, *args):
		if (self.__request.is_finished == False):
			print "Not Finished!"
			return
		try:
			tmpDir = join(self.__currentPath, "tmp")
			binDir = join(self.__currentPath, "bin")
			zipFilePath = join(tmpDir, "tmp_viewer.zip")
			zipFile = ZipFile(zipFilePath)
			assert zipFile.testzip() is None, "Corrupted zip file."
			filesList = zipFile.namelist()
			print filesList, self.__usedLib, self.__filename
			assert len(filesList) == 2 and self.__usedLib in filesList and self.__filename in filesList,\
				"Zip file content is invalid."
			zipFile.extractall(binDir)
			if (self.__system == 'linux'):
				chmod(join(binDir, self.__filename), 0755)
				chmod(join(binDir, self.__usedLib), 0700)

		except Exception, e:
			print "Error getting the viewer_file: " + str(e)

		if (exists(zipFilePath) == True):
			unlink(zipFilePath)

		self.__renderLaunch()

	def _updateProgress(self, request, currentSize, totalSize):
		self.__downloadProgress.value = currentSize
		if (self.__downloadProgress.parent is None):
			self.__downloadProgress.max = totalSize
			self.__renderDownload(addProgress = True)

	def _downloadStart(self, *args):
		tmpDir = join(self.__currentPath, "tmp")
		if (exists(tmpDir) == False):
			mkdir(tmpDir)

		binDir = join(self.__currentPath, "bin")
		if (exists(binDir) == False):
			mkdir(binDir)

		url = self.__serverIp + "/" + self.__getUrl + "/" + self.__system + "_" + self.__arch
		zipFilePath = join(tmpDir, "tmp_viewer.zip")
		self.__request = UrlRequest(
			url,
			on_success = self._download_finish,
			on_progress = self._updateProgress,
			file_path = zipFilePath)

	def __launch(self, *args):
		if (self.__widthInput.text == "0" or self.__heightInput.text == "0"):
			return

		self._defaults["Display"]["ScreenWidth"] = self.__widthInput.text
		self._defaults["Display"]["ScreenHeight"] = self.__heightInput.text
		self._defaults["Physics"]["ShowDebug"] = boolToStr(self.__debugPhysicsCheckbox.active)
		self._defaults["Camera"]["Position"] = "(" + str(int(self.__widthInput.text) / 2) + ", " + \
				str(int(self.__heightInput.text) / 2) + ", 0)"

		try:
			ModulesAccess.get("FilesManager").exportScene(
				join(self.__currentPath, "bin", self.__iniName),
				join(self.__currentPath, "tiles"),
				True,
				self._defaults
			)

			chdir("bin")
			spawnve(P_NOWAITO, self.__filename, [self.__filename], self.__environ)
			chdir("..")
			

		except Exception, e:
			print "Error launching the application: " + str(e)

	def __startVariables(self):
		arch = machine()
		if (arch.find("64") != -1):
			self.__arch = "64"
		else:
			self.__arch = "32"

		self.__currentPath = abspath(dirname(argv[0]))
		self.__system = system().lower()
		self.__environ = environ.copy()
		if (self.__system == "linux"):
			if (self.__environ.has_key("LD_LIBRARY_PATH") == True):
				self.__environ['LD_LIBRARY_PATH'] += ":."
			else:
				self.__environ['LD_LIBRARY_PATH'] = "."
		self.__serverIp = "http://162.243.96.233:5000"
		self.__getUrl = "get_viewer"
		if (self.__system == "linux"):
			self.__usedLib = "liborxd.so"
		else:
			self.__usedLib = "liborxd.dll"
		self.__filename = "viewer_" + self.__system + "_" + self.__arch
		self.__iniName = self.__filename + '.ini'
		if (self.__system == "windows"):
			self.__filename += ".exe"

	def __startUi(self):
		self.__layout = BoxLayout(orientation = "vertical")
		self.__downloadLine = BoxLayout(orientation = "horizontal", **defaultLineSize)
		self.__downloadLine.add_widget(AlignedLabel(text = "You don't have the viewer.", **defaultLabelSize))
		self.__downloadLine.add_widget(CancelableButton(text = 'Download', on_release = self._downloadStart,
			**defaultSmallButtonSize))
		self.__downloadProgress = ProgressBar(**defaultLineSize)
		self.__finishLine = BoxLayout(orientation = "horizontal", **defaultLineSize)
		self.__launchButton = CancelableButton(text = 'Launch', on_release = self.__launch, **defaultSmallButtonSize)
		self.__cancelButton = CancelableButton(text = 'Cancel', on_release = self.close, **defaultSmallButtonSize)

		inputSize = defaultInputSize.copy()
		inputSize['size_hint'] = (None, None)
		inputSize['width'] = 100
		labelInputSize = defaultInputSize.copy()

		self.__widthLine = BoxLayout(orientation = "horizontal", **labelInputSize)
		self.__widthInput = NumberInput(text = self._defaults["Display"]["ScreenWidth"], module = "OrxViewer")
		self.__widthLine.add_widget(AlignedLabel(text = "Width:"))
		self.__widthLine.add_widget(self.__widthInput)

		self.__heightLine = BoxLayout(orientation = "horizontal", **labelInputSize)
		self.__heightInput = NumberInput(text = self._defaults["Display"]["ScreenHeight"], module = "OrxViewer")
		self.__heightLine.add_widget(AlignedLabel(text = "Height:"))
		self.__heightLine.add_widget(self.__heightInput)

		self.__debugPhysicsLine = BoxLayout(orientation = "horizontal", **defaultLineSize)
		self.__debugPhysicsCheckbox = CheckBox(active = True, **defaultCheckboxSize)
		self.__debugPhysicsLine.add_widget(self.__debugPhysicsCheckbox)
		self.__debugPhysicsLine.add_widget(AlignedLabel(text = 'Debug physics.', **defaultLabelSize))

		self.__popup = Popup(title = 'Orx Viewer', content = self.__layout, auto_dismiss = False, **orxViewerSize)

	def __renderDownload(self, addProgress = False):
		self.__layout.clear_widgets()
		self.__finishLine.clear_widgets()
		self.__layout.add_widget(self.__downloadLine)
		if (addProgress == True):
			self.__layout.add_widget(self.__downloadProgress)
		self.__layout.add_widget(self.getSeparator())
		self.__finishLine.add_widget(self.getSeparator())
		self.__finishLine.add_widget(self.__cancelButton)
		self.__layout.add_widget(self.__finishLine)

	def __renderLaunch(self, *args):
		self.__layout.clear_widgets()
		self.__finishLine.clear_widgets()
		self.__layout.add_widget(self.__widthLine)
		self.__layout.add_widget(self.__heightLine)
		self.__layout.add_widget(self.getSeparator())
		self.__finishLine.add_widget(self.getSeparator())
		self.__layout.add_widget(self.__debugPhysicsLine)
		self.__finishLine.add_widget(self.__launchButton)
		self.__finishLine.add_widget(self.__cancelButton)
		self.__layout.add_widget(self.__finishLine)

	def __init__(self):
		super(OrxViewer, self).__init__()
		ModulesAccess.add("OrxViewer", self)
		self.__startVariables()
		self.__startUi()

	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		if (self._hasViewer() == False):
			self.__renderDownload()
		else:
			self.__renderLaunch()
		self.__popup.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()
