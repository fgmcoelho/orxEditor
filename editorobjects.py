from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.graphics.vertex_instructions import Line
from kivy.graphics import Color

from os import sep as pathSeparator
from time import time

from collision import CollisionInformation
from editorutils import AutoReloadTexture
from editorheritage import SpaceLimitedObject

scatterTime = 0
imageTime = 0
posTime = 0

class SceneAction:
	def __init__(self, action, objectsList, args = []):
		assert (type(objectsList) is list)
		assert ((len (args) == 0) or (len(args) == len (objectsList)))

		self.__objectsList = objectsList[:]
		self.__undoList = []
		self.__redoList = []
		self.__actionArgs = args[:]
		self.__name = action

		if (action == "increaseScale"):
			for obj in self.__objectsList:
				self.__undoList.append(obj.decreaseScale)
				self.__redoList.append(obj.increaseScale)

		elif (action == "decreaseScale"):
			for obj in self.__objectsList:
				self.__undoList.append(obj.increaseScale)
				self.__redoList.append(obj.decreaseScale)

		elif (action == "flipOnX"):
			for obj in self.__objectsList:
				self.__undoList.append(obj.flipOnX)
				self.__redoList.append(obj.flipOnX)

		elif (action == "flipOnY"):
			for obj in self.__objectsList:
				self.__undoList.append(obj.flipOnY)
				self.__redoList.append(obj.flipOnY)

		elif (action == "copySelection"):
			for obj in self.__objectsList:
				self.__undoList.append(obj.hide)
				self.__redoList.append(obj.show)

		elif (action == "move"):
			for obj in self.__objectsList:
				self.__undoList.append(obj.moveAbsoluteReverse)
				self.__redoList.append(obj.moveAbsolute)

		elif (action == "delete"):
			for obj in self.__objectsList:
				self.__undoList.append(obj.show)
				self.__redoList.append(obj.hide)

		elif (action == "create"):
			for obj in self.__objectsList:
				self.__undoList.append(obj.hide)
				self.__redoList.append(obj.show)

	def redo(self):
		i = 0
		for method in self.__redoList:
			if (self.__actionArgs == []):
				method()
			else:
				method(self.__actionArgs[i])
				i += 1

	def undo(self):
		i = 0
		for method in self.__undoList:
			if (self.__actionArgs == []):
				method()
			else:
				method(self.__actionArgs[i])
				i += 1

	def getName(self):
		return self.__name

	def clear(self):
		for obj in self.__objectsList:
			if (obj.getHidden() == True):
				obj.finish()

class SceneActionHistory:
	def __init__(self):
		self.__transaction = 0
		self.__historyList = []
		self.__redoList = []

	def __clearRedoList(self):
		for action in self.__redoList:
			action.clear()

		self.__redoList = []

	def registerAction(self, action):
		assert(isinstance(action, SceneAction))
		self.__historyList.append(action)
		if (self.__redoList != []):
			self.__clearRedoList()
		self.__transaction += 1

	def undo(self):
		if (self.__historyList != []):
			action = self.__historyList.pop()
			action.undo()
			self.__redoList.append(action)
			self.__transaction += 1

	def redo(self):
		if (self.__redoList != []):
			action = self.__redoList.pop()
			action.redo()
			self.__historyList.append(action)
			self.__transaction += 1

	def getTransaction(self):
		return self.__transaction

class RenderObjectGuardian:
	def __addObjectToLimits(self, obj):
		if (self.__objectLimits == []):
			self.__objectLimits = [obj, obj, obj, obj]
		else:
			pos = obj.getPos()
			size = obj.getSize()

			if (pos[0] < self.__objectLimits[0].getPos()[0]):
				self.__objectLimits[0] = obj
			if (pos[1] < self.__objectLimits[1].getPos()[1]):
				self.__objectLimits[1] = obj
			if (pos[0] + size[0] > self.__objectLimits[2].getPos()[0] + self.__objectLimits[2].getSize()[0]):
				self.__objectLimits[2] = obj
			if (pos[1] + size[1] > self.__objectLimits[3].getPos()[1] + self.__objectLimits[3].getSize()[1]):
				self.__objectLimits[3] = obj

	def __updateSelectionLimits(self):
		first = True
		cur = None
		for obj in self.__multiSelectionObjects:
			if (first == True):
				pos = obj.getPos()
				size = obj.getSize()
				cur = [pos[0], pos[1], pos[0] + size[0], pos[1] + size[1]]
				self.__objectLimits = [obj, obj, obj, obj]
				first = False
			else:
				pos = obj.getPos()
				size = obj.getSize()
				if (pos[0] < cur[0]):
					cur[0] = pos[0]
					self.__objectLimits[0] = obj
				if (pos[1] < cur[1]):
					cur[1] = pos[1]
					self.__objectLimits[1] = obj
				if (pos[0] + size[0] > cur[2]):
					cur[2] = pos[0] + size[0]
					self.__objectLimits[2] = obj
				if (pos[1] + size[1] > cur[3]):
					cur[3] = pos[1] + size[1]
					self.__objectLimits[3] = obj

	def __getSelectionLimits(self):
		return (
			self.__objectLimits[0].getPos()[0],
			self.__objectLimits[1].getPos()[1],
			self.__objectLimits[2].getPos()[0] + self.__objectLimits[2].getSize()[0],
			self.__objectLimits[3].getPos()[1] + self.__objectLimits[3].getSize()[1]
		)

	def __reviewSelection(self):
		newSelection = []
		updateSelection = False
		for obj in self.__multiSelectionObjects:
			if (obj.getHidden() == False):
				newSelection.append(obj)
				if (updateSelection == False and obj in self.__objectLimits):
					updateSelection = True

		if (updateSelection == True):
			self.__updateSelectionLimits()

		self.__multiSelectionObjects = newSelection

	def __init__(self):
		self.__maxLayer = 0
		self.__moveStarted = False
		self.__movePositions = []
		self.__multiSelectionObjects = []
		self.__objectLimits = []
		self.__history = SceneActionHistory()

	def undo(self):
		self.__history.undo()
		self.__reviewSelection()

	def redo(self):
		self.__history.redo()
		self.__reviewSelection()

	def getTransaction(self):
		return self.__history.getTransaction()

	def endMovement(self):
		if (self.__moveStarted == True):
			t = time()
			if (self.__movePositions != [] and self.__multiSelectionObjects != []):
				start = self.__movePositions[0]
				end = self.__multiSelectionObjects[0].getPos()
				amountMovedList = []
				x = end[0] - start[0]
				y = end[1] - start[1]
				if (x == 0 and y == 0):
					# Movement was started, but the final position kept the same.
					self.__moveStarted = False
					return

				for obj in self.__multiSelectionObjects:
					amountMovedList.append((x, y))

				action = SceneAction("move", self.__multiSelectionObjects, amountMovedList)
				self.__history.registerAction(action)

			self.__moveStarted = False
			print "Finishing movement: ", time() - t

	def isSelected(self, value):
		if (self.__multiSelectionObjects != []):
			return value in self.__multiSelectionObjects

		return False

	def addObjectToSelection(self, value):
		print value.getHidden()
		if (value.getHidden() == True):
			return self.__multiSelectionObjects

		selectionSet = set(self.__multiSelectionObjects)
		if (value not in selectionSet):
			parent = value.getParent()
			if (parent is None):
				parent = value

			self.__multiSelectionObjects.append(parent)
			self.__addObjectToLimits(parent)

			selectionSet.add(parent)
			parent.setMarked()

			for obj in parent.getChildren():
				currentLen = len(selectionSet)
				selectionSet.add(obj)
				if (len(selectionSet) != currentLen):
					self.__multiSelectionObjects.append(obj)
					obj.setMarked()
					# TODO: It is probably smarter to add the children in the limits function, as
					# it can cache values
					self.__addObjectToLimits(obj)

		return self.__multiSelectionObjects

	def propagateTranslation(self, callingObject, translation, post, anchor):
		if (len(self.__multiSelectionObjects) == 1):
			return

		if (self.__moveStarted == False):
			self.__movePositions = []
			for obj in self.__multiSelectionObjects:
				self.__movePositions.append(obj.getPos())

			self.__moveStarted = True

		limitObjects = set(self.__objectLimits)

		res = True
		for obj in limitObjects:
			if (obj != callingObject):
				res &= obj.applyTranslationStart(translation, post, anchor)

		if (res == False):
			inverseTranslation = translation.inverse()
			for obj in limitObjects:
				obj.applyPureTransform(inverseTranslation, post, anchor)
			if callingObject not in limitObjects:
				callingObject.applyPureTransform(inverseTranslation, post, anchor)
		else:
			for obj in self.__multiSelectionObjects:
				if (obj not in limitObjects and obj != callingObject):
					obj.applyPureTransform(translation, post, anchor)

	def deleteSelection(self):
		deletedObjects = self.__multiSelectionObjects[:]
		self.__multiSelectionObjects = []
		self.__objectLimits = []
		for obj in deletedObjects:
			obj.hide()

		action = SceneAction("delete", deletedObjects)
		self.__history.registerAction(action)

		return deletedObjects

	def increaseScale(self):
		if len(self.__multiSelectionObjects) == 1:
			self.__multiSelectionObjects[0].increaseScale()

			action = SceneAction("increaseScale", [ self.__multiSelectionObjects[0] ] )
			self.__history.registerAction(action)

			return self.__multiSelectionObjects[0]

		return None

	def decreaseScale(self):
		if len(self.__multiSelectionObjects) == 1:
			self.__multiSelectionObjects[0].decreaseScale()

			action = SceneAction("decreaseScale", [ self.__multiSelectionObjects[0] ] )
			self.__history.registerAction(action)

			return self.__multiSelectionObjects[0]

		return None

	def flipSelectionOnX(self):
		tempSelection = self.__multiSelectionObjects[:]
		for obj in tempSelection:
			self.__multiSelectionObjects = [ obj ]
			obj.flipOnX()

		self.__multiSelectionObjects = tempSelection

		action = SceneAction("flipOnX", self.__multiSelectionObjects)
		self.__history.registerAction(action)

		return self.__multiSelectionObjects

	def flipSelectionOnY(self):
		tempSelection = self.__multiSelectionObjects[:]
		for obj in tempSelection:
			self.__multiSelectionObjects = [ obj ]
			obj.flipOnY()

		self.__multiSelectionObjects = tempSelection

		action = SceneAction("flipOnY", self.__multiSelectionObjects)
		self.__history.registerAction(action)

		return self.__multiSelectionObjects

	def alignSelectionToGrid(self):
		# By default every translation one object in the multiple selection is
		# propagated to the others. So we need to clean the list to alighn each
		# object properly.
		# We also need to force and end movement to be sure action won't get
		# lost.
		if (self.__multiSelectionObjects != []):
			self.endMovement()

			initialSelection = self.__multiSelectionObjects[:]
			tempSelection = []
			for obj in self.__multiSelectionObjects:
				if (obj.getParent() is None):
					tempSelection.append(obj)

			movementDoneList = []
			orderedObjects = []
			allZero = True
			for obj in tempSelection:
				oldPosList = [obj.getPos()]
				self.__multiSelectionObjects = [ obj ]
				for childObj in obj.getChildren():
					oldPosList.append(childObj.getPos())
					self.__multiSelectionObjects.append(childObj)

				# Aligning this object will move all its children by the same amount
				obj.alignToGrid()

				i = 0
				for obj in self.__multiSelectionObjects:
					orderedObjects.append(obj)
					sx, sy = oldPosList[i]
					fx, fy = obj.getPos()
					movementDoneList.append((fx - sx, fy - sy))
					if (fx - sx != 0 or fy - sy != 0):
						allZero = False
					i += 1

			if (allZero == False):
				action = SceneAction("move", orderedObjects, movementDoneList)
				self.__history.registerAction(action)

			self.__moveStarted = False
			self.__multiSelectionObjects = initialSelection
			self.__updateSelectionLimits()

	def setSingleSelectionObject(self, value):
		self.unsetSelection()
		parent = value.getParent()
		if (parent is None):
			parent = value

		self.__multiSelectionObjects.append(parent)
		parent.setMarked()
		for obj in parent.getChildren():
			obj.setMarked()
			self.__multiSelectionObjects.append(obj)

		self.__updateSelectionLimits()
		return self.__multiSelectionObjects

	def unselectObject(self, value):
		selectionSet = set(self.__multiSelectionObjects)
		if (value in selectionSet):
			updateSelection = False
			parent = value.getParent()
			if (parent is None):
				parent = value

			childrenAndParentSet = set(parent.getChildren())
			childrenAndParentSet.add(parent)
			newSelection = []
			for obj in self.__multiSelectionObjects:
				if (obj not in childrenAndParentSet):
					newSelection.append(obj)
			self.__multiSelectionObjects = newSelection
			for obj in childrenAndParentSet:
				obj.unsetMarked()
				if (updateSelection == False and obj in self.__objectLimits):
					updateSelection = True

			if (updateSelection == True):
				self.__updateSelectionLimits()

		return self.__multiSelectionObjects

	def unsetSelection(self):
		if (self.__multiSelectionObjects != []):
			for obj in self.__multiSelectionObjects:
				obj.unsetMarked()
			self.__multiSelectionObjects = []
			self.__objectLimits = []

	def copySelection(self, direction, newId, tileSize, maxX, maxY):
		tot = time()
		assert (direction in ['left', 'right', 'up', 'down'])

		if (self.__multiSelectionObjects == []):
			return []

		startX, startY, endX, endY = self.__getSelectionLimits()

		if (direction == 'left'):
			xAdjust = (startX - endX)
			yAdjust = 0

		elif (direction == 'right'):
			xAdjust = -(startX - endX)
			yAdjust = 0

		elif (direction == 'up'):
			xAdjust = 0
			yAdjust = -(startY - endY)

		elif (direction == 'down'):
			xAdjust = 0
			yAdjust = (startY - endY)

		# First we need to check if we have enough size to copy the whole selection:
		global scatterTime
		scatterTime = 0
		global imageTime
		imageTime = 0
		global posTime
		posTime = 0

		t = time()
		for obj in self.__multiSelectionObjects:
			pos = obj.getPos()
			newPos = (pos[0] + xAdjust, pos[1] + yAdjust)
			size = obj.getSize()

			if (not (newPos[0] >= 0 and newPos[1] >= 0 and newPos[0] <= maxX and newPos[1] <= maxY
					and newPos[0] + size[0] <= maxX and newPos[1] + size[1] <= maxY)):
				return []

		print "Checking limits took: ", time() - t

		t = time()
		objectsToCreate = []
		for obj in self.__multiSelectionObjects:
			if (obj.getParent() is None):
				objectsToCreate.append(obj)
		print "Checking parents took: ", time() - t

		t = time()
		newSelection = []
		for obj in objectsToCreate:
			pos = obj.getPos()
			newPos = (pos[0] + xAdjust, pos[1] + yAdjust)
			size = obj.getSize()
			newObj = RenderedObject(newId, obj, newPos, tileSize, maxX, maxY, self)
			newId += 1
			newSelection.append(newObj)
			for childObj in obj.getChildren():
				pos = childObj.getPos()
				newPos = (pos[0] + xAdjust, pos[1] + yAdjust)
				size = childObj.getSize()
				newChildObj = RenderedObject(newId, childObj, newPos, tileSize, maxX, maxY, self)
				newObj.addChild(newChildObj)
				newId += 1
				newSelection.append(newChildObj)
		print "Creating children took: ", time() - t
		print "Scatter time: ", scatterTime, " Image time: ", imageTime, "Pos time: ", posTime

		t = time()
		if (newSelection != []):
			for obj in self.__multiSelectionObjects:
				obj.unsetMarked()

			for obj in newSelection:
				obj.setMarked()

			self.__multiSelectionObjects = newSelection
			self.__updateSelectionLimits()
			action = SceneAction("copySelection", newSelection)
			self.__history.registerAction(action)
		print "Selecting new objecs took: ", time() - t
		print "Total time: ", time() - tot
		print "-----------------------------------------------------"

		return newSelection

	def getSelection(self):
		return self.__multiSelectionObjects[:]

	def createNewObject(self, idToUse, obj, pos, tileSize, maxX, maxY, autoSelect = True):
		renderedObject = RenderedObject(idToUse, obj, pos, tileSize, maxX, maxY, self)
		if (autoSelect == True):
			self.setSingleSelectionObject(renderedObject)

		action = SceneAction("create", [renderedObject])
		self.__history.registerAction(action)

		return renderedObject

	def mergeObjects(self):
		if (len(self.__multiSelectionObjects) >= 2):
			parentObjects = []
			for obj in self.__multiSelectionObjects:
				if (obj.getParent() is None and len(obj.getChildren()) > 0):
					parentObjects.append(obj)

			numberOfParents = len(parentObjects)
			if (numberOfParents == 0):
				parent = self.__multiSelectionObjects[0]
			elif (numberOfParents == 1):
				parent = parentObjects[0]
			else:
				numberOfChildren = 0
				for obj in parentObjects:
					if (numberOfChildren < len(obj.getChildren())):
						numberOfChildren = len(obj.getChildren())
						parent = obj

				for obj in parentObjects:
					obj.resetChildren()

			for obj in self.__multiSelectionObjects:
				if (obj != parent and obj.getParent() is not parent):
					parent.addChild(obj)

class SpritedObjectInfo:
	def __init__(self, virtualPath, coords, spriteSize):
		self.__virtualPath = virtualPath
		self.__spriteCoords = coords
		self.__spriteSize = spriteSize

	def getVirtualPath(self):
		return self.__virtualPath

	def getSpriteCoords(self):
		return self.__spriteCoords

	def getSpriteSize(self):
		return self.__spriteSize

class BaseObject:
	def getCachedSprite(self):
		if (self.__cachedSprite is None):
			self.__cachedSprite = AutoReloadTexture(self.getSize(), self.getBaseImage())
		return self.__cachedSprite.getTexture()

	def __init__(self, baseImage, identifier, virtualPath = None, spriteCoords = None, spriteSize = None):
		assert (virtualPath is None and spriteCoords is None and spriteSize is None) or \
			(virtualPath is not None and spriteCoords is not None and spriteSize is not None), \
			"Invalid attributes received, information for sprite info must be all None or all filled."

		self.__identifier = identifier
		self.__baseImage = baseImage
		if (virtualPath is None):
			self.__fullPath = baseImage.source
			self.__spriteInfo = None
		else:
			self.__fullPath = virtualPath
			self.__spriteInfo = SpritedObjectInfo(virtualPath, spriteCoords, spriteSize)

		self.__size = baseImage.texture.size
		self.__cachedSprite = None

	def getIdentifier(self):
		return self.__identifier

	def getSize(self):
		return self.__size

	def getPath(self):
		return self.__fullPath

	def getBaseImage(self):
		return self.__baseImage

	def getSpriteInfo(self):
		return self.__spriteInfo

class RenderedObject (Scatter, SpaceLimitedObject):
	def __checkAndTransform(self, trans, post_multiply=False, anchor=(0, 0)):
		if (self.__forceMove == False and self.__renderGuardian.isSelected(self) == False):
			return

		if (self.__forceMove == False):
			self.__renderGuardian.propagateTranslation(self, trans, post_multiply, anchor)

		xBefore, yBefore = self.bbox[0]
		self.__defaultApplyTransform(trans, post_multiply, anchor)
		x, y = self.bbox[0]
		if (xBefore == x and yBefore == y):
			return

		self._set_pos(self.ajustPositionByLimits(x, y, self.__sx, self.__sy, self.__maxX, self.__maxY))

	def applyTranslationStart(self, translation, post_multiply, anchor):
		self.__defaultApplyTransform(translation, post_multiply, anchor)
		x, y = self.bbox[0]
		if ((x < 0) or (x + self.__sx > self.__maxX) or (y < 0) or (y + self.__sy > self.__maxY)):
			return False

		return True

	def applyPureTransform(self, translation, post_multiply, anchor):
		self.__defaultApplyTransform(translation, post_multiply, anchor)

	def setMarked(self):
		if (self.__borderLine is None):
			with self.image.canvas:
				Color(1., 0., 0.)
				sx, sy = self.size
				self.__borderLine = Line(points = [0, 0, sx, 0, sx, sy, 0, sy, 0, 0])

	def unsetMarked(self):
		if (self.__borderLine is not None):
			self.image.canvas.remove(self.__borderLine)
			self.__borderLine = None

	def increaseScale(self):
		self.__forceMove = True
		self.setScale (self.__scale + 0.25, True)
		self.__forceMove = False

	def decreaseScale(self):
		self.__forceMove = True
		self.setScale (self.__scale - 0.25, True)
		self.__forceMove = False

	def setMerged(self, value):
		self.__merged = value

	def setScale(self, newScale, preservePos = False):
		if (newScale == 0.0):
			return

		newLimitX = (self.__baseSize[0] * newScale) + self.bbox[0][0]
		newLimitY = (self.__baseSize[1] * newScale) - self.bbox[0][1]
		if (newLimitX > self.__maxX or newLimitY > self.__maxY):
			return

		if (preservePos == True):
			oldPos = self.bbox[0]

		mustRemark = False
		if (self.__borderLine is not None):
			self.unsetMarked()
			mustRemark = True

		self.__scale = newScale
		self.scale = self.__scale
		self.__sx, self.__sy = self.bbox[1]

		if (preservePos == True):
			self._set_pos(oldPos)

		if (mustRemark == True):
			self.setMarked()

	def setCollisionInfo(self, value):
		self.__collisionInfo = value

	def __flipVertical(self):
		mustRemark = False
		if (self.__borderLine is not None):
			self.unsetMarked()
			mustRemark = True

		sizeToUse = self.image.size
		newTexture = self.image.texture
		newTexture.flip_vertical()
		self.remove_widget(self.image)
		self.image = Image(texture = newTexture, size = (sizeToUse), nocache = True)
		self.add_widget(self.image)

		if (mustRemark == True):
			self.setMarked()

	def __flipHorizontal(self):
		mustRemark = False
		if (self.__borderLine is not None):
			self.unsetMarked()
			mustRemark = True

		newTexture = self.image.texture
		uvx, uvy = newTexture.uvpos
		uvw, uvh = newTexture.uvsize
		uvx += uvw
		uvw = -uvw
		newTexture.uvpos = (uvx, uvy)
		newTexture.uvsize = (uvw, uvh)
		sizeToUse = self.image.size
		self.remove_widget(self.image)
		self.image = Image(texture = newTexture, size = (sizeToUse), nocache = True)
		self.add_widget(self.image)

		if (mustRemark == True):
			self.setMarked()

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

		self._set_pos((x, y))

	def __handleTouchDown(self, touch):
		print "Touch down Event on child.", touch.pos
		self.__defaultTouchDown(touch)

	def __handleTouchUp(self, touch):
		print "Touch up Event on child."
		self.__renderGuardian.endMovement()

		self.__defaultTouchUp(touch)

	def __handleTouchMove(self, touch):
		print "Touch move Event on child."
		self.__defaultTouchMove(touch)

	def __init__(self, identifier, obj, pos, tileSize, maxX, maxY, guardianToUse):
		assert (isinstance(obj, BaseObject) or isinstance(obj, RenderedObject))
		assert (type(maxX) is int and type(maxY) is int)
		global imageTime
		global scatterTime
		global posTime

		self.__id = identifier
		self.__spriteInfo = obj.getSpriteInfo()
		path = obj.getPath()

		#TODO: Find why this is not working on Windows.
		sepIndex = path.rfind(pathSeparator)
		if (sepIndex != -1):
			self.__name = path[sepIndex+1:-4] + '_' + str(self.__id)
		else:
			sepIndex = path.rfind('/')
			if (sepIndex != -1):
				self.__name = path[sepIndex+1:-4] + '_' + str(self.__id)
			else:
				self.__name = path[0:-4] + '_' + str(self.__id)

		if (isinstance(obj, BaseObject)):
			self.__baseSize = obj.getSize()
			self.__texture = obj.getCachedSprite()
			self.image = Image(size = self.__baseSize, texture = self.__texture)
			self.__sx = self.__baseSize[0]
			self.__sy = self.__baseSize[1]
			self.__scale = 1.0
			self.__layer = 'default'
			self.__collisionInfo = None

		else:
			t = time()
			self.__baseSize = obj.getBaseSize()
			self.__sx, self.__sy = obj.getSize()
			self.__texture = obj.getTexture()
			self.image = Image(size = self.__baseSize, texture = self.__texture)
			self.__layer = obj.getLayer()
			if (obj.getCollisionInfo() is None):
				self.__collisionInfo = None
			else:
				self.__collisionInfo = CollisionInformation.copy(obj.getCollisionInfo())

			imageTime += time() - t

		t = time()
		super(RenderedObject, self).__init__(do_rotation = False, do_scale = False, size_hint = (None, None),
			size = self.__baseSize, auto_bring_to_front = False)
		self.add_widget(self.image)
		scatterTime += time() - t

		t = time()
		self.__children = []
		self.__parent = None
		self.__merged = False
		self.__renderGuardian = guardianToUse
		self.__isFinished = False
		self.__isHidden = False
		self.__forceMove = False
		self.__borderLine = None
		self.__flipX = False
		self.__flipY = False

		self.__tileSize = tileSize
		self.__maxX = maxX
		self.__maxY = maxY
		self.__path = path
		self._set_pos(pos)
		if (isinstance(obj, RenderedObject) == True):
			self.setScale(obj.getScale(), True)
			if (obj.getFlipX() == True):
				self.flipOnX()
			if (obj.getFlipY() == True):
				self.flipOnY()

		self.__defaultTouchDown = self.on_touch_down
		self.on_touch_down = self.__handleTouchDown
		self.__defaultTouchUp = self.on_touch_up
		self.on_touch_up = self.__handleTouchUp
		self.__defaultTouchMove = self.on_touch_move
		self.on_touch_move = self.__handleTouchMove

		self.__defaultApplyTransform = self.apply_transform
		self.apply_transform = self.__checkAndTransform
		posTime += time() - t

	def hide(self):
		self.unsetMarked()
		self.remove_widget(self.image)
		self.__isHidden = True

	def show(self):
		self.add_widget(self.image)
		self.__isHidden = False

	def resetAllWidgets(self):
		self.remove_widget(self.image)

	def moveAbsoluteReverse(self, amount):
		self.moveAbsolute((-amount[0], -amount[1]))

	def moveAbsolute(self, amount):
		self.__forceMove = True
		pos = self.getPos()
		self._set_pos((pos[0] + amount[0], pos[1] + amount[1]))
		self.__forceMove = False

	def addChild(self, child):
		child.setParent(self)
		self.__children.append(child)

	def resetChildren(self):
		for obj in self.__children:
			obj.setParent(None)
		self.__children = []

	def getLimits(self):
		pos = self.getPos()
		size = self.getSize()
		l = [pos, (pos[0] + size[0], pos[1] + size[1])]
		for childObj in self.__children:
			pos = childObj.getPos()
			size = childObj.getSize()
			l.append(pos)
			l.append((pos[0] + size[0], pos[1] + size[1]))

		maxX, maxY = map(max, zip(*l))
		minX, minY = map(min, zip(*l))
		return (minX, minY, maxX, maxY)

	def setParent(self, value):
		self.__parent = value

	def getParent(self):
		return self.__parent

	def getChildren(self):
		return self.__children

	def getIdentifier(self):
		return self.__id

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

	def setLayer(self, newName):
		self.__layer = newName

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

	def getMerged(self):
		return self.__merged

	def finish(self):
		self.__isFinished = True

	def getHidden(self):
		return self.__isHidden

	def getFinished(self):
		return self.__isFinished

	def getTexture(self):
		return self.__texture
