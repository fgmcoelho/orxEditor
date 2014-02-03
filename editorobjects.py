from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from os import listdir, getcwd, sep as pathSeparator

class ObjectTypes:
	baseObject = 1
	renderedObject = 2

class BaseObject:

	def __init__(self, baseImage, identifier, virtualPath = None):
		self.__identifier = identifier
		self.__baseImage = baseImage
		if (virtualPath == None):
			self.__fullPath = baseImage.source
			self.__isSprite = False
		else:
			self.__fullPath = virtualPath
			self.__isSprite = True
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
		
		xBefore, yBefore = self.bbox[0]

		self.__defaultApplyTransform(trans, post_multiply, anchor)
		
		x, y = self.bbox[0]
		if (xBefore == x and yBefore == y):
			return

		if (x < 0):
			x = 0
		elif (x + self.__sx > self.__maxX):
			x = self.__maxX - self.__sx

		if (y < 0):
			y = 0
		elif (y + self.__sy > self.__maxY):
			y = self.__maxY - self.__sy

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

	def flipOnY(self):
		self.__flipY = not self.__flipY
		
		x, y = self.bbox[0]
		self.__flipVertical()
		self._set_pos((x,y))

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
		
		if (self.__alignToGrid == True and self.collide_point(*touch.pos) == True):
			self.alignToGrid()

		self.__defaultTouchUp(touch)

	def __handleTouchMove(self, touch):

		self.__defaultTouchMove(touch)

	def __init__(self, identifier, obj, pos, tileSize, alignToGrid, maxX, maxY, objectDescriptorRef):
		assert (isinstance(obj, BaseObject) or isinstance(obj, RenderedObject))
		assert (type(maxX) is int and type(maxY) is int)
		
		self.__id = identifier
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
		self.__objectType = ObjectTypes.renderedObject
		self.__alignToGrid = alignToGrid
		self.__tileSize = tileSize
		self.__maxX = maxX
		self.__maxY = maxY
		self.__path = path
		self._set_pos(pos)
		self.__objectDescriptorReference = objectDescriptorRef

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

