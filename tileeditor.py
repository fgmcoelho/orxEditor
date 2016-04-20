#/usr/bin/python

# HOTFIX FOR KIVY 1.9.1, Windows version!
from platform import system
from sys import executable, exit, argv
from os.path import dirname, join, exists
from os import environ, execvpe, getcwd
import kivy

def exit_known_bug():
	print environ['path']
	print 'You ran into a known Kivy issue, I tried automatically fixing it for you but I failed.'
	print 'Stupid me! =('
	print 'Please check the solution here:'
	print 'https://github.com/kivy/kivy/issues/3957'
	exit()

if (kivy.__version__ == '1.9.1' and system().lower() == 'windows'):
	try:
		from kivy.uix.label import Label
	except:
		if (environ.get('BUG_FIX_1.9.1') == '1'):
			exit_known_bug()

		pythonPath = dirname(executable)
		fullPath = join(pythonPath, 'share', 'gstreamer', 'bin')
		print fullPath
		if (exists(fullPath) == True):
			environ['path'] =  fullPath + ';' + environ['path']
			environ['BUG_FIX_1.9.1'] = '1'
			print ' '.join(argv)
			execvpe('python', ['-i', 'tileeditor.py'], environ)
		else:
			exit_known_bug()

# END OF HOTFIX 1.9.1 Windows
from kivy import require
require('1.8.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.config import Config
from kivy.core.window import Window

from uisizes import mainLayoutLeftMenuSize, defaultLabelSize, sceneMiniMapSize, defaultLineSize, mainLayoutBottomSize,\
	defaultSmallButtonSize, defaultLargeButtonSize
from keyboard import KeyboardGuardian, KeyboardAccess
from scene import SceneHandler, SceneMiniMap
from tilemapfiles import FilesManager
from collision import CollisionFlagEditorPopup, CollisionEditorPopup
from collisionform import CollisionFormEditorPopup
from collisioninfo import CollisionGuardian
from resourceloader import ResourceLoaderPopup
from animationeditor import AnimationEditor
from editorutils import Dialog, CancelableToggleButton
from editorheritage import SeparatorLabel
from layer import LayerInformationPopup, LayerSelector
from layerinfo import LayerGuardian
from editorobjects import BaseObject
from orxviewer import OrxViewer
from objectsmenu import NewBaseObjectDisplay, NewBaseObjectsMenu
from objectdescriptor import ObjectDescriptor
from modulesaccess import ModulesAccess
from editorutils import AlignedLabel
from filesoptionsmenu import FilesOptionsMenu
from animationeditor import AnimationSelector

from cProfile import Profile
from time import time

class OrxEditor(App, KeyboardAccess, SeparatorLabel):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] in ['shift', 'ctrl', 'lctrl', 'rctrl']):
			self.__sceneHandler.processKeyUp(keycode)

		if (keycode[1] == 'escape'):
			ModulesAccess.get('FilesOptions').open()

	# Overloaded method
	def _processKeyDown(self, keyboard, keycode, text, modifiers):
		if ((len(keycode[1]) == 1 and keycode[1] in 'qwertasdfg\\z\'`xcvmn') or
				keycode[1] in ['shift', 'ctrl', 'lctrl', 'rctrl', 'delete', 'pageup', 'pagedown']):
			self.__sceneHandler.processKeyDown(keycode, modifiers)
		elif (keycode[1] == 'spacebar'):
			obj = ModulesAccess.get('BaseObjectDisplay').getCurrentObject()
			if (isinstance(obj, BaseObject) == True):
				ModulesAccess.get('SceneHandler').draw(obj)
		elif (keycode[1] in ['up', 'down', 'left', 'right']):
			if ('ctrl' in modifiers):
				ModulesAccess.get('BaseObjectsMenu').updateSelectedNode(keycode[1])
		elif (keycode[1] == "f5"):
			ModulesAccess.get("OrxViewer").open()
		elif (keycode[1] == 'p' and self._debugTools == True):
			if (self._profiler is None):
				self._profiler = Profile()
				self._profiler.enable()
			else:
				self._profiler.disable()
				self._profiler.dump_stats('profile_logs/profiler_' + str(time()) + '.stats')
				self._profiler = None
		elif (keycode[1] == 'o' and self._debugTools == True):
			if (self._timer is None):
				self._timer = time()
			else:
				print "Total time: ", time() - self._timer
				self._timer = None
		elif (keycode[1] == 'l'):
			ModulesAccess.get('AnimationSelector').open()
		elif (keycode[1] == 'tab'):
			describedObjects = ModulesAccess.get('ObjectDescriptor').getCurrentObject()
			if (describedObjects is None):
				ModulesAccess.get('BaseObjectDisplay').updateDescriptor()
			elif (type(describedObjects) is list):
				ModulesAccess.get('BaseObjectDisplay').updateDescriptor()
			elif (isinstance(describedObjects, BaseObject) == True):
				ModulesAccess.get('SceneHandler').updateDescriptorBySelection()
			else:
				ModulesAccess.get('BaseObjectDisplay').updateDescriptor()

	def confirm_exit(self, source=''):
		if (self.__sceneHandler.hasChanges() == True):
			Dialog(self.stop, 'Confirmation',
				'You have unsaved changes, are you sure\n'\
				'you want to leave the program?',
				'Yes', 'No', None, None).open()
			return True
		return False

	def build_config(self, c):
		Config.set('graphics', 'width', 800)
		Config.set('graphics', 'height', 600)
		Config.set('graphics', 'fullscreen', 0)
		Config.set('input', 'mouse', 'mouse,disable_multitouch')
		Config.set('kivy', 'desktop', 1)
		Config.set('kivy', 'log_enable', 0)
		Config.set('kivy', 'exit_on_escape', 0)
		Config.write()

	def moduleButtonMethod(self, button, touch):
		if (button.state == 'normal'):
			button.state = 'down'
		else:
			button.state = 'normal'
		self.updateButtons(button)

	def updateButtons(self, lastPressed):
		self._bottomModulesLine.clear_widgets()
		for register in self.__buttonsPriorityList:
			if register['order'] == len(self.__buttonsPriorityList):
				self._bottomModulesLine.add_widget(self.getSeparator())
			if register['button'].state == 'down':
				self._bottomModulesLine.add_widget(ModulesAccess.get(register['module']).getLayout())

	def build(self):
		super(OrxEditor, self).__init__()

		ModulesAccess.add('Main', self)

		self._debugTools = False
		self._profiler = None
		self._timer = None
		Window.on_request_close = self.confirm_exit

		#Keyboard handler:
		KeyboardGuardian.Instance()
		KeyboardGuardian.Instance().acquireKeyboard(self)

		# Global Guardians
		LayerGuardian()
		CollisionGuardian()

		# Popup Modules
		LayerInformationPopup()
		CollisionFlagEditorPopup()
		CollisionEditorPopup()
		CollisionFormEditorPopup()
		ResourceLoaderPopup()
		AnimationEditor()
		AnimationSelector()
		FilesOptionsMenu()

		# Left Menu Handler
		NewBaseObjectDisplay()
		NewBaseObjectsMenu()
		ObjectDescriptor()
		LayerSelector()

		# Files handlers
		FilesManager()
		OrxViewer()

		# Scene Editor handlers:
		SceneMiniMap()
		self.__sceneHandler = SceneHandler()

		# Top part of the screen
		top = BoxLayout(orientation = 'horizontal')

		leftMenuBase = BoxLayout(
			orientation = 'vertical', size_hint = (None, 1), width = 200
		)
		leftMenuBase.add_widget(ModulesAccess.get('BaseObjectsMenu').getLayout())

		rightScreen = BoxLayout(
			orientation = 'vertical',
			size_hint = (1.0, 1.0),
		)
		rightScreen.add_widget(self.__sceneHandler.getLayout())

		top.add_widget(leftMenuBase)
		top.add_widget(rightScreen)

		# Bottom part of the screen
		bottom = BoxLayout(orientation = 'vertical', height = 220, size_hint = (1.0, None))

		self._buttonsLine = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		self._showBaseObjectDisplay = CancelableToggleButton(text = 'Preview Display', state = 'down',
			method = self.moduleButtonMethod, **defaultLargeButtonSize)
		self._showDescriptor = CancelableToggleButton(text = 'Object Descriptor', state = 'down',
			method = self.moduleButtonMethod, **defaultLargeButtonSize)
		self._showMiniMap = CancelableToggleButton(text = 'MiniMap', state = 'down', method = self.moduleButtonMethod,
			**defaultSmallButtonSize)
		self._showLayers = CancelableToggleButton(text = 'Layers', state = 'down', method = self.moduleButtonMethod,
			**defaultSmallButtonSize)

		toolsSize = defaultLabelSize.copy()
		toolsSize['width'] = 200
		toolsSize['size_hint'] = (None, None)
		self._buttonsLine.add_widget(AlignedLabel(text= 'Loaded tools:', **toolsSize))
		self._buttonsLine.add_widget(self._showBaseObjectDisplay)
		self._buttonsLine.add_widget(self._showDescriptor)
		self._buttonsLine.add_widget(self._showLayers)
		self._buttonsLine.add_widget(self._showMiniMap)
		self._buttonsLine.add_widget(self.getSeparator())

		self._bottomModulesLine = BoxLayout(orientation = 'horizontal', **mainLayoutBottomSize)

		self._bottomModulesLine.add_widget(ModulesAccess.get('BaseObjectDisplay').getLayout())
		self._bottomModulesLine.add_widget(ModulesAccess.get('ObjectDescriptor').getLayout())
		self._bottomModulesLine.add_widget(ModulesAccess.get('LayerSelector').getLayout())
		self._bottomModulesLine.add_widget(self.getSeparator())
		self._bottomModulesLine.add_widget(ModulesAccess.get('MiniMap').getLayout())

		self.__buttonsPriorityList = [
			{
				'button': self._showBaseObjectDisplay,
				'module': 'BaseObjectDisplay',
				'order': 1
			},
			{
				'button': self._showDescriptor,
				'module': 'ObjectDescriptor',
				'order': 2
			},
			{
				'button': self._showLayers,
				'module': 'LayerSelector',
				'order': 3
			},
			{
				'button': self._showMiniMap,
				'module': 'MiniMap',
				'order': 4
			}
		]

		bottom.add_widget(self._buttonsLine)
		bottom.add_widget(self._bottomModulesLine)

		self.root = BoxLayout(orientation = 'vertical')
		self.root.add_widget(top)
		self.root.add_widget(bottom)

		return self.root

if __name__ == '__main__':
	te = OrxEditor()
	try:
		Window.maximize()
	except:
		# maximize may not be supported
		pass

	te.run()

