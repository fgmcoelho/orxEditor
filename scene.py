from singleton import Singleton
from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout

from editorobjects import ObjectTypes, RenderedObject, RenderObjectGuardian
from objectdescriptor import ObjectDescriptor, MultipleSelectionDescriptor
from kivy.graphics.vertex_instructions import Line
from kivy.graphics import Color

from operator import itemgetter

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

@Singleton
class Scene:
	
	def __init__(self):
		self.__alignToGrid = False
		self.__objectDict = {}
		self.__layout = RelativeLayout(size_hint = (None, None))
		self.loadValues()

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
		if self.__objectDict != {}:
			for key in self.__objectDict:
				self.__objectDict[key].resetAllWidgets()
			self.__objectDict = {}

		with self.__layout.canvas:
			Color(0., 1., 0.)
			i = 0
			while i < sx:
				Line(points = [
					i, 0, 
					i, sy], width = 2
				)
				i += self.__tileSize
			i = 0
			while i < sy:
				Line(points = [
					0, i, 
					sx, i], width = 2
				)
				i += self.__tileSize
		
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

	def increaseScale(self):
		obj = RenderObjectGuardian.Instance().increaseScale()
		if (obj != None):
			ObjectDescriptor.Instance().setObject(obj)
	
	def decreaseScale(self):
		obj = RenderObjectGuardian.Instance().decreaseScale()
		if (obj != None):
			ObjectDescriptor.Instance().setObject(obj)

	def flipOnX(self):
		flippedObjects = RenderObjectGuardian.Instance().flipSelectionOnX()
		numberOfFlippedObjects = len(flippedObjects)
		if (numberOfFlippedObjects == 1):
			ObjectDescriptor.Instance().setObject(flippedObjects[0])
		elif (numberOfFlippedObjects > 1):
			MultipleSelectionDescriptor.Instance().setValues(numberOfFlippedObjects)

	def flipOnY(self):
		flippedObjects = RenderObjectGuardian.Instance().flipSelectionOnY()
		numberOfFlippedObjects = len(flippedObjects)
		if (numberOfFlippedObjects == 1):
			ObjectDescriptor.Instance().setObject(flippedObjects[0])
		elif (numberOfFlippedObjects > 1):
			MultipleSelectionDescriptor.Instance().setValues(numberOfFlippedObjects)

	def removeObject(self):
			
		deletedObjects = RenderObjectGuardian.Instance().deleteSelection()
		for obj in deletedObjects:
			identifier = obj.getIdentifier()
			del self.__objectDict[identifier]
		if (len(deletedObjects) != 0):	
			ObjectDescriptor.Instance().clearCurrentObject()
		
	def alignToGrid(self):
		RenderObjectGuardian.Instance().alignSelectionToGrid()

	def copyObject(self, direction):
		newObjects = RenderObjectGuardian.Instance().copySelection(direction, self.__id, self.__tileSize, self.__maxX, self.__maxY)
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
		RenderObjectGuardian.Instance().unsetSelection()
	
	def resetAllWidgets(self):
		for objectId in self.__objectDict.keys():
			self.__objectDict[objectId].resetAllWidgets()
			self.__objectDict[objectId] = None
			del self.__objectDict[objectId] 

		self.__objectDict = {}
		self.__id = 0
	
	def __createNewObjectAndAddToScene(self, obj, pos):
		renderedObject = RenderedObject(self.__id, obj, pos, self.__tileSize, self.__maxX, self.__maxY)
		RenderObjectGuardian.Instance().setSingleSelectionObject(renderedObject)
		
		self.__layout.add_widget(renderedObject)
		self.__objectDict[self.__id] = renderedObject
		self.__id += 1

		return renderedObject

	def getLayout(self):
		return self.__layout

	def addObject(self, obj, relativeX, relaviveY):
		pos = (int(relativeX * self.__maxX), int(relaviveY * self.__maxY))
		newRenderedObject = self.__createNewObjectAndAddToScene(obj, pos)
		ObjectDescriptor.Instance().setObject(newRenderedObject)

	def getObjectsDict(self):
		return self.__objectDict


@Singleton
class SceneHandler:

	def setIsShiftPressed(self, value):
		self.__isShiftPressed = value
	
	def setIsCtrlPressed(self, value):
		self.__isCtrlPressed = value

	def __ignoreMoves(self, touch):
		return None
	
	def __handleScrollAndPassTouchUpToChildren(self, touch):
		
		Scene.Instance().redraw()
		self.__defaultTouchUp(touch)

	def __handleScrollAndPassTouchDownToChildren(self, touch):
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
		
		else:
			clickedObjectsList = []
			childDict = Scene.Instance().getObjectsDict()
			for key in childDict.keys():
				if childDict[key].collide_point(*self.__scrollView.to_widget(*touch.pos)):
					clickedObjectsList.append(childDict[key])
				
			highestLayer = -100
			selectedObject = None
			for obj in clickedObjectsList:
				if (highestLayer < obj.getLayer()):
					highestLayer = obj.getLayer()
					selectedObject = obj

			if (selectedObject != None):
				if (touch.is_double_tap == False):
					if (self.__isCtrlPressed == False):
						ObjectDescriptor.Instance().setObject(selectedObject)
						RenderObjectGuardian.Instance().setSingleSelectionObject(selectedObject)
					else:
						RenderObjectGuardian.Instance().addObjectToSelection(selectedObject)
				else:
					RenderObjectGuardian.Instance().unselectObject(selectedObject)

		self.__defaultTouchDown(touch)
	
	def __init__(self, rightScreen, maxWidthProportion = 1.0, maxHeightProportion = 0.667):
		
		self.__isShiftPressed = False
		self.__isCtrlPressed = False
		self.__maxWidthProportion = maxWidthProportion
		self.__maxHeightProportion = maxHeightProportion
		
		self.__scrollView = ScrollView(scroll_timeout = 0, size_hint = (maxWidthProportion, maxHeightProportion))
		self.__scrollView.on_touch_move = self.__ignoreMoves
		self.__defaultTouchDown = self.__scrollView.on_touch_down
		self.__defaultTouchUp = self.__scrollView.on_touch_up

		self.__scrollView.on_touch_down = self.__handleScrollAndPassTouchDownToChildren
		self.__scrollView.on_touch_up = self.__handleScrollAndPassTouchUpToChildren

		self.__scrollView.add_widget(Scene.Instance().getLayout())
		rightScreen.add_widget(self.__scrollView)
		
	def draw(self, obj):
		relativeX = self.__scrollView.hbar[0]
		relaviveY = self.__scrollView.vbar[0]
		Scene.Instance().addObject(obj, relativeX, relaviveY)

	def getLayout(self):
		return self.__scrollView

