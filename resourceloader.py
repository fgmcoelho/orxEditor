from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.scrollview import ScrollView
from kivy.graphics.vertex_instructions import Line
from kivy.graphics import Color

from os.path import basename

from uisizes import resourceLoderSize, defaultLabelSize, defaultButtonSize, defaultInputSize, defaultFontSize,\
	defaultDoubleLineSize
from editorheritage import SeparatorLabel, LayoutGetter, MouseModifiers
from editorutils import CancelableButton, AutoReloadTexture, Alert, Dialog, convertKivyCoordToOrxCoord, ChangesConfirm
from editorutils import NumberInput, AlignedLabel, EmptyScrollEffect
from editorobjects import resetAnitionOnObjectList
from keyboard import KeyboardAccess, KeyboardGuardian
from splittedimagemap import SplittedImageExporter, SplittedImageImporter
from spriteinfo import SpriteSelection, AnimationInfo, LinkInfo
from modulesaccess import ModulesAccess

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
		self.draw((0., 1., 0., 0.3))

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
		self.draw((1., 0., 0., 1.0))

	def unselect(self):
		if (self.__marked):
			self.draw((0., 1., 0., 0.3))
			self.__marked = False

	def clear(self):
		self.__canvasRef.remove(self.__color)
		self.__canvasRef.remove(self.__operation)

	def getMarked(self):
		return self.__marked

class ResourceLoaderDisplay(LayoutGetter, MouseModifiers):
	def __clearGraphicGrid(self):
		self.__currentSelection = None
		for line in self.__gridGraphics:
			for cell in line:
				cell.unselect()

	def __posToGridCoords(self, x, y):
		i = (x - self.__xSkip) / self.__xSize
		if (i < 0):
			return (None, None)
		elif (i >= self.__columns):
			return (None, None)

		end = (self.__originalSize[1]) - self.__ySkip
		start = end - (self.__rows * self.__ySize)
		if (y < start or y > end):
			return (None, None)

		j = self.__rows - ((y - start) / self.__ySize)
		return (int(j), int(i))

	def __handleTouchMove(self, touch):
		if (touch.is_mouse_scrolling == True):
			return

		if (self._layout.collide_point(*touch.pos) == False):
			return
		if(touch.button == 'left'):
			self.updateSelection(touch)
		if (touch.button == 'right'):
			self.__defaultTouchMove(touch)

	def __handleScrollAndPassTouchDownToChildren(self, touch):
		if (self._layout.collide_point(*touch.pos) == False):
			return

		if (touch.is_mouse_scrolling == True):
			if (touch.button == "scrollup"):
				self.decreaseZoom()
			elif (touch.button == "scrolldown"):
				self.increaseZoom()
			return

		self.updateMouseDown(touch)
		if (self._isLeftPressed == True and self._isRightPressed == False):
			self._layout.do_scroll = False

		if (touch.button == 'left'):
			imgCoords = self.__currentImage.to_widget(touch.pos[0], touch.pos[1])
			if (self.__currentImage is not None and self.__currentImage.collide_point(*imgCoords) == True):
				self.startSelection(touch)
			else:
				self.__clearGraphicGrid()

		self.__defaultTouchDown(touch)

	def __handleScrollAndPassTouchUpToChildren(self, touch):
		if (touch.is_mouse_scrolling == True):
			return

		self.updateMouseUp(touch)
		if (self._isRightPressed == True or self._isLeftPressed == False):
			self._layout.do_scroll = True

		if (touch.button == 'left'):
			self.finishSelection(touch)

		elif (touch.button == 'right'):
			self.__defaultTouchUp(touch)

	def __clearSelectionGrid(self):
		for line in self.__gridGraphics:
			for cell in line:
				cell.clear()
		self.__gridGraphics = []

		if (self.__selectionPreview is not None):
			self.__currentImage.canvas.remove(self.__selectionPreview)

		self.__selectionPreview = None
		self.__currentSelection = None

	def __drawFromValues(self, xInc, yInc, xSkip = 0, ySkip = 0):
		self.__clearSelectionGrid()
		self.__xSize = xInc
		self.__ySize = yInc
		self.__xSkip = xSkip
		self.__ySkip = ySkip
		self.__doDrawGrid()

	def __redrawGrid(self):
		coords = []
		i = 0
		for line in self.__gridGraphics:
			j = 0
			for cell in line:
				if (cell.getMarked() == True):
					coords.append((i, j))
				j += 1
			i += 1

		self.__doDrawGrid()
		for i, j in coords:
			self.__gridGraphics[i][j].select()

	def __doDrawGrid(self):
		j = self.__originalSize[1] - self.__ySkip
		while j - self.__ySize >= 0:
			i = self.__xSkip
			line = []
			while i + self.__xSize <= self.__originalSize[0]:
				line.append(GridCell(self.__currentImage.canvas, i, j, self.__xSize, self.__ySize))
				i += self.__xSize
			j -= self.__ySize
			self.__gridGraphics.append(line)

		if (self.__gridGraphics != []):
			self.__columns = len(self.__gridGraphics[0])
			self.__rows = len(self.__gridGraphics)

	def __setStartState(self):
		self.__zoom = 1.0
		self.__selectionStarted = False
		self.__selectionStartPos = None
		self.__currentSelection = None
		self.__gridGraphics = []

	def __applyZoom(self, adjust):
		layoutSize = tuple(self._scrollLayout.size)
		scale = int(self.__currentImage.scale)
		layoutSize = (self.__originalSize[0] * (scale + adjust) , self.__originalSize[1] * (scale + adjust) )
		self._scrollLayout.size = layoutSize
		self.__currentImage.scale += adjust
		self.__currentImage._set_pos((0, 0))
		if (self.__gridGraphics != []):
			self.__redrawGrid()

	def __init__(self, **kwargs):
		super(self.__class__, self).__init__(**kwargs)
		self._layout = ScrollView(size_hint = (1.0, 1.0), effect_cls = EmptyScrollEffect)
		self.__defaultTouchMove = self._layout.on_touch_move
		self.__defaultTouchDown = self._layout.on_touch_down
		self.__defaultTouchUp = self._layout.on_touch_up
		self._layout.on_touch_down = self.__handleScrollAndPassTouchDownToChildren
		self._layout.on_touch_up = self.__handleScrollAndPassTouchUpToChildren
		self._layout.on_touch_move = self.__handleTouchMove

		self.__setStartState()
		self.__selectionPreview = None
		self.__zoomTranslate = None
		self.__zoomScale = None
		self._scrollLayout = RelativeLayout(size_hint = (None, None), size = (100, 100))
		self.__currentImage = None
		self._layout.add_widget(self._scrollLayout)

	def updateSelection(self, touch):
		pass

	def startSelection(self, touch):
		if (self.__currentImage is not None and self.__gridGraphics != [] and self.__selectionStarted == False):
			self.__clearGraphicGrid()
			posToUse = self.__currentImage.to_widget(*touch.pos)
			sj, si = self.__posToGridCoords(*posToUse)
			if (sj == None or si == None):
				return
			self.__selectionStartPos = posToUse
			self.__selectionStarted = True
			self.__gridGraphics[sj][si].select()

	def finishSelection(self, touch):
		if (self.__currentImage is not None and self.__gridGraphics != [] and self.__selectionStarted == True):
			pos = self.__currentImage.to_widget(*touch.pos)
			fj, fi = self.__posToGridCoords(*pos)
			sj, si = self.__posToGridCoords(*self.__selectionStartPos)
			if (fj == None or fi == None or sj == None or si == None):
				self.__selectionStarted = False
				return
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

			self.__currentSelection = SpriteSelection(
				(loopStartIndexI * self.__xSize) + self.__xSkip,
				self.__originalSize[1] - (((loopFinalIndexJ + 1) * self.__ySize) + self.__ySkip),
				(loopFinalIndexI - loopStartIndexI + 1) * self.__xSize,
				(loopFinalIndexJ - loopStartIndexJ + 1) * self.__ySize,
				(loopFinalIndexI - loopStartIndexI + 1),
				(loopFinalIndexJ - loopStartIndexJ + 1)
			)
		self.__selectionStarted = False

	def increaseZoom(self, *args):
		if (self.__currentImage is not None):
			if (self.__currentImage.scale >= 8):
				return
			self.__applyZoom(1)

	def decreaseZoom(self, *args):
		if (self.__currentImage is not None):
			if (self.__currentImage.scale <= 1):
				return
			self.__applyZoom(-1)

	def loadImage(self, path):
		self.clearPreview()
		self.__setStartState()
		if (self.__currentImage is not None):
			self._scrollLayout.remove_widget(self.__currentImage)
			self._scrollLayout.canvas.clear()

		im = Image(source = path)
		self.__texture = AutoReloadTexture(im.texture.size, im)
		self.__currentImage = Image(size = im.texture.size, texture = self.__texture.getTexture())
		self.__originalSize = tuple(im.texture.size)
		reloadableImage = Image(size = im.texture.size, texture = self.__texture.getTexture())
		self.__currentImage = Scatter(do_translation = False, do_scale = False, do_rotation = False)
		self.__currentImage.add_widget(reloadableImage)
		self._scrollLayout.size = tuple((int(im.texture.size[0]), int(im.texture.size[1])))
		self._scrollLayout.add_widget(self.__currentImage)
		self._layout.scroll_x = 0.0
		self._layout.scroll_y = 1.0
		self._layout._update_effect_x_bounds()
		self._layout._update_effect_y_bounds()

	def drawGridByDivisions(self, xDivisions, yDivisions):
		xInc = int(self.__originalSize[0] / xDivisions)
		yInc = int(self.__originalSize[1] / yDivisions)
		self.__drawFromValues(xInc, yInc)

	def drawGridBySize(self, xSize, ySize, xSkip, ySkip):
		self.__drawFromValues(xSize, ySize, xSkip, ySkip)

	def getCurrentSelection(self):
		return self.__currentSelection

	def previewSelection(self, selection):
		self.__clearSelectionGrid()
		x = selection.getX()
		y = selection.getY()
		xSize = selection.getSizeX()
		ySize = selection.getSizeY()
		with self.__currentImage.canvas:
			self.__selectionPreview = Line(points = [
				x, y,
				x, y + ySize,
				x + xSize, y + ySize,
				x + xSize, y],
				close = True, width = 1
			)

	def clearPreview(self):
		if (self.__selectionPreview is not None):
			self.__currentImage.canvas.remove(self.__selectionPreview)
			self.__selectionPreview = None

	def getSize(self):
		return self._scrollLayout.size

class ResourceLoaderList(LayoutGetter):
	def __handleScrollAndPassTouchDownToChildren(self, touch):
		if (self._layout.collide_point(*touch.pos) == False):
			return

		self.__defaultTouchDown(touch)

	def __callShowMethod(self, label, touch):
		if (label.collide_point(*touch.pos) == True and touch.is_mouse_scrolling == False and
				touch.is_double_tap == True and self.getSelection() is not None):
			self.__showMethod()

	def __doAddItemRender(self, selection, identifier):
		pos = convertKivyCoordToOrxCoord((selection.getX(), selection.getY() + selection.getSizeY()), self.__maxY)
		node = TreeViewLabel(text='Pos: (' + str(pos[0]) + ', ' + str(pos[1]) + ') | Size: (' + \
				str(selection.getSizeX()) + ', ' + str(selection.getSizeY()) + ')', id = 'selection#' + \
				str(identifier), on_touch_down = self.__callShowMethod)
		self.__tree.add_node(node)
		self._layout.height = self.__tree.minimum_height

	def __renderLoadedList(self, selectionItems):
		for item in selectionItems:
			self.__doAddItemRender(item[1], item[0])

	def __doAddItem(self, selection):
		identifier = self.__resourceInfo.addSelection(selection)
		self.__doAddItemRender(selection, identifier)
		ModulesAccess.get('ResourceLoader').registerChanges()

	def __clearUi(self):
		for node in self.__tree.children:
			self.__tree.remove_node(node)

		self._layout.height = self.__tree.minimum_height

	def _adjustTreeSize(self, *args):
		self._scrollLayout.size[1] = self.__tree.minimum_height

	def getSelection(self):
		if (self.__tree.selected_node is not None):
			itemName, itemId = self.__tree.selected_node.id.split('#')
			if (itemName != 'root'):
				return self.__resourceInfo.getSelectionById(int(itemId))
		return None

	def getNumberOfSelections(self):
		if (self.__resourceInfo is not None):
			return self.__resourceInfo.getNumberOfSelections()
		return 0

	def getNumberOfAnimations(self):
		if (self.__resourceInfo is not None):
			return self.__resourceInfo.getNumberOfAnimationInfos()
		return 0

	def getNumberOfLinks(self):
		if (self.__resourceInfo is not None):
			return self.__resourceInfo.getNumberOfLinks()
		return 0

	def getNumberOfRelatedAnimationsAndLinks(self, selection):
		if (selection is not None and self.__resourceInfo is not None and selection.getId() is not None):
			return self.__resourceInfo.countAnimationInfoAndLinksWithSelectionId(selection.getId())
		return 0, 0

	def getNamesOfRelatedAnimations(self, selection):
		if (selection is not None and self.__resourceInfo is not None and selection.getId() is not None):
			return self.__resourceInfo.getAnimationNamesWithSelectionId(selection.getId())
		return []

	def clearAllItems(self):
		self.__clearUi()
		self.__resourceInfo.clear()
		ModulesAccess.get('ResourceLoader').registerChanges()

	def removeItem(self):
		if (self.__tree.selected_node is not None):
			itemName, itemId = self.__tree.selected_node.id.split('#')
			if (itemName != 'root'):
				self.__tree.remove_node(self.__tree.selected_node)
				self.__resourceInfo.removeSelectionById(int(itemId))
				self.__tree.select_node(self.__tree.root)
				self._layout.height = self.__tree.minimum_height
				ModulesAccess.get('ResourceLoader').registerChanges()

	def addItemList(self, selectionList):
		count = 0
		for selection in selectionList:
			if (self.__resourceInfo.hasSameSelection(selection) == False):
				self.__doAddItem(selection)
			else:
				count += 1

		if (count != 0):
			if (count == 1):
				warn = Alert('Error', '1 selection could not be added because it\nhas already been added.', 'Ok')
			else:
				warn = Alert('Error',
					str(count) + ' selections could not be added because they\nhave already been added.', 'Ok'
				)

			warn.open()

	def addItem(self, selection):
		if (self.__resourceInfo.hasSameSelection(selection) == True):
			warn = Alert('Error', 'This selection has already been added.', 'Ok')
			warn.open()
			return

		self.__doAddItem(selection)

	def loadImage(self, imageToUse, maxY):
		self.__clearUi()
		self.__maxY = maxY
		self.__resourceInfo = SplittedImageImporter().load(imageToUse)
		self.__renderLoadedList(self.__resourceInfo.getSelectionItems())

	def __init__(self, showMethod, **kwargs):
		self.__resourceInfo = None
		self._layout = ScrollView(effect_cls = EmptyScrollEffect, scroll = (1.0, 1.0))
		self.__tree = TreeView(root_options = dict(text='Resources', id='root#0'), size_hint = (1.0, 1.0),
			expand_root = False)
		self._scrollLayout = RelativeLayout(size = (300, 100), size_hint = (None, None))
		self._scrollLayout.add_widget(self.__tree)
		self._layout.add_widget(self._scrollLayout)
		self.__showMethod = showMethod

		self.__defaultTouchDown = self._layout.on_touch_down
		self._layout.on_touch_down = self.__handleScrollAndPassTouchDownToChildren
		self.__tree.bind(minimum_height=self._adjustTreeSize)

	def save(self):
		if (self.__resourceInfo is not None):
			futureName = basename(self.__resourceInfo.getPath())
			ModulesAccess.get('BaseObjectsMenu').ignoreUpdate(futureName)
			SplittedImageExporter.save(self.__resourceInfo)

			removedAnimations = self.__resourceInfo.getRemovedAnimationNames()
			objList = ModulesAccess.get('SceneHandler').getCurrentSceneObjects()
			resetAnitionOnObjectList(objList, removedAnimations)

			ModulesAccess.get('BaseObjectsMenu').updateResource(self.__resourceInfo)

	def getResourcePath(self):
		return self.__resourceInfo.getPath()

	def importTemplate(self, otherPath):
		if self.__resourceInfo.getPath() == otherPath:
			Alert(
				'Warning',
				'Template file is same as current.',
				'Ok'
			).open()
			return

		templateInfo = SplittedImageImporter().load(otherPath)
		selectionMap = {}
		selectionAddedCount, selectionNotAddedCount = 0, 0

		for selection in templateInfo.getSelectionList():
			searchId = self.__resourceInfo.searchSelection(selection)
			if (searchId == -1):
				newId = self.__resourceInfo.addSelection(selection)
				selectionMap[selection.getId()] = newId
				selectionAddedCount += 1
			else:
				selectionMap[selection.getId()] = searchId
				selectionNotAddedCount += 1

		animationNames = set(self.__resourceInfo.getAnimationNames())
		animationAddedCount, animationNotAddedCount = 0, 0
		animationMap = {}
		for animationInfo in templateInfo.getAnimationInfoList():
			newName = animationInfo.getName()
			if (newName in animationNames):
				newName = 'Copy_of_' + newName
				baseNewName = newName
				i = 0
				while (newName in animationNames):
					newName = baseNewName + '_' + str(i)
					i += 1

			newAnimationInfo = AnimationInfo(newName, animationInfo.getDuration())
			for frameInfo in animationInfo.getFramesInfo():
				newAnimationInfo.addFrameInfo(selectionMap[frameInfo.getId()])

			searchId = self.__resourceInfo.searchAnimation(newAnimationInfo)
			if (searchId == -1):
				newId = self.__resourceInfo.addAnimationInfo(newAnimationInfo)
				animationMap[animationInfo.getId()] = newId
				animationAddedCount += 1
			else:
				animationMap[animationInfo.getId()] = searchId
				animationNotAddedCount += 1

		linkAddedCount, linkNotAddedCount = 0, 0
		for link in templateInfo.getLinksList():
			sourceId = animationMap[link.getSourceId()]
			destinationId = animationMap[link.getDestinationId()]
			newLinkInfo = LinkInfo(sourceId, destinationId, link.getPriority(), link.getProperty())
			searchId = self.__resourceInfo.searchLink(newLinkInfo)
			if (searchId == -1):
				self.__resourceInfo.addLink(newLinkInfo)
				linkAddedCount += 1
			else:
				linkNotAddedCount += 1




class ResourceLoaderPopup(KeyboardAccess, SeparatorLabel, LayoutGetter, ChangesConfirm):
	# Overloaded method
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'tab'):
			if (self.__state in ['divisions', 'size']):
				if (self.__isShiftPressed == False):
					NumberInput.selectInputByFocus(self.__state)
				else:
					NumberInput.selectInputByFocus(self.__state, reverse = True)

		elif (keycode[1] == 'enter'):
			self.__splitImage()

		elif (keycode[1] == 'up' and self.__state == 'size' and self.__checkAnyHasFocus('size') == False):
			try:
				ySize = int(self.__ySizeInput.text)
				ySkip = int(self.__ySkipInput.text)
				assert ySize != 0
			except:
				return
			ySkip -= 1
			ySkip = ySkip % ySize
			self.__ySkipInput.text = str(ySkip)
			self.__splitImage()

		elif (keycode[1] == 'down' and self.__state == 'size' and self.__checkAnyHasFocus('size') == False):
			try:
				ySize = int(self.__ySizeInput.text)
				ySkip = int(self.__ySkipInput.text)
				assert ySize != 0
			except:
				return
			ySkip += 1
			ySkip = ySkip % ySize
			self.__ySkipInput.text = str(ySkip)
			self.__splitImage()

		elif (keycode[1] == 'left' and self.__state == 'size' and self.__checkAnyHasFocus('size') == False):
			try:
				xSize = int(self.__xSizeInput.text)
				xSkip = int(self.__xSkipInput.text)
				assert xSize != 0
			except:
				return
			xSkip -= 1
			xSkip = xSkip % xSize
			self.__xSkipInput.text = str(xSkip)
			self.__splitImage()

		elif (keycode[1] == 'right' and self.__state == 'size' and self.__checkAnyHasFocus('size') == False):
			try:
				xSize = int(self.__xSizeInput.text)
				xSkip = int(self.__xSkipInput.text)
				assert xSize != 0
			except:
				return
			xSkip += 1
			xSkip = xSkip % xSize
			self.__xSkipInput.text = str(xSkip)
			self.__splitImage()

		elif (keycode[1] == 'a'):
			self.__display.increaseZoom()

		elif (keycode[1] == 's'):
			self.__display.decreaseZoom()

		elif (keycode[1] == 'o'):
			self.__processAddSelection()

		elif (keycode[1] == 'p'):
			self.__processAddPartsSelection()

		elif (keycode[1] == 'delete'):
			self.__processRemoveFromSelection()

		elif (keycode[1] == 'escape'):
			self.alertExit()

	# Overloaded method
	def _processKeyDown(self, keyboard, keycode, text, modifiers):
		if ('shift' in modifiers):
			self.__isShiftPressed = True
		else:
			self.__isShiftPressed = False

	def __checkAnyHasFocus(self, state):
		if (state == 'divisions'):
			return self.__xDivisionsInput.focus or self.__yDivisionsInput.focus
		else:
			return (self.__xSizeInput.focus or self.__ySizeInput.focus or
				self.__xSkipInput.focus or self.__ySkipInput.focus)

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
				if (xSkip >= xSize):
					xSkip = xSkip % xSize
					self.__xSkipInput.text = str(xSkip)
			except:
				xSkip = 0
			try:
				ySkip = int(self.__ySkipInput.text)
				if (ySkip >= ySize):
					ySkip = ySkip % ySize
					self.__ySkipInput.text = str(ySkip)
			except:
				ySkip = 0

			self.__display.drawGridBySize(xSize, ySize, xSkip, ySkip)

	def __changeMethod(self, *args):
		if (self.__state == 'divisions'):
			self.__state = 'size'
			self.__loadSizeLeftMenu()
		else:
			self.__state = 'divisions'
			self.__loadDivisionLeftMenu()

	def __processCancel(self, *args):
		self.alertExit()

	def __processDone(self, *args):
		self.__selectionTree.save()
		self.close()

	def __doSetAsTemplate(self):
		self.__templatePath = self.__selectionTree.getResourcePath()

	def __setAsTemplate(self, *args):
		if (self.__templatePath == ''):
			Alert(
				'Success',
				'Template path successfully set to:\n' + basename(self.__selectionTree.getResourcePath()),
				'Ok'
			).open()
			self.__doSetAsTemplate()
		elif (self.__templatePath == self.__selectionTree.getResourcePath()):
			Alert(
				'Success',
				'Template path successfully set to:\n' + basename(self.__selectionTree.getResourcePath()),
				'Ok'
			).open()
		else:
			Dialog(
				self.__doSetAsTemplate,
				'Confirmation',
				'Are you sure you want to replace\n' + self.__templatePath + '\nby\n' +
					basename(self.__selectionTree.getResourcePath()) + '?',
				'Yes', 'No'
			).open()

	def __applyTemplate(self, *args):
		if (self.__templatePath != ''):
			self.__selectionTree.importTemplate(self.__templatePath)

	def __createLeftMenuUi(self):
		# x divisions
		inputOptions = defaultInputSize.copy()
		inputOptions['multiline'] = False
		self.__xDivisionsInput = NumberInput(text = '0', module = 'divisions', **inputOptions)
		self.__yDivisionsInput = NumberInput(text = '0', module = 'divisions', **inputOptions)

		# size divisions
		self.__xSizeInput = NumberInput(text = '0', module = 'size', **inputOptions)
		self.__ySizeInput = NumberInput(text = '0', module = 'size', **inputOptions)
		self.__xSkipInput = NumberInput(text = '0', module = 'size', **inputOptions)
		self.__ySkipInput = NumberInput(text = '0', module = 'size', **inputOptions)

		# buttons, mostly shared
		self.__cancelButton = CancelableButton(on_release = self.__processCancel, text = 'Cancel', **defaultButtonSize)
		self.__doneButton = CancelableButton(on_release = self.__processDone, text = 'Done', **defaultButtonSize)
		self.__splitButton = CancelableButton(on_release = self.__splitImage, text = 'Split (enter)',
			**defaultButtonSize)
		self.__switchButton = CancelableButton(on_release = self.__changeMethod, text = 'Change method',
			**defaultButtonSize)
		self.__zoomPlusButton = CancelableButton(on_release = self.__display.increaseZoom, text = 'Zoom + (a)',
			**defaultButtonSize)
		self.__zoomMinusButton = CancelableButton(on_release = self.__display.decreaseZoom, text = 'Zoom - (s)',
			**defaultButtonSize)
		self.__setAsTemplateButton = CancelableButton(on_release = self.__setAsTemplate, text = 'Set as template',
			**defaultButtonSize)
		self.__applyTemplateButton = CancelableButton(on_release = self.__applyTemplate, text = 'Apply template',
			**defaultButtonSize)

		multipleLineSize = defaultDoubleLineSize.copy()
		multipleLineSize['height'] = defaultFontSize * 5
		self.__helpText = AlignedLabel(
			text = 'Once the grid\nis drawn you\ncan use the\narrow keys to\nmove the grid.',
			**multipleLineSize)

	def __loadDivisionLeftMenu(self, focusIndex = None):
		self.__leftMenu.clear_widgets()
		self.__leftMenu.add_widget(AlignedLabel(text = 'Divisions on x', **defaultLabelSize))
		self.__leftMenu.add_widget(self.__xDivisionsInput)
		self.__leftMenu.add_widget(AlignedLabel(text = 'Divisions on y', **defaultLabelSize))
		self.__leftMenu.add_widget(self.__yDivisionsInput)
		self.__leftMenu.add_widget(self.getSeparator())
		self.__leftMenu.add_widget(self.__switchButton)
		self.__leftMenu.add_widget(self.__zoomPlusButton)
		self.__leftMenu.add_widget(self.__zoomMinusButton)
		self.__leftMenu.add_widget(self.__setAsTemplateButton)
		self.__leftMenu.add_widget(self.__applyTemplateButton)
		self.__leftMenu.add_widget(self.__splitButton)
		self.__leftMenu.add_widget(self.__doneButton)
		self.__leftMenu.add_widget(self.__cancelButton)

	def __loadSizeLeftMenu(self):
		self.__leftMenu.clear_widgets()
		self.__leftMenu.add_widget(AlignedLabel(text = 'Size on x', **defaultLabelSize))
		self.__leftMenu.add_widget(self.__xSizeInput)
		self.__leftMenu.add_widget(AlignedLabel(text = 'Size on y', **defaultLabelSize))
		self.__leftMenu.add_widget(self.__ySizeInput)
		self.__leftMenu.add_widget(AlignedLabel(text = 'Skip on x', **defaultLabelSize))
		self.__leftMenu.add_widget(self.__xSkipInput)
		self.__leftMenu.add_widget(AlignedLabel(text = 'Skip on y', **defaultLabelSize))
		self.__leftMenu.add_widget(self.__ySkipInput)
		self.__leftMenu.add_widget(self.__helpText)
		self.__leftMenu.add_widget(self.getSeparator())
		self.__leftMenu.add_widget(self.__switchButton)
		self.__leftMenu.add_widget(self.__zoomPlusButton)
		self.__leftMenu.add_widget(self.__zoomMinusButton)
		self.__leftMenu.add_widget(self.__setAsTemplateButton)
		self.__leftMenu.add_widget(self.__applyTemplateButton)
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

	def __doClearSelection(self, *args):
		self.__selectionTree.removeItem()
		self.__display.clearPreview()

	def __processRemoveFromSelection(self, *args):
		selection = self.__selectionTree.getSelection()
		if (selection is not None):
			animationNumber, linksNumber = self.__selectionTree.getNumberOfRelatedAnimationsAndLinks(selection)
			if animationNumber == 0:
				message = 'This will remove the selecton.\nThis operation can\'t be reverted!'
			else:
				objList = ModulesAccess.get('SceneHandler').getCurrentSceneObjects()
				relatedAnimsNames = set(self.__selectionTree.getNamesOfRelatedAnimations(selection))
				objCount = 0
				for obj in objList:
					objAnimation = obj.getAnimation()
					if (objAnimation is not None and objAnimation in relatedAnimsNames):
						objCount += 1

				if (linksNumber == 0):
					message = 'This will remove the selection and\n%d animation%s.\n' % \
						(animationNumber, 's' if animationNumber > 1 else '')
				else:
					message = 'This will remove the selection,\n%d animation%s and\n'\
						'%d animation link%s.\n' % \
						(
							animationNumber, 's' if animationNumber > 1 else '',
							linksNumber, 's' if linksNumber > 1 else ''
						)
				if (objCount > 0):
					message += 'It will also reset the animation on %d object%s.\n' % \
						(objCount, 's' if objCount > 1 else '')

				message += 'This operation can\'t be reverted!'

			dialog = Dialog(self.__doClearSelection,
				'Confirmation', message,
				'Ok', 'Cancel')
			dialog.open()

	def __doClearAllItems(self, *args):
		self.__selectionTree.clearAllItems()
		self.__display.clearPreview()

	def __processClearSelection(self, *args):
		numberOfSelections = self.__selectionTree.getNumberOfSelections()
		if (numberOfSelections == 0):
			return
		else:
			animationNumber = self.__selectionTree.getNumberOfAnimations()
			linksNumber = self.__selectionTree.getNumberOfLinks()
			objList = ModulesAccess.get('SceneHandler').getCurrentSceneObjects()
			objCount = 0
			for obj in objList:
				if (obj.getAnimation() is not None):
					objCount += 1

			message = 'This will remove %d selection%s' % (numberOfSelections, "s" if numberOfSelections > 1 else "")
			if (animationNumber > 0):
				message += '%s\n%d animation%s' % (
					',' if linksNumber > 0 or objCount > 0 else ' and',
					animationNumber,
					's' if animationNumber > 1 else ''
				)

			if (linksNumber > 0):
				message += '%s\n%d animation link%s' % (
					',' if objCount > 0 else ' and',
					linksNumber,
					's' if linksNumber > 1 else ''
				)

			if (objCount > 0):
				message += ' and\n%d object%s animation%s' % (
					objCount, 's' if objCount > 0 else '', 's' if objCount > 0 else ''
				)

			message += '.\nThis operation can\'t be reverted.'
			dialog = Dialog(self.__doClearAllItems,
				'Confirmation', message,
				'Ok', 'Cancel')
			dialog.open()

	def __createRightMenuUi(self):
		self.__selectionTree = ResourceLoaderList(size_hint = (1.0, 1.0), showMethod = self.__showSelection)

		self.__addFullSelection = CancelableButton(text = 'Add as one (o)', on_release = self.__processAddSelection,
			**defaultLabelSize)
		self.__addPartSelection = CancelableButton(text = 'Add parts (p)',
			on_release = self.__processAddPartsSelection, **defaultLabelSize)
		self.__showSelection = CancelableButton(text = 'Show', on_release = self.__showSelection,
			**defaultLabelSize)
		self.__removeCurrent = CancelableButton(text = 'Remove (del)', on_release = self.__processRemoveFromSelection,
			**defaultLabelSize)
		self.__clearSelection = CancelableButton(text = 'Clear', on_release = self.__processClearSelection,
			**defaultLabelSize)

		self.__rightMenu.add_widget(self.__selectionTree.getLayout())
		self.__rightMenu.add_widget(self.__addFullSelection)
		self.__rightMenu.add_widget(self.__addPartSelection)
		self.__rightMenu.add_widget(self.__showSelection)
		self.__rightMenu.add_widget(self.__removeCurrent)
		self.__rightMenu.add_widget(self.__clearSelection)

	def __setStartState(self):
		self.__state = 'size'
		self.__loadSizeLeftMenu()

	def __init__(self):
		super(ResourceLoaderPopup, self).__init__()
		self.__isShiftPressed = False
		self.__display = ResourceLoaderDisplay()

		self.__popup = Popup(title = 'Resource Loader', auto_dismiss = False)
		self._layout = BoxLayout(orientation = 'horizontal')

		self.__leftMenu = BoxLayout(orientation = 'vertical', size_hint = (None, 1.0),
			width = resourceLoderSize['width'])
		self.__createLeftMenuUi()
		self.__setStartState()

		self.__middleMenu = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__middleMenu.add_widget(self.__display.getLayout())

		self.__rightMenu = BoxLayout(orientation = 'vertical', size_hint = (None, 1.0),
			width = resourceLoderSize['width'])
		self.__createRightMenuUi()

		self._layout.add_widget(self.__leftMenu)
		self._layout.add_widget(self.__middleMenu)
		self._layout.add_widget(self.__rightMenu)

		self.__templatePath = ''
		self.__shouldSetTemplate = False

		self.__popup.content = self._layout
		ModulesAccess.add('ResourceLoader', self)

	def open(self, path):
		KeyboardGuardian.Instance().acquireKeyboard(self)

		self.resetChanges()
		self.__setStartState()
		self.__display.loadImage(path)
		sizeToUse = self.__display.getSize()
		self.__selectionTree.loadImage(path, sizeToUse[1])
		self.__popup.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__popup.dismiss()

