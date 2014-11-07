from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.checkbox import CheckBox
from kivy.graphics.vertex_instructions import Line
from kivy.graphics import Color
from kivy.graphics.texture import Texture

from editorheritage import SpecialScrollControl
from editorutils import CancelableButton, AutoReloadTexture, AlertPopUp, Dialog
from keyboard import KeyboardAccess, KeyboardGuardian

class WhiteImage:
	def __init__(self):
		newTexture = Texture.create(size = (64, 64))
		size = 64 * 64 * 4
		i = 0
		buf = ''
		while i < size:
			buf += chr(0xFF)
			i += 1

		newTexture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')

		self.__image = Image(size = (64, 64), texture = newTexture)

	def setColor(self, color):
		self.__image.color = color

	def getImage(self):
		return self.__image

class NumberInput(TextInput):
	def insert_text(self, substring, from_undo = False):
		if (substring in "0123456789"):
			super(NumberInput, self).insert_text(substring, from_undo = from_undo)

	def __init__(self, **kwargs):
		super(NumberInput, self).__init__(**kwargs)

class SpriteSelection:
	def __init__(self, x, y, xSize, ySize, xParts = 1, yParts = 1):
		self.__x = x
		self.__y = y
		self.__xSize = xSize
		self.__ySize = ySize
		self.__xParts = xParts
		self.__yParts = yParts

	def compare(self, otherSelection):
		if (self.__x == otherSelection.getX() and self.__xSize == otherSelection.getSizeX() and
				self.__y == otherSelection.getY() and self.__ySize == otherSelection.getSizeY()):
			return True
		else:
			return False

	def getX(self):
		return self.__x

	def getY(self):
		return self.__y

	def getSizeX(self):
		return self.__xSize

	def getSizeY(self):
		return self.__ySize

	def getPartsX(self):
		return self.__xParts

	def getPartsY(self):
		return self.__yParts

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

class ResourceLoaderDisplay(SpecialScrollControl):

	def __clearGraphicGrid(self):
		self.__currentSelection = None
		for line in self.__gridGraphics:
			for cell in line:
				cell.unselect()

	def __posToGridCoords(self, x, y):
		i, j = int((x + self.__xSkip) / self.__xSize), int((y - self.__ySkip) / self.__ySize)
		if (i < 0):
			i = 0
		elif (i >= self.__columns):
			i = self.__columns - 1

		j = self.__rows - j - 1
		if (j < 0):
			j = 0
		elif (j >= self.__rows):
			j = self.__rows - 1

		return (j, i)

	def __handleTouchMove(self, touch):
		if (self._scrollView.collide_point(*touch.pos) == False):
			return

		self.updateSelection(touch)

	def __handleScrollAndPassTouchDownToChildren(self, touch):
		if (self._scrollView.collide_point(*touch.pos) == False):
			return

		if (touch.is_mouse_scrolling == True):
			return self.specialScroll(touch)

		imgCoords = self.__currentImage.to_widget(touch.pos[0], touch.pos[1])
		if (self.__currentImage is not None and self.__currentImage.collide_point(*imgCoords) == True):
			self.startSelection(touch)
		else:
			self.__clearGraphicGrid()

	def __handleScrollAndPassTouchUpToChildren(self, touch):
		if (self.__currentImage is not None):
			imgCoords = self.__currentImage.to_widget(touch.pos[0], touch.pos[1])
			if(self.__currentImage.collide_point(*imgCoords)):
				adjY = self.__currentImage.texture_size[1] - int(imgCoords[1]) - 1
				pixelAddress = ((adjY * self.__currentImage.texture_size[0]) + int(imgCoords[0]) - 1) * 4
				clickedColor = (
					ord(self.__currentImage.texture.pixels[pixelAddress]),
					ord(self.__currentImage.texture.pixels[pixelAddress + 1]),
					ord(self.__currentImage.texture.pixels[pixelAddress + 2]),
					ord(self.__currentImage.texture.pixels[pixelAddress + 3])
				)
				self.__updateColorMethod(clickedColor)

		self.finishSelection(touch)

	def __clearSelectionGrid(self):
		self.__layout.clear_widgets()
		self.__layout.canvas.clear()
		self.__layout.add_widget(self.__currentImage)
		self.__gridGraphics = []
		self.__selectionPreview = None
		self.__currentSelection = None

	def __doDrawGrid(self, xInc, yInc, xSkip = 0, ySkip = 0):
		self.__clearSelectionGrid()
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
			self.__columns = len(self.__gridGraphics[0])
			self.__rows = len(self.__gridGraphics)

	def __init__(self, **kwargs):
		super(ResourceLoaderDisplay, self).__init__(size_hint = (1.0, 1.0))
		self._scrollView.on_touch_move = self.__handleTouchMove
		self.__defaultTouchDown = self._scrollView.on_touch_down
		self.__defaultTouchUp = self._scrollView.on_touch_up
		self._scrollView.on_touch_down = self.__handleScrollAndPassTouchDownToChildren
		self._scrollView.on_touch_up = self.__handleScrollAndPassTouchUpToChildren

		self.__selectionStarted = False
		self.__selectionStartPos = None
		self.__layout = RelativeLayout(size_hint = (None, None), size = (100, 100))
		self.__currentImage = None
		self.__selectionPreview = None
		self.__updateColorMethod = kwargs['colorMethod']
		self.__suggestions = []
		self.__gridGraphics = []
		self.__currentSelection = None
		self._scrollView.add_widget(self.__layout)

	def updateSelection(self, touch):
		pass

	def startSelection(self, touch):
		if (self.__currentImage is not None and self.__gridGraphics != [] and self.__selectionStarted == False):
			self.__clearGraphicGrid()
			self.__selectionStarted = True
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
			self.__currentSelection = SpriteSelection(
				(loopStartIndexI * self.__xSize) + self.__xSkip,
				(loopStartIndexJ * self.__ySize) + self.__ySkip,
				(loopFinalIndexI - loopStartIndexI + 1) * self.__xSize,
				(loopFinalIndexJ - loopStartIndexJ + 1) * self.__ySize,
				(loopFinalIndexI - loopStartIndexI + 1),
				(loopFinalIndexJ - loopStartIndexJ + 1)
			)

	def loadImage(self, path):
		if (self.__currentImage is not None):
			self.__layout.canvas.clear()
			self.__layout.remove_widget(self.__currentImage)

		im = Image(source = path)
		self.__texture = AutoReloadTexture(im.texture.size, im)
		self.__currentImage = Image(size = im.texture.size, texture = self.__texture.getTexture())
		self.__layout.size = im.texture.size
		self.__layout.add_widget(self.__currentImage)

	def drawGridByDivisions(self, xDivisions, yDivisions):
		xInc = int(self.__layout.size[0] / xDivisions)
		yInc = int(self.__layout.size[1] / yDivisions)
		self.__doDrawGrid(xInc, yInc)

	def drawGridBySize(self, xSize, ySize, xSkip, ySkip):
		self.__doDrawGrid(xSize, ySize, xSkip, ySkip)

	def getCurrentSelection(self):
		return self.__currentSelection

	def previewSelection(self, selection):
		self.__clearSelectionGrid()
		x = selection.getX()
		y = selection.getY()
		xSize = selection.getSizeX()
		ySize = selection.getSizeY()
		with self.__layout.canvas:
			self.__selectionPreview = Line(points = [
				x, self.__layout.size[1] - y,
				x, self.__layout.size[1] - y - ySize,
				x + xSize, self.__layout.size[1] - y - ySize,
				x + xSize, self.__layout.size[1] - y],
				close = True, width = 1
			)

class ResourceLoaderList(SpecialScrollControl):

	def __ignoreMoves(self, touch):
		pass

	def __handleScrollAndPassTouchDownToChildren(self, touch):
		if (self._scrollView.collide_point(*touch.pos) == False):
			return

		if (touch.is_mouse_scrolling == True):
			if (self.__layout.height != self.__tree.minimum_height):
				self.__layout.height = self.__tree.minimum_height

			return self.specialScroll(touch)

		self.__defaultTouchDown(touch)

	def __doClearAllItems(self, *args):
		for node in self.__tree.children:
			self.__tree.remove_node(node)

		self.__selectionDict = {}
		self.__layout.height = self.__tree.minimum_height

	def __doAddItem(self, selection):
		node = TreeViewLabel(text='Pos: (' + str(selection.getX()) + ', ' + str(selection.getY()) + ') | Size: (' + \
				str(selection.getSizeX()) + ', ' + str(selection.getSizeY()) + ')', id = 'selection#' + \
				str(self.__selectionId))

		self.__selectionDict[self.__selectionId] = selection
		self.__selectionId += 1
		self.__tree.add_node(node)
		self.__layout.height = self.__tree.minimum_height

	def getSelection(self):
		if (self.__tree.selected_node is not None):
			itemName, itemId = self.__tree.selected_node.id.split('#')
			if (itemName != 'root'):
				return self.__selectionDict[int(itemId)]

	def clearAllItems(self):
		if (len(self.__selectionDict) == 0):
			return
		elif (len(self.__selectionDict) == 1):
			dialog = Dialog(self.__doClearAllItems,
				'Confirmation', 'This will remove 1 selection.\nThis operation can\'t be reverted.',
				'Ok', 'Cancel')
		else:
			dialog = Dialog(self.__doClearAllItems, 'Confirmation', 'This will remove ' + \
					str(len(self.__selectionDict)) + ' selections.\nThis operation can\'t be reverted.',
				'Ok', 'Cancel')

		dialog.open()

	def removeItem(self):
		if (self.__tree.selected_node is not None):
			itemName, itemId = self.__tree.selected_node.id.split('#')
			if (itemName != 'root'):
				self.__tree.remove_node(self.__tree.selected_node)
				del self.__selectionDict[int(itemId)]
				self.__tree.select_node(self.__tree.root)
				self.__layout.height = self.__tree.minimum_height

	def addItemList(self, selectionList):
		count = 0
		for selection in selectionList:
			doAdd = True
			for savedSelection in self.__selectionDict.values():
				if (savedSelection.compare(selection) == True):
					count += 1
					doAdd = False
					break
			if (doAdd == True):
				self.__doAddItem(selection)

		if (count != 0):
			if (count == 1):
				warn = AlertPopUp('Error', '1 selection could not be added because it\nhas already been added.', 'Ok')
			else:
				warn = AlertPopUp('Error',
					str(count) + ' selections could not be added because they\nhave already been added.', 'Ok'
				)

			warn.open()
			return

	def addItem(self, selection):
		for savedSelection in self.__selectionDict.values():
			if (savedSelection.compare(selection) == True):
				warn = AlertPopUp('Error', 'This selection has already been added.', 'Ok')
				warn.open()
				return

		self.__doAddItem(selection)

	def __init__(self, **kwargs):
		super(ResourceLoaderList, self).__init__(**kwargs)
		self.__selectionDict = {}
		self.__selectionId = 0
		self._scrollView.on_touch_move = self.__ignoreMoves
		self.__defaultTouchDown = self._scrollView.on_touch_down
		self._scrollView.on_touch_down = self.__handleScrollAndPassTouchDownToChildren
		self.__tree = TreeView(root_options = dict(text='Resources', id='root#0'), size_hint = (1.0, 1.0),
			expand_root = False)
		self.__layout = RelativeLayout(size = (300, 100), size_hint = (None, None))
		self.__layout.add_widget(self.__tree)
		self._scrollView.add_widget(self.__layout)


class ResourceLoaderPopup(KeyboardAccess):
	# Overloaded method
	def _processKeyUp(self, keyboard, keycode):

		if (keycode[1] == 'shift'):
			self.__display.setIsShiftPressed(False)
			self.__selectionTree.setIsShiftPressed(False)

		elif (keycode[1] == 'ctrl'):
			self.__display.setIsCtrlPressed(False)
			self.__selectionTree.setIsShiftPressed(False)

	# Overloaded method
	def _processKeyDown(self, keyboard, keycode, text, modifiers):

		if (keycode[1] == 'shift'):
			self.__display.setIsShiftPressed(True)
			self.__selectionTree.setIsShiftPressed(True)

		elif (keycode[1] == 'ctrl'):
			self.__display.setIsCtrlPressed(True)
			self.__selectionTree.setIsCtrlPressed(True)

		elif (keycode[1] == 'escape'):
			KeyboardGuardian.Instance().dropKeyboard(self)

	def __splitImage(self, *args):
		if (self.__state == 'divisions'):
			try:
				xDivisions = int(self.__xDivisionsInput.text)
				yDivisions = int(self.__yDivisionsInput.text)
				assert xDivisions > 0 and yDivisions > 0
			except:
				return

			self.__display.drawGridByDivisions(xDivisions, yDivisions)
		else:
			try:
				xSize = int(self.__xSizeInput.text)
				ySize = int(self.__ySizeInput.text)
				assert xSize > 0 and ySize > 0
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

	def __save(self):
		pass

	def __changeMethod(self, *args):
		if (self.__state == 'divisions'):
			self.__state = 'size'
			self.__loadSizeLeftMenu()
		else:
			self.__state = 'divisions'
			self.__loadDivisionLeftMenu()

	def __processCancel(self, *args):
		if (self.__state == 'saving'):
			self.__state = self.__previousState
			if (self.__state == 'divisions'):
				self.__loadDivisionLeftMenu()
			else:
				self.__loadSizeLeftMenu()
		else:
			self.close()

	def __processDone(self, *args):
		if (self.__state == 'saving'):
			self.__save()
			self.close()
		else:
			self.__previousState = self.__state
			self.__state = 'saving'
			self.__loadSaveMenu()

	def __setColorOnWhiteImage(self, newColor):
		colorToUse = (
			float(newColor[0])/255.0,
			float(newColor[1])/255.0,
			float(newColor[2])/255.0,
			float(newColor[3])/255.0,
		)
		self.__whiteImage.setColor(colorToUse)

	def __loadSaveMenu(self):
		self.__leftMenu.clear_widgets()
		self.__leftMenu.add_widget(self.__exportColorToAlphaLine)
		self.__leftMenu.add_widget(self.__whiteImage.getImage())
		self.__leftMenu.add_widget(self.__keepOriginalLine)
		self.__leftMenu.add_widget(Label(text = '', size_hint = (1.0, 0.5)))
		self.__leftMenu.add_widget(self.__doneButton)
		self.__leftMenu.add_widget(self.__cancelButton)

	def __createLeftMenuUi(self):
		# x divisions
		self.__xDivisionsInput = NumberInput(multiline = False, size_hint = (1.0, 0.05), text = '0')
		self.__yDivisionsInput = NumberInput(multiline = False, size_hint = (1.0, 0.05), text = '0')

		# size divisions
		self.__xSizeInput = NumberInput(multiline = False, size_hint = (1.0, 0.05), text = '32')
		self.__ySizeInput = NumberInput(multiline = False, size_hint = (1.0, 0.05), text = '32')
		self.__xSkipInput = NumberInput(multiline = False, size_hint = (1.0, 0.05), text = '0')
		self.__ySkipInput = NumberInput(multiline = False, size_hint = (1.0, 0.05), text = '0')

		# save menu
		self.__keepOriginalLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		self.__keepOriginalCheckbox = CheckBox(size_hint = (0.2, 1.0))
		self.__keepOriginalLine.add_widget(self.__keepOriginalCheckbox)
		self.__keepOriginalLine.add_widget(Label(text = 'Keep\nimage\non list.', size_hint = (0.8, 1.0)))
		self.__exportColorToAlphaLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		self.__exportColorToAlphaCheckbox = CheckBox(size_hint = (0.2, 1.0))
		self.__exportColorToAlphaLine.add_widget(self.__exportColorToAlphaCheckbox)
		self.__exportColorToAlphaLine.add_widget(Label(text = 'Export\ncolor to\nalpha.', size_hint = (0.8, 1.0)))
		self.__whiteImage = WhiteImage()
		self.__whiteImage.getImage().size_hint = (1.0, 0.2)

		# buttons, mostly shared
		self.__cancelButton = CancelableButton(on_release = self.__processCancel, text = 'Cancel',
				size_hint = (1.0, 0.05))
		self.__doneButton = CancelableButton(on_release = self.__processDone, text = 'Done', size_hint = (1.0, 0.05))
		self.__splitButton = CancelableButton(on_release = self.__splitImage, text = 'Split', size_hint = (1.0, 0.05))
		self.__switchButton = CancelableButton(on_release = self.__changeMethod, text = 'Change method',
			size_hint = (1.0, 0.05))

	def __loadDivisionLeftMenu(self):
		self.__leftMenu.clear_widgets()
		self.__leftMenu.add_widget(Label(text = 'Divisions on x', size_hint = (1.0, 0.05)))
		self.__leftMenu.add_widget(self.__xDivisionsInput)
		self.__leftMenu.add_widget(Label(text = 'Divisions on y', size_hint = (1.0, 0.05)))
		self.__leftMenu.add_widget(self.__yDivisionsInput)
		self.__leftMenu.add_widget(Label(text = '', size_hint = (1.0, 0.6)))
		self.__leftMenu.add_widget(self.__switchButton)
		self.__leftMenu.add_widget(self.__splitButton)
		self.__leftMenu.add_widget(self.__doneButton)
		self.__leftMenu.add_widget(self.__cancelButton)

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
		self.__leftMenu.add_widget(Label(text = '', size_hint = (1.0, 0.4)))
		self.__leftMenu.add_widget(self.__switchButton)
		self.__leftMenu.add_widget(self.__splitButton)
		self.__leftMenu.add_widget(self.__doneButton)
		self.__leftMenu.add_widget(self.__cancelButton)

	def __processAddSelection(self, *args):
		selection = self.__display.getCurrentSelection()
		if (selection is not None):
			self.__selectionTree.addItem(selection)

	def __processAddPartsSelection(self, *args):
		selection = self.__display.getCurrentSelection()
		if (selection is not None):
			sizeX = selection.getSizeX() / selection.getPartsX()
			sizeY = selection.getSizeY() / selection.getPartsY()
			x = selection.getX()
			y = selection.getY()
			l = []
			for i in range(selection.getPartsX()):
				for j in range(selection.getPartsY()):
					selectionToAdd = SpriteSelection(
							x + (i * sizeX),
							y + (j * sizeY),
							sizeX,
							sizeY
					)
					l.append(selectionToAdd)

			self.__selectionTree.addItemList(l)

	def __showSelection(self, *args):
		selection = self.__selectionTree.getSelection()
		if (selection is not None):
			self.__display.previewSelection(selection)

	def __processRemoveFromSelection(self, *args):
		self.__selectionTree.removeItem()

	def __processClearSelection(self, *args):
		self.__selectionTree.clearAllItems()

	def __createRightMenuUi(self):
		self.__selectionTree = ResourceLoaderList(size_hint = (1.0, 0.75))
		self.__addFullSelection = CancelableButton(text = 'Add as one', size_hint = (1.0, 0.05),
			on_release = self.__processAddSelection)
		self.__addPartSelection = CancelableButton(text = 'Add parts', size_hint = (1.0, 0.05),
			on_release = self.__processAddPartsSelection)
		self.__showSelection = CancelableButton(text = 'Show', size_hint = (1.0, 0.05),
			on_release = self.__showSelection)
		self.__removeCurrent = CancelableButton(text = 'Remove', size_hint = (1.0, 0.05),
			on_release = self.__processRemoveFromSelection)
		self.__clearSelection = CancelableButton(text = 'Clear', size_hint = (1.0, 0.05),
			on_release = self.__processClearSelection)

		self.__rightMenu.add_widget(self.__selectionTree.getLayout())
		self.__rightMenu.add_widget(self.__addFullSelection)
		self.__rightMenu.add_widget(self.__addPartSelection)
		self.__rightMenu.add_widget(self.__showSelection)
		self.__rightMenu.add_widget(self.__removeCurrent)
		self.__rightMenu.add_widget(self.__clearSelection)

	def __init__(self):
		super(ResourceLoaderPopup, self).__init__()

		self.__popup = Popup(title = 'Resource Loader')
		self.__state = 'size'

		self.__layout = BoxLayout(orientation = 'horizontal')

		self.__leftMenu = BoxLayout(orientation = 'vertical', size_hint = (0.15, 1.0))
		self.__createLeftMenuUi()
		self.__loadSizeLeftMenu()

		self.__middleMenu = BoxLayout(orientation = 'vertical', size_hint = (0.7, 1.0))
		self.__display = ResourceLoaderDisplay(colorMethod = self.__setColorOnWhiteImage)
		self.__middleMenu.add_widget(self.__display.getLayout())

		self.__rightMenu = BoxLayout(orientation = 'vertical', size_hint = (0.15, 1.0))
		self.__createRightMenuUi()

		self.__layout.add_widget(self.__leftMenu)
		self.__layout.add_widget(self.__middleMenu)
		self.__layout.add_widget(self.__rightMenu)

		self.__popup.content = self.__layout

	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__display.loadImage('tiles/wateranimate2.png')
		self.__popup.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()

