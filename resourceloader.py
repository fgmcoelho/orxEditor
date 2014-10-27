from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics.vertex_instructions import Line
from kivy.graphics import Color

from editorheritage import SpecialScrollControl
from editorutils import CancelableButton, AutoReloadTexture
from keyboard import KeyboardAccess, KeyboardGuardian

class ResourceLoaderDisplay:


	def __init__(self, **kwargs):
		self.__layout = RelativeLayout(size_hint = (None, None), size = (100, 100))
		self.__currentImage = None
		self.__operations = []
		self.__suggestions = []

	def loadSuggestions(self, axis):
		assert axis in ('x', 'y')
		if (axis == 'x'):
			coord = 0
		else:
			coord = 1
		self.__suggestions = []
		size = self.__layout.size[coord]
		for i in range(8, size/2):
			if (size % i == 0):
				self.__suggestions.append(i)


	def loadImage(self, path):
		if (self.__currentImage is not None):
			self.__layout.remove_widget(self.__currentImage)
	
		im = Image(source = path)
		self.__texture = AutoReloadTexture(im.texture.size, im)
		self.__currentImage = Image(size = im.texture.size, texture = self.__texture.getTexture())
		self.__layout.size = im.texture.size
		self.__layout.add_widget(self.__currentImage)

	def __doDrawGrid(self, xInc, yInc, xSkip = 0, ySkip = 0):
		for op in self.__operations:
			self.__layout.canvas.remove(op)

		with self.__layout.canvas:
			Color(0., 1., 0., 0.3)
			i = xSkip
			while i < self.__layout.size[0]:
				self.__operations.append(
					Line(points = [
						i, 0,
						i, self.__layout.size[1]]
					)
				)
				i += xInc
			
			i = self.__layout.size[1] - ySkip
			while i > 0:
				self.__operations.append(
					Line(points = [
						0, i,
						self.__layout.size[0], i]
					)
				)
				i -= yInc

	def drawGridByDivisions(self, xDivisions, yDivisions):
		xInc = int(self.__layout.size[0] / xDivisions)
		yInc = int(self.__layout.size[1] / yDivisions)
		self.__doDrawGrid(xInc, yInc)
	
	def drawGridBySize(self, xSize, ySize, xSkip, ySkip):
		self.__doDrawGrid(xSize, ySize, xSkip, ySkip)

	def getLayout(self):
		return self.__layout

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
		
	def __handleScrollAndPassTouchDownToChildren(self, touch):
		if (self._scrollView.collide_point(*touch.pos) == False):
			return

		if (touch.is_mouse_scrolling == True):
			return self.specialScroll(touch)

	def __handleScrollAndPassTouchUpToChildren(self, touch):
		pass

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
				xSkip = int(self.__ySkipInput.text)
				ySkip = int(self.__ySkipInput.text)
			except:
				xSkip = 0
				ySize = 0
			
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
		self.__xSizeInput = TextInput(multiline = False, size_hint = (1.0, 0.05))
		self.__ySizeInput = TextInput(multiline = False, size_hint = (1.0, 0.05))
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
		self.__leftMenu.add_widget(Label(text = '', size_hint = (1.0, 0.55)))
		self.__leftMenu.add_widget(self.__switchButton)
		self.__leftMenu.add_widget(self.__splitButton)
		self.__leftMenu.add_widget(self.__closeButton)

	def __init__(self):
		self.__popup = Popup(title = 'Resource Loader')
		self.__method = 'divisions'
		
		super(ResourceLoaderPopup, self).__init__(size_hint = (1.0, 1.0))
		self._scrollView.on_touch_move = self._ignoreMoves
		self.__defaultTouchDown = self._scrollView.on_touch_down
		self.__defaultTouchUp = self._scrollView.on_touch_up
		self._scrollView.on_touch_down = self.__handleScrollAndPassTouchDownToChildren
		self._scrollView.on_touch_up = self.__handleScrollAndPassTouchUpToChildren

		self.__layout = BoxLayout(orientation = 'horizontal')
		self.__leftMenu = BoxLayout(orientation = 'vertical', size_hint = (0.25, 1.0))
		self.__createLeftMenuUi()
		self.__loadDivisionLeftMenu()
		self.__rightMenu = BoxLayout(orientation = 'vertical', size_hint = (0.75, 1.0))
		self.__display = ResourceLoaderDisplay()

		self._scrollView.add_widget(self.__display.getLayout())
		self.__rightMenu.add_widget(self._scrollView)

		self.__layout.add_widget(self.__leftMenu)
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

