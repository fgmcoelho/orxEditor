#!/usr/bin/python
from kivy import require
require('1.7.2')

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.config import Config
from kivy.core.window import Window

from sys import argv, exit

from optionsmenu import OptionsMenu
from scene import Scene, SceneHandler,SceneAttributes
from objectsmenu import ObjectsMenu
from editorobjects import RenderObjectGuardian
from tilemapfiles import FilesManager
from objectdescriptor import ObjectDescriptor

class KeyboardAccess:
	
	def getKeyboardAccess(self, keyDownMethod = None, keyUpMethod = None):
		self.__keyDownMethod = keyDownMethod
		self.__keyUpMethod = keyUpMethod
		self.__keyboard = Window.request_keyboard(self.__finishKeyboard, self)
	
		if (self.__keyDownMethod != None):
			self.__keyboard.bind(on_key_down=self.__keyDownMethod)

		if (self.__keyUpMethod != None):
			self.__keyboard.bind(on_key_up=self.__keyUpMethod)


	def __finishKeyboard(self):
		if (self.__keyDownMethod != None):
			self.__keyboard.unbind(on_key_down=self.__keyDownMethod)

		if (self.__keyUpMethod != None):
			self.__keyboard.unbind(on_key_up=self.__keyUpMethod)
				
		self.__keyboard = None


class KeyboardShortcutHandler (KeyboardAccess):
	
	def __init__(self):
		self.getKeyboardAccess(self.__processKeyDown, self.__processKeyUp)
	
	def __processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'shift'):
			SceneHandler.Instance().setIsShiftPressed(False)

		elif (keycode[1] == 'ctrl'):
			SceneHandler.Instance().setIsCtrlPressed(False)

	def __processKeyDown(self, keyboard, keycode, text, modifiers):
		#print('The key', keycode, 'have been pressed')
		#print(' - text is %r' % text)
		#print(' - modifiers are %r' % modifiers)

		if (keycode[1] == 'q'):
			Scene.Instance().alignToGrid()

		elif (keycode[1] == 'a'):
			Scene.Instance().copyObject("left")

		elif (keycode[1] == 's'):
			Scene.Instance().copyObject("down")
		
		elif (keycode[1] == 'd'):
			Scene.Instance().copyObject("right")
		
		elif (keycode[1] == 'w'):
			Scene.Instance().copyObject("up")

		elif (keycode[1] == 'e'):
			Scene.Instance().unselectAll()

		elif (keycode[1] == 'shift'):
			SceneHandler.Instance().setIsShiftPressed(True)

		elif (keycode[1] == 'ctrl'):
			SceneHandler.Instance().setIsCtrlPressed(True)

		elif (keycode[1] == 'delete'):
			Scene.Instance().removeObject()

		elif (keycode[1] == 'escape'):
			exit()

		elif (keycode[1] == 'r'):
			Scene.Instance().increaseScale()

		elif (keycode[1] == 't'):
			Scene.Instance().decreaseScale()

		elif (keycode[1] == 'f'):
			Scene.Instance().flipOnX()
		
		elif (keycode[1] == 'g'):
			Scene.Instance().flipOnY()

		elif (keycode[1] == '\''):
			Scene.Instance().toggleGrid()

		elif (keycode[1] == 'z'):
			Scene.Instance().undo()

		elif (keycode[1] == '\\'):
			Scene.Instance().redo()
		
		return True

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
		
		self.filesManager = FilesManager.Instance()
		self.renderGuardian = RenderObjectGuardian.Instance()
		self.sceneAttributes = SceneAttributes.Instance(40, 20, 20)
		self.scene = Scene.Instance()
		self.sceneHandler = SceneHandler.Instance(self.rightScreen)

		self.objectHandler = OptionsMenu.Instance(self.rightScreen)
		self.leftMenuHandler = ObjectsMenu(self.leftMenuBase)
		self.shortcutHandler = KeyboardShortcutHandler()

		Clock.schedule_interval(Scene.Instance().clear, 30)

		return self.root
	
if __name__ == '__main__':
	TileEditor().run()
