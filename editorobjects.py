from singleton import Singleton

from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from os import listdir, getcwd, sep as pathSeparator

from kivy.graphics.vertex_instructions import Line
from kivy.graphics import Color

@Singleton
class RenderObjectGuardian:
	def __init__(self):
		self.__maxLayer = 0
		self.__operationObject = None
		self.__moveStarted = False
		self.__startMovement = None
		self.__endMovement = None
		self.__multiSelectionObjects = []

	def startMovement(self, x, y):
		if (self.__moveStarted == False):
			self.__moveStarted = True
			self.__startMovement = (x, y)

	def endMovement(self):
		pass

	def isSelected(self, value):
		if (self.__operationObject != None):
			return value == self.__operationObject

		elif (self.__multiSelectionObjects != []):
			print "looking for object in multi selection: " + str( value in self.__multiSelectionObjects)
			return value in self.__multiSelectionObjects

		return False
	
	def setSingleSelectionObject(self, value):
		if (self.__multiSelectionObjects != []):
			self.__multiSelectionObjects = []

		self.__operationObject = value

	def addMultiSelectionObject(self, value):
		if (self.__operationObject != None):
			self.__operationObject = None

		if (value not in self.__multiSelectionObjects):
			self.__multiSelectionObjects.append(value)

	def getMaxLayer(self):
		return self.__maxLayer

	def setMaxLayer(self, value):
		self.__maxLayer = value

	def propagateTranslation(self, value, translation, post, anchor):
		for obj in self.__multiSelectionObjects:
			if (obj != value):
				obj.applyTranslation(translation, post, anchor)

class ObjectTypes:
	baseObject = 1
	renderedObject = 2

class SpritedObjectInfo:
	def __init__(self, virtualPath, coords):
		self.__virtualPath = virtualPath
		self.__spriteCoords = coords

	def getVirtualPath(self):
		return self.__virtualPath

	def getSpriteCoords(self):
		return self.__spriteCoords

class BaseObject:

	def __init__(self, baseImage, identifier, virtualPath = None, spriteCoords = None):
		self.__identifier = identifier
		self.__baseImage = baseImage
		if (virtualPath == None):
			self.__fullPath = baseImage.source
			self.__spriteInfo = None
		else:
			self.__fullPath = virtualPath
			self.__spriteInfo = SpritedObjectInfo(virtualPath, spriteCoords)

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

	def getSpriteInfo(self):
		return self.__spriteInfo

class RenderedObject (Scatter):

	def __checkAndTransform(self, trans, post_multiply=False, anchor=(0, 0)):
		
		if (RenderObjectGuardian.Instance().isSelected(self) == False):
			return

		RenderObjectGuardian.Instance().propagateTranslation(self, trans, post_multiply, anchor)

		xBefore, yBefore = self.bbox[0]

		self.__defaultApplyTransform(trans, post_multiply, anchor)
		
		x, y = self.bbox[0]
		if (xBefore == x and yBefore == y):
			return

		if (self.__isMoving == False):
			self.__movingStart = (xBefore, yBefore)
			self.__isMoving = True

		if (x < 0):
			x = 0
		elif (x + self.__sx > self.__maxX):
			x = self.__maxX - self.__sx

		if (y < 0):
			y = 0
		elif (y + self.__sy > self.__maxY):
			y = self.__maxY - self.__sy

		self._set_pos((int(x), int(y)))

	def applyTranslation(self, translation, post_multiply, anchor):
		self.__defaultApplyTransform(translation, post_multiply, anchor)

	def setMarked(self):
		#with self.image.canvas:
		#	Color(1., 0., 0.)
		#	sx, sy = self.getSize()
		#	x = Line(points = [0, 0, sx, 0, sx, sy, 0, sy, 0, 0])
		self.image.color[3] = 0.7

	def unsetMarked(self):
		#pass
		#self.image.canvas.clear()
		self.image.color[3] = 1.0

	def increaseScale(self):
		self.setScale (self.__scale + 0.25, True)
	
	def decreaseScale(self):
		self.setScale (self.__scale - 0.25, True)

	def setScale(self, newScale, preservePos = False):
		if (newScale == 0.0):
			return
		
		if (preservePos == True):
			oldPos = self.bbox[0]
		
		self.__scale = newScale
		self.scale = self.__scale
		self.__sx, self.__sy = self.bbox[1]

		if (preservePos == True):
			self._set_pos(oldPos)

	def setCollisionInfo(self, value):
		self.__collisionInfo = value

	def __flipVertical(self):
		newTexture = self.image.texture
		newTexture.flip_vertical()
		sizeToUse = self.image.size
		self.remove_widget(self.image)
		self.image = Image(texture = newTexture, size = (sizeToUse))
		self.add_widget(self.image)

	def __flipHorizontal(self):
		newTexture = self.image.texture
		uvx, uvy = newTexture.uvpos
		uvw, uvh = newTexture.uvsize
		uvx += uvw
		uvw = -uvw
		newTexture.uvpos = (uvx, uvy)
		newTexture.uvsize = (uvw, uvh)
		sizeToUse = self.image.size
		self.remove_widget(self.image)
		self.image = Image(texture = newTexture, size = (sizeToUse))
		self.add_widget(self.image)

	def flipOnX(self):
		self.__flipX = not self.__flipX
	
		x, y = self.bbox[0]
		self.__flipHorizontal()
		self._set_pos((x,y))

	def increaseLayer(self):
		self.__layer += 1

	def decreaseLayer(self):
		self.__layer -= 1

	def flipOnY(self):
		self.__flipY = not self.__flipY
		
		x, y = self.bbox[0]
		self.__flipVertical()
		self._set_pos((x,y))

	def move(self, x, y):
		self._set_pos((x, y))

	def alignToGrid(self):
		x, y = self.bbox[0]
		distX = x % self.__tileSize
		if (distX != 0):
			if (distX < self.__tileSize/2):
				x -= x % self.__tileSize
			else:
				x += self.__tileSize - (x % self.__tileSize)
		
		distY = y % self.__tileSize
		if (distY != 0):
			if (distY < self.__tileSize/2):
				y -= y % self.__tileSize
			else:
				y += self.__tileSize - (y % self.__tileSize)

		tries = 0
		while (self.getPos() != (x, y) and tries < 3):
			if (tries != 0):
				print self.getPos()
				print ((x,y))
			self._set_pos((x, y))
			tries += 1
		
		if (self.__isMoving == True):
			self.__isMoving = False
			self.__movingStart = None

	def __handleTouchDown(self, touch):

		self.__defaultTouchDown(touch)

	def __handleTouchUp(self, touch):
		self.__defaultTouchUp(touch)

	def __handleTouchMove(self, touch):

		self.__defaultTouchMove(touch)

	def __init__(self, identifier, obj, pos, tileSize, maxX, maxY):
		assert (isinstance(obj, BaseObject) or isinstance(obj, RenderedObject))
		assert (type(maxX) is int and type(maxY) is int)
		
		self.__markLine = None
		self.__id = identifier
		self.__spriteInfo = obj.getSpriteInfo()
		path = obj.getPath()

		sepIndex = path.rfind(pathSeparator)
		if (sepIndex != -1):
			self.__name = path[sepIndex+1:-4] + '_' + str(self.__id)
		else:
			self.__name = path[0:-4] + '_' + str(self.__id)

		if (isinstance(obj, BaseObject)):
			self.__baseSize = obj.getSize()
			self.image = Image(size = self.__baseSize, texture = obj.getBaseImage().texture)
			self.__sx = self.__baseSize[0]
			self.__sy = self.__baseSize[1]
			self.__scale = 1.0
			self.__layer = 1
			self.__flipX = False
			self.__flipY = False
			self.__collisionInfo = None

		else:
			self.__baseSize = obj.getBaseSize()
			self.__sx, self.__sy = obj.getSize()
			self.image = Image(size = (self.__sx, self.__sy), texture = obj.getImage().texture)
			self.__scale = obj.getScale()
			self.__layer = obj.getLayer()
			self.__flipX = obj.getFlipX()
			self.__flipY = obj.getFlipY()
			self.__collisionInfo = obj.getCollisionInfo()
		
		super(RenderedObject, self).__init__(do_rotation = False, do_scale = False, size_hint = (None, None), 
			size = self.__baseSize, auto_bring_to_front = False)


		self.add_widget(self.image)
		self.__isMoving = False
		self.__movingStart = None
		self.__objectType = ObjectTypes.renderedObject
		self.__tileSize = tileSize
		self.__maxX = maxX
		self.__maxY = maxY
		self.__path = path
		self._set_pos(pos)

		self.__defaultTouchDown = self.on_touch_down
		self.on_touch_down = self.__handleTouchDown
		self.__defaultTouchUp = self.on_touch_up
		self.on_touch_up = self.__handleTouchUp
		self.__defaultApplyTransform = self.apply_transform
		self.apply_transform = self.__checkAndTransform
		self.__defaultTouchMove = self.on_touch_move
		self.on_touch_move = self.__handleTouchMove

	def resetAllWidgets(self):
		self.remove_widget(self.image)

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
	
	def getName(self):
		return self.__name
	
	def getCollisionInfo(self):
		return self.__collisionInfo

	def getImage(self):
		return self.image

	def getSpriteInfo(self):
		return self.__spriteInfo

