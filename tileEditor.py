#!/usr/bin/python
from kivy import require
require('1.7.2')

from kivy.app import App
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

from sys import argv, exit
from ConfigParser import ConfigParser
from os.path import isdir, isfile, join, exists
from os import listdir, getcwd


class ObjectTypes:
	baseObject = 1
	renderedObject = 2

class ConfigurationAccess:
	
	def getConfigValue(self, value):
		global ConfigObject
		return ConfigObject.getValue(value)

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
	
	def __init__(self, scene, sceneHandler, objectDescriptor):
		self.__sceneReference= scene
		self.__sceneHandlerReference = sceneHandler
		self.__objectDescriptorReference =  objectDescriptor
		self.getKeyboardAccess(self.__processKeyDown, self.__processKeyUp)
	
	def __processKeyUp(self, keyboard, keycode):
		#print('The key', keycode, 'have been released.')
		
		if (keycode[1] == 'shift'):
			self.__sceneHandlerReference.setIsShiftPressed(False)

	def __processKeyDown(self, keyboard, keycode, text, modifiers):
		#print('The key', keycode, 'have been pressed')
		#print(' - text is %r' % text)
		#print(' - modifiers are %r' % modifiers)

		if (keycode[1] == 'q'):
			self.__sceneReference.alignToGrid()

		elif (keycode[1] == 'a'):
			self.__sceneReference.alignAndCopyObject("left")

		elif (keycode[1] == 's'):
			self.__sceneReference.alignAndCopyObject("down")
		
		elif (keycode[1] == 'd'):
			self.__sceneReference.alignAndCopyObject("right")
		
		elif (keycode[1] == 'w'):
			self.__sceneReference.alignAndCopyObject("up")

		elif (keycode[1] == 'e'):
			self.__objectDescriptorReference.clearCurrentObject()

		elif (keycode[1] == 'shift'):
			self.__sceneHandlerReference.setIsShiftPressed(True)

		elif (keycode[1] == 'delete'):
			self.__sceneReference.removeObject()

		elif (keycode[1] == 'escape'):
			exit()

		return True


class TileEditorConfig:

	def __init__(self, confFile = 'config.ini'):
		assert (isfile(confFile))
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

	def getType(self):
		return self.__objectType
	

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

	def setMarked(self):
		self.image.color[3] = 0.7

	def unsetMarked(self):
		self.image.color[3] = 1.0

	def alignToGrid(self):
		x, y = self.bbox[0]

		distX = x % self.__tileSize
		if (distX < self.__tileSize/2):
			x -= x % self.__tileSize
		else:
			x += self.__tileSize - (x % self.__tileSize)
		
		distY = y % self.__tileSize
		if (distY < self.__tileSize/2):
			y -= y % self.__tileSize
		else:
			y += self.__tileSize - (y % self.__tileSize)

		self._set_pos((x, y))

	def __handleTouch(self, touch):

		if (self.collide_point(*touch.pos) == True):
			self.__objectDescriptorReference.setObject(self)

		self.__defaultTouchDown(touch)

	def __init__(self, identifier, path, size, pos, tileSize, alignToPixel, maxX, maxY, objectDescriptorRef):
		
		super(RenderedObject, self).__init__(do_rotation = False, do_scale = False, size_hint = (None, None), 
			size = size, auto_bring_to_front = False)
		self.image = Image(source = path, size = size)
		self.add_widget(self.image)

		self.__id = identifier
		self.__objectType = ObjectTypes.renderedObject
		self.__sx = size[0]
		self.__sy = size[1]
		self.__alignToPixel = alignToPixel
		self.__tileSize = tileSize
		self.__maxX = maxX
		self.__maxY = maxY
		self.__path = path
		self._set_pos(pos)

		self.__defaultTouchDown = self.on_touch_down
		self.on_touch_down = self.__handleTouch
		self.__defaultApplyTransform = self.apply_transform
		self.apply_transform = self.__checkAndTransform
		self.__objectDescriptorReference = objectDescriptorRef

	def getIdentifier(self):
		return self.__id

	def getType(self):
		return self.__objectType

	def getPath(self):
		return self.__path

	def getSize(self):
		return (self.__sx, self.__sy)

	def getPos(self):
		return self.bbox[0]


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

	def removeObject(self):
		obj = self.__objectDescriptorReference.getCurrentObject()
		if (obj != None and obj.getType() == ObjectTypes.renderedObject):
			self.__layout.remove_widget(obj)
			identifier = obj.getIdentifier()
			del self.__objectDict[identifier]
			obj = None
			self.__objectDescriptorReference.clearCurrentObject()
		
	def alignToGrid(self):
		obj = self.__objectDescriptorReference.getCurrentObject()
		if (obj != None and obj.getType() == ObjectTypes.renderedObject):
			obj.alignToGrid()

	def alignAndCopyObject(self, direction):
		obj = self.__objectDescriptorReference.getCurrentObject()
		if (obj == None or obj.getType() != ObjectTypes.renderedObject):
			return None
		
		obj.alignToGrid()
		pos = obj.getPos()
		size = obj.getSize()

		if (direction == "left") and (pos[0] >= size[0]):
			newPos = (pos[0] - size[0], pos[1])
			newRenderedObject = self.__createNewObjectAndAddToScene(obj.getPath(), size, newPos)
			self.__objectDescriptorReference.setObject(newRenderedObject)

		elif (direction == "right") and (pos[0] + size[0]*2 <= self.__maxX):
			newPos = (pos[0] + size[0], pos[1])
			newRenderedObject = self.__createNewObjectAndAddToScene(obj.getPath(), size, newPos)
			self.__objectDescriptorReference.setObject(newRenderedObject)

		elif (direction == "up" and pos[1] + size[1] * 2 <= self.__maxY):
			newPos = (pos[0], pos[1] + size[1])
			newRenderedObject = self.__createNewObjectAndAddToScene(obj.getPath(), size, newPos)
			self.__objectDescriptorReference.setObject(newRenderedObject)
		
		elif (direction == "down" and pos[1] >= size[1]):
			newPos = (pos[0], pos[1] - size[1])
			newRenderedObject = self.__createNewObjectAndAddToScene(obj.getPath(), size, newPos)
			self.__objectDescriptorReference.setObject(newRenderedObject)

	def __createNewObjectAndAddToScene(self, path, size, pos):
		renderedObject = RenderedObject(self.__id, path, size, pos, self.__tileSize, self.__alignToPixel, 
			self.__maxX, self.__maxY, self.__objectDescriptorReference)
		
		self.__layout.add_widget(renderedObject)
		self.__objectDict[self.__id] = renderedObject
		self.__id += 1

		return renderedObject


	def getLayout(self):
		return self.__layout

	def addObject(self, path, size, relativeX, relaviveY):
		pos = (int(relativeX * self.__maxX), int(relaviveY * self.__maxY))
		self.__createNewObjectAndAddToScene(path, size, pos)
	
class SceneHandler:

	def setIsShiftPressed(self, value):
		self.__isShiftPressed = value
	
	def __ignoreMoves(self, touch):
		return None

	def __handleScrollAndPassTouchesToChildren(self, touch):

		if (self.scrollView.collide_point(*touch.pos) == False):
			return

		if (touch.is_mouse_scrolling == True):
			if (self.__isShiftPressed == False):
				if (touch.button == "scrollup" and self.scrollView.scroll_y > 0):
					self.scrollView.scroll_y -= 0.05
				elif (touch.button == "scrolldown" and self.scrollView.scroll_y < 1.0):
					self.scrollView.scroll_y += 0.05
			else:
				if (touch.button == "scrollup" and self.scrollView.scroll_x > 0):
					self.scrollView.scroll_x -= 0.05
				elif (touch.button == "scrolldown" and self.scrollView.scroll_x < 1.0):
					self.scrollView.scroll_x += 0.05

			return 

		self.__defaultTouchDown(touch)
		
	
	def __init__(self, rightScreen, scene, maxWidthProportion = 0.75, maxHeightProportion = 0.667):
		

		self.__isShiftPressed = False
		
		self.maxWidthProportion = maxWidthProportion
		self.maxHeightProportion = maxHeightProportion
		
		self.sceneReference = scene
		
		self.scrollView = ScrollView(size_hint=(None, None),  scroll_timeout = 0)
		self.scrollView.on_touch_move = self.__ignoreMoves
		self.__defaultTouchDown = self.scrollView.on_touch_down
		self.scrollView.on_touch_down = self.__handleScrollAndPassTouchesToChildren


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
			self.setObject(obj)

	def __drawObject(self, obj):
		self.sceneHandlerReference.draw(obj.getPath(), obj.getSize())

	def setObject(self, obj):

		if (self.currentObject != None and self.currentObject.getType() == ObjectTypes.renderedObject):
			self.currentObject.unsetMarked()

		path = obj.getPath()
		size = obj.getSize()
		cwd = getcwd() + '/'
		if (cwd == path[:len(cwd)]):
			path = path[len(cwd):]
		self.pathLabel.text = 'Path: ' + str(path)
		self.sizeLabel.text = 'Size: ' + str(size)
		self.currentObject = obj

		if (self.currentObject.getType() == ObjectTypes.renderedObject):
			obj.setMarked()

	def getCurrentObject(self):
		return self.currentObject

	def clearCurrentObject(self):
		if (self.currentObject != None and self.currentObject.getType() == ObjectTypes.renderedObject):
			self.currentObject.unsetMarked()
		
		self.pathLabel.text = 'Path: '
		self.sizeLabel.text = 'Size: '
		self.currentObject = None

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
		Config.set('input', 'mouse', 'mouse,disable_multitouch')
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
		self.shortcutHandler = KeyboardShortcutHandler(self.scene, self.sceneHandler, self.objectHandler)

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
	if (len(argv) >= 2):
		ConfigObject = TileEditorConfig(argv[1])
		
	else:
		ConfigObject = TileEditorConfig()
	
	TileEditor().run()
