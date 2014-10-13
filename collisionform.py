from singleton import Singleton

from kivy.uix.popup import Popup
from kivy.uix.scatter import Scatter
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.graphics.vertex_instructions import Mesh, Line
from kivy.graphics import Color
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from math import ceil

from editorutils import AutoReloadTexture, CancelableButton, vector2Multiply, distance
from editorheritage import SpecialScrollControl
from collisioninfo import CollisionPartInformation
from keyboard import KeyboardAccess, KeyboardGuardian

class CollisionPartDisplay(RelativeLayout):
	def __init__(self, obj, expandLevel = 1.0):
		if (obj is None):
			return

		self.__texture = AutoReloadTexture(obj.getSize(), obj.getImage())
		super(CollisionPartDisplay, self).__init__(size_hint = (None, None), size = obj.getSize())
		self.__image = Scatter(do_rotation = False, do_translation = False, do_scale = False)
		im = Image(texture = self.__texture.getTexture(), size = obj.getSize(), allow_strech = True)
		self.__image.add_widget(im)
		self.__image.size =  obj.getSize()
		self.__operation = None
		self.add_widget(self.__image)
		self.__expandLevel = expandLevel
		self.size = vector2Multiply(tuple(self.size), self.__expandLevel)
		if (self.__expandLevel == 1.0):
			self.__image.pos = (0, 0)
		else:
			self.__image.pos = (self.size[0]/(self.__expandLevel * 2.), self.size[1]/(self.__expandLevel * 2.))
		self.__originalSize = tuple(self.size)
		self.__operation = None

	def clearDrawnForm(self):
		if (self.__operation != None):
			self.canvas.remove(self.__operation)
			self.__operation = None

	def __drawDefaultBox(self):
		self.clearDrawnForm()

		with self.canvas:
			Color(0., 1.0, .0, 0.3)
			imgPos = tuple(self.__image.pos)
			imgSize = tuple(self.__image.size)
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

		imgPos = tuple(self.__image.pos)
		imgSize = tuple(self.__image.size)
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
			imgPos = tuple(self.__image.pos)
			imgSize = tuple(self.__image.size)
			self.__operation = Mesh (
				vertices = [
					imgPos[0], imgPos[0], 0, 0,
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

		with self.canvas:
			Color(0., 1.0, .0, 0.3)
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

	def resize(self, x):
		self.size = vector2Multiply(self.__originalSize, x)
		self.__image.pos = (self.size[0]/4., self.size[1]/4.)

class CollisionFormEditorPoints(Scatter):

	dotSize = 11
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

	def __updateOnMove(self, touch):
		self.__updateMethod(self)
		self.__defaut_touch_move(touch)

	def __init__(self, updateMethod):
		super(CollisionFormEditorPoints, self).__init__(do_rotation = False, do_scale = False,
			size = (CollisionFormEditorPoints.dotSize, CollisionFormEditorPoints.dotSize), size_hint = (None, None),
			auto_bring_to_front = False)

		self.__updateMethod = updateMethod
		self.__defaut_touch_move = self.on_touch_move
		self.on_touch_move = self.__updateOnMove

		img = Image (size = (CollisionFormEditorPoints.dotSize, CollisionFormEditorPoints.dotSize))
		self.add_widget(img)
		#with self.canvas:
		#	Color (1, 0, 1, 0)
		#	Rectangle(pos = self.pos, size = self.size)


class CollisionFlagFormEditorLayout(SpecialScrollControl, KeyboardAccess):

	# Overloaded method
	def _processKeyUp(self, keyboard, keycode):

		if (keycode[1] == 'shift'):
			self.setIsShiftPressed(False)

		elif (keycode[1] == 'ctrl'):
			self.setIsCtrlPressed(False)

		if (keycode[1] == 'delete' and self.__lastPointPressed is not None):
			form = self.__workingPart.getFormType()
			numberOfPoints = len(self.__pointsList)
			if (form == 'mesh' and numberOfPoints > 3):
				self.__display.remove_widget(self.__lastPointPressed)
				self.__pointsList.remove(self.__lastPointPressed)
				self.__updatePoints(None)

	# Overloaded method
	def _processKeyDown(self, keyboard, keycode, text, modifiers):
		if (keycode[1] == 'shift'):
			self.setIsShiftPressed(True)

		elif (keycode[1] == 'ctrl'):
			self.setIsCtrlPressed(True)

	def __updatePoints(self, point):
		self.__lastPointPressed = point
		l = []
		for point in self.__pointsList:
			l.append(point.getPos())

		self.__workingPart.setPoints(l)
		self.__display.drawPart(self.__workingPart)

	def render(self, part, obj):
		self._scrollView.clear_widgets()
		self.__display = CollisionPartDisplay(obj, 2.0)
		#self._zoomList.append(self.__display.getImage())
		self.__originalPart = part
		self.__workingPart = CollisionPartInformation.copy(part)

		self.__display.drawPart(self.__workingPart)
		self._scrollView.add_widget(self.__display)

		self.__pointsList = []
		form = self.__workingPart.getFormType()
		points = self.__workingPart.getPoints()
		if (form == 'box'):
			self.__pointsList.append(CollisionFormEditorPoints(self.__updatePoints))
			self.__display.add_widget(self.__pointsList[0])
			self.__pointsList.append(CollisionFormEditorPoints(self.__updatePoints))
			self.__display.add_widget(self.__pointsList[1])
			if (points == None):
				imgPos = tuple(self.__display.getImage().pos)
				imgSize = tuple(self.__display.getImage().size)
				self.__pointsList[0].setPos(imgPos)
				self.__pointsList[1].setPos((imgPos[0] + imgSize[0], imgPos[1] + imgSize[1]))

		elif (form == 'sphere'):
			self.__pointsList.append(CollisionFormEditorPoints(self.__updatePoints))
			self.__display.add_widget(self.__pointsList[0])
			self.__pointsList.append(CollisionFormEditorPoints(self.__updatePoints))
			self.__display.add_widget(self.__pointsList[1])
			if (points == None):
				imgPos = tuple(self.__display.getImage().pos)
				imgSize = tuple(self.__display.getImage().size)
				midPoint = (imgPos[0] + imgSize[0]/2., imgPos[1] + imgSize[1]/2.)
				self.__pointsList[0].setPos(midPoint)
				self.__pointsList[1].setPos((obj.getSize()[0], obj.getSize()[1]/2))

		elif (form == 'mesh'):
			if (points == None):
				for i in range(4):
					point = CollisionFormEditorPoints(self.__updatePoints)
					self.__pointsList.append(point)
					self.__display.add_widget(point)

				imgPos = tuple(self.__display.getImage().pos)
				imgSize = tuple(self.__display.getImage().size)
				self.__pointsList[0].setPos(imgPos)
				self.__pointsList[1].setPos((imgPos[0] + imgSize[0], imgPos[1]))
				self.__pointsList[2].setPos((imgPos[0] + imgSize[0], imgPos[1] + imgSize[1]))
				self.__pointsList[3].setPos((imgPos[0], imgPos[1] + imgSize[1]))

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
		if (self._scrollView.collide_point(*touch.pos) == False):
			return

		if (touch.is_double_tap == True):
			form = self.__workingPart.getFormType()
			if (form == 'mesh'):
				newPoint = CollisionFormEditorPoints(self.__updatePoints)
				newPoint.setPos(self.__display.to_widget(*touch.pos))
				indexToInsert = self.__findBestPlaceForMesh(newPoint)
				self.__pointsList.insert(indexToInsert + 1, newPoint)
				self.__display.add_widget(newPoint)
				self.__updatePoints(newPoint)

			return

		if (touch.is_mouse_scrolling == True):
			oldZoom = self._zoom
			self.specialScroll(touch)
			if (oldZoom != self._zoom):
				self.__display.resize(self._zoom)
				self.__replacePoints(self._zoom)

			return

		self.__defaultTouchDown(touch)

	def __init__(self):
		super(CollisionFlagFormEditorLayout, self).__init__(size_hint = (1.0, 0.9))

		self.__defaultTouchDown = self._scrollView.on_touch_down
		self._scrollView.on_touch_move = self._ignoreMoves
		self._scrollView.on_touch_down = self.__handleScrollAndPassTouchDownToChildren
		self._scrollView.scroll_y = 0.5
		self._scrollView.scroll_x = 0.5
		self.__lastPointPressed = None

@Singleton
class CollisionFlagFormEditorPopup:

	def __init__(self):

		self.__layout = BoxLayout(orientation = 'vertical')
		self.__popup = Popup(title = 'Collision Form Editor', content = self.__layout)
		self.__mainScreen = CollisionFlagFormEditorLayout()
		self.__bottomMenu = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		self.__cancelButton = CancelableButton(text = 'Cancel', size_hint = (0.15, 1.0),
				on_release = self.dismissPopUp)
		self.__doneButton = CancelableButton(text = 'Done', size_hint = (0.15, 1.0))
		self.__tooltipLabel = Label(text='', size_hint = (0.6, 1.0))

		self.__bottomMenu.add_widget(self.__tooltipLabel)
		self.__bottomMenu.add_widget(Label(text ='', size_hint = (0.1, 1.0)))
		self.__bottomMenu.add_widget(self.__cancelButton)
		self.__bottomMenu.add_widget(self.__doneButton)

		self.__layout.add_widget(self.__mainScreen.getLayout())
		self.__layout.add_widget(self.__bottomMenu)

	def dismissPopUp(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self.__mainScreen)

		self.__popup.dismiss()

	def showPopUp(self, part, obj):
		KeyboardGuardian.Instance().acquireKeyboard(self.__mainScreen)
		if (part.getFormType() == 'mesh'):
			self.__tooltipLabel.text = 'Double click to Add a point.\nPress delete to remove the last used point.'
		else:
			self.__tooltipLabel.text = ''

		self.__mainScreen.render(part, obj)
		self.__popup.open()
