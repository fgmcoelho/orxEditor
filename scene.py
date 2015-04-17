from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics.vertex_instructions import Line
from kivy.graphics.fbo import Fbo
from kivy.graphics import Color, Canvas, Rectangle, ClearColor, ClearBuffers, Scale, Translate, InstructionGroup
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.properties import ObjectProperty, NumericProperty

from operator import itemgetter

from editorheritage import SpecialScrollControl, LayoutGetter
from editorobjects import RenderObjectGuardian
from editorutils import AlertPopUp, AutoReloadTexture
from objectdescriptor import ObjectDescriptor, MultipleSelectionDescriptor
from layerinfo import LayerGuardian
from modulesaccess import ModulesAccess

class OrderSceneObjects:
	def _order_objects(self, objectDict):
		objectsList = []
		nameToPriorityDict = LayerGuardian.Instance().getNameToPriorityDict()
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

	def _startGridInstuctions(self):
		self._gridGroup = InstructionGroup()
		self._gridGroup.add(Color(0., 1., 0.))
		i = 0
		while i < self._maxX:
			self._gridGroup.add(Line(points = [
				i, 0,
				i, self._maxY], width = 2
			))
			i += self._tileSize
		i = 0
		while i < self._maxY:
			self._gridGroup.add(Line(points = [
				0, i,
				self._maxX, i], width = 2
			))
			i += self._tileSize

	def getMiniMapTexture(self):
		if (self._showGrid == True):
			self.hideGrid()

		# TODO: Investigate this code!
		if self._layout.parent is not None:
			canvas_parent_index = self._layout.parent.canvas.indexof(self._layout.canvas)
			self._layout.parent.canvas.remove(self._layout.canvas)

		fbo = Fbo(size=self._layout.size, with_stencilbuffer=True)
		with fbo:
			ClearColor(0, 0, 0, 1)
			ClearBuffers()
			#Scale(1, -1, 1)
			#Translate(-self._layout.x, -self._layout.y - self._layout.height, 0)

		fbo.add(self._layout.canvas)
		fbo.draw()
		img = Image(texture = fbo.texture, size = fbo.texture.size)
		popup = Popup(auto_dismiss = True, content = img, title = 'aaa', size_hint = (0.5, 0.5))
		popup.open()
		fbo.remove(self._layout.canvas)

		if self._layout.parent is not None:
			self._layout.parent.canvas.insert(canvas_parent_index, self._layout.canvas)

		if (self._showGrid == True):
			self.showGrid()
			self.redraw()

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
			self._sceneAttr = SceneAttributes(40, 100, 100)
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
			self._layout.add_widget(obj[0])
			if (self._alignToGrid == True):
				obj[0].alignToGrid()

	def _updateDesctriptorBySelection(self):
		newObjects = self._renderGuardian.getSelection()
		numberOfNewObjects = len(newObjects)
		if (numberOfNewObjects == 1):
			ObjectDescriptor.Instance().setObject(newObjects[0])
		elif (numberOfNewObjects > 1):
			MultipleSelectionDescriptor.Instance().setValues(numberOfNewObjects)
		else:
			ObjectDescriptor.Instance().clearCurrentObject()

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

	def increaseScale(self):
		obj = self._renderGuardian.increaseScale()
		if (obj is not None):
			ObjectDescriptor.Instance().setObject(obj)

	def decreaseScale(self):
		obj = self._renderGuardian.decreaseScale()
		if (obj is not None):
			ObjectDescriptor.Instance().setObject(obj)

	def flipOnX(self):
		flippedObjects = self._renderGuardian.flipSelectionOnX()
		numberOfFlippedObjects = len(flippedObjects)
		if (numberOfFlippedObjects == 1):
			ObjectDescriptor.Instance().setObject(flippedObjects[0])
		elif (numberOfFlippedObjects > 1):
			MultipleSelectionDescriptor.Instance().setValues(numberOfFlippedObjects)

	def flipOnY(self):
		flippedObjects = self._renderGuardian.flipSelectionOnY()
		numberOfFlippedObjects = len(flippedObjects)
		if (numberOfFlippedObjects == 1):
			ObjectDescriptor.Instance().setObject(flippedObjects[0])
		elif (numberOfFlippedObjects > 1):
			MultipleSelectionDescriptor.Instance().setValues(numberOfFlippedObjects)

	def removeObject(self):
		deletedObjects = self._renderGuardian.deleteSelection()
		if (len(deletedObjects) != 0):
			ObjectDescriptor.Instance().clearCurrentObject()

	def alignToGrid(self):
		self._renderGuardian.alignSelectionToGrid()

	def copyObject(self, direction):
		newObjects = self._renderGuardian.copySelection(direction, self._id, self._tileSize, self._maxX,
			self._maxY)
		for renderedObject in newObjects:
			self._layout.add_widget(renderedObject)
			self._objectDict[self._id] = renderedObject
			self._id += 1

		numberOfNewObjects = len(newObjects)
		if (numberOfNewObjects == 1):
			ObjectDescriptor.Instance().setObject(newObjects[0])
		elif (numberOfNewObjects > 1):
			MultipleSelectionDescriptor.Instance().setValues(numberOfNewObjects)

	def unselectAll(self):
		self._renderGuardian.unsetSelection()
		ObjectDescriptor.Instance().clearCurrentObject()

	def resetAllWidgets(self):
		for objectId in self._objectDict.keys():
			self._objectDict[objectId].resetAllWidgets()
			self._objectDict[objectId] = None
			del self._objectDict[objectId]

		self._objectDict = {}
		self._id = 0

	def addObject(self, obj, relativeX = None, relaviveY = None, exactlyX = None, exactlyY = None):
		assert (relativeX is not None and relaviveY is not None) or (exactlyX is not None and \
			exactlyY is not None), "Invalid argument received."
		sx, sy = obj.getSize()
		if (sx > self._maxX or sy > self._maxY):
			errorAlert = AlertPopUp(
				'Error',
				'Object could not be rendered because\nit is bigger than the scene space.',
				'Ok'
			)
			errorAlert.open()
			return

		if (relativeX is not None and relaviveY is not None):
			pos = (int(relativeX * self._maxX), int(relaviveY * self._maxY))
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

		ObjectDescriptor.Instance().setObject(newRenderedObject)

	def addObjectByInfo(self, baseObject, identifier, pos, scale, flipOnX, flipOnY, layer, collisionInfo):
		newRenderedObject = self._renderGuardian.createNewObject(identifier, baseObject, pos, self._tileSize,
			self._maxX, self._maxY)

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

class SceneHandler (SpecialScrollControl):
	# Overloaded method
	def processKeyUp(self, keyboard, keycode):

		if (keycode[1] == 'shift'):
			self.setIsShiftPressed(False)

		elif (keycode[1] == 'ctrl'):
			self.setIsCtrlPressed(False)

	# Overloaded method
	def processKeyDown(self, keyboard, keycode, text, modifiers):
		if (keycode[1] == 'q'):
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

		elif (keycode[1] == 'ctrl'):
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

		elif (keycode[1] == 'y'):
			self.__sceneList[self.__currentIndex].getMiniMapTexture()

	def __getSelectedObjectByClick(self, touch):
		clickedObjectsList = []
		childDict = self.__sceneList[self.__currentIndex].getObjectsDict()
		for key in childDict.keys():
			if (childDict[key].collide_point(*self.__sceneList[self.__currentIndex].getLayout().to_widget(*touch.pos,
					relative = False)) == True and childDict[key].getHidden() == False):
				clickedObjectsList.append(childDict[key])

		first = True
		selectedObject = None
		for obj in clickedObjectsList:

			if (first == True):
				selectedObject = obj
				first = False
			else:
				if (selectedObject.getIdentifier() < obj.getIdentifier()):
					selectedObject = obj

		return selectedObject

	def __selectObject(self, objectToSelect):
		if (self._isCtrlPressed == False):
			ObjectDescriptor.Instance().setObject(objectToSelect)
			self.__sceneList[self.__currentIndex].getRenderGuardian().setSingleSelectionObject(objectToSelect)
		else:
			selectedObjectsList = self.__sceneList[self.__currentIndex].getRenderGuardian().addObjectToSelection(
				objectToSelect
			)
			numberOfSelectedObjects = len(selectedObjectsList)
			if (numberOfSelectedObjects == 1):
				ObjectDescriptor.Instance().setObject(selectedObjectsList[0])
			elif(numberOfSelectedObjects > 1):
				MultipleSelectionDescriptor.Instance().setValues(numberOfSelectedObjects)

	def __unselectObject(self, objectToUnselect):
		selectedObjectsList = self.__sceneList[self.__currentIndex].getRenderGuardian().unselectObject(objectToUnselect)
		numberOfSelectedObjects = len(selectedObjectsList)
		if (numberOfSelectedObjects == 0):
			ObjectDescriptor.Instance().clearCurrentObject()
		elif(numberOfSelectedObjects == 1):
			ObjectDescriptor.Instance().setObject(selectedObjectsList[0])
		else:
			MultipleSelectionDescriptor.Instance().setValues(numberOfSelectedObjects)

	def __handleScrollAndPassTouchUpToChildren(self, touch):
		self.__sceneList[self.__currentIndex].redraw()
		self.__defaultTouchUp(touch)

	def __handleScrollAndPassTouchDownToChildren(self, touch):
		if (self._scrollView.collide_point(*touch.pos) == False):
			return

		if (touch.is_mouse_scrolling == True):
			return self.specialScroll(touch)

		else:
			selectedObject = self.__getSelectedObjectByClick(touch)
			if (selectedObject is not None):
				if (touch.is_double_tap == False):
					self.__selectObject(selectedObject)
				else:
					self.__unselectObject(selectedObject)

		self.__defaultTouchDown(touch)

	def __init__(self):
		super(SceneHandler, self).__init__()
		self._scrollView.on_touch_move = self._ignoreMoves
		self.__defaultTouchDown = self._scrollView.on_touch_down
		self.__defaultTouchUp = self._scrollView.on_touch_up

		self._scrollView.on_touch_down = self.__handleScrollAndPassTouchDownToChildren
		self._scrollView.on_touch_up = self.__handleScrollAndPassTouchUpToChildren

		self.__sceneList = []
		self.__sceneList.append(Scene())
		self.__currentIndex = 0

		self._scrollView.add_widget(self.__sceneList[self.__currentIndex].getLayout())
		ModulesAccess.add('SceneHandler', self)

	def draw(self, obj):
		mouse_pos = Window.mouse_pos
		if (self._scrollView.collide_point(*mouse_pos) == True):
			x, y = self._scrollView.to_widget(*mouse_pos)
			sx, sy = obj.getSize()
			exactlyX = int(x - (sx/2))
			exactlyY = int(y - (sy/2))
			self.__sceneList[self.__currentIndex].addObject(obj, exactlyX = exactlyX, exactlyY = exactlyY)
		else:
			relativeX = self._scrollView.hbar[0]
			relaviveY = self._scrollView.vbar[0]
			self.__sceneList[self.__currentIndex].addObject(obj, relativeX = relativeX, relaviveY = relaviveY)

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
		self._scrollView.clear_widgets()
		self._scrollView.add_widget(newScene.getLayout())

		self.__sceneList[self.__currentIndex] = newScene

	def getCurrentSceneAttributes(self):
		return self.__sceneList[self.__currentIndex].getSceneAttributes()

	def addObjectByInfo(self, baseObject, identifier, pos, scale, flipOnX, flipOnY, layer, collisionInfo):
		self.__sceneList[self.__currentIndex].addObjectByInfo(baseObject, identifier, pos, scale, flipOnX, flipOnY,
			layer, collisionInfo)

	def setSceneObjectId(self, newId):
		self.__sceneList[self.__currentIndex].setCurrentId(newId)

	def getSceneObjectId(self):
		return self.__sceneList[self.__currentIndex].getCurrentId()
