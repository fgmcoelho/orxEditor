from kivy.uix.popup import Popup
from kivy.uix.scatter import Scatter
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.graphics.vertex_instructions import Mesh, Line
from kivy.graphics import Color
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

from math import ceil

from editorutils import CancelableButton, vector2Multiply, distance, isConvexPolygon, Alert, AlignedLabel, \
	EmptyScrollEffect, ChangesConfirm
from editorheritage import SpaceLimitedObject, LayoutGetter, MouseModifiers, KeyboardModifiers
from collisioninfo import CollisionPartInformation
from keyboard import KeyboardAccess, KeyboardGuardian
from modulesaccess import ModulesAccess
from uisizes import defaultDoubleLineSize, defaultSmallButtonSize

class CollisionFormScatterCache:
	def clearCache(self):
		self.__cacheDict = {}

	def getFromCache(self, obj):
		if (obj.getIdentifier() in self.__cacheDict):
			return self.__cacheDict[obj.getIdentifier()]
		else:
			return None

	def addToCache(self, obj, scatter):
		assert obj.getIdentifier() not in self.__cacheDict, "Inserted element that is already on cache!"
		self.__cacheDict[obj.getIdentifier()] = scatter

	def __init__(self):
		self.__cacheDict = {}
		ModulesAccess.add("CollisionFormCache", self)

class CollisionPartDisplay(RelativeLayout):
	def __drawObjectTexture(self, obj, considerChildren):
		im = Image(texture = obj.getTexture(), size = obj.getBaseSize(), allow_strech = True)
		minX, minY, maxX, maxY = self.__limits
		if (considerChildren == True):
			objPos = obj.getPos()
		else:
			objPos = (0, 0)
		im.pos = ((objPos[0] - minX), (objPos[1] - minY))
		self.__image.add_widget(im)

	def __init__(self, obj, expandLevel = 1.0):
		if (obj is None):
			return

		if (obj.getChildren() == []):
			self.__originalSize = vector2Multiply(obj.getBaseSize(), expandLevel)
			self.__limits = (0, 0, obj.getBaseSize()[0], obj.getBaseSize()[1])
		else:
			self.__limits = obj.getLimits()
			minX, minY, maxX, maxY = self.__limits
			self.__originalSize = vector2Multiply((maxX - minX, maxY - minY), expandLevel)

		super(CollisionPartDisplay, self).__init__(size_hint = (None, None), size = self.__originalSize)
		if (expandLevel == 1.0):
			self.__originalPos = (0, 0)
		else:
			self.__originalPos = (self.size[0]/(expandLevel * 2.), self.size[1]/(expandLevel * 2.))

		minX, minY, maxX, maxY = self.__limits
		self.__image = ModulesAccess.get("CollisionFormCache").getFromCache(obj)
		if (self.__image is None):
			self.__image = Scatter(do_translation = False, do_rotation = False, do_scale = False,
				size = (maxX - minX, maxY - minY))
			if (obj.getChildren() == []):
				self.__drawObjectTexture(obj, False)
			else:
				self.__drawObjectTexture(obj, True)

			for childObj in obj.getChildren():
				self.__drawObjectTexture(childObj, True)

			ModulesAccess.get("CollisionFormCache").addToCache(obj, self.__image)

		else:
			self.__image.scale = 1
			if self.__image.parent is not None:
				self.__image.parent.remove_widget(self.__image)

		self.__image.pos = self.__originalPos
		self.__operation = None
		self.__expandLevel = expandLevel
		self.add_widget(self.__image)
		self.__zoom = 1

	def clearDrawnForm(self):
		if (self.__operation != None):
			self.canvas.remove(self.__operation)
			self.__operation = None

	def __drawDefaultBox(self):
		self.clearDrawnForm()

		with self.canvas:
			Color(0., 1.0, .0, 0.3)
			minX, minY, maxX, maxY = self.__limits
			imgPos = self.__originalPos
			imgSize = (maxX - minX, maxY - minY)
			self.__operation = Line(
				points = [
					imgPos[0], imgPos[1],
					imgPos[0], imgPos[1] + imgSize[1],
					imgPos[0] + imgSize[0], imgPos[1] + imgSize[1],
					imgPos[0] + imgSize[0], imgPos[1]
				],
				close = True
			)

	def __drawDefinedBox(self, points):
		self.clearDrawnForm()
		fx, fy = points[0]
		sx, sy = points[1]
		with self.canvas:
			Color(0., 1.0, .0, 0.3)
			self.__operation = Line(
				points = [
					fx, fy,
					fx, sy,
					sx, sy,
					sx, fy,
				],
				close = True
			)

	def __drawDefaultSphere(self):
		self.clearDrawnForm()

		minX, minY, maxX, maxY = self.__limits
		imgPos = self.__originalPos
		imgSize = (maxX - minX, maxY - minY)
		with self.canvas:
			Color(0., 1.0, .0, 0.3)
			self.__operation = Line(
				circle = (
					imgPos[0] + imgSize[0]/2.,
					imgPos[1] + imgSize[1]/2.,
					imgSize[0]/2.,
				)
			)

	def __drawDefinedSphere(self, points):
		self.clearDrawnForm()
		fx, fy = points[0]
		radius = distance(points[0], points[1])
		with self.canvas:
			Color(0., 1.0, .0, 0.3)
			self.__operation = Line(
				circle = (
					fx,
					fy,
					radius
				)
			)

	def __drawDefaultMesh(self):
		self.clearDrawnForm()

		with self.canvas:
			Color(0., 1.0, .0, 0.3)
			minX, minY, maxX, maxY = self.__limits
			imgPos = self.__originalPos
			imgSize = (maxX - minX, maxY - minY)
			self.__operation = Mesh (
				vertices = [
					imgPos[0], imgPos[1], 0, 0,
					imgPos[0] + imgSize[0], imgPos[1], 0, 0,
					imgPos[0] + imgSize[0], imgPos[1] + imgSize[1], 0, 0,
					imgPos[0], imgPos[1] + imgSize[1], 0, 0,
				],
				indices = range(4),  mode = 'line_loop'
			)

	def __drawDefinedMesh(self, points):
		self.clearDrawnForm()

		verticesList = []
		for point in points:
			verticesList.extend([point[0], point[1], 0, 0])

		if (isConvexPolygon(points) == True):
			colorToUse = (0., 1.0, .0, 0.3)
		else:
			colorToUse = (1.0, .0, 0., 0.3)

		with self.canvas:
			Color(*colorToUse)
			self.__operation = Mesh(
				vertices = verticesList,
				indices = range(len(points)),
				mode = 'line_loop'
			)

	def drawPart(self, part):
		form = part.getFormType()
		points = part.getPoints()
		if (form == "box"):
			if (points == None):
				self.__drawDefaultBox()
			else:
				self.__drawDefinedBox(points)

		elif (form == "sphere"):
			if (points == None):
				self.__drawDefaultSphere()
			else:
				self.__drawDefinedSphere(points)
		elif (form == "mesh"):
			if (points == None):
				self.__drawDefaultMesh()
			else:
				self.__drawDefinedMesh(points)

	def getExpandLevel(self):
		return self.__expandLevel

	def getImage(self):
		return self.__image

	def applyZoom(self, adjust):
		newZoom = self.__zoom + adjust
		if (newZoom < 1 or newZoom > 8):
			return

		self.__zoom = newZoom
		self.size = vector2Multiply(self.__originalSize, self.__zoom)
		newPos = vector2Multiply(self.__originalPos, self.__zoom)
		self.__image.scale = self.__zoom
		self.__image._set_pos(newPos)

	def getSize(self):
		return tuple(self.size)

	def getOriginalSize(self):
		return self.__originalSize

	def getOriginalPostision(self):
		return self.__originalPos

	def getImageSize(self):
		minX, minY, maxX, maxY = self.__limits
		return (maxX - minX, maxY - minY)

class CollisionFormEditorPoints(Scatter, SpaceLimitedObject):
	dotSize = 11
	existingDots = []
	keepRatio = [False]
	moveAll = [False]

	@staticmethod
	def resetStartingState():
		CollisionFormEditorPoints.existingDots = []
		CollisionFormEditorPoints.keepRatio = [False]
		CollisionFormEditorPoints.moveAll = [False]

	@staticmethod
	def setMoveAll(value):
		CollisionFormEditorPoints.moveAll = [value]

	@staticmethod
	def setKeepRatio(value):
		CollisionFormEditorPoints.keepRatio = [value]

	def __checkAndTransform(self, trans, post_multiply=False, anchor=(0, 0)):
		xBefore, yBefore = self.bbox[0]
		self.__defaultApplyTransform(trans, post_multiply, anchor)
		x, y = self.bbox[0]
		if (xBefore == x and yBefore == y):
			return

		if (self.isOutOfLimits() == True):
			self._set_pos(self.ajustPositionByLimits(x, y, CollisionFormEditorPoints.dotSize,
				CollisionFormEditorPoints.dotSize, self.__maxX, self.__maxY))
			return

		if (CollisionFormEditorPoints.moveAll[0] == True and self.__propagateMovement == True):
			outOfLimits = False
			for point in CollisionFormEditorPoints.existingDots:
				if (point != self):
					point.applyTransform(trans)
					outOfLimits |= point.isOutOfLimits()

			if (outOfLimits == True):
				for point in CollisionFormEditorPoints.existingDots:
					point.applyTransform(trans.inverse())

		elif (CollisionFormEditorPoints.keepRatio[0] == True and self.__propagateMovement == True):
			outOfLimits = False
			for point in CollisionFormEditorPoints.existingDots:
				if (point != self):
					point.applyTransform(trans.inverse())
					outOfLimits |= point.isOutOfLimits()

			if (outOfLimits == True):
				for point in CollisionFormEditorPoints.existingDots:
					if (point == self):
						point.applyTransform(trans.inverse())
					else:
						point.applyTransform(trans)

	def _updateOnMove(self, touch):
		if (touch.button == 'right' or self.__marked == False):
			return

		if (CollisionFormEditorPoints.keepRatio[0] == True):
			self.setPropagateMovement(True)

		if (CollisionFormEditorPoints.moveAll[0] == True):
			self.setPropagateMovement(True)

		self.__updateMethod(self)
		self.__defaut_touch_move(touch)
		self.setPropagateMovement(False)

		if(CollisionFormEditorPoints.keepRatio[0] == True):
			self.setPropagateMovement(False)

		if (CollisionFormEditorPoints.moveAll[0] == True):
			self.setPropagateMovement(False)

	def isOutOfLimits(self):
		x, y = self.getPos()
		if (x < 0 or x > self.__maxX or y < 0 or y > self.__maxY):
			return True
		else:
			return False

	def applyTransform(self, trans):
		self.__defaultApplyTransform(trans)

	def getPos(self):
		x, y = self.pos
		x += ceil(CollisionFormEditorPoints.dotSize/2.)
		y += ceil(CollisionFormEditorPoints.dotSize/2.)
		return (x, y)

	def setPos(self, newPos):
		x, y = newPos
		x -= ceil(CollisionFormEditorPoints.dotSize/2.)
		y -= ceil(CollisionFormEditorPoints.dotSize/2.)
		self.pos = (x, y)

	def applyZoom(self, adjust):
		newZoom = self.__zoom + adjust
		if (newZoom < 1 or newZoom > 8):
			return

		x, y = tuple(self.getPos())
		parentOriginalSize = self.parent.getOriginalSize()
		x /= float(self.__zoom * parentOriginalSize[0])
		y /= float(self.__zoom * parentOriginalSize[1])

		self.__zoom = newZoom
		newSize = vector2Multiply(parentOriginalSize, self.__zoom)
		newX = x * newSize[0]
		newY = y * newSize[1]
		self.__maxX = newSize[0]
		self.__maxY = newSize[1]

		self.setPos((newX, newY))

	def setPropagateMovement(self, value):
		self.__propagateMovement = value

	def _markPoint(self, touch):
		if(touch.button == 'left' and self.collide_point(*touch.pos) == True):
			self.__marked = True
			self.__defaultTouchDown(touch)

	def _unmarkPoint(self, touch):
		if (touch.button == 'left'):
			if (self.__marked == True):
				self.__defaultTouchUp(touch)
			self.__marked = False

	def __init__(self, updateMethod, limits):
		super(CollisionFormEditorPoints, self).__init__(do_rotation = False, do_scale = False,
			size = (CollisionFormEditorPoints.dotSize, CollisionFormEditorPoints.dotSize), size_hint = (None, None),
			auto_bring_to_front = False)

		self.__propagateMovement = False
		self.__marked = False
		self.__updateMethod = updateMethod
		self.__defaut_touch_move = self.on_touch_move
		self.__defaultTouchDown = self.on_touch_down
		self.__defaultTouchUp = self.on_touch_up
		self.on_touch_move = self._updateOnMove
		self.on_touch_down = self._markPoint
		self.on_touch_up = self._unmarkPoint

		self.__maxX, self.__maxY = limits
		self.__zoom = 1

		self.__defaultApplyTransform = self.apply_transform
		self.apply_transform = self.__checkAndTransform

		img = Image(size = (CollisionFormEditorPoints.dotSize, CollisionFormEditorPoints.dotSize))
		self.add_widget(img)
		CollisionFormEditorPoints.existingDots.append(self)

class CollisionFormEditorLayout(KeyboardAccess, LayoutGetter, MouseModifiers, KeyboardModifiers):
	# Overloaded method
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'shift'):
			CollisionFormEditorPoints.setKeepRatio(False)

		elif (keycode[1] in ['ctrl', 'lctrl', 'rctrl']):
			self._isCtrlPressed = False
			CollisionFormEditorPoints.setMoveAll(False)

		if (keycode[1] == 'delete' and self.__lastPointPressed is not None):
			form = self.__workingPart.getFormType()
			numberOfPoints = len(self.__pointsList)
			if (form == 'mesh' and numberOfPoints > 3):
				self.__display.remove_widget(self.__lastPointPressed)
				self.__pointsList.remove(self.__lastPointPressed)
				self.__updatePoints(None)
				ModulesAccess.get('CollisionFormEditor').registerChanges()

		elif(keycode[1] == 'escape'):
			ModulesAccess.get('CollisionFormEditor').alertExit()

	# Overloaded method
	def _processKeyDown(self, keyboard, keycode, text, modifiers):
		if (keycode[1] == 'shift'):
			CollisionFormEditorPoints.setKeepRatio(True)

		elif (keycode[1] in ['ctrl', 'lctrl', 'rctrl']):
			self._isCtrlPressed = True
			CollisionFormEditorPoints.setMoveAll(True)

		elif (keycode[1] == 'a'):
			self.applyZoom(1)

		elif (keycode[1] == 's'):
			self.applyZoom(-1)

	def __updatePoints(self, point):
		self.__lastPointPressed = point
		l = []
		for point in self.__pointsList:
			l.append(point.getPos())

		self.__workingPart.setPoints(l)
		self.__display.drawPart(self.__workingPart)
		ModulesAccess.get('CollisionFormEditor').registerChanges()

	def __getStartingPositions(self, form):
		imgPos = tuple(self.__display.getOriginalPostision())
		imgSize = tuple(self.__display.getImageSize())
		if (form == 'box'):
			return (imgPos, ((imgPos[0] + imgSize[0], imgPos[1] + imgSize[1])))
		elif (form == 'sphere'):
			return ((imgPos[0] + imgSize[0]/2., imgPos[1] + imgSize[1]/2.), (imgSize[0], imgSize[1]/2))
		else:
			return (imgPos, (imgPos[0] + imgSize[0], imgPos[1]), (imgPos[0] + imgSize[0], imgPos[1] + imgSize[1]),
				(imgPos[0], imgPos[1] + imgSize[1]))

	def __copyPartAndTransform(self, part):
		newPart = CollisionPartInformation.copy(part)
		points = newPart.getPoints()
		if points is not None:
			transformedPoints = []
			for point in points:
				transformedPoints.append(self.__display.getImage().to_parent(point[0], point[1]))

			newPart.setPoints(transformedPoints)

		return newPart

	def __findBestPlaceForMesh(self, newPoint):
		assert isinstance(newPoint, CollisionFormEditorPoints)
		l = []
		for point in self.__pointsList:
			l.append(distance(point.pos, newPoint.pos))

		smallest = l[0]
		smallestIndex = 0
		for i in range(1, len(l)):
			if (smallest > l[i]):
				smallest = l[i]
				smallestIndex = i

		return smallestIndex

	def __handleScrollAndPassTouchDownToChildren(self, touch):
		if (self._layout.collide_point(*touch.pos) == False or touch.button == "scrollup" or
				touch.button == "scrolldown"):
			return

		self.updateMouseDown(touch)
		if (self._isLeftPressed == True and self._isRightPressed == False):
			self._layout.do_scroll = False

		if (touch.button == "left" and touch.is_double_tap == True and self._isCtrlPressed == True):
			form = self.__workingPart.getFormType()
			points = self.__workingPart.getPoints()
			if (points is None):
				numberOfPoints = 4
			else:
				numberOfPoints = len(points)

			if (form == 'mesh' and numberOfPoints < 8):
				displaySize = self.__display.getSize()
				newPoint = CollisionFormEditorPoints(self.__updatePoints, displaySize)
				newPoint.setPos(self.__display.to_widget(*touch.pos))
				indexToInsert = self.__findBestPlaceForMesh(newPoint)
				self.__pointsList.insert(indexToInsert + 1, newPoint)
				self.__display.add_widget(newPoint)
				self.__updatePoints(newPoint)

		self.__defaultTouchDown(touch)

	def __handleScrollAndPassTouchUpToChildren(self, touch):
		if (self._layout.collide_point(*touch.pos) == True and
				(touch.button == "scrollup" or touch.button == "scrolldown")):
			if (touch.button == "scrollup"):
				self.decreaseZoom()
			else:
				self.increaseZoom()
			return

		self.updateMouseUp(touch)
		if (self._isRightPressed == True or self._isLeftPressed == False):
			self._layout.do_scroll = True

		if (touch.button == 'right'):
			self.__defaultTouchUp(touch)

	def __handleTouchMove(self, touch):
		if (self._layout.collide_point(*touch.pos) == False or touch.button == "scrollup" or
				touch.button == "scrolldown"):
			return
		if (touch.button == 'right'):
			self.__defaultTouchMove(touch)

	def __init__(self):
		super(CollisionFormEditorLayout, self).__init__()
		self.__lastPointPressed = None

		self._layout = ScrollView(effect_cls = EmptyScrollEffect, scroll_y = 0.5, scroll_x = 0.5)
		self._layout._update_effect_x_bounds()
		self._layout._update_effect_y_bounds()

		self.__defaultTouchDown = self._layout.on_touch_down
		self.__defaultTouchMove = self._layout.on_touch_move
		self.__defaultTouchUp = self._layout.on_touch_up
		self._layout.on_touch_down = self.__handleScrollAndPassTouchDownToChildren
		self._layout.on_touch_move = self.__handleTouchMove
		self._layout.on_touch_up = self.__handleScrollAndPassTouchUpToChildren

	def render(self, part, obj):
		CollisionFormEditorPoints.resetStartingState()
		self._layout.clear_widgets()
		#print "Creating collision part display from form!"
		self.__display = CollisionPartDisplay(obj, 2.0)
		displaySize = self.__display.getSize()
		self.__originalPart = part
		self.__workingPart = self.__copyPartAndTransform(part)

		self.__display.drawPart(self.__workingPart)
		self._layout.add_widget(self.__display)

		self.__pointsList = []
		form = self.__workingPart.getFormType()
		points = self.__workingPart.getPoints()
		if (form == 'box'):
			self.__pointsList.append(CollisionFormEditorPoints(self.__updatePoints, displaySize))
			self.__display.add_widget(self.__pointsList[0])
			self.__pointsList.append(CollisionFormEditorPoints(self.__updatePoints, displaySize))
			self.__display.add_widget(self.__pointsList[1])
			if (points is None):
				positions = self.__getStartingPositions(form)
			else:
				positions = points

			self.__pointsList[0].setPos(positions[0])
			self.__pointsList[1].setPos(positions[1])

		elif (form == 'sphere'):
			self.__pointsList.append(CollisionFormEditorPoints(self.__updatePoints, displaySize))
			self.__display.add_widget(self.__pointsList[0])
			self.__pointsList.append(CollisionFormEditorPoints(self.__updatePoints, displaySize))
			self.__display.add_widget(self.__pointsList[1])
			if (points is None):
				positions = self.__getStartingPositions(form)
			else:
				positions = points
			self.__pointsList[0].setPos(positions[0])
			self.__pointsList[1].setPos(positions[1])

		elif (form == 'mesh'):
			if (points is None):
				positions = self.__getStartingPositions(form)
			else:
				positions = points

			for i in range(len(positions)):
				point = CollisionFormEditorPoints(self.__updatePoints, displaySize)
				point.setPos(positions[i])
				self.__display.add_widget(point)
				self.__pointsList.append(point)

	def savePoints(self):
		newPoints = self.__workingPart.getPoints()
		if (newPoints is not None):
			form = self.__workingPart.getFormType()
			anyChanges = False
			for pos1, pos2 in zip(newPoints, self.__getStartingPositions(form)):
				if (int(pos1[0]) != int(pos2[0]) or int(pos1[1]) != int(pos2[1])):
					anyChanges = True
					break

			if (anyChanges == True):
				transformedPoints = []
				for point in newPoints:
					transformedPoint = self.__display.getImage().to_local(*point)
					transformedPoints.append((int(transformedPoint[0]), int(transformedPoint[1])))

				if (form == 'mesh' and isConvexPolygon(transformedPoints) == False):
					return False

				self.__originalPart.setPoints(transformedPoints)

		return True

	def applyZoom(self, adjust):
		self.__display.applyZoom(adjust)
		for point in self.__pointsList:
			point.applyZoom(adjust)
		self.__updatePoints(None)

	def increaseZoom(self, *args):
		self.applyZoom(1)

	def decreaseZoom(self, *args):
		self.applyZoom(-1)

class CollisionFormEditorPopup(ChangesConfirm):
	def __saveAndClose(self, *args):
		if (self.__mainScreen.savePoints() == False):
			self.__meshErrorAlert.open()
		else:
			ModulesAccess.get('CollisionEditor').registerChangesFromTabs()
			self.close()

	def __init__(self):
		super(CollisionFormEditorPopup, self).__init__()
		ModulesAccess.add('CollisionFormEditor', self)
		self.__layout = BoxLayout(orientation = 'vertical')
		self.__popup = Popup(title = 'Collision Form Editor', content = self.__layout, auto_dismiss = False)
		self.__mainScreen = CollisionFormEditorLayout()
		self.__bottomMenu = BoxLayout(orientation = 'horizontal', **defaultDoubleLineSize)
		gridSize = defaultDoubleLineSize.copy()
		gridSize["width"] = defaultSmallButtonSize["width"] * 2
		gridSize["size_hint"] = defaultSmallButtonSize["size_hint"]
		self.__buttonsGrid = GridLayout(cols = 2, rows = 2, **gridSize)
		self.__zoomPlusButton = CancelableButton(text = "Zoom + (a)", on_release = self.__mainScreen.increaseZoom,
			**defaultSmallButtonSize)
		self.__zoomMinusButton = CancelableButton(text = "Zoom - (s)", on_release = self.__mainScreen.decreaseZoom,
			**defaultSmallButtonSize)
		self.__cancelButton = CancelableButton(text = 'Cancel', on_release = self.alertExit, **defaultSmallButtonSize)
		self.__doneButton = CancelableButton(text = 'Done', on_release = self.__saveAndClose, **defaultSmallButtonSize)
		self.__tooltipLabel = AlignedLabel(text='', **defaultDoubleLineSize)
		self.__meshErrorAlert = Alert(
			title = 'Error',
			text = 'The mesh must be a convex polygon.\nThe mesh will be green when it is convex.',
			closeButtonText = 'Ok.',
		)

		self.__bottomMenu.add_widget(self.__tooltipLabel)
		self.__buttonsGrid.add_widget(self.__zoomPlusButton)
		self.__buttonsGrid.add_widget(self.__zoomMinusButton)
		self.__buttonsGrid.add_widget(self.__cancelButton)
		self.__buttonsGrid.add_widget(self.__doneButton)
		self.__bottomMenu.add_widget(self.__buttonsGrid)

		self.__layout.add_widget(self.__mainScreen.getLayout())
		self.__layout.add_widget(self.__bottomMenu)

	def close(self, *args):
		ModulesAccess.get('CollisionEditor').preview()
		KeyboardGuardian.Instance().dropKeyboard(self.__mainScreen)
		self.__popup.dismiss()

	def open(self, part, obj):
		self.resetChanges()
		KeyboardGuardian.Instance().acquireKeyboard(self.__mainScreen)
		if (part.getFormType() == 'mesh'):
			self.__tooltipLabel.text = 'Hold Ctrl: Move all. Hold Shift: Keep ratio.\n' \
				'Ctrl + Double click: Add a point. Delete: remove last used point.'
		else:
			self.__tooltipLabel.text = 'Hold Ctrl: Move all. Hold Shift: Keep ratio.'

		self.__mainScreen.render(part, obj)
		self.__popup.open()
