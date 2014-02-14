from singleton import Singleton
from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout

from editorobjects import ObjectTypes, RenderedObject, RenderObjectGuardian
from optionsmenu import ObjectDescriptor

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
		
		sceneAttr = SceneAttributes.Instance()
		self.__tileSize = sceneAttr.getValue('TilesSize')
		sx = sceneAttr.getValue('TilesMaxX') * self.__tileSize
		sy = sceneAttr.getValue('TilesMaxY') * self.__tileSize

		self.__alignToGrid = True
		self.__layout = RelativeLayout(size=(sx, sy), size_hint = (None, None))
		
		self.__id = 0
		self.__objectDict = {}
		self.__maxX = sx
		self.__minX = 0.0
		self.__maxY = sy
		self.__minY = 0.0

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

		elif (direction == "right") and (pos[0] + size[0]*2 <= self.__maxX):
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
		renderedObject = RenderedObject(self.__id, obj, pos, self.__tileSize, self.__alignToGrid, 
			self.__maxX, self.__maxY)
		
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

			if (obj != None):
				ObjectDescriptor.Instance().setObject(obj)
				RenderObjectGuardian.Instance().setOperationObject(obj)

		self.__defaultTouchDown(touch)
	
	def __init__(self, rightScreen, maxWidthProportion = 1.0, maxHeightProportion = 0.667):
		
		self.__isShiftPressed = False
		self.__maxWidthProportion = maxWidthProportion
		self.__maxHeightProportion = maxHeightProportion
		
		self.__scrollView = ScrollView(scroll_timeout = 0, size_hint = (maxWidthProportion, maxHeightProportion))
		self.__scrollView.on_touch_move = self.__ignoreMoves
		self.__defaultTouchDown = self.__scrollView.on_touch_down
		self.__scrollView.on_touch_down = self.__handleScrollAndPassTouchesToChildren

		self.__scrollView.add_widget(Scene.Instance().getLayout())
		rightScreen.add_widget(self.__scrollView)
		
	def draw(self, obj):
		relativeX = self.__scrollView.hbar[0]
		relaviveY = self.__scrollView.vbar[0]
		Scene.Instance().addObject(obj, relativeX, relaviveY)

	def getLayout(self):
		return self.__scrollView

