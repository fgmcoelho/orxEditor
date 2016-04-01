#/usr/bin/python
from kivy import require
require('1.8.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.config import Config
from kivy.core.window import Window

from uisizes import mainLayoutSize, defaultLabelSize, sceneMiniMapSize
from keyboard import KeyboardGuardian, KeyboardAccess
from scene import SceneHandler, SceneMiniMap
from tilemapfiles import FilesManager
from collision import CollisionFlagEditorPopup, CollisionEditorPopup
from collisionform import CollisionFormEditorPopup
from collisioninfo import CollisionGuardian
from resourceloader import ResourceLoaderPopup
from animationeditor import AnimationEditor
from editorutils import Dialog

from layer import LayerInformationPopup
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

class OrxEditor(App, KeyboardAccess):
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

	def build(self):
		self._debugTools = False
		self._profiler = None
		self._timer = None
		Window.on_request_close = self.confirm_exit

		self.root = BoxLayout(orientation='horizontal', padding = 0, spacing = 0)

		self.leftMenuBase = BoxLayout(
			orientation='vertical',
			padding = 0,
			spacing = 0,
			size_hint = mainLayoutSize['leftMenuSizeHint'],
			width = mainLayoutSize['leftMenuWidth'],
		)

		self.rightScreen = BoxLayout(
			orientation = 'vertical',
			padding = 0,
			spacing = 0,
			size_hint = (1.0, 1.0),
		)

		self.root.add_widget(self.leftMenuBase)
		self.root.add_widget(self.rightScreen)

		#Keyboard handler:
		KeyboardGuardian.Instance()

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

		# Left Menu Handler
		NewBaseObjectDisplay()
		NewBaseObjectsMenu()
		ObjectDescriptor()

		# Files handlers
		FilesManager()
		OrxViewer()

		# Scene Editor handlers:
		SceneMiniMap()

		FilesOptionsMenu()

		AnimationSelector()

		self.__sceneHandler = SceneHandler()
		self.rightScreen.add_widget(self.__sceneHandler.getLayout())
		KeyboardGuardian.Instance().acquireKeyboard(self)

		# Bottom Menu Handler
		self.leftMenuBase.add_widget(ModulesAccess.get('BaseObjectsMenu').getLayout())
		self.leftMenuBase.add_widget(ModulesAccess.get('BaseObjectDisplay').getLayout())
		bottomMenu = BoxLayout(orientation = 'horizontal', height = mainLayoutSize['bottomMenuHeight'],
			size_hint = (1.0, None))
		self.rightScreen.add_widget(bottomMenu)

		leftBottomMenu = BoxLayout(orientation = 'vertical')
		leftBottomMenu.add_widget(AlignedLabel(text = 'Object descriptor', **defaultLabelSize))
		leftBottomMenu.add_widget(ModulesAccess.get('ObjectDescriptor').getLayout())
		bottomMenu.add_widget(leftBottomMenu)

		rightBottomMenu = BoxLayout(orientation = 'vertical', width = sceneMiniMapSize['size'][0], size_hint_x = None)
		rightBottomMenu.add_widget(AlignedLabel(text = 'MiniMap', **defaultLabelSize))
		rightBottomMenu.add_widget(ModulesAccess.get('MiniMap').getLayout())
		bottomMenu.add_widget(rightBottomMenu)

		return self.root

if __name__ == '__main__':
	te = OrxEditor()
	try:
		Window.maximize()
	except:
		# maximize may not be supported
		pass

	te.run()

