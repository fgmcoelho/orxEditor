from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics.vertex_instructions import Line
from kivy.graphics.fbo import Fbo
from kivy.graphics import Color, Rectangle, ClearColor, ClearBuffers, InstructionGroup
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

from operator import itemgetter
from time import time

from editorheritage import LayoutGetter, KeyboardModifiers, MouseModifiers
from editorobjects import RenderObjectGuardian
from editorutils import Alert, EmptyScrollEffect
from modulesaccess import ModulesAccess
from uisizes import sceneMiniMapSize
from math import ceil

class SceneMiniMap(LayoutGetter):
	def _scrollCoords(self, pos, rectangleSize, mapSize):
		if (pos <= rectangleSize/2.0):
			return 0.0
		elif (pos >= (mapSize - (rectangleSize/2.0))):
			return 1.0
		else:
			return (pos - rectangleSize/2.0)/(mapSize - rectangleSize)

	def _scrollByTouch(self, touch):
		x, y = self._image.to_local(touch.pos[0], touch.pos[1], True)
		xToScroll = self._scrollCoords(x, self._rectangleSx, self._size[0])
		yToScroll = self._scrollCoords(y, self._rectangleSy, self._size[1])
		ModulesAccess.get('SceneHandler').scrollFromMiniMap(xToScroll, yToScroll)
		self.updateQuad()

	def _processTouchUp(self, touch):
		if (self._moving == True):
			self._moving = False

	def _processTouchDown(self, touch):
		if (self._image.collide_point(*touch.pos) == True):
			self._moving = True
			self._scrollByTouch(touch)

	def _processTouchMove(self, touch):
		if (self._image.collide_point(*touch.pos) == True and self._moving == True):
			self._scrollByTouch(touch)

	def __init__(self):
		super(SceneMiniMap, self).__init__()

		self._size = sceneMiniMapSize['size']
		self._layout = RelativeLayout(size = self._size, size_hint = (None, None))
		self._image = Image(size = self._size)
		self._layout.add_widget(self._image)
		self._rectangle = None
		self._representedId = None
		self._representedSize = None
		self._moving = True
		ModulesAccess.add('MiniMap', self)
		self._image.on_touch_move = self._processTouchMove
		self._image.on_touch_down = self._processTouchDown
		self._image.on_touch_up = self._processTouchUp

	def updateQuad(self, *args):
		if (self._representedSize is not None):
			if (self._rectangle is not None):
				self._layout.canvas.remove(self._rectangle)

			hbar = ModulesAccess.get('SceneHandler').getLayout().hbar
			vbar = ModulesAccess.get('SceneHandler').getLayout().vbar
			self._rectangleSx = ceil(self._size[0] * hbar[1])
			self._rectangleSy = ceil(self._size[1] * vbar[1])
			self._rectanglePx = ceil(self._size[0] * hbar[0])
			self._rectanglePy = ceil(self._size[1] * vbar[0])
			with self._layout.canvas:
				Color(1., 0., 0., 0.3)
				self._rectangle = Rectangle(
					size = (self._rectangleSx, self._rectangleSy),
					pos = (self._rectanglePx, self._rectanglePy)
				)

	def updateMinimap(self, newTexture):
		self._image.texture = newTexture
		if (self._representedId != newTexture.id):
			self._representedId = newTexture.id
			self._representedSize = tuple(newTexture.size)
			self.updateQuad()

class OrderSceneObjects(object):
	def _order_objects(self, objectDict):
		objectsList = []
		nameToPriorityDict = ModulesAccess.get('LayerGuardian').getNameToPriorityDict()
		for key in objectDict.keys():
			objectsList.append(
				(
					objectDict[key],
					nameToPriorityDict[objectDict[key].getLayer()],
					objectDict[key].getIdentifier()
				)
			)

		objectsOrderedList = sorted(objectsList, key=itemgetter(1, 2))
		return objectsOrderedList

	def __init__(self):
		super(OrderSceneObjects, self).__init__()

class SceneAttributes:
	def __init__(self, tileSize, numberOfTilesX, numberOfTilesY):
		self.__valuesDict = {
			'TilesMaxX'  : numberOfTilesX,
			'TilesMaxY'  : numberOfTilesY,
			'TilesSize'  : tileSize,
		}

	def getValue(self, name):
		if (name in self.__valuesDict):
			return self.__valuesDict[name]
		else:
			return None

	def setValues(self, name, value):
		self.__valuesDict[name] = value

class Scene(OrderSceneObjects, LayoutGetter):
	def __init__(self, attributes = None):
		self._alignToGrid = False
		self._objectDict = {}
		self._layout = RelativeLayout(size_hint = (None, None), on_resize = self.redraw)
		self._renderGuardian = RenderObjectGuardian()
		self.loadValues(attributes)
		self._fbo = Fbo(size=self._layout.size, with_stencilbuffer=True)

	def _startGridInstuctions(self):
		self._gridGroup = InstructionGroup()
		self._gridGroup.add(Color(0x7b/float(0xFF), 0x61/float(0xFF), 0x3E/float(0xFF)))
		i = 0
		while i < self._maxX:
			self._gridGroup.add(Line(points = [
				i, 0,
				i, self._maxY], width = 1,
				dash_offset = 4, dash_length = 1,
			))
			i += self._tileSize
		i = 0
		while i < self._maxY:
			self._gridGroup.add(Line(points = [
				0, i,
				self._maxX, i], width = 1,
				dash_offset = 4, dash_length = 1,
			))
			i += self._tileSize

	def getMiniMapTexture(self):
		selectedObjects = self._renderGuardian.getSelection()
		for obj in selectedObjects:
			obj.unsetMarked()

		parent = self._layout.parent
		parent.remove_widget(self._layout)

		if (self._showGrid == True):
			self.hideGrid()

		with self._fbo:
			ClearColor(0, 0, 0, 1)
			ClearBuffers()

		self._fbo.add(self._layout.canvas)
		self._fbo.draw()
		texture = self._fbo.texture
		self._fbo.remove(self._layout.canvas)

		if (self._showGrid == True):
			self.showGrid()
			self.redraw()

		parent.add_widget(self._layout)

		for obj in selectedObjects:
			obj.setMarked()

		return texture

	def showGrid(self):
		self._layout.canvas.add(self._gridGroup)

	def hideGrid(self):
		self._layout.canvas.remove(self._gridGroup)

	def toggleGrid(self):
		if (self._showGrid == True):
			self.hideGrid()
		else:
			self.showGrid()

		self._showGrid = not self._showGrid
		self.redraw()

	def loadValues(self, attributes = None):
		self._layout.canvas.clear()
		if (attributes is None):
			self._sceneAttr = SceneAttributes(32, 50, 50)
		else:
			self._sceneAttr = attributes

		self._tileSize = self._sceneAttr.getValue('TilesSize')
		sx = self._sceneAttr.getValue('TilesMaxX') * self._tileSize
		sy = self._sceneAttr.getValue('TilesMaxY') * self._tileSize
		self._layout.size= (sx, sy)
		self._id = 0
		self._maxX = sx
		self._minX = 0.0
		self._maxY = sy
		self._minY = 0.0
		self._startGridInstuctions()
		self._showGrid = True
		if self._objectDict != {}:
			for key in self._objectDict:
				self._objectDict[key].resetAllWidgets()
			self._objectDict = {}

		self.showGrid()

	def redraw(self):
		objectsOrderedList = self._order_objects(self._objectDict)
		self._layout.clear_widgets()
		for obj in objectsOrderedList:
			if (obj[0].getMerged() == False):
				self._layout.add_widget(obj[0])
			if (self._alignToGrid == True):
				obj[0].alignToGrid()

	def _updateDesctriptorBySelection(self):
		newObjects = self._renderGuardian.getSelection()
		ModulesAccess.get('ObjectDescriptor').set(newObjects)

	def undo(self):
		self._renderGuardian.undo()
		self._updateDesctriptorBySelection()

	def redo(self):
		self._renderGuardian.redo()
		self._updateDesctriptorBySelection()

	def clear(self, unusedDt = None):
		for key in self._objectDict.keys():
			if (self._objectDict[key].getFinished() == True):
				self._layout.remove_widget(self._objectDict[key])
				self._objectDict[key] = None
				del self._objectDict[key]

	def __changeLayerByAdjust(self, adj):
		selectedObjects = self._renderGuardian.getSelection()
		if (selectedObjects != []):
			layerNameToPriority = ModulesAccess.get('LayerGuardian').getNameToPriorityDict()
			layerPriorityToName = dict(zip(layerNameToPriority.values(), layerNameToPriority.keys()))
			for obj in selectedObjects:
				layer = obj.getLayer()
				priority = layerNameToPriority[layer] + adj
				if (priority in layerPriorityToName):
					obj.setLayer(layerPriorityToName[priority])
			self.redraw()
			ModulesAccess.get('ObjectDescriptor').set(selectedObjects)

	def increaseLayer(self):
		self.__changeLayerByAdjust(1)

	def decreaseLayer(self):
		self.__changeLayerByAdjust(-1)

	def increaseScale(self):
		obj = self._renderGuardian.increaseScale()
		if (obj is not None):
			ModulesAccess.get('ObjectDescriptor').set(obj)

	def decreaseScale(self):
		obj = self._renderGuardian.decreaseScale()
		if (obj is not None):
			ModulesAccess.get('ObjectDescriptor').set(obj)

	def flipOnX(self):
		flippedObjects = self._renderGuardian.flipSelectionOnX()
		ModulesAccess.get('ObjectDescriptor').set(flippedObjects)

	def flipOnY(self):
		flippedObjects = self._renderGuardian.flipSelectionOnY()
		ModulesAccess.get('ObjectDescriptor').set(flippedObjects)

	def removeObject(self):
		self._renderGuardian.deleteSelection()
		ModulesAccess.get('BaseObjectDisplay').setDisplay(None)

	def alignToGrid(self):
		self._renderGuardian.alignSelectionToGrid()

	def copyObject(self, direction):
		newObjects = self._renderGuardian.copySelection(direction, self._id, self._tileSize, self._maxX, self._maxY)
		for renderedObject in newObjects:
			self._layout.add_widget(renderedObject)
			self._objectDict[self._id] = renderedObject
			self._id += 1

		if (newObjects != []):
			ModulesAccess.get('ObjectDescriptor').set(newObjects)

	def unselectAll(self):
		self._renderGuardian.unsetSelection()
		ModulesAccess.get('BaseObjectDisplay').setDisplay(None)

	def selectAll(self):
		self._renderGuardian.unsetSelection()
		selection = []
		for obj in self._objectDict.values():
			if (obj.getHidden() == False and obj.getFinished() == False):
				selection = self._renderGuardian.addObjectToSelection(obj)
		ModulesAccess.get('ObjectDescriptor').set(selection)

	def mergeObjects(self):
		self._renderGuardian.mergeObjects()

	def resetAllWidgets(self):
		for objectId in self._objectDict.keys():
			self._objectDict[objectId].resetAllWidgets()
			self._objectDict[objectId] = None
			del self._objectDict[objectId]

		self._objectDict = {}
		self._id = 0

	def addObject(self, obj, relativeX = None, relativeY = None, exactlyX = None, exactlyY = None):
		assert (relativeX is not None and relativeY is not None) or (exactlyX is not None and \
			exactlyY is not None), "Invalid argument received."
		sx, sy = obj.getSize()
		if (sx > self._maxX or sy > self._maxY):
			errorAlert = Alert(
				'Error',
				'Object could not be rendered because\nit is bigger than the scene space.',
				'Ok'
			)
			errorAlert.open()
			return

		if (relativeX is not None and relativeY is not None):
			pos = (int(relativeX * self._maxX), int(relativeY * self._maxY))
		else:
			pos = (exactlyX, exactlyY)
		if (pos[0] + sx > self._maxX):
			finalX = self._maxX - sx
		else:
			finalX = pos[0]
		if (pos[1] + sy > self._maxY):
			finalY = self._maxY - sy
		else:
			finalY = pos[1]

		newRenderedObject = self._renderGuardian.createNewObject(self._id, obj, (finalX, finalY),
			self._tileSize, self._maxX, self._maxY)

		self._layout.add_widget(newRenderedObject)
		self._objectDict[self._id] = newRenderedObject
		self._id += 1

		ModulesAccess.get('ObjectDescriptor').set(newRenderedObject)

	def addObjectByInfo(self, baseObject, identifier, pos, scale, flipOnX, flipOnY, layer, collisionInfo):
		newRenderedObject = self._renderGuardian.createNewObject(identifier, baseObject, pos, self._tileSize,
			self._maxX, self._maxY, autoSelect = False)

		if (flipOnX == True):
			newRenderedObject.flipOnX()

		if (flipOnY == True):
			newRenderedObject.flipOnY()

		if (scale != 1.0):
			newRenderedObject.setScale(scale, True)

		if (collisionInfo is not None):
			newRenderedObject.setCollisionInfo(collisionInfo)

		newRenderedObject.setLayer(layer)
		self._layout.add_widget(newRenderedObject)
		self._objectDict[identifier] = newRenderedObject

	def getObjectsDict(self):
		return self._objectDict

	def getAllValidObjects(self):
		objectsList = []
		for obj in self._objectDict.values():
			if (obj.getHidden() == False and obj.getFinished() == False):
				objectsList.append(obj)

		return objectsList

	def getSelectedObjects(self):
		return self._renderGuardian.getSelection()

	def getRenderGuardian(self):
		return self._renderGuardian

	def getSceneAttributes(self):
		return self._sceneAttr

	def getCurrentId(self):
		return self._id

	def setCurrentId(self, newId):
		assert self._id <= newId
		self._id = newId

	def getMaxSize(self):
		return (self._maxX, self._maxY)

	def getTransaction(self):
		return self._renderGuardian.getTransaction()

class SceneHandler(LayoutGetter, MouseModifiers, KeyboardModifiers):
	def processKeyUp(self, keycode):
		if (keycode[1] == 'shift'):
			self.setIsShiftPressed(False)

		elif (keycode[1] in ['ctrl', 'lctrl', 'rctrl']):
			self.setIsCtrlPressed(False)

	def processKeyDown(self, keycode, modifiers = None):
		t = time()
		if (modifiers is not None and 'ctrl' in modifiers and keycode[1] == 'a'):
			self.__sceneList[self.__currentIndex].selectAll()

		elif (keycode[1] == 'q'):
			self.__sceneList[self.__currentIndex].alignToGrid()

		elif (keycode[1] == 'a'):
			self.__sceneList[self.__currentIndex].copyObject("left")

		elif (keycode[1] == 's'):
			self.__sceneList[self.__currentIndex].copyObject("down")

		elif (keycode[1] == 'd'):
			self.__sceneList[self.__currentIndex].copyObject("right")

		elif (keycode[1] == 'w'):
			self.__sceneList[self.__currentIndex].copyObject("up")

		elif (keycode[1] == 'e'):
			self.__sceneList[self.__currentIndex].unselectAll()

		elif (keycode[1] == 'shift'):
			self.setIsShiftPressed(True)

		elif (keycode[1] in ['ctrl', 'lctrl', 'rctrl']):
			self.setIsCtrlPressed(True)

		elif (keycode[1] == 'delete'):
			self.__sceneList[self.__currentIndex].removeObject()

		elif (keycode[1] == 'r'):
			self.__sceneList[self.__currentIndex].increaseScale()

		elif (keycode[1] == 't'):
			self.__sceneList[self.__currentIndex].decreaseScale()

		elif (keycode[1] == 'f'):
			self.__sceneList[self.__currentIndex].flipOnX()

		elif (keycode[1] == 'g'):
			self.__sceneList[self.__currentIndex].flipOnY()

		elif (keycode[1] == '\'' or keycode[1] == '`'):
			self.__sceneList[self.__currentIndex].toggleGrid()

		elif (keycode[1] == 'z'):
			self.__sceneList[self.__currentIndex].undo()

		elif (keycode[1] == '\\'):
			self.__sceneList[self.__currentIndex].redo()

		elif (keycode[1] == 'pageup'):
			self.__sceneList[self.__currentIndex].increaseLayer()

		elif (keycode[1] == 'pagedown'):
			self.__sceneList[self.__currentIndex].decreaseLayer()

		elif (keycode[1] == 'm'):
			self.__sceneList[self.__currentIndex].mergeObjects()

		if (keycode[1] not in ['ctrl', 'lctrl', 'rctrl'] and keycode[1] != 'shift'):
			Clock.unschedule(self.__scheduleTextureUpdate)
			Clock.schedule_once(self.__scheduleTextureUpdate, 0.1)

		print "Time to process touch down: ", time() - t


	def __scheduleTextureUpdate(self, *args):
		ModulesAccess.get('MiniMap').updateMinimap(self.__sceneList[self.__currentIndex].getMiniMapTexture())

	def __getSelectedObjectByClick(self, touch):
		clickedObjectsList = []
		childDict = self.__sceneList[self.__currentIndex].getObjectsDict()
		for key in childDict.keys():
			if (childDict[key].collide_point(*self.__sceneList[self.__currentIndex].getLayout().to_widget(*touch.pos,
					relative = False)) == True and childDict[key].getHidden() == False):
				clickedObjectsList.append(childDict[key])

		first = True
		selectedObject = None
		layerNameToPriority = ModulesAccess.get('LayerGuardian').getNameToPriorityDict()
		for obj in clickedObjectsList:
			if (first == True):
				selectedObject = obj
				selectedObjectPriority = layerNameToPriority[selectedObject.getLayer()]
				first = False
			else:
				objPriority = layerNameToPriority[obj.getLayer()]
				if (objPriority > selectedObjectPriority):
					selectedObject = obj
					selectedObjectPriority = objPriority
				elif (objPriority == selectedObjectPriority and selectedObject.getIdentifier() < obj.getIdentifier()):
					selectedObject = obj
					selectedObjectPriority = objPriority

		return selectedObject

	def __selectObject(self, objectToSelect):
		ModulesAccess.get('BaseObjectDisplay').setDisplay(None)
		if (self._isCtrlPressed == False):
			selectedList = self.__sceneList[self.__currentIndex].getRenderGuardian().getSelection()
			if (objectToSelect in selectedList):
				ModulesAccess.get('ObjectDescriptor').set(selectedList)
			else:
				selection = self.__sceneList[self.__currentIndex].getRenderGuardian().setSingleSelectionObject(
					objectToSelect
				)
				ModulesAccess.get('ObjectDescriptor').set(selection)

		else:
			selectedObjectsList = self.__sceneList[self.__currentIndex].getRenderGuardian().addObjectToSelection(
				objectToSelect
			)
			ModulesAccess.get('ObjectDescriptor').set(selectedObjectsList)

	def __unselectObject(self, objectToUnselect):
		selectedObjectsList = self.__sceneList[self.__currentIndex].getRenderGuardian().unselectObject(objectToUnselect)
		ModulesAccess.get('ObjectDescriptor').set(selectedObjectsList)

	def __handleScrollAndPassTouchUpToChildren(self, touch):
		self.updateMouseUp(touch)
		if (self._isRightPressed == True or self._isLeftPressed == False):
			self._layout.do_scroll = True


		if (touch.button == "left"):
			if (self.__clickedObject is not None):
				print "Calling touch up"
				self.__clickedObject.on_touch_up(touch)

			if (self.__startTransction != self.__sceneList[self.__currentIndex].getTransaction()):
				self.__sceneList[self.__currentIndex].redraw()
				ModulesAccess.get('MiniMap').updateMinimap(self.__sceneList[self.__currentIndex].getMiniMapTexture())

			if (self.__clickedObject is not None):
				self.__clickedObject = None
				return True
		else:
			self.__defaultTouchUp(touch)
			return True

	def __handleScrollAndPassTouchDownToChildren(self, touch):
		if (touch.button == 'scrollup'):
			if (self._isCtrlPressed == True):
				ModulesAccess.get('BaseObjectsMenu').updateSelectedNode('down')
			return True
		elif (touch.button == 'scrolldown'):
			if (self._isCtrlPressed == True):
				ModulesAccess.get('BaseObjectsMenu').updateSelectedNode('up')
			return True
		elif (touch.button == 'middle'):
			ModulesAccess.get('BaseObjectsMenu').updateSelectedNode('leftright')
			return True

		self.__startTransction = self.__sceneList[self.__currentIndex].getTransaction()
		if (self._layout.collide_point(*touch.pos) == True):
			self.updateMouseDown(touch)
			if (self._isLeftPressed == True and self._isRightPressed == False):
				self._layout.do_scroll = False

			if (touch.button == "left"):
				selectedObject = self.__getSelectedObjectByClick(touch)
				if (selectedObject is not None):
					if (touch.is_double_tap == False):
						self.__selectObject(selectedObject)
						self.__clickedObject = selectedObject
						self.__clickedObject.on_touch_down(touch)
						print "Calling selected object touch down"
					else:
						self.__unselectObject(selectedObject)
						self.__clickedObject = None
				elif (touch.is_double_tap == True):
					self.__sceneList[self.__currentIndex].unselectAll()
					return True
			else:
				self.__defaultTouchDown(touch)
				return True

	def __handleScrollAndPassMoveToChildren(self, touch):
		if (self.__clickedObject is not None):
			print "Calling selected object touch move"
			self.__clickedObject.on_touch_move(touch)

		if (touch.button == "right"):
			self.__defaultTouchMove(touch)

		return True

	def __scrollMove(self, *args):
		self.__defaultScroll(*args)
		ModulesAccess.get("MiniMap").updateQuad()

	def __init__(self):
		super(SceneHandler, self).__init__()
		self._layout = ScrollView(
			effect_cls = EmptyScrollEffect,
		)
		self.__defaultTouchMove = self._layout.on_touch_move
		self.__defaultTouchDown = self._layout.on_touch_down
		self.__defaultTouchUp = self._layout.on_touch_up
		self.__defaultScroll = self._layout.on_scroll_move

		self._layout.on_touch_move = self.__handleScrollAndPassMoveToChildren
		self._layout.on_touch_down = self.__handleScrollAndPassTouchDownToChildren
		self._layout.on_touch_up = self.__handleScrollAndPassTouchUpToChildren
		self._layout.on_scroll_move = self.__scrollMove

		self.__sceneList = []
		self.__sceneList.append(Scene())
		self.__currentIndex = 0
		self.__clickedObject = None

		self._layout.add_widget(self.__sceneList[self.__currentIndex].getLayout())
		ModulesAccess.add('SceneHandler', self)
		minimap = ModulesAccess.get('MiniMap')
		minimap.updateMinimap(self.__sceneList[self.__currentIndex].getMiniMapTexture())
		self._layout.bind(size = minimap.updateQuad)

	def scrollFromMiniMap(self, x, y):
		self._layout.scroll_x = x
		self._layout.scroll_y = y
		self._layout._update_effect_x_bounds()
		self._layout._update_effect_y_bounds()

	def draw(self, obj):
		mouse_pos = Window.mouse_pos
		if (self._layout.collide_point(*mouse_pos) == True):
			x, y = self._layout.to_widget(*mouse_pos)
			sx, sy = obj.getSize()
			mx, my = self.__sceneList[self.__currentIndex].getMaxSize()
			exactlyX = int(x - (sx/2))
			exactlyY = int(y - (sy/2))
			if (exactlyX < 0):
				exactlyX = 0
			elif (exactlyX + sx > mx):
				exactlyX = mx - sx

			if (exactlyY < 0):
				exactlyY = 0
			elif (exactlyY + sy > my):
				exactlyY = my - sy

			self.__sceneList[self.__currentIndex].addObject(obj, exactlyX = exactlyX, exactlyY = exactlyY)
		else:
			relativeX = self._layout.hbar[0]
			relativeY = self._layout.vbar[0]
			self.__sceneList[self.__currentIndex].addObject(obj, relativeX = relativeX, relativeY = relativeY)

		Clock.unschedule(self.__scheduleTextureUpdate)
		Clock.schedule_once(self.__scheduleTextureUpdate, 0.1)

	def redraw(self):
		self.__sceneList[self.__currentIndex].redraw()

	def getAllObjects(self):
		allObjectsList = []
		for singleScene in self.__sceneList:
			allObjectsList.extend(singleScene.getAllValidObjects())

		return allObjectsList

	def getCurrentSceneObjects(self):
		return self.__sceneList[self.__currentIndex].getAllValidObjects()

	def getCurrentSelection(self):
		return self.__sceneList[self.__currentIndex].getSelectedObjects()

	def clearScenes(self, dt = None):
		for singleScene in self.__sceneList:
			singleScene.clear(dt)

	# TODO: This method still considers a single scene condition.
	def newScene(self, attributes):
		newScene = Scene(attributes)
		self._layout.clear_widgets()
		self._layout.add_widget(newScene.getLayout())
		self.__sceneList[self.__currentIndex] = newScene
		ModulesAccess.get('BaseObjectDisplay').setDisplay(None)

		Clock.unschedule(self.__scheduleTextureUpdate)
		Clock.schedule_once(self.__scheduleTextureUpdate, 0.1)

	def getCurrentSceneAttributes(self):
		return self.__sceneList[self.__currentIndex].getSceneAttributes()

	def addObjectByInfo(self, baseObject, identifier, pos, scale, flipOnX, flipOnY, layer, collisionInfo):
		self.__sceneList[self.__currentIndex].addObjectByInfo(baseObject, identifier, pos, scale, flipOnX, flipOnY,
			layer, collisionInfo)

	def setSceneObjectId(self, newId):
		self.__sceneList[self.__currentIndex].setCurrentId(newId)

	def getSceneObjectId(self):
		return self.__sceneList[self.__currentIndex].getCurrentId()
