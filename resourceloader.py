from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.graphics.vertex_instructions import Line
from kivy.graphics import Color

from editorheritage import SpecialScrollControl
from editorutils import CancelableButton, AutoReloadTexture
from keyboard import KeyboardAccess, KeyboardGuardian

class SpriteSelection:
	def __init__(self, x, y, xSize, ySize):
		self.__x = x
		self.__y = y
		self.__xSize = xSize
		self.__ySize = ySize

class GridCell:
	def __init__(self, canvas, x, y, xSize, ySize):
		self.__x = x
		self.__y = y
		self.__xSize = xSize
		self.__ySize = ySize
		self.__canvasRef = canvas
		self.__operation = None
		self.__color = None
		self.__marked = False
		self.draw((0., 1., 0., 1.))

	def draw(self, colorToUse):
		if (self.__operation is not None):
			self.__canvasRef.remove(self.__operation)
			self.__canvasRef.remove(self.__color)
			self.__canvasRef.ask_update()

		self.__color = Color(*colorToUse)
		self.__operation = Line(points = [
			self.__x, self.__y,
			self.__x, self.__y - self.__ySize,
			self.__x + self.__xSize, self.__y - self.__ySize,
			self.__x + self.__xSize, self.__y],
			close = True, width = 1
		)
		self.__canvasRef.add(self.__color)
		self.__canvasRef.add(self.__operation)
		self.__canvasRef.ask_update()

	def select(self):
		self.__marked = True
		self.draw((1., 0., 0., 1.))

	def unselect(self):
		if (self.__marked):
			self.draw((0., 1., 0., 1.))

class ResourceLoaderDisplay:

	def __clearGraphicGrid(self):
		for line in self.__gridGraphics:
			for cell in line:
				cell.unselect()

	def __posToGridCoords(self, x, y):
		i, j = int((x + self.__xSkip) / self.__xSize), int((y - self.__ySkip) / self.__ySize)
		return (self.__rows - j - 1, i)

	def updateSelection(self, touch):
		pass

	def startSelection(self, touch):
		if (self.__currentImage is not None and self.__gridGraphics != [] and self.__selectionStarted == False):
			self.__clearGraphicGrid()
			self.__selectionStarted = True
			self.__currentSelectionLimits = None
			self.__selectionStartPos = self.__currentImage.to_widget(*touch.pos)
			sj, si = self.__posToGridCoords(*self.__selectionStartPos)
			self.__gridGraphics[sj][si].select()

	def finishSelection(self, touch):
		if (self.__currentImage is not None and self.__gridGraphics != [] and self.__selectionStarted == True):
			pos = self.__currentImage.to_widget(*touch.pos)
			fj, fi = self.__posToGridCoords(*pos)
			sj, si = self.__posToGridCoords(*self.__selectionStartPos)
			loopStartIndexI = min(si, fi)
			loopStartIndexJ = min(sj, fj)
			loopFinalIndexI = max(si, fi)
			loopFinalIndexJ = max(sj, fj)

			tempI = loopStartIndexI
			while (tempI <= loopFinalIndexI):
				tempJ = loopStartIndexJ
				while(tempJ <= loopFinalIndexJ):
					self.__gridGraphics[tempJ][tempI].select()
					tempJ += 1
				tempI += 1

			self.__selectionStarted = False
			self.__currentSelectionLimits = ((loopStartIndexI, loopStartIndexJ), (loopFinalIndexI, loopFinalIndexJ))

	def __init__(self, **kwargs):
		self.__selectionStarted = False
		self.__selectionStartPos = None
		self.__layout = RelativeLayout(size_hint = (None, None), size = (100, 100))
		self.__currentImage = None
		self.__suggestions = []
		self.__gridGraphics = []
		self.__currentSelectionLimits = None

	def loadImage(self, path):
		if (self.__currentImage is not None):
			self.__layout.remove_widget(self.__currentImage)

		im = Image(source = path)
		self.__texture = AutoReloadTexture(im.texture.size, im)
		self.__currentImage = Image(size = im.texture.size, texture = self.__texture.getTexture())
		self.__layout.size = im.texture.size
		self.__layout.add_widget(self.__currentImage)

	def __doDrawGrid(self, xInc, yInc, xSkip = 0, ySkip = 0):

		self.__layout.clear_widgets()
		self.__layout.canvas.clear()
		self.__layout.add_widget(self.__currentImage)
		self.__gridGraphics = []
		self.__xSize = xInc
		self.__ySize = xInc
		self.__xSkip = xSkip
		self.__ySkip = ySkip

		j = self.__layout.size[1] - ySkip
		while j - yInc >= 0:
			i = xSkip
			line = []
			while i + xInc <= self.__layout.size[0]:
				line.append(GridCell(self.__layout.canvas, i + xSkip, j - ySkip, xInc, yInc))
				i += xInc
			j -= yInc
			self.__gridGraphics.append(line)

		if (self.__gridGraphics != []):
			self.__lines = len(self.__gridGraphics[0])
			self.__rows = len(self.__gridGraphics)

	def drawGridByDivisions(self, xDivisions, yDivisions):
		xInc = int(self.__layout.size[0] / xDivisions)
		yInc = int(self.__layout.size[1] / yDivisions)
		self.__doDrawGrid(xInc, yInc)

	def drawGridBySize(self, xSize, ySize, xSkip, ySkip):
		self.__doDrawGrid(xSize, ySize, xSkip, ySkip)

	def getLayout(self):
		return self.__layout

	def getCurrentSelection(self):
		return self.__currentSelectionLimits

class ResourceLoaderPopup(SpecialScrollControl, KeyboardAccess):
	# Overloaded method
	def _processKeyUp(self, keyboard, keycode):

		if (keycode[1] == 'shift'):
			self.setIsShiftPressed(False)

		elif (keycode[1] == 'ctrl'):
			self.setIsCtrlPressed(False)

	# Overloaded method
	def _processKeyDown(self, keyboard, keycode, text, modifiers):

		if (keycode[1] == 'shift'):
			self.setIsShiftPressed(True)

		elif (keycode[1] == 'ctrl'):
			self.setIsCtrlPressed(True)

	def __handleTouchMove(self, touch):
		if (self._scrollView.collide_point(*touch.pos) == False):
			return

		self.__display.updateSelection(touch)

	def __handleScrollAndPassTouchDownToChildren(self, touch):
		if (self._scrollView.collide_point(*touch.pos) == False):
			return

		if (touch.is_mouse_scrolling == True):
			return self.specialScroll(touch)

		self.__display.startSelection(touch)

	def __handleScrollAndPassTouchUpToChildren(self, touch):
		if (self._scrollView.collide_point(*touch.pos) == False):
			return

		self.__display.finishSelection(touch)

	def __splitImage(self, *args):
		if (self.__method == 'divisions'):
			try:
				xDivisions = int(self.__xDivisionsInput.text)
				yDivisions = int(self.__yDivisionsInput.text)
			except:
				return

			self.__display.drawGridByDivisions(xDivisions, yDivisions)
		else:
			try:
				xSize = int(self.__xSizeInput.text)
				ySize = int(self.__ySizeInput.text)
			except:
				return

			try:
				xSkip = int(self.__xSkipInput.text)
			except:
				xSkip = 0
			try:
				ySkip = int(self.__ySkipInput.text)
			except:
				ySkip = 0

			self.__display.drawGridBySize(xSize, ySize, xSkip, ySkip)

	def __changeMethod(self, *args):
		if (self.__method == 'divisions'):
			self.__method = 'size'
			self.__loadSizeLeftMenu()
		else:
			self.__method = 'divisions'
			self.__loadDivisionLeftMenu()

	def __createLeftMenuUi(self):
		self.__xDivisionsInput = TextInput(multiline = False, size_hint = (1.0, 0.05))
		self.__yDivisionsInput = TextInput(multiline = False, size_hint = (1.0, 0.05))
		self.__xSizeInput = TextInput(multiline = False, size_hint = (1.0, 0.05), text = '32')
		self.__ySizeInput = TextInput(multiline = False, size_hint = (1.0, 0.05), text = '32')
		self.__xSkipInput = TextInput(multiline = False, size_hint = (1.0, 0.05))
		self.__ySkipInput = TextInput(multiline = False, size_hint = (1.0, 0.05))
		self.__closeButton = CancelableButton(on_release = self.close, text = 'Close', size_hint = (1.0, 0.05))
		self.__splitButton = CancelableButton(on_release = self.__splitImage, text = 'Split', size_hint = (1.0, 0.05))
		self.__switchButton = CancelableButton(on_release = self.__changeMethod, text = 'Change method', size_hint = (1.0, 0.05))

	def __loadDivisionLeftMenu(self):
		self.__leftMenu.clear_widgets()
		self.__leftMenu.add_widget(Label(text = 'Divisions on x', size_hint = (1.0, 0.05)))
		self.__leftMenu.add_widget(self.__xDivisionsInput)
		self.__leftMenu.add_widget(Label(text = 'Divisions on y', size_hint = (1.0, 0.05)))
		self.__leftMenu.add_widget(self.__yDivisionsInput)
		self.__leftMenu.add_widget(Label(text = '', size_hint = (1.0, 0.65)))
		self.__leftMenu.add_widget(self.__switchButton)
		self.__leftMenu.add_widget(self.__splitButton)
		self.__leftMenu.add_widget(self.__closeButton)

	def __loadSizeLeftMenu(self):
		self.__leftMenu.clear_widgets()
		self.__leftMenu.add_widget(Label(text = 'Size on x', size_hint = (1.0, 0.05)))
		self.__leftMenu.add_widget(self.__xSizeInput)
		self.__leftMenu.add_widget(Label(text = 'Size on y', size_hint = (1.0, 0.05)))
		self.__leftMenu.add_widget(self.__ySizeInput)
		self.__leftMenu.add_widget(Label(text = 'Skip on x', size_hint = (1.0, 0.05)))
		self.__leftMenu.add_widget(self.__xSkipInput)
		self.__leftMenu.add_widget(Label(text = 'Skip on y', size_hint = (1.0, 0.05)))
		self.__leftMenu.add_widget(self.__ySkipInput)
		self.__leftMenu.add_widget(Label(text = '', size_hint = (1.0, 0.45)))
		self.__leftMenu.add_widget(self.__switchButton)
		self.__leftMenu.add_widget(self.__splitButton)
		self.__leftMenu.add_widget(self.__closeButton)

	def __processAddSelection(self, *args):
		self.__selectionTree.add_node(TreeViewLabel(text='Selection'))

	def __createRightMenuUi(self):
		self.__selectionTree = TreeView(root_options=dict(text='Resources'), size_hint = (1.0, 0.8))
		self.__addFullSelection = CancelableButton(text = 'Add as one', size_hint = (1.0, 0.05),
			on_release = self.__processAddSelection)
		self.__addPartSelection = CancelableButton(text = 'Add parts', size_hint = (1.0, 0.05))
		self.__removeCurrent = CancelableButton(text = 'Remove', size_hint = (1.0, 0.05))
		self.__clearSelection = CancelableButton(text = 'Clear', size_hint = (1.0, 0.05))

		self.__rightMenu.add_widget(self.__selectionTree)
		self.__rightMenu.add_widget(self.__addFullSelection)
		self.__rightMenu.add_widget(self.__addPartSelection)
		self.__rightMenu.add_widget(self.__removeCurrent)
		self.__rightMenu.add_widget(self.__clearSelection)

	def __init__(self):
		self.__popup = Popup(title = 'Resource Loader')
		self.__method = 'size'

		super(ResourceLoaderPopup, self).__init__(size_hint = (1.0, 1.0))
		self._scrollView.on_touch_move = self.__handleTouchMove
		self.__defaultTouchDown = self._scrollView.on_touch_down
		self.__defaultTouchUp = self._scrollView.on_touch_up
		self._scrollView.on_touch_down = self.__handleScrollAndPassTouchDownToChildren
		self._scrollView.on_touch_up = self.__handleScrollAndPassTouchUpToChildren
		self.__layout = BoxLayout(orientation = 'horizontal')

		self.__leftMenu = BoxLayout(orientation = 'vertical', size_hint = (0.15, 1.0))
		self.__createLeftMenuUi()
		self.__loadSizeLeftMenu()

		self.__middleMenu = BoxLayout(orientation = 'vertical', size_hint = (0.7, 1.0))
		self.__display = ResourceLoaderDisplay()
		self._scrollView.add_widget(self.__display.getLayout())
		self.__middleMenu.add_widget(self._scrollView)

		self.__rightMenu = BoxLayout(orientation = 'vertical', size_hint = (0.15, 1.0))
		self.__createRightMenuUi()

		self.__layout.add_widget(self.__leftMenu)
		self.__layout.add_widget(self.__middleMenu)
		self.__layout.add_widget(self.__rightMenu)

		self.__popup.content = self.__layout

	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__display.loadImage('tiles/wateranimate2.png')
		#self.__display.loadImage('tiles/grounds.png')
		self.__popup.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()

