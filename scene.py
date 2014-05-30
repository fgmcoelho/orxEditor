from singleton import Singleton
from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout

from editorobjects import ObjectTypes, RenderedObject, RenderObjectGuardian
from objectdescriptor import ObjectDescriptor
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
		self.__alignToGrid = True
		self.__objectDict = {}
		self.__layout = RelativeLayout(size_hint = (None, None))
		self.__objectDict = {}
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
			objectsList.append((self.__objectDict[key], self.__objectDict[key].getLayer()))

		self.__layout.clear_widgets()
		objectsOrderedList = sorted(objectsList, key=itemgetter(1))
		for obj in objectsOrderedList:
			self.__layout.add_widget(obj[0])
			obj[0].alignToGrid()

	def increaseScale(self):
		obj = ObjectDescriptor.Instance().getCurrentObject()
		if (obj != None and obj.getType() == ObjectTypes.renderedObject):
			obj.increaseScale()
			ObjectDescriptor.Instance().setObject(obj)
	
	def decreaseScale(self):
		obj = ObjectDescriptor.Instance().getCurrentObject()
		if (obj != None and obj.getType() == ObjectTypes.renderedObject):
			obj.decreaseScale()
			ObjectDescriptor.Instance().setObject(obj)

	def flipOnX(self):
		obj = ObjectDescriptor.Instance().getCurrentObject()
		if (obj != None and obj.getType() == ObjectTypes.renderedObject):
			obj.flipOnX()
			ObjectDescriptor.Instance().setObject(obj)
		
	def flipOnY(self):
		obj = ObjectDescriptor.Instance().getCurrentObject()
		if (obj != None and obj.getType() == ObjectTypes.renderedObject):
			obj.flipOnY()
			ObjectDescriptor.Instance().setObject(obj)

	def increaseLayer(self):
		obj = ObjectDescriptor.Instance().getCurrentObject()
		if (obj != None and obj.getType() == ObjectTypes.renderedObject):
			obj.increaseLayer()
			ObjectDescriptor.Instance().setObject(obj)

	def decreaseLayer(self):
		obj = ObjectDescriptor.Instance().getCurrentObject()
		if (obj != None and obj.getType() == ObjectTypes.renderedObject):
			obj.decreaseLayer()
			ObjectDescriptor.Instance().setObject(obj)

	def removeObject(self):
		obj = ObjectDescriptor.Instance().getCurrentObject()
		if (obj != None and obj.getType() == ObjectTypes.renderedObject):
			self.__layout.remove_widget(obj)
			identifier = obj.getIdentifier()
			del self.__objectDict[identifier]
			obj = None
			ObjectDescriptor.Instance().clearCurrentObject()
		
	def alignToGrid(self):
		obj = ObjectDescriptor.Instance().getCurrentObject()
		if (obj != None and obj.getType() == ObjectTypes.renderedObject):
			obj.alignToGrid()

	def alignAndCopyObject(self, direction):
		obj = ObjectDescriptor.Instance().getCurrentObject()
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

		elif (direction == "right") and (pos[0] + size[0] * 2 <= self.__maxX):
			newPos = (pos[0] + size[0], pos[1])

		elif (direction == "up" and pos[1] + size[1] * 2 <= self.__maxY):
			newPos = (pos[0], pos[1] + size[1])
		
		elif (direction == "down" and pos[1] >= size[1]):
			newPos = (pos[0], pos[1] - size[1])
	
		if (newPos != None):
			newRenderedObject = self.__createNewObjectAndAddToScene(obj, newPos)
			ObjectDescriptor.Instance().setObject(newRenderedObject)
	
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
				if (self.__isCtrlPressed == False):
					ObjectDescriptor.Instance().setObject(selectedObject)
					RenderObjectGuardian.Instance().setSingleSelectionObject(selectedObject)
				else:
					RenderObjectGuardian.Instance().addMultiSelectionObject(selectedObject)

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

