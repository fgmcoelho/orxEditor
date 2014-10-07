#!/usr/bin/python
from kivy import require
require('1.7.2')

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.config import Config

from keyboard import KeyboardGuardian
from optionsmenu import OptionsMenu
from scene import SceneHandler, SceneAttributes
from objectsmenu import ObjectsMenu
from tilemapfiles import FilesManager
from collision import CollisionGuardian, CollisionFlagsEditor, CollisionInformationPopup, CollisionFlagFormEditorPopup
from communicationobjects import CollisionToSceneCommunication, SceneToObjectsMenu

class TileEditor(App):

	def build_config(self, c):
		Config.set('graphics', 'width', 800)
		Config.set('graphics', 'height', 600)
		Config.set('graphics', 'fullscreen', 0)
		Config.set('input', 'mouse', 'mouse,disable_multitouch')
		Config.write()

	def build(self):

		self.root = BoxLayout(orientation='horizontal', padding = 0, spacing = 0)

		self.leftMenuBase = BoxLayout(
			orientation='vertical',
			padding = 0,
			spacing = 0,
			size_hint = (0.25, 1.0)
		)

		self.rightScreen = BoxLayout(
			orientation = 'vertical',
			padding = 0,
			spacing = 0,
			size_hint = (0.75, 1.0),
		)

		self.root.add_widget(self.leftMenuBase)
		self.root.add_widget(self.rightScreen)

		#Keyboard handler:
		KeyboardGuardian.Instance()

		# Files handlers
		FilesManager.Instance()

		# Scene Editor handlers:
		SceneAttributes.Instance(40, 20, 20)
		self.__sceneHandler = SceneHandler()
		self.rightScreen.add_widget(self.__sceneHandler.getLayout())
		KeyboardGuardian.Instance().acquireKeyboard(self.__sceneHandler)

		# Collision Handlers:
		CollisionGuardian.Instance()
		CollisionFlagFormEditorPopup.Instance()
		CollisionInformationPopup.Instance()
		CollisionFlagsEditor.Instance()

		# Bottom Menu Handler
		OptionsMenu.Instance(self.rightScreen)

		# Left Menu Handler
		ObjectsMenu.Instance()
		self.leftMenuBase.add_widget(ObjectsMenu.Instance().getLayout())

		# Communication Objects
		CollisionToSceneCommunication.Instance(self.__sceneHandler.getCurrentSelection, self.__sceneHandler.getAllObjects)
		SceneToObjectsMenu.Instance(self.__sceneHandler.draw)

		# Periodic functions:
		Clock.schedule_interval(self.__sceneHandler.clearScenes, 30)

		return self.root

if __name__ == '__main__':
	TileEditor().run()
