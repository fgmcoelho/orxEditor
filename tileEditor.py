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
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.core.window import Window
from kivy.graphics.texture import Texture

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

		elif (keycode[1] == 'r'):
			self.__sceneReference.increaseScale()

		elif (keycode[1] == 't'):
			self.__sceneReference.decreaseScale()

		#elif (keycode[1] == 'f'):
		#	self.__sceneReference.flipOnX()
		
		#elif (keycode[1] == 'g'):
		#	self.__sceneReference.flipOnY()

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

	def increaseScale(self):
		self.setScale (self.__scale + 0.25, True)

	
	def decreaseScale(self):
		self.setScale (self.__scale - 0.25, True)

	def setScale(self, newScale, preservePos = False):
		if (preservePos == True):
			oldPos = self.bbox[0]
		
		self.__scale = newScale
		self.scale = self.__scale
		self.__sx, self.__sy = self.bbox[1]

		if (preservePos == True):
			print self.bbox
			self._set_pos(oldPos)


	def __flipVertical(self):

		print self.bbox
		self.remove_widget(self.image)
		newTexture = self.image.texture
		newTexture.flip_vertical()
		self.image = None
		self.image = Image(texture = newTexture, size_hint = (None, None))
		self.add_widget(self.image)
		print self.bbox

	def flipOnX(self):
		self.__flipX = not self.__flipX
	
		self.__flipVertical()
		self.rotation = (self.rotation + 180) % 360

	def flipOnY(self):
		self.__flipY = not self.__flipY
		self.__flipVertical()

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

	def __handleTouchDown(self, touch):

		if (self.collide_point(*touch.pos) == True):
			self.__objectDescriptorReference.setObject(self)

		self.__defaultTouchDown(touch)

	def __handleTouchUp(self, touch):
		
		#if (self.collide_point(*touch.pos) == True):
		#	self.alignToGrid()

		self.__defaultTouchUp(touch)

	def __init__(self, identifier, path, baseSize, pos, tileSize, alignToPixel, maxX, maxY, 
		objectDescriptorRef, scale = 1.0, layer = 1, flipX = False, flipY = False):
		
		self.__baseSize = baseSize
		size  = (self.__baseSize[0] * scale, self.__baseSize[1] * scale)
		
		super(RenderedObject, self).__init__(do_rotation = False, do_scale = False, size_hint = (None, None), 
			size = self.__baseSize, auto_bring_to_front = False)
		self.image = Image(source = path, size = self.__baseSize)
		
		self.add_widget(self.image)
		self.__lastTransform = None
		self.__id = identifier
		self.__objectType = ObjectTypes.renderedObject
		self.__sx = size[0]
		self.__sy = size[1]
		self.__alignToPixel = alignToPixel
		self.__tileSize = tileSize
		self.__maxX = maxX
		self.__maxY = maxY
		self.__path = path
		self.__scale = scale
		self.__layer = layer
		self.__flipX = flipX
		self.__flipY = flipY
		self._set_pos(pos)

		self.__defaultTouchDown = self.on_touch_down
		self.on_touch_down = self.__handleTouchDown
		self.__defaultTouchUp = self.on_touch_up
		self.on_touch_up = self.__handleTouchUp
		self.__defaultApplyTransform = self.apply_transform
		self.apply_transform = self.__checkAndTransform
		self.__objectDescriptorReference = objectDescriptorRef

		self.setScale(self.__scale, True)

	def getIdentifier(self):
		return self.__id

	def getType(self):
		return self.__objectType

	def getPath(self):
		return self.__path

	def getSize(self):
		return (self.__sx, self.__sy)

	def getBaseSize(self):
		return self.__baseSize

	def getPos(self):
		return self.bbox[0]

	def getScale(self):
		return self.__scale

	def getLayer(self):
		return self.__layer

	def getFlipX(self):
		return self.__flipX

	def getFlipY(self):
		return self.__flipY


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

	def increaseScale(self):
		obj = self.__objectDescriptorReference.getCurrentObject()
		if (obj != None and obj.getType() == ObjectTypes.renderedObject):
			obj.increaseScale()
			self.__objectDescriptorReference.setObject(obj)
	
	def decreaseScale(self):
		obj = self.__objectDescriptorReference.getCurrentObject()
		if (obj != None and obj.getType() == ObjectTypes.renderedObject):
			obj.decreaseScale()
			self.__objectDescriptorReference.setObject(obj)

	def flipOnX(self):
		obj = self.__objectDescriptorReference.getCurrentObject()
		if (obj != None and obj.getType() == ObjectTypes.renderedObject):
			obj.flipOnX()
			self.__objectDescriptorReference.setObject(obj)
		
	def flipOnY(self):
		obj = self.__objectDescriptorReference.getCurrentObject()
		if (obj != None and obj.getType() == ObjectTypes.renderedObject):
			obj.flipOnY()
			self.__objectDescriptorReference.setObject(obj)


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
		
		#obj.alignToGrid()
		pos = obj.getPos()
		size = obj.getSize()
		scale = obj.getScale()
		layer = obj.getLayer()
		flipX = obj.getFlipX()
		flipY = obj.getFlipY()
		baseSize = obj.getBaseSize()


		newPos = None
		if (direction == "left") and (pos[0] >= size[0]):
			newPos = (pos[0] - size[0], pos[1])

		elif (direction == "right") and (pos[0] + size[0]*2 <= self.__maxX):
			newPos = (pos[0] + size[0], pos[1])

		elif (direction == "up" and pos[1] + size[1] * 2 <= self.__maxY):
			newPos = (pos[0], pos[1] + size[1])
		
		elif (direction == "down" and pos[1] >= size[1]):
			newPos = (pos[0], pos[1] - size[1])
	
		if (newPos != None):
			newRenderedObject = self.__createNewObjectAndAddToScene(obj.getPath(), baseSize, newPos, scale, layer, flipX, flipY)
			self.__objectDescriptorReference.setObject(newRenderedObject)

	
	def __createNewObjectAndAddToScene(self, path, size, pos, scale = 1.0, layer = 1, flipX = False, flipY = False):
		renderedObject = RenderedObject(self.__id, path, size, pos, self.__tileSize, self.__alignToPixel, 
			self.__maxX, self.__maxY, self.__objectDescriptorReference, scale, layer, flipX, flipY)
		
		self.__layout.add_widget(renderedObject)
		self.__objectDict[self.__id] = renderedObject
		self.__id += 1

		return renderedObject


	def getLayout(self):
		return self.__layout

	def addObject(self, path, size, relativeX, relaviveY):
		pos = (int(relativeX * self.__maxX), int(relaviveY * self.__maxY))
		newRenderedObject = self.__createNewObjectAndAddToScene(path, size, pos)
		self.__objectDescriptorReference.setObject(newRenderedObject)
	
class SceneHandler:

	def setIsShiftPressed(self, value):
		self.__isShiftPressed = value
	
	def __ignoreMoves(self, touch):
		return None

	def __handleScrollAndPassTouchesToChildren(self, touch):

		if (self.__scrollView.collide_point(*touch.pos) == False):
			return

		if (touch.is_mouse_scrolling == True):
			if (self.__isShiftPressed == False):
				if (touch.button == "scrollup" and self.__scrollView.scroll_y > 0):
					self.__scrollView.scroll_y -= 0.05
				elif (touch.button == "scrolldown" and self.__scrollView.scroll_y < 1.0):
					self.__scrollView.scroll_y += 0.05
			else:
				if (touch.button == "scrollup" and self.__scrollView.scroll_x > 0):
					self.__scrollView.scroll_x -= 0.05
				elif (touch.button == "scrolldown" and self.__scrollView.scroll_x < 1.0):
					self.__scrollView.scroll_x += 0.05

			return 

		self.__defaultTouchDown(touch)
		
	
	def __init__(self, rightScreen, scene, maxWidthProportion = 0.75, maxHeightProportion = 0.667):
		

		self.__isShiftPressed = False
		
		self.__maxWidthProportion = maxWidthProportion
		self.__maxHeightProportion = maxHeightProportion
		
		self.__sceneReference = scene
		
		self.__scrollView = ScrollView(size_hint=(None, None),  scroll_timeout = 0)
		self.__scrollView.on_touch_move = self.__ignoreMoves
		self.__defaultTouchDown = self.__scrollView.on_touch_down
		self.__scrollView.on_touch_down = self.__handleScrollAndPassTouchesToChildren


		self.__scrollView.add_widget(self.__sceneReference.getLayout())
		rightScreen.add_widget(self.__scrollView)
		
		self.updateLayoutSizes()

	def updateLayoutSizes(self):
		
		wx, wy = Window.size
		
		xSize = wx * self.__maxWidthProportion
		ySize = wy * self.__maxHeightProportion
		
		self.__scrollView.size = (xSize, ySize)

	def draw(self, path, size):
		relativeX = self.__scrollView.hbar[0]
		relaviveY = self.__scrollView.vbar[0]
		self.__sceneReference.addObject(path, size, relativeX, relaviveY)

	def getLayout(self):
		return self.__scrollView

class CollisionInformationPopup:

	def __init__(self):
		pass

class BaseObjectDescriptor:
	
	def __init__(self, accordionItem):
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__pathLabel = Label(text = 'Path: ', size_hint = (1.0, 0.5))
		self.__sizeLabel = Label(text = 'Size: ', size_hint = (1.0, 0.5))
		self.__layout.add_widget(self.__pathLabel)
		self.__layout.add_widget(self.__sizeLabel)
		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)

	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False

	def setValues(self, path, size):
		self.__pathLabel.text = 'Path: ' + str(path)
		self.__sizeLabel.text = 'Size: ' + str(size)
		self.setActive()

class RenderedObjectDescriptor:
	def __init__(self, accordionItem):
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__pathLabel = Label(text = 'Path: ', size_hint = (1.0, 0.333))
		
		self.__sizeScaleLayerBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.333))
		self.__sizeLabel = Label(text = 'Size: ', size_hint = (0.333, 1.0))
		self.__scaleLabel = Label(text = 'Scale: ', size_hint = (0.333, 1.0))
		self.__layerLabel = Label(text = 'Layer: ', size_hint = (0.3334, 1.0))
		
		self.__sizeScaleLayerBox.add_widget(self.__sizeLabel)
		self.__sizeScaleLayerBox.add_widget(self.__scaleLabel)
		self.__sizeScaleLayerBox.add_widget(self.__layerLabel)

		self.__collisionBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.334))
		self.__collisionLabelsBox = BoxLayout (orientation = 'vertical', size_hint = (0.7, 1.0))
		self.__collisionSelfLabel = Label(text = 'Collision SelfFlags: 0x0000')
		self.__collisionCheckLabel = Label(text = 'Collision CheckFlags: 0x0000')
		self.__collisionHandler = Button(text = 'Edit Collision', size_hint = (0.3, 1.0))
		
		self.__collisionLabelsBox.add_widget(self.__collisionSelfLabel)
		self.__collisionLabelsBox.add_widget(self.__collisionCheckLabel)
		
		self.__collisionBox.add_widget(self.__collisionLabelsBox)
		self.__collisionBox.add_widget(self.__collisionHandler)

		self.__layout.add_widget(self.__pathLabel)
		self.__layout.add_widget(self.__sizeScaleLayerBox)
		self.__layout.add_widget(self.__collisionBox)
		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)
	
	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False

	def setValues(self, path, size, scale, layer):
		self.__pathLabel.text = 'Path: ' + str(path)
		self.__sizeLabel.text = 'Size: ' + str(size)
		self.__scaleLabel.text = 'Scale: ' + str(scale)
		self.__layerLabel.text = 'Layer: ' + str(layer)
		self.setActive()

class OptionsMenu:
	def __init__(self, accordionItem):
		self.__layout = GridLayout(rows = 4, cols = 1, size_hint = (1.0, 1.0))
		self.__newButton = Button(text = 'New Scene', size_hint = (1.0, 0.25))
		self.__loadButton = Button(text = 'Load Scene', size_hint = (1.0, 0.25))
		self.__saveButton = Button(text = 'Save Scene', size_hint = (1.0, 0.25))
		self.__exportButton = Button(text = 'Export Scene', size_hint = (1.0, 0.25))
		
		self.__layout.add_widget(self.__newButton)
		self.__layout.add_widget(self.__loadButton)
		self.__layout.add_widget(self.__saveButton)
		self.__layout.add_widget(self.__exportButton)

		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)

	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False

class ObjectDescriptor:
	def __init__(self, rightScreen, sceneHandler, maxWidthProportion = 0.75, maxHeightProportion = 0.333):
		
		self.sceneHandlerReference = sceneHandler
		self.currentObject = None
		self.maxWidthProportion = maxWidthProportion
		self.maxHeightProportion = maxHeightProportion

		self.__layout = Accordion(orientation = 'horizontal')
		self.updateLayoutSizes()

		self.__accordionItems = {
			'BaseObject' : AccordionItem(title = 'Base Objects', size_hint = (None, None)),
			'RenderedObject' : AccordionItem (title = 'Rendered Object', size_hint = (None, None)),
			'Options' : AccordionItem(title = 'Options', size_hint = (None, None)),
		}

		self.__baseObjectDescriptor = BaseObjectDescriptor(self.__accordionItems['BaseObject'])
		self.__renderedObjectDescriptor = RenderedObjectDescriptor(self.__accordionItems['RenderedObject'])
		self.__optionsMenu = OptionsMenu(self.__accordionItems['Options'])

		self.__layout.add_widget(self.__accordionItems['BaseObject'])
		self.__layout.add_widget(self.__accordionItems['RenderedObject'])
		self.__layout.add_widget(self.__accordionItems['Options'])

		self.__baseObjectDescriptor.setActive()

		rightScreen.add_widget(self.__layout)

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

		if (obj.getType() == ObjectTypes.renderedObject):
			self.__renderedObjectDescriptor.setValues(path, size, obj.getScale(), obj.getLayer())
			obj.setMarked()
		
		else:
			self.__baseObjectDescriptor.setValues(path, size)

		self.currentObject = obj

	def getCurrentObject(self):
		return self.currentObject

	def clearCurrentObject(self):
		if (self.currentObject != None and self.currentObject.getType() == ObjectTypes.renderedObject):
			self.currentObject.unsetMarked()
		
		self.__baseObjectDescriptor.setValues('', '')
		self.currentObject = None

	def updateLayoutSizes(self):
		
		wx, wy = Window.size
		
		xSize = wx * self.maxWidthProportion
		ySize = wy * self.maxHeightProportion
		
		self.__layout.size = (xSize, ySize)


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
