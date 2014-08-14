from singleton import Singleton

from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics.vertex_instructions import Line
from kivy.graphics import Color

from operator import itemgetter

from editorheritage import SpecialScrollControl
from editorobjects import RenderObjectGuardian
from keyboard import KeyboardAccess
from objectdescriptor import ObjectDescriptor, MultipleSelectionDescriptor

@Singleton
class SceneAttributes:
	def __init__(self, tileSize, numberOfTilesX, numberOfTilesY):
		self.__valuesDict = { 
			'TilesMaxX'  : numberOfTilesX,
			'TilesMaxY'  : numberOfTilesY,
			'TilesSize'  : tileSize,
		}

	def getValue(self, value):
		if (value in self.__valuesDict):
			return self.__valuesDict[value]
		else:
			return None

class Scene:
	
	def __init__(self):
		self.__alignToGrid = False
		self.__objectDict = {}
		self.__layout = RelativeLayout(size_hint = (None, None), on_resize = self.redraw)
		self.__renderGuardian = RenderObjectGuardian()
		self.loadValues()

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

	def toggleGrid(self):
		if (self.__showGrid == True):
			self.hideGrid()
		else:
			self.showGrid()

		self.__showGrid = not self.__showGrid
		
		self.redraw()

	def loadValues(self):
		self.__layout.canvas.clear()
		sceneAttr = SceneAttributes.Instance()
		self.__tileSize = sceneAttr.getValue('TilesSize')
		sx = sceneAttr.getValue('TilesMaxX') * self.__tileSize
		sy = sceneAttr.getValue('TilesMaxY') * self.__tileSize
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

		self.showGrid()
		
	def redraw(self):
		objectsList = []
		for key in self.__objectDict.keys():
			objectsList.append((self.__objectDict[key], self.__objectDict[key].getIdentifier()))

		self.__layout.clear_widgets()
		objectsOrderedList = sorted(objectsList, key=itemgetter(1))
		for obj in objectsOrderedList:
			self.__layout.add_widget(obj[0])
			if (self.__alignToGrid == True):
				obj[0].alignToGrid()

	def undo(self):
		self.__renderGuardian.undo()

	def redo(self):
		self.__renderGuardian.redo()

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
		newObjects = self.__renderGuardian.copySelection(direction, self.__id, self.__tileSize, self.__maxX, self.__maxY)
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

	def addObject(self, obj, relativeX, relaviveY):
		pos = (int(relativeX * self.__maxX), int(relaviveY * self.__maxY))
		
		newRenderedObject = self.__renderGuardian.createNewObject(self.__id, obj, pos, self.__tileSize, self.__maxX, 
				self.__maxY)
		
		self.__layout.add_widget(newRenderedObject)
		self.__objectDict[self.__id] = newRenderedObject
		self.__id += 1

		ObjectDescriptor.Instance().setObject(newRenderedObject)

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


class SceneHandler (SpecialScrollControl, KeyboardAccess):
	
	# Overloaded method
	def _processKeyUp(self, keyboard, keycode):
	
		if (keycode[1] == 'shift'):
			self.setIsShiftPressed(False)

		elif (keycode[1] == 'ctrl'):
			self.setIsCtrlPressed(False)
	
	# Overloaded method
	def _processKeyDown(self, keyboard, keycode, text, modifiers):

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

		elif (keycode[1] == '\''):
			self.__sceneList[self.__currentIndex].toggleGrid()

		elif (keycode[1] == 'z'):
			self.__sceneList[self.__currentIndex].undo()

		elif (keycode[1] == '\\'):
			self.__sceneList[self.__currentIndex].redo()

	def __getSelectedObjectByClick(self, touch):
		clickedObjectsList = []
		childDict = self.__sceneList[self.__currentIndex].getObjectsDict()
		for key in childDict.keys():
			if (childDict[key].collide_point(*self.__sceneList[self.__currentIndex].getLayout().to_widget(*touch.pos, relative = False)) == True 
					and childDict[key].getHidden() == False):
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
			selectedObjectsList = self.__sceneList[self.__currentIndex].getRenderGuardian().addObjectToSelection(objectToSelect)
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

	def __ignoreMoves(self, touch):
		return None
	
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
			print selectedObject
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
		
		self._scrollView.on_touch_move = self.__ignoreMoves
		self.__defaultTouchDown = self._scrollView.on_touch_down
		self.__defaultTouchUp = self._scrollView.on_touch_up

		self._scrollView.on_touch_down = self.__handleScrollAndPassTouchDownToChildren
		self._scrollView.on_touch_up = self.__handleScrollAndPassTouchUpToChildren

		self.__sceneList = []
		self.__sceneList.append(Scene())
		self.__currentIndex = 0

		self._scrollView.add_widget(self.__sceneList[self.__currentIndex].getLayout())
				
	def draw(self, obj):
		relativeX = self._scrollView.hbar[0]
		relaviveY = self._scrollView.vbar[0]
		self.__sceneList[self.__currentIndex].addObject(obj, relativeX, relaviveY)

	def getAllObjects(self):
		allObjectsList = []
		for singleScene in self.__sceneList:
			allObjectsList.extend(singleScene.getAllValidObjects())
		
		return allObjectsList
		
	def getCurrentSelection(self):
		return self.__sceneList[self.__currentIndex].getSelectedObjects()

	def clearScenes(self, dt = None):
		for singleScene in self.__sceneList:
			singleScene.clear(dt)
		