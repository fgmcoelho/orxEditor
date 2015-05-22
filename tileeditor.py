#/usr/bin/python
from kivy import require
require('1.8.0')

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.config import Config
from kivy.core.window import Window


from uisizes import mainLayoutSize, descriptorLabelDefault, sceneMiniMapSize
from keyboard import KeyboardGuardian, KeyboardAccess
from scene import SceneHandler, SceneMiniMap
from optionsmenu import OptionsMenu
from objectsmenu import ObjectsMenu
from tilemapfiles import FilesManager
from collision import CollisionGuardian, CollisionFlagsEditor, CollisionInformationPopup, CollisionFlagFormEditorPopup
from resourceloader import ResourceLoaderPopup
from layer import LayerInformationPopup
from communicationobjects import CollisionToSceneCommunication, SceneToObjectsMenu, SceneToFilesManager
from communicationobjects import CollisionToCollisionForm, ObjectDescriptorToResourceLoarder, LayerToSceneCommunication
from communicationobjects import ResourceLoaderToObjectDescriptor, FileOptionsMenuToScene

from objectsmenu import NewBaseObjectDisplay, NewBaseObjectsMenu
from objectdescriptor import NewObjectDescriptor
from modulesaccess import ModulesAccess
from editorutils import AlignedLabel

class TileEditor(App, KeyboardAccess):

	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] in ['shift', 'ctrl', 'lctrl', 'rctrl']):
			self.__sceneHandler.processKeyUp(keyboard, keycode)

	# Overloaded method
	def _processKeyDown(self, keyboard, keycode, text, modifiers):
		if ((len(keycode[1]) == 1 and keycode[1] in 'qwertasdfg\\z\'`xcvy') or
				keycode[1] in ['shift', 'ctrl', 'lctrl', 'rctrl', 'delete']):
			self.__sceneHandler.processKeyDown(keyboard, keycode, text, modifiers)

		elif (len(keycode[1]) == 1 and keycode[1] in '123456789'):
			if ('ctrl' in modifiers):
				ObjectsMenu.Instance().setShortcut(keycode[1])
			else:
				ObjectsMenu.Instance().processShortcut(keycode[1])

	def confirm_exit(self, *args):
		# TODO:  exit confirmation here!
		print 'We got exit confirmation: ', args
		return False

	def test_dropfile(self, *args):
		print 'Files dropped: ', args

	def test_dropfile(self, *args):
		print "File dropped: ", args

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
		Window.on_request_close = self.confirm_exit
		Window.on_dropfile = self.test_dropfile

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

		# Files handlers
		FilesManager.Instance()

		# Scene Editor handlers:
		SceneMiniMap()

		self.__sceneHandler = SceneHandler()
		self.rightScreen.add_widget(self.__sceneHandler.getLayout())
		KeyboardGuardian.Instance().acquireKeyboard(self)

		# Collision Handlers:
		CollisionGuardian.Instance()
		CollisionFlagFormEditorPopup.Instance()
		CollisionInformationPopup.Instance()
		CollisionFlagsEditor.Instance()

		# Bottom Menu Handler
		#OptionsMenu.Instance(self.rightScreen)

		# Left Menu Handler
		#ObjectsMenu.Instance()
		#self.leftMenuBase.add_widget(ObjectsMenu.Instance().getLayout())
		NewBaseObjectDisplay()
		NewBaseObjectsMenu()
		NewObjectDescriptor()

		self.leftMenuBase.add_widget(ModulesAccess.get('BaseObjectsMenu').getLayout())
		self.leftMenuBase.add_widget(ModulesAccess.get('BaseObjectDisplay').getLayout())
		bottomMenu = BoxLayout(orientation = 'horizontal', height = mainLayoutSize['bottomMenuHeight'],
			size_hint = (1.0, None))
		self.rightScreen.add_widget(bottomMenu)

		leftBottomMenu = BoxLayout(orientation = 'vertical')
		leftBottomMenu.add_widget(AlignedLabel(text = 'Object descriptor', **descriptorLabelDefault))
		leftBottomMenu.add_widget(ModulesAccess.get('ObjectDescriptor').getLayout())
		bottomMenu.add_widget(leftBottomMenu)

		rightBottomMenu = BoxLayout(orientation = 'vertical', width = sceneMiniMapSize['size'][0], size_hint_x = None)
		rightBottomMenu.add_widget(AlignedLabel(text = 'MiniMap', **descriptorLabelDefault))
		rightBottomMenu.add_widget(ModulesAccess.get('MiniMap').getLayout())
		bottomMenu.add_widget(rightBottomMenu)

		# ResourceLoader
		self.__resourcePopup = ResourceLoaderPopup()

		# Layers
		LayerInformationPopup.Instance()

		# Communication Objects
		CollisionToSceneCommunication.Instance(self.__sceneHandler.getCurrentSelection,
			self.__sceneHandler.getAllObjects)
		SceneToObjectsMenu.Instance(self.__sceneHandler.draw)
		SceneToFilesManager.Instance(self.__sceneHandler.getCurrentSceneObjects,
			self.__sceneHandler.getCurrentSceneAttributes, self.__sceneHandler.newScene,
			self.__sceneHandler.addObjectByInfo, self.__sceneHandler.setSceneObjectId,
			self.__sceneHandler.getSceneObjectId)
		CollisionToCollisionForm.Instance(CollisionInformationPopup.Instance().callPreview)
		ObjectDescriptorToResourceLoarder.Instance(self.__resourcePopup.open)
		#ResourceLoaderToObjectDescriptor.Instance(ObjectsMenu.Instance().reloadResource)
		LayerToSceneCommunication.Instance(self.__sceneHandler.getCurrentSelection,
			self.__sceneHandler.getAllObjects, self.__sceneHandler.redraw)
		FileOptionsMenuToScene.Instance(self.__sceneHandler.newScene)

		# Periodic functions:
		Clock.schedule_interval(self.__sceneHandler.clearScenes, 30)

		return self.root

if __name__ == '__main__':
	te = TileEditor()
	try:
		Window.maximize()
	except:
		# maximize may not be supported
		pass

	te.run()

