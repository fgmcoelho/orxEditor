from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics.vertex_instructions import Line
from kivy.graphics.fbo import Fbo
from kivy.graphics import Color, Canvas, Rectangle, ClearColor, ClearBuffers, Scale, Translate
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.properties import ObjectProperty, NumericProperty

from operator import itemgetter

from editorheritage import SpecialScrollControl
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

class MiniMapScene(RelativeLayout, OrderSceneObjects):
	texture = ObjectProperty(None, allownone=True)
	alpha = NumericProperty(1)
	def __init__(self, **kwargs):
		self.canvas = Canvas()
		with self.canvas:
			self.fbo = Fbo(size=self.size)
			self.fbo_color = Color(1, 1, 1, 1)
			self.fbo_rect = Rectangle()

		with self.fbo:
			ClearColor(0, 0, 0, 0)
			ClearBuffers()

		# wait that all the instructions are in the canvas to set texture
		self.texture = self.fbo.texture
		super(MiniMapScene, self).__init__(**kwargs)

	def add_widget(self, *largs):
		# trick to attach graphics instruction to fbo instead of canvas
		canvas = self.canvas
		self.canvas = self.fbo
		ret = super(MiniMapScene, self).add_widget(*largs)
		self.canvas = canvas
		print ret
		return ret

	def clear_widgets(self):
		canvas = self.canvas
		self.canvas = self.fbo
		super(MiniMapScene, self).clear_widgets()
		self.canvas = canvas

	def remove_widget(self, *largs):
		canvas = self.canvas
		self.canvas = self.fbo
		super(MiniMapScene, self).remove_widget(*largs)
		self.canvas = canvas

	def on_size(self, instance, value):
		print "aaaa"
		self.fbo.size = value
		self.texture = self.fbo.texture
		self.fbo_rect.size = value

	def on_pos(self, instance, value):
		print "bbbb"
		self.fbo_rect.pos = value

	def on_texture(self, instance, value):
		print "cccc"
		self.fbo_rect.texture = value

	def on_alpha(self, instance, value):
		self.fbo_color.rgba = (1, 1, 1, value)

	def getTexture(self):
		img = Image(texture = self.fbo.texture)
		popup = Popup(title = 'testing', content = img, auto_dismiss = True)
		popup.open()

	def populateMap(self, objectDict):
		objectsOrderedList = self._order_objects(objectDict)
		self.clear_widgets()
		for obj in objectsOrderedList:
			self.add_widget(obj[0])

class Scene(OrderSceneObjects):

	def __init__(self, attributes = None):
		self.__alignToGrid = False
		self.__objectDict = {}
		self.__layout = RelativeLayout(size_hint = (None, None), on_resize = self.redraw)
		self.__renderGuardian = RenderObjectGuardian()
		self.loadValues(attributes)

	def getMiniMapTexture(self):
		#self.hideGrid()
		if self.__layout.parent is not None:
			canvas_parent_index = self.__layout.parent.canvas.indexof(self.__layout.canvas)
			self.__layout.parent.canvas.remove(self.__layout.canvas)
		
		fbo = Fbo(size=self.__layout.size, with_stencilbuffer=True)
		with fbo:
			ClearColor(0, 0, 0, 1)
			ClearBuffers()
			Scale(1, -1, 1)
			Translate(-self.__layout.x, -self.__layout.y - self.__layout.height, 0)

		fbo.add(self.__layout.canvas)
		fbo.draw()
		img = Image(texture = fbo.texture, size = fbo.texture.size)
		popup = Popup(auto_dismiss = True, content = img, title = 'aaa', size_hint = (0.5, 0.5))
		popup.open()
		fbo.remove(self.__layout.canvas)

		if self.__layout.parent is not None:
			self.__layout.parent.canvas.insert(canvas_parent_index, self.__layout.canvas)
		#self.showGrid()

	def showGrid(self):
		with self.__layout.canvas:
			Color(0., 1., 0.)
			i = 0
			while i < self.__maxX:
				Line(points = [
					i, 0,
					i, self.__maxY], width = 2
				)
				i += self.__tileSize
			i = 0
			while i < self.__maxY:
				Line(points = [
					0, i,
					self.__maxX, i], width = 2
				)
				i += self.__tileSize
		self.__layout.canvas.ask_update()

	def hideGrid(self):
		with self.__layout.canvas:
			Color(0., 0., 0.)
			i = 0
			while i < self.__maxX:
				Line(points = [
					i, 0,
					i, self.__maxY], width = 2
				)
				i += self.__tileSize
			i = 0
			while i < self.__maxY:
				Line(points = [
					0, i,
					self.__maxX, i], width = 2
				)
				i += self.__tileSize
		self.__layout.canvas.ask_update()

	def toggleGrid(self):
		if (self.__showGrid == True):
			self.hideGrid()
		else:
			self.showGrid()

		self.__showGrid = not self.__showGrid

		self.redraw()

	def loadValues(self, attributes = None):
		self.__layout.canvas.clear()
		if (attributes is None):
			self.__sceneAttr = SceneAttributes(40, 100, 100)
		else:
			self.__sceneAttr = attributes

		self.__tileSize = self.__sceneAttr.getValue('TilesSize')
		sx = self.__sceneAttr.getValue('TilesMaxX') * self.__tileSize
		sy = self.__sceneAttr.getValue('TilesMaxY') * self.__tileSize
		self.__layout.size= (sx, sy)
		self.__id = 0
		self.__maxX = sx
		self.__minX = 0.0
		self.__maxY = sy
		self.__minY = 0.0
		self.__showGrid = True
		if self.__objectDict != {}:
			for key in self.__objectDict:
				self.__objectDict[key].resetAllWidgets()
			self.__objectDict = {}

		#self.showGrid()

	def redraw(self, avoidClear = False):
		objectsOrderedList = self._order_objects(self.__objectDict)
		if (avoidClear == False):
			self.__layout.clear_widgets()
		for obj in objectsOrderedList:
			self.__layout.add_widget(obj[0])
			if (self.__alignToGrid == True):
				obj[0].alignToGrid()

	def __updateDesctriptorBySelection(self):
		newObjects = self.__renderGuardian.getSelection()
		numberOfNewObjects = len(newObjects)
		if (numberOfNewObjects == 1):
			ObjectDescriptor.Instance().setObject(newObjects[0])
		elif (numberOfNewObjects > 1):
			MultipleSelectionDescriptor.Instance().setValues(numberOfNewObjects)
		else:
			ObjectDescriptor.Instance().clearCurrentObject()

	def undo(self):
		self.__renderGuardian.undo()
		self.__updateDesctriptorBySelection()

	def redo(self):
		self.__renderGuardian.redo()
		self.__updateDesctriptorBySelection()

	def clear(self, unusedDt = None):
		for key in self.__objectDict.keys():
			if (self.__objectDict[key].getFinished() == True):
				self.__layout.remove_widget(self.__objectDict[key])
				self.__objectDict[key] = None
				del self.__objectDict[key]

	def increaseScale(self):
		obj = self.__renderGuardian.increaseScale()
		if (obj is not None):
			ObjectDescriptor.Instance().setObject(obj)

	def decreaseScale(self):
		obj = self.__renderGuardian.decreaseScale()
		if (obj is not None):
			ObjectDescriptor.Instance().setObject(obj)

	def flipOnX(self):
		flippedObjects = self.__renderGuardian.flipSelectionOnX()
		numberOfFlippedObjects = len(flippedObjects)
		if (numberOfFlippedObjects == 1):
			ObjectDescriptor.Instance().setObject(flippedObjects[0])
		elif (numberOfFlippedObjects > 1):
			MultipleSelectionDescriptor.Instance().setValues(numberOfFlippedObjects)

	def flipOnY(self):
		flippedObjects = self.__renderGuardian.flipSelectionOnY()
		numberOfFlippedObjects = len(flippedObjects)
		if (numberOfFlippedObjects == 1):
			ObjectDescriptor.Instance().setObject(flippedObjects[0])
		elif (numberOfFlippedObjects > 1):
			MultipleSelectionDescriptor.Instance().setValues(numberOfFlippedObjects)

	def removeObject(self):
		deletedObjects = self.__renderGuardian.deleteSelection()
		if (len(deletedObjects) != 0):
			ObjectDescriptor.Instance().clearCurrentObject()

	def alignToGrid(self):
		self.__renderGuardian.alignSelectionToGrid()

	def copyObject(self, direction):
		newObjects = self.__renderGuardian.copySelection(direction, self.__id, self.__tileSize, self.__maxX,
			self.__maxY)
		for renderedObject in newObjects:
			self.__layout.add_widget(renderedObject)
			self.__objectDict[self.__id] = renderedObject
			self.__id += 1

		numberOfNewObjects = len(newObjects)
		if (numberOfNewObjects == 1):
			ObjectDescriptor.Instance().setObject(newObjects[0])
		elif (numberOfNewObjects > 1):
			MultipleSelectionDescriptor.Instance().setValues(numberOfNewObjects)

	def unselectAll(self):
		self.__renderGuardian.unsetSelection()
		ObjectDescriptor.Instance().clearCurrentObject()

	def resetAllWidgets(self):
		for objectId in self.__objectDict.keys():
			self.__objectDict[objectId].resetAllWidgets()
			self.__objectDict[objectId] = None
			del self.__objectDict[objectId]

		self.__objectDict = {}
		self.__id = 0

	def getLayout(self):
		return self.__layout

	def addObject(self, obj, relativeX = None, relaviveY = None, exactlyX = None, exactlyY = None):
		assert (relativeX is not None and relaviveY is not None) or (exactlyX is not None and \
			exactlyY is not None), "Invalid argument received."
		sx, sy = obj.getSize()
		if (sx > self.__maxX or sy > self.__maxY):
			errorAlert = AlertPopUp(
				'Error', 
				'Object could not be rendered because\nit is bigger than the scene space.',
				'Ok'
			)
			errorAlert.open()
			return

		if (relativeX is not None and relaviveY is not None):
			pos = (int(relativeX * self.__maxX), int(relaviveY * self.__maxY))
		else:
			pos = (exactlyX, exactlyY)
		if (pos[0] + sx > self.__maxX):
			finalX = self.__maxX - sx
		else:
			finalX = pos[0]
		if (pos[1] + sy > self.__maxY):
			finalY = self.__maxY - sy
		else:
			finalY = pos[1]

		newRenderedObject = self.__renderGuardian.createNewObject(self.__id, obj, (finalX, finalY),
				self.__tileSize, self.__maxX, self.__maxY)

		self.__layout.add_widget(newRenderedObject)
		self.__objectDict[self.__id] = newRenderedObject
		self.__id += 1

		ObjectDescriptor.Instance().setObject(newRenderedObject)
	
	def addObjectByInfo(self, baseObject, identifier, pos, scale, flipOnX, flipOnY, layer, collisionInfo):
		newRenderedObject = self.__renderGuardian.createNewObject(identifier, baseObject, pos, self.__tileSize, 
			self.__maxX, self.__maxY)

		if (flipOnX == True):
			newRenderedObject.flipOnX()

		if (flipOnY == True):
			newRenderedObject.flipOnY()

		if (scale != 1.0):
			newRenderedObject.setScale(scale, True)

		if (collisionInfo is not None):
			newRenderedObject.setCollisionInfo(collisionInfo)	
		
		newRenderedObject.setLayer(layer)
		self.__layout.add_widget(newRenderedObject)
		self.__objectDict[identifier] = newRenderedObject

	def getObjectsDict(self):
		return self.__objectDict

	def getAllValidObjects(self):
		objectsList = []
		for obj in self.__objectDict.values():
			if (obj.getHidden() == False and obj.getFinished() == False):
				objectsList.append(obj)

		return objectsList

	def getSelectedObjects(self):
		return self.__renderGuardian.getSelection()

	def getRenderGuardian(self):
		return self.__renderGuardian

	def getSceneAttributes(self):
		return self.__sceneAttr

	def getCurrentId(self):
		return self.__id

	def setCurrentId(self, newId):
		assert self.__id <= newId
		self.__id = newId

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

	def __init__(self, maxWidthProportion = 1.0, maxHeightProportion = 0.667):

		self.__maxWidthProportion = maxWidthProportion
		self.__maxHeightProportion = maxHeightProportion

		super(SceneHandler, self).__init__(size_hint = (maxWidthProportion, maxHeightProportion))

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
