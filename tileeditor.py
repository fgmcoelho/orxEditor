#!/usr/bin/python
from kivy import require
require('1.7.2')

from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
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

from editorutils import Dialog, AlertPopUp, strToDoubleFloatTuple
from editorobjects import BaseObject, RenderedObject, ObjectTypes
from splittedimagemap import SplittedImageMap

class CollisionTypes:
	box = 1
	sphere = 2

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

		elif (keycode[1] == 'f'):
			self.__sceneReference.flipOnX()
		
		elif (keycode[1] == 'g'):
			self.__sceneReference.flipOnY()

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
			'TilesAlignToGrid' : bool(self.__configParser.get('TileEditor', 'alignToGrid')),
			'AssetsPath' : str(self.__configParser.get('Assets', 'path')),
		}

	def getValue(self, value):
		if (value in self.__valuesDict):
			return self.__valuesDict[value]
		else:
			return None


class Scene (ConfigurationAccess):
	
	def __init__(self):
		
		self.__tileSize = self.getConfigValue('TilesSize')
		sx = self.getConfigValue('TilesMaxX') * self.__tileSize
		sy = self.getConfigValue('TilesMaxY') * self.__tileSize

		self.__alignToGrid = self.getConfigValue('TilesAlignToGrid')
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
		
		if (self.__alignToGrid == True):
			obj.alignToGrid()
		pos = obj.getPos()
		size = obj.getSize()
		scale = obj.getScale()
		layer = obj.getLayer()
		flipX = obj.getFlipX()
		flipY = obj.getFlipY()
		baseSize = obj.getBaseSize()
		collisionInfo = obj.getCollisionInfo()
		if (collisionInfo != None):
			collisionInfo = collisionInfo.copy()

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
			newRenderedObject = self.__createNewObjectAndAddToScene(obj, newPos)
			self.__objectDescriptorReference.setObject(newRenderedObject)
	
	def resetAllWidgets(self):
		for objectId in self.__objectDict.keys():
			self.__objectDict[objectId].resetAllWidgets()
			self.__objectDict[objectId] = None
			del self.__objectDict[objectId] 

		self.__objectDict = {}
		self.__id = 0
	
	def __createNewObjectAndAddToScene(self, obj, pos):
		renderedObject = RenderedObject(self.__id, obj, pos, self.__tileSize, self.__alignToGrid, 
			self.__maxX, self.__maxY, self.__objectDescriptorReference)
		
		self.__layout.add_widget(renderedObject)
		self.__objectDict[self.__id] = renderedObject
		self.__id += 1

		return renderedObject

	def getLayout(self):
		return self.__layout

	# TODO: UPDATE HERE
	# THE WHOLE SAVE/LOAD MODULE MUST BE REWRITTEN...
	def addObjectFullInfo(self, obj, pos):
		self.__createNewObjectAndAddToScene(obj, pos)

	def addObject(self, obj, relativeX, relaviveY):
		pos = (int(relativeX * self.__maxX), int(relaviveY * self.__maxY))
		newRenderedObject = self.__createNewObjectAndAddToScene(obj, pos)
		self.__objectDescriptorReference.setObject(newRenderedObject)

	def getObjectsDict(self):
		return self.__objectDict
	
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
				if (touch.button == "scrolldown" and self.__scrollView.scroll_x > 0):
					self.__scrollView.scroll_x -= 0.05
				elif (touch.button == "scrollup" and self.__scrollView.scroll_x < 1.0):
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

	def draw(self, obj):
		relativeX = self.__scrollView.hbar[0]
		relaviveY = self.__scrollView.vbar[0]
		self.__sceneReference.addObject(obj, relativeX, relaviveY)

	def getLayout(self):
		return self.__scrollView

class CollisionFlag:
	def __init__(self, name, hexValue):
		self.__name = name
		self.__hexValue = hexValue

	def getName(self):
		return self.__name

	def getHexValue(self):
		return self.__hexValue

	def collides(self, other):
		return self.__hexValue | other

class CollisionInformation:

	def __init__(self, selfFlag, checkMask, isSolid, isDynamic, allowSleep, collisionType):
		self.__selfFlag = selfFlag
		self.__checkMask = checkMask
		self.__isSolid = isSolid
		self.__isDynamic = isDynamic
		self.__allowSleep = allowSleep
		self.__collisionType = collisionType

	def getSelfFlag(self):
		return self.__selfFlag

	def getCheckMask(self):
		return self.__checkMask

	def getIsSolid(self):
		return self.__isSolid

	def getIsDynamic(self):
		return self.__isDynamic

	def getAllowSleep(self):
		return self.__allowSleep

	def getCollisionType(self):
		return self.__collisionType
	
	def setSelfFlag(self, value):
		self.__selfFlag = value

	def setCheckMask(self, value):
		self.__checkMask = value

	def setIsSolid(self, value):
		self.__isSolid = value

	def setIsDynamic(self, value):
		self.__isDynamic = value

	def setAllowSleep(self, value):
		self.__allowSleep = value

	def setCollisionType(self, value):
		self.__collisionType = value

	def copy(self):
		return CollisionInformation(self.getSelfFlag(), self.getCheckMask(), self.getIsSolid(), self.getIsDynamic(),
			self.getAllowSleep(), self.getCollisionType())

	def isEquals(self, other):
		return (self.getSelfFlag() == other.getSelfFlag() & 
			self.getCheckMask() == other.getCheckMask() &
			self.getIsSolid() == other.getIsSolid() &
			self.getIsDynamic() == other.getIsDynamic() &
			self.getAllowSleep() == other.getAllowSleep() &
			self.getCollisionType() == other.getCollisionType())



class CollisionInformationPopup:

	@staticmethod
	def validateMask(inputReference):
		value = inputReference.text
		valid = True
		
		if (value == ''):
			valid = False

		else:
			value = value.strip()
			base = 10
			if (value[0:2] == '0x' or value[0:2] == '0X'):
				base = 16
			
			elif (value[0:2] == '0b' or value[0:2] == '0B'):
				base = 2

			elif (value[0] == '0'):
				base = 8

			try:
				x = int (value, base)
				valid = True
				if (x < 0 or x > 0xFFFF):
					valid = False
			except:
				valid = False

		if (valid == False):
			inputReference.background_color = [1, 0, 0, 1]
		else:
			inputReference.background_color = [1, 1, 1, 1]

	def __setDefaultValues(self):
		self.__selfFlagInput.text = '0xFFFF'
		self.__checkMaskInput.text = '0xFFFF'
		self.__solidSwitch.active = False
		self.__dynamicSwitch.active = False
		self.__allowSleepSwitch.active = False
		self.__typeBoxSelect.active = True
		self.__typeSphereSelect.active = False

	def __setObjectValues(self, obj):
		self.__selfFlagInput.text = obj.getSelfFlag()
		self.__checkMaskInput.text = obj.getCheckMask()
		self.__solidSwitch.active = obj.getIsSolid()
		self.__dynamicSwitch.active = obj.getIsDynamic()
		self.__allowSleepSwitch.active = obj.getAllowSleep()
		if (obj.getCollisionType() == CollisionTypes.box):
			self.__typeBoxSelect.active = True
			self.__typeSphereSelect.active = False
		else:
			self.__typeBoxSelect.active = False
			self.__typeSphereSelect.active = True

	def __reloadValues(self):
		if (self.__editingObject == None):
			self.__setDefaultValues()

		else:
			collisionInfo = self.__editingObject.getCollisionInfo()
			if (collisionInfo == None):
				self.__setDefaultValues()
			else:
				self.__setObjectValues(collisionInfo)

	def __init__(self):
		self.__collisionPopUp = Popup (title = 'Collision configs', auto_dismiss = False)
		self.__collisionGrid = GridLayout(cols = 2, rows = 7, size_hint = (1.0, 1.0))
		
		self.__collisionGrid.add_widget(Label(text = 'SelfFlag:'))
		self.__selfFlagInput = TextInput(text='0xFFFF', multiline = False)
		self.__selfFlagInput.bind(on_text_validate=CollisionInformationPopup.validateMask)
		self.__collisionGrid.add_widget(self.__selfFlagInput)

		self.__collisionGrid.add_widget(Label(text = 'Check Mask:'))
		self.__checkMaskInput = TextInput(text='0xFFFF', multiline = False, on_text_validate=CollisionInformationPopup.validateMask)
		self.__collisionGrid.add_widget(self.__checkMaskInput)
		
		self.__collisionGrid.add_widget(Label(text = 'Solid?'))
		self.__solidSwitch = Switch(active = False)
		self.__collisionGrid.add_widget(self.__solidSwitch)

		self.__collisionGrid.add_widget(Label(text = 'Dynamic?'))
		self.__dynamicSwitch = Switch(active = False)
		self.__collisionGrid.add_widget(self.__dynamicSwitch)

		self.__collisionGrid.add_widget(Label(text = 'Allow sleep?'))
		self.__allowSleepSwitch = Switch(active = False)
		self.__collisionGrid.add_widget(self.__allowSleepSwitch)
		
		self.__collisionGrid.add_widget(Label(text = 'Type:'))
		self.__typesGrid = GridLayout (cols = 2, rows = 2)
		self.__typeBoxSelect = CheckBox(active = True, group = 'collision_type')
		self.__typesGrid.add_widget(self.__typeBoxSelect)
		self.__typesGrid.add_widget(Label(text = 'Box'))
		self.__typeSphereSelect = CheckBox(active = False, group = 'collision_type')
		self.__typesGrid.add_widget(self.__typeSphereSelect)
		self.__typesGrid.add_widget(Label(text = 'Sphere'))
		self.__collisionGrid.add_widget(self.__typesGrid)

		self.__okButton = Button(text = 'Done')
		self.__okButton.bind(on_release=self.__createOrEditCollisionInfo)
		self.__cancelButton = Button (text = 'Cancel')
		self.__cancelButton.bind(on_release=self.__collisionPopUp.dismiss)
		self.__collisionGrid.add_widget(self.__okButton)
		self.__collisionGrid.add_widget(self.__cancelButton)
		
		self.__collisionPopUp.content = self.__collisionGrid
		self.__editingObject = None
	
	
		self.__errorPopUp = AlertPopUp('Error', 'No Object selected!\nYou need to select one object from the scene', 'Ok')
		self.__postCreateOrEditMethod = None
		
	def __createOrEditCollisionInfo(self, useless):
		if (self.__editingObject != None):
			if (self.__selfFlagInput.background_color==[1, 0, 0, 1] or self.__checkMaskInput.background_color==[1, 0, 0, 1]):
				self.__errorPopUp.setText('Invalid flag input.')
				self.__errorPopUp.open()
				return
			
			if (self.__typeBoxSelect.active == True):
				collisionType = CollisionTypes.box
			else:
				collisionType = CollisionTypes.sphere

			if (self.__editingObject.getCollisionInfo() == None):

				newCollisionInfo = CollisionInformation(
					self.__selfFlagInput.text, 
					self.__checkMaskInput.text, 
					self.__solidSwitch.active, 
					self.__dynamicSwitch.active, 
					self.__allowSleepSwitch.active, 
					collisionType
				)
				self.__editingObject.setCollisionInfo(newCollisionInfo)
			
			else:
				collisionObject = self.__editingObject.getCollisionInfo()
				collisionObject.setSelfFlag(self.__selfFlagInput.text)
				collisionObject.setCheckMask(self.__checkMaskInput.text)
				collisionObject.setIsSolid(self.__solidSwitch.active)
				collisionObject.setIsDynamic(self.__dynamicSwitch.active)
				collisionObject.setAllowSleep(self.__allowSleepSwitch.active)
				collisionObject.setCollisionType(collisionType)

		self.__editingObject = None
		self.getPopUp().dismiss()

		if (self.__postCreateOrEditMethod != None):
			self.__postCreateOrEditMethod()
				
	def setPostCreateOrEditMethod(self, value):
		self.__postCreateOrEditMethod = value

	def getPopUp(self):
		return self.__collisionPopUp

	def showPopUp(self, obj):
		
		if (obj == None or (obj != None and obj.getType() != ObjectTypes.renderedObject)):
			self.__errorPopUp.setText('No Object selected!\nYou need to select one object from the scene')
			self.__errorPopUp.open()
		
		else:
			self.__editingObject = obj
			self.__reloadValues()
			self.__collisionPopUp.open()
			
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

	def setValues(self, path = '', size=''):
		self.__pathLabel.text = 'Path: ' + str(path)
		self.__sizeLabel.text = 'Size: ' + str(size)
		self.setActive()

class RenderedObjectDescriptor:
	def __init__(self, accordionItem, popUpMethod):
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__pathLabel = Label(text = 'Path: ', size_hint = (1.0, 0.2))

		self.__nameLabel = Label(text = 'Name: ', size_hint = (1.0, 0.2))

		self.__flipBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__flipxLabel = Label(text = 'Flipped on X: ', size_hint = (0.5, 1.0))
		self.__flipyLabel = Label(text = 'Flipped on Y: ', size_hint = (0.5, 1.0))
		self.__flipBox.add_widget(self.__flipxLabel)
		self.__flipBox.add_widget(self.__flipyLabel)

		self.__sizeScaleLayerBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__sizeLabel = Label(text = 'Size: ', size_hint = (0.333, 1.0))
		self.__scaleLabel = Label(text = 'Scale: ', size_hint = (0.333, 1.0))
		self.__layerLabel = Label(text = 'Layer: ', size_hint = (0.3334, 1.0))
		
		self.__sizeScaleLayerBox.add_widget(self.__sizeLabel)
		self.__sizeScaleLayerBox.add_widget(self.__scaleLabel)
		self.__sizeScaleLayerBox.add_widget(self.__layerLabel)

		self.__collisionBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__collisionInfoLabel = Label(text = 'Has collision info: ')
		self.__collisionHandler = Button(text = 'Edit Collision', size_hint = (0.3, 1.0))
		self.__collisionHandler.bind(on_release=popUpMethod)
		
		self.__collisionBox.add_widget(self.__collisionInfoLabel)
		self.__collisionBox.add_widget(self.__collisionHandler)

		self.__layout.add_widget(self.__pathLabel)
		self.__layout.add_widget(self.__nameLabel)
		self.__layout.add_widget(self.__flipBox)
		self.__layout.add_widget(self.__sizeScaleLayerBox)
		self.__layout.add_widget(self.__collisionBox)

		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)
	
	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False

	def setValues(self, path = '', size = '', scale = '', layer = '', name = '', flipX = '', flipY = '', collisionInfo = None):
		self.__setValues(path, size, scale, layer, name, flipX, flipY, collisionInfo)
		self.setActive()

	def setValueNoActive(self, path = '', size = '', scale = '', layer = '', name = '', flipX = '', flipY = '', 
			collisionInfo = None):
		self.__setValues(path, size, scale, layer, name, flipX, flipY, collisionInfo)

	def __setValues(self, path, size, scale, layer, name, flipX, flipY, collisionInfo):
		self.__pathLabel.text = 'Path: ' + str(path)
		self.__sizeLabel.text = 'Size: ' + str(size)
		self.__scaleLabel.text = 'Scale: ' + str(scale)
		self.__layerLabel.text = 'Layer: ' + str(layer)
		self.__nameLabel.text = 'Name: ' + str(name)
		self.__flipxLabel.text = 'Flipped on X: ' + str(flipX)
		self.__flipyLabel.text = 'Flipped on Y: ' + str(flipY)
		if (collisionInfo == None):
			self.__collisionInfoLabel.text = 'Has collision info: None'
		else:
			self.__collisionInfoLabel.text = 'Has collision info: Available'
		

class OptionsMenu:
	
	def __newSceneFinish(self, notUsed = None):
		self.__newSceneMethodReference(notUsed)
		self.__newSceneDialog.dismiss()

	def __newScene(self, notUsed = None):
		self.__newSceneDialog.open()

	def __saveSceneFinish(self, notUsed = None):
		self.__saveSceneMethodReference(join(self.__fileChooser.path, self.__fileChooserInput.text))
		self.__fileChooserPopUp.dismiss()
		self.__saveSceneDialog.dismiss()
		self.__lastPath = self.__fileChooser.path

	def __validateSelectedOsf(self, entry, notUsed = None):
		if (isfile(entry[0]) == True):
			sepIndex = entry[0].rfind(pathSeparator)
			if (sepIndex != -1):
				self.__fileChooserInput.text = entry[0][sepIndex+1:]
			else:
				self.__fileChooserInput.text = entry[0]
		else:
			self.__errorPopUp.setText('Invalid file selected.')
			self.__errorPopUp.open()

	def __validateAndContinueToSave(self, notUsed = None):
		if (self.__fileChooserInput.text == ''):
			self.__errorPopUp.setText('No file selected.')
			self.__errorPopUp.open()
			return

		if (isfile(join(self.__fileChooser.path, self.__fileChooserInput.text)) == True):
			self.__saveSceneDialog.open()
		else:
			self.__saveSceneFinish()

	def __saveScene(self, notUsed = None):
		self.__fileChooser.path = self.__lastPath
		self.__fileChooser.filters = ['*.osf']
		self.__fileChooser.on_submit = self.__validateSelectedOsf
		self.__fileChooserOkButton.on_release = self.__validateAndContinueToSave
		self.__fileChooserPopUp.open()

	def __loadSceneFinish(self, notUsed = None):
		self.__loadSceneMethodReference(join(self.__fileChooser.path, self.__fileChooserInput.text))
		self.__fileChooserPopUp.dismiss()
		self.__lastPath = self.__fileChooser.path

	def __validateAndContinueToLoad(self, notUsed = None):
		if (self.__fileChooserInput.text == ''):
			self.__errorPopUp.setText('No file selected.')
			self.__errorPopUp.open()
			return

		if (isfile(join(self.__fileChooser.path, self.__fileChooserInput.text)) == True):
			self.__loadSceneFinish()
		else:
			self.__errorPopUp.setText("Selected file doesn't exist.")
			self.__errorPopUp.open()

	def __loadScene(self, notUsed = None):
		self.__fileChooser.path = self.__lastPath
		self.__fileChooser.filters = ['*.osf']
		self.__fileChooser.on_submit = self.__validateSelectedOsf
		self.__fileChooserOkButton.on_release = self.__validateAndContinueToLoad
		self.__fileChooserPopUp.open()

	def __startBasicButtonsLayout(self):
		self.__layout = GridLayout(rows = 4, cols = 1, size_hint = (1.0, 1.0))
		self.__newButton = Button(text = 'New Scene', size_hint = (1.0, 0.25), on_release = self.__newScene)
		self.__loadButton = Button(text = 'Load Scene', size_hint = (1.0, 0.25), on_release = self.__loadScene)
		self.__saveButton = Button(text = 'Save Scene', size_hint = (1.0, 0.25), on_release = self.__saveScene)
		self.__exportButton = Button(text = 'Export Scene', size_hint = (1.0, 0.25))
		
		self.__layout.add_widget(self.__newButton)
		self.__layout.add_widget(self.__loadButton)
		self.__layout.add_widget(self.__saveButton)
		self.__layout.add_widget(self.__exportButton)

	def __startConfirmationPopUp(self):
		self.__newSceneDialog = Dialog(
			self.__newSceneFinish, 'Confirmation', 
			'Starting a new scene will remove all the\nnon saved changes.\nAre you sure?', 'Ok', 'Cancel'
		)
		self.__saveSceneDialog = Dialog(
			self.__saveSceneFinish, 'Confirmation',
			'This will override the selected file.\nContinue?', 'Ok', 'Cancel'
		)

	def __startFileChooser(self):
		
		self.__fileChooserLayout = BoxLayout(orientation = 'vertical')
		self.__fileChooserPopUp = Popup(auto_dismiss = False, title = 'Select the file:')
		self.__fileChooserInputLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		filenameLabel = Label(text = 'File:', size_hint = (0.3, 1.0))
		self.__fileChooserInput = TextInput(multiline = False, size_hint = (0.7, 1.0))
		self.__fileChooserInputLayout.add_widget(filenameLabel)
		self.__fileChooserInputLayout.add_widget(self.__fileChooserInput)
		self.__fileChooser = FileChooserIconView(size_hint = (1.0, 0.9))

		self.__fileChooserYesNoLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		self.__fileChooserOkButton = Button(text = 'Ok')
		self.__fileChooserCancelButton = Button(text = 'Cancel', on_release = self.__fileChooserPopUp.dismiss)
		self.__fileChooserYesNoLayout.add_widget(self.__fileChooserOkButton)
		self.__fileChooserYesNoLayout.add_widget(self.__fileChooserCancelButton)

		self.__fileChooserLayout.add_widget(self.__fileChooserInputLayout)
		self.__fileChooserLayout.add_widget(self.__fileChooser)
		self.__fileChooserLayout.add_widget(self.__fileChooserYesNoLayout)
		self.__fileChooserPopUp.content = self.__fileChooserLayout
		self.__lastPath = getcwd()


	def __init__(self, accordionItem, newSceneMethod, saveSceneMethod, loadSceneMethod):

		self.__newSceneMethodReference = newSceneMethod
		self.__saveSceneMethodReference = saveSceneMethod
		self.__loadSceneMethodReference = loadSceneMethod

		self.__startBasicButtonsLayout()	
		self.__startConfirmationPopUp()	
		self.__startFileChooser()
		self.__errorPopUp = AlertPopUp('Error', '', 'Ok')

		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)

	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False

class ObjectDescriptor:
	
	def updateObjectDescriptors(self):
		self.setObject(self.__currentObject)

	def openCollisionPopUp(self, ignore):
		
		self.__collisionPopUpReference.showPopUp(self.__currentObject)
		
		if (self.__currentObject != None):
			self.setObject(self.__currentObject)

	def __init__(self, rightScreen, sceneHandler, collisionPopUp, newSceneMethod, saveSceneMethod, loadSceneMethod,
			maxWidthProportion = 0.75, maxHeightProportion = 0.333):
		
		self.__collisionPopUpReference = collisionPopUp
		self.__collisionPopUpReference.setPostCreateOrEditMethod(self.updateObjectDescriptors)
		self.__sceneHandlerReference = sceneHandler
		self.__currentObject = None
		self.__maxWidthProportion = maxWidthProportion
		self.__maxHeightProportion = maxHeightProportion

		self.__layout = Accordion(orientation = 'horizontal')
		self.updateLayoutSizes()

		self.__accordionItems = {
			'BaseObject' : AccordionItem(title = 'Base Objects', size_hint = (None, None)),
			'RenderedObject' : AccordionItem (title = 'Rendered Object', size_hint = (None, None)),
			'Options' : AccordionItem(title = 'Options', size_hint = (None, None)),
		}

		self.__baseObjectDescriptor = BaseObjectDescriptor(self.__accordionItems['BaseObject'])
		self.__renderedObjectDescriptor = RenderedObjectDescriptor(self.__accordionItems['RenderedObject'], self.openCollisionPopUp)
		self.__optionsMenu = OptionsMenu(self.__accordionItems['Options'], newSceneMethod, saveSceneMethod, loadSceneMethod)

		self.__layout.add_widget(self.__accordionItems['BaseObject'])
		self.__layout.add_widget(self.__accordionItems['RenderedObject'])
		self.__layout.add_widget(self.__accordionItems['Options'])

		self.__baseObjectDescriptor.setActive()

		rightScreen.add_widget(self.__layout)

	def resetAllWidgets(self):
		self.__baseObjectDescriptor.setValues()
		self.__renderedObjectDescriptor.setValueNoActive()
			
	def setOrDrawObject(self, obj):
		if (self.__currentObject == obj):
			self.__drawObject(obj)
		else:
			self.setObject(obj)

	def __drawObject(self, obj):
		self.__sceneHandlerReference.draw(obj)

	def setObject(self, obj):

		if (self.__currentObject != None and self.__currentObject.getType() == ObjectTypes.renderedObject):
			self.__currentObject.unsetMarked()

		path = obj.getPath()
		size = obj.getSize()
		cwd = getcwd() + '/'
		if (cwd == path[:len(cwd)]):
			path = path[len(cwd):]

		if (obj.getType() == ObjectTypes.renderedObject):
			self.__renderedObjectDescriptor.setValues(path, size, obj.getScale(), obj.getLayer(), obj.getName(), obj.getFlipX(),
				obj.getFlipY(), obj.getCollisionInfo())
			obj.setMarked()
		
		else:
			self.__baseObjectDescriptor.setValues(path, size)

		self.__currentObject = obj

	def getCurrentObject(self):
		return self.__currentObject

	def clearCurrentObject(self):
		if (self.__currentObject == None):
			return
		
		if (self.__currentObject.getType() == ObjectTypes.renderedObject):
			self.__currentObject.unsetMarked()
			self.__renderedObjectDescriptor.setValues()
			self.__baseObjectDescriptor.setValues()
		else:
			self.__baseObjectDescriptor.setValues()
			self.__renderedObjectDescriptor.setValues()
		
		self.__currentObject = None

	def updateLayoutSizes(self):
		
		wx, wy = Window.size
		
		xSize = wx * self.__maxWidthProportion
		ySize = wy * self.__maxHeightProportion
		
		self.__layout.size = (xSize, ySize)

class MenuObject:

	def __handle(self, image, touch):
		if (touch.is_mouse_scrolling == False and self.getDisplayImage().collide_point(*touch.pos) == True and 
				touch.is_double_tap == True):
			self.__objectHandlerReference.setOrDrawObject(self.getBaseObject())


	def __init__(self, baseObject, size, objectHandler):
		self.__baseObject = baseObject
		self.__objectHandlerReference = objectHandler
		self.__displayImage = Image(texture = baseObject.getBaseImage().texture, size = size, size_hint = (None, None),
			on_touch_down = self.__handle)

	def getBaseObject(self):
		return self.__baseObject
	
	def getDisplayImage(self):
		return self.__displayImage

class LeftMenuHandler (ConfigurationAccess):
	
	def __loadPng(self, item, pngsToIgnoreList):
		fullPath = join(getcwd(), self.getConfigValue('AssetsPath'), item)
		if (fullPath in pngsToIgnoreList):
			return

		img = Image(source = fullPath)
		obj = BaseObject(img, self.__numberOfItems)
		self.__menuObjectsList.append(MenuObject(obj, (64, 64), self.__objectHandlerReference))
		self.__numberOfItems += 1

	def __loadOpf(self, item, pngsToIgnoreList):
		opfLoader = SplittedImageMap()
		opfLoader.importFromOpf(join(getcwd(), self.getConfigValue('AssetsPath'),item))
		imagesList = opfLoader.getImagesList()
		for img in imagesList:
			obj = BaseObject(img, self.__numberOfItems, opfLoader.getBaseImagePath())
			self.__menuObjectsList.append(MenuObject(obj, (64, 64), self.__objectHandlerReference))
			self.__numberOfItems += 1

		print ("Adding %s to the ignore list!" % (obj.getPath(), ))
		pngsToIgnoreList.append(obj.getPath())

	def __loadItems(self):
		l = listdir(join(getcwd(), self.getConfigValue('AssetsPath')))
		self.__menuObjectsList = []
		self.__numberOfItems = 0
		pngsToIgnoreList = []
		for item in l:
			if (item[-4:] == '.opf'):
				self.__loadOpf(item, pngsToIgnoreList)

		for item in l:
			if (item[-4:] == '.png' and item not in pngsToIgnoreList):
				self.__loadPng(item, pngsToIgnoreList)
		
		if (self.__layout == None):
			self.__layout = GridLayout(cols=1, rows = self.__numberOfItems, size_hint = (None, None), spacing = (0, 3))
		else:
			self.__layout.rows = self.__numberOfItems 

		for menuObject in self.__menuObjectsList:
			img = menuObject.getDisplayImage()
			self.__layout.add_widget(img)
		
	def __init__(self, leftMenu, objectHandler, maxWidthProportion = 0.25, maxHeightProportion = 1.0):
		self.__objectHandlerReference = objectHandler
		self.__maxWidthProportion = maxWidthProportion
		self.__maxHeightProportion = maxHeightProportion
		self.__layout = None

		self.__loadItems()

		self.__scrollView = ScrollView(size_hint = (None, None) )
		self.__scrollView.add_widget(self.__layout)
		self.__scrollView.do_scroll_x = False


		leftMenu.add_widget(self.__scrollView)

		self.updateLayoutSizes()

	def resetAllWidgets(self):
		for menuObject in self.__menuObjectsList:
			self.__layout.remove_widget(menuObject.getDisplayImage())
			menuObject = None

		self.__loadItems()
		

	def updateLayoutSizes(self):
		wx, wy = Window.size
		
		xSize = wx * self.__maxWidthProportion
		ySize = wy * self.__maxHeightProportion

		scrollViewWidth = 0
		if (self.__numberOfItems * xSize < ySize):
			scrollViewWidth = ySize
		else:
			scrollViewWidth = 68 * self.__numberOfItems

		self.__layout.size = (xSize, scrollViewWidth)
		self.__scrollView.size = (xSize, ySize)

class TileEditor(App, ConfigurationAccess):
	
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
	
	def saveScene(self, filename):

		parser = ConfigParser()
		tileEditorSectionName = 'TileEditor'
		assetsSectionName = 'Assets'
		objectListName = 'ObjectList'
		
		parser.add_section(tileEditorSectionName)
		parser.set(tileEditorSectionName, 'maxX', self.getConfigValue('TilesMaxX'))
		parser.set(tileEditorSectionName, 'maxY', self.getConfigValue('TilesMaxY'))
		parser.set(tileEditorSectionName, 'size', self.getConfigValue('TilesSize'))
		parser.set(tileEditorSectionName, 'alignToGrid', self.getConfigValue('TilesAlignToGrid'))

		parser.add_section(assetsSectionName)
		parser.set(assetsSectionName, 'path', self.getConfigValue('AssetsPath'))

		renderedObjectsDict = self.scene.getObjectsDict()
		objectsInScene = ''
		for inSceneId in renderedObjectsDict.keys():
			objectsInScene += renderedObjectsDict[inSceneId].getName() + ' # '

		parser.add_section(objectListName)
		parser.set(objectListName, 'ObjectNames', objectsInScene)

		for inSceneId in renderedObjectsDict.keys():
			newSectionName = renderedObjectsDict[inSceneId].getName() 
			parser.add_section(newSectionName)
			parser.set(newSectionName, 'path', str(renderedObjectsDict[inSceneId].getPath()))
			parser.set(newSectionName, 'pos', str(renderedObjectsDict[inSceneId].getPos()))
			parser.set(newSectionName, 'flipX', str(int(renderedObjectsDict[inSceneId].getFlipX())))
			parser.set(newSectionName, 'flipY', str(int(renderedObjectsDict[inSceneId].getFlipY())))
			parser.set(newSectionName, 'scale', str(renderedObjectsDict[inSceneId].getScale()))
			parser.set(newSectionName, 'layer', str(renderedObjectsDict[inSceneId].getLayer()))
			parser.set(newSectionName, 'size', str(renderedObjectsDict[inSceneId].getBaseSize()))
			
			collisionObject = renderedObjectsDict[inSceneId].getCollisionInfo()
			if (collisionObject == None):
				parser.set(newSectionName, 'hascollisioninfo', 0)
			else:
				parser.set(newSectionName, 'hascollisioninfo', 1)
				collisionInfoSectionName = newSectionName + '_collision_info'
				parser.add_section(collisionInfoSectionName)
				parser.set(collisionInfoSectionName, 'selfFlag', str(collisionObject.getSelfFlag()))
				parser.set(collisionInfoSectionName, 'checkMask', str(collisionObject.getCheckMask()))
				parser.set(collisionInfoSectionName, 'Solid', str(int(collisionObject.getIsSolid())))
				parser.set(collisionInfoSectionName, 'dynamic', str(int(collisionObject.getIsDynamic())))
				parser.set(collisionInfoSectionName, 'allowSleep', str(int(collisionObject.getAllowSleep())))
				parser.set(collisionInfoSectionName, 'type', str(collisionObject.getCollisionType()))

		f = open(filename, 'w')
		parser.write(f)


	def loadScene(self, filename):
		global ConfigObject 
		ConfigObject = TileEditorConfig(filename)
		self.resetAllWidgets()
		
		parser = ConfigParser()
		parser.read(filename)
		objectList = parser.get('ObjectList', 'objectnames').split('#')
		for name in objectList:
			name = name.strip()
			if (name == ''):
				continue
			path = str(parser.get(name, 'path'))
			pos = strToDoubleFloatTuple(parser.get(name, 'pos'))
			flipX = bool(int(parser.get(name, 'flipX')))
			flipY = bool(int(parser.get(name, 'flipY')))
			scale = float(parser.get(name, 'scale'))
			layer = float(parser.get(name, 'layer'))
			size = strToDoubleFloatTuple(parser.get(name, 'size'))
			hasCollisionInfo = bool(int(parser.get(name, 'hascollisioninfo')))
			newCollisionInfo = None
			if (hasCollisionInfo == True):
				collisionInfoSectionName = name + '_collision_info'
				selfFlag = parser.get(collisionInfoSectionName, 'selfFlag')
				checkMask = parser.get(collisionInfoSectionName, 'checkMask')
				solid = bool(int(parser.get(collisionInfoSectionName, 'Solid')))
				dynamic = bool(int(parser.get(collisionInfoSectionName, 'dynamic')))
				allowSleep = bool(int(parser.get(collisionInfoSectionName, 'allowSleep')))
				collisionType = parser.get(collisionInfoSectionName, 'type')
				newCollisionInfo = CollisionInformation(selfFlag, checkMask, solid, dynamic, allowSleep, collisionType)
			
			self.scene.addObjectFullInfo(path, size, pos, scale, layer, flipX, flipY, newCollisionInfo)

				
	def newScene(self, filename):
		self.resetAllWidgets()

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
		
		self.scene = Scene()
		self.collisionPopUp = CollisionInformationPopup()

		self.sceneHandler = SceneHandler(self.rightScreen, self.scene)
		self.objectHandler = ObjectDescriptor(
			self.rightScreen, self.sceneHandler, self.collisionPopUp, self.newScene, self.saveScene,
			self.loadScene
		)
		self.leftMenuHandler = LeftMenuHandler(self.leftMenuBase, self.objectHandler)
		self.scene.setObjectDescriptorReference(self.objectHandler) # unfortunate cross reference here
		self.shortcutHandler = KeyboardShortcutHandler(self.scene, self.sceneHandler, self.objectHandler)

		TileEditor.resizeList.append(self.sceneHandler)
		TileEditor.resizeList.append(self.objectHandler)
		TileEditor.resizeList.append(self.leftMenuHandler)

		Window.on_resize = self.resizeTest

		return self.root
	
global ConfigObject
if __name__ == '__main__':
	if (len(argv) >= 2):
		ConfigObject = TileEditorConfig(argv[1])
		
	else:
		ConfigObject = TileEditorConfig()
	
	TileEditor().run()
