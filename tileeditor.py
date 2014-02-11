#!/usr/bin/python
from kivy import require
require('1.7.2')

from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.config import Config
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.uix.switch import Switch
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.core.window import Window
from kivy.graphics.texture import Texture

from sys import argv, exit
from ConfigParser import ConfigParser
from os.path import isdir, isfile, join, exists
from os import listdir, getcwd, sep as pathSeparator

from optionsmenu import ObjectDescriptor
from scene import Scene, SceneHandler,SceneAttributes
from collision import CollisionInformationPopup
from objectsmenu import ObjectsMenu

from editorutils import Dialog, AlertPopUp, strToDoubleFloatTuple
from editorobjects import BaseObject, RenderedObject, ObjectTypes

class CollisionTypes:
	box = 1
	sphere = 2

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
		#print('The key', keycode, 'have been released.')
		
		if (keycode[1] == 'shift'):
			SceneHandler.Instance().setIsShiftPressed(False)

	def __processKeyDown(self, keyboard, keycode, text, modifiers):
		#print('The key', keycode, 'have been pressed')
		#print(' - text is %r' % text)
		#print(' - modifiers are %r' % modifiers)

		if (keycode[1] == 'q'):
			Scene.Instance().alignToGrid()

		elif (keycode[1] == 'a'):
			Scene.Instance().alignAndCopyObject("left")

		elif (keycode[1] == 's'):
			Scene.Instance().alignAndCopyObject("down")
		
		elif (keycode[1] == 'd'):
			Scene.Instance().alignAndCopyObject("right")
		
		elif (keycode[1] == 'w'):
			Scene.Instance().alignAndCopyObject("up")

		elif (keycode[1] == 'e'):
			SceneHandler.Instance().clearCurrentObject()

		elif (keycode[1] == 'shift'):
			SceneHandler.Instance().setIsShiftPressed(True)

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

		return True

class TileEditor(App):
	
	resizeList = []

	def build_config(self, c):
		
		Config.set('graphics', 'width', 800)
		Config.set('graphics', 'height', 600)
		Config.set('graphics', 'fullscreen', 0)
		Config.set('input', 'mouse', 'mouse,disable_multitouch')
		Config.write()

	@staticmethod
	def resizeTest(x, y):
		for widget in TileEditor.resizeList:
			widget.updateLayoutSizes()
	

	def resetAllWidgets(self, useless = None):
		self.objectHandler.resetAllWidgets()
		self.leftMenuHandler.resetAllWidgets()
		self.scene.resetAllWidgets()

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
		
		self.sceneAttributes = SceneAttributes.Instance(64, 20, 20)
		self.scene = Scene.Instance()
		self.sceneHandler = SceneHandler.Instance(self.rightScreen)
		self.collisionPopUp = CollisionInformationPopup()

		self.objectHandler = ObjectDescriptor.Instance(self.rightScreen, self.collisionPopUp)
		self.leftMenuHandler = ObjectsMenu(self.leftMenuBase)
		self.shortcutHandler = KeyboardShortcutHandler()

		Window.on_resize = self.resizeTest

		return self.root
	
if __name__ == '__main__':
	TileEditor().run()
