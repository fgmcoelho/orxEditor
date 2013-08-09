#!/usr/bin/python
from kivy import require
require('1.7.2')

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter
from kivy.config import Config
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.core.window import Window

from ConfigParser import ConfigParser

from os.path import isdir, isfile, join, exists
from os import listdir, walk, stat, chown, getcwd

class ObjectTypes:
	baseObject = 1
	renderedObject = 2

class ConfigurationAccess:
	
	def getConfigValue(self, value):
		global ConfigObject
		return ConfigObject.getValue(value)

class KeyboardShortcutHandler:
	
	def __init__(self, scene):
		self.__scene = scene

class TileEditorConfig:

	def __init__(self, confFile = 'config.ini'):
		self.__configParser = ConfigParser()
		self.__configParser.read(confFile)
		self.__valuesDict = { 
			'TilesMaxX'  : int(self.__configParser.get('TileEditor', 'maxX')),
			'TilesMaxY'  : int(self.__configParser.get('TileEditor', 'maxY')),
			'TilesSize'  : int(self.__configParser.get('TileEditor', 'size')),
			'TilesAlignToPixel' : bool(self.__configParser.get('TileEditor', 'alignToPixel')),
			'AssetsPath' : str(self.__configParser.get('Assets', 'path')),
		}

	def getValue(self, value):
		if (value in self.__valuesDict):
			return self.__valuesDict[value]
		else:
			return None

class BaseObject:

	def __init__(self, baseImage, identifier):
		self.__identifier = identifier
		self.__baseImage = baseImage
		self.__fullPath = baseImage.source
		self.__size = baseImage.texture.size
		self.__objectType = ObjectTypes.baseObject

	def getIdentifier(self):
		return self.__identifier

	def getSize(self):
		return self.__size
	
	def getPath(self):
		return self.__fullPath

	def getBaseImage(self):
		return self.__baseImage
	

class RenderedObject (Scatter):

	def __checkAndTransform(self, trans, post_multiply=False, anchor=(0, 0)):
		self.__defaultApplyTransform(trans, post_multiply, anchor)
		x, y = self.bbox[0]

		if (x < 0):
			x = 0
		elif (x + self.__sx > self.__maxX):
			x = self.__maxX - self.__sx

		if (y < 0):
			y = 0
		elif (y + self.__sy > self.__maxY):
			y = self.__maxY - self.__sy

		if (self.__alignToPixel == True):
			self._set_pos((int(x), int(y)))

	def alignToGrid(self):
		x, y = self.bbox[0]
		distX = x % self.__tileSize
		if (distX < __tileSize/2):
			x -= x % self.__tileSize
		else:
			x += self.__tileSize - (x % self.__tileSize)
		
		distY = y % self.__tileSize
		if (distY < __tileSize/2):
			y -= y % self.__tileSize
		else:
			y += self.__tileSize - (y % self.__tileSize)

	def __init__(self, identifier, path, size, pos, tileSize, alignToPixel, maxX, maxY):
		
		super(RenderedObject, self).__init__(do_rotation = False, do_scale = False)
		image = Image(source = path, size = size)
		self.add_widget(image)

		self.__id = identifier
		self.__objectType = ObjectTypes.renderedObject
		self.__sx = size[0]
		self.__sy = size[1]
		self.__alignToPixel = alignToPixel
		self.__tileSize = tileSize
		self.__maxX = maxX
		self.__maxY = maxY
		self._set_pos(pos)

		self.__defaultApplyTransform = self.apply_transform
		self.apply_transform = self.__checkAndTransform

class Scene (ConfigurationAccess):
	
	def __init__(self):
		
		self.__tileSize = self.getConfigValue('TilesSize')
		sx = self.getConfigValue('TilesMaxX') * self.__tileSize
		sy = self.getConfigValue('TilesMaxY') * self.__tileSize

		self.__alignToPixel = self.getConfigValue('TilesAlignToPixel')
		self.__layout = RelativeLayout(size=(sx, sy), size_hint = (None, None))
		
		self.__id = 0
		self.__objectDict = {}
		self.__maxX = sx
		self.__minX = 0.0
		self.__maxY = sy
		self.__minY = 0.0
		self.__objectDescriptorReference = None

	def setObjectDescriptorReference(self, value):
		self.__objectDescriptorReference = value

	def alignToGrid(self):
		pass

	def getLayout(self):
		return self.__layout

	def addObject(self, path, size, relativeX, relaviveY):
		pos = (int(relativeX * self.__maxX), int(relaviveY * self.__maxY))
		renderedObject = RenderedObject(self.__id, path, size, pos, self.__tileSize, self.__alignToPixel, self.__maxX, self.__maxY)
		self.__layout.add_widget(renderedObject)

		self.__objectDict[self.__id] = renderedObject
		self.__id += 1
		

class SceneHandler :
	def __init__(self, rightScreen, scene, maxWidthProportion = 0.75, maxHeightProportion = 0.667):
		
		self.maxWidthProportion = maxWidthProportion
		self.maxHeightProportion = maxHeightProportion
		
		self.sceneReference = scene
		
		self.scrollView = ScrollView(size_hint=(None, None),  scroll_timeout = 100)
		self.scrollView.add_widget(self.sceneReference.getLayout())
		rightScreen.add_widget(self.scrollView)
		
		self.updateLayoutSizes()

	def updateLayoutSizes(self):
		
		wx, wy = Window.size
		
		xSize = wx * self.maxWidthProportion
		ySize = wy * self.maxHeightProportion
		
		self.scrollView.size = (xSize, ySize)

	def draw(self, path, size):
		relativeX = self.scrollView.hbar[0]
		relaviveY = self.scrollView.vbar[0]
		self.sceneReference.addObject(path, size, relativeX, relaviveY)

	def getLayout(self):
		return self.scrollView
	
	def handleTouch(self, touch):
		pass

class ObjectDescriptor:
	def __init__(self, rightScreen, sceneHandler, maxWidthProportion = 0.75, maxHeightProportion = 0.333):
		
		self.sceneHandlerReference = sceneHandler
		self.currentObject = None
		self.maxWidthProportion = maxWidthProportion
		self.maxHeightProportion = maxHeightProportion

		self.layout = BoxLayout(orientation = 'vertical', size_hint = (None, None))
		self.pathLabel = Label(text = 'Path: ')
		self.sizeLabel = Label(text = 'Size: ')
		self.collisionLabel = Label(text = 'Collision: ')
		
		self.layout.add_widget(self.pathLabel)
		self.layout.add_widget(self.sizeLabel)
		self.layout.add_widget(self.collisionLabel)

		rightScreen.add_widget(self.layout)

		self.updateLayoutSizes()

	def setOrDrawObject(self, obj):
		if (self.currentObject == obj):
			self.__drawObject(obj)
		else:
			self.__setObject(obj)

	def __drawObject(self, obj):
		self.sceneHandlerReference.draw(obj.getPath(), obj.getSize())

	def __setObject(self, obj):

		path = obj.getPath()
		size = obj.getSize()
		cwd = getcwd() + '/'
		if (cwd == path[:len(cwd)]):
			path = path[len(cwd):]
		self.pathLabel.text = 'Path: ' + str(path)
		self.sizeLabel.text = 'Size: ' + str(size)
		self.currentObject = obj

	def updateLayoutSizes(self):
		
		wx, wy = Window.size
		
		xSize = wx * self.maxWidthProportion
		ySize = wy * self.maxHeightProportion
		
		self.layout.size = (xSize, ySize)


class LeftMenuHandler (ConfigurationAccess):
	
	def __init__(self, leftMenu, objectHandler, maxWidthProportion = 0.25, maxHeightProportion = 1.0):
		self.menuObjectsList = []
		self.objectHandlerReference = objectHandler
		self.maxWidthProportion = maxWidthProportion
		self.maxHeightProportion = maxHeightProportion

		l = listdir(join(getcwd(), self.getConfigValue('AssetsPath')))
		self.numberOfItems = 0
		for item in l:
			if (item[-4:] == '.png'):
				img = Image(source = join(getcwd(), self.getConfigValue('AssetsPath'),item))
				obj = BaseObject(img, self.numberOfItems)
				self.menuObjectsList.append(obj)
				self.numberOfItems += 1
		

		self.layout = GridLayout(cols=1, rows = self.numberOfItems, size_hint = (None, None))
		for menuObject in self.menuObjectsList:
			self.layout.add_widget(menuObject.getBaseImage())

		self.scrollView = ScrollView(size_hint = (None, None) )
		self.scrollView.add_widget(self.layout)
		self.scrollView.do_scroll_x = False

		leftMenu.add_widget(self.scrollView)

		self.updateLayoutSizes()

	def updateLayoutSizes(self):
		wx, wy = Window.size
		
		xSize = wx * self.maxWidthProportion
		ySize = wy * self.maxHeightProportion

		scrollViewWidth = 0
		if (self.numberOfItems * xSize < ySize):
			scrollViewWidth = ySize
		else:
			scrollViewWidth = xSize * self.numberOfItems

		self.layout.size = (xSize, scrollViewWidth)
		self.scrollView.size = (xSize, ySize)


	def handleTouch(self, touch):
		for menuObject in self.menuObjectsList:
			if (touch.is_mouse_scrolling == False and menuObject.getBaseImage().collide_point(*touch.pos) == True and 
					touch.is_double_tap == True):
				self.objectHandlerReference.setOrDrawObject(menuObject)
				return True

		return False
				
class TileEditor(App):
	
	resizeList = []

	def dispatchTouch(self, touch):
		res = False
		if (self.leftMenuBase.collide_point(*touch.pos) == True):
			res = self.leftMenuHandler.handleTouch(touch)

		#if (self.sceneHandler.getLayout().collide_point(*touch.pos) == True):
		#	self.sceneHandler.handleTouch(touch)

		if (res == False):
			self.__defaultTouchUp(touch)

	def build_config(self, c):
		Config.set('graphics', 'width', 800)
		Config.set('graphics', 'height', 600)
		Config.set('graphics', 'fullscreen', 0)
		Config.write()

	@staticmethod
	def resizeTest(x, y):
		for widget in TileEditor.resizeList:
			widget.updateLayoutSizes()
	
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
		
		self.scene = Scene()
		self.sceneHandler = SceneHandler(self.rightScreen, self.scene)
		self.objectHandler = ObjectDescriptor(self.rightScreen, self.sceneHandler)
		self.leftMenuHandler = LeftMenuHandler(self.leftMenuBase, self.objectHandler)
		self.scene.setObjectDescriptorReference(self.objectHandler) # unfortunate reference here

		TileEditor.resizeList.append(self.sceneHandler)
		TileEditor.resizeList.append(self.objectHandler)
		TileEditor.resizeList.append(self.leftMenuHandler)

		#self.root.on_touch_down = self.dispatchTouch
		#self.root.on_touch_move = self.dispatchTouch
		self.__defaultTouchUp = self.root.on_touch_up 
		self.root.on_touch_up = self.dispatchTouch
		
		Window.on_resize = self.resizeTest

		return self.root

global ConfigObject
if __name__ == '__main__':
	ConfigObject = TileEditorConfig()
	TileEditor().run()
