#!/usr/bin/python
from kivy import require
require('1.7.2')

from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.config import Config
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.uix.gridlayout import GridLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.core.window import Window
from kivy.uix.progressbar import ProgressBar
from kivy.graphics.texture import Texture

from sys import argv, exit
from ConfigParser import ConfigParser
from os.path import isdir, isfile, join, exists
from os import listdir, getcwd, sep as pathSeparator

from editorutils import Dialog, AlertPopUp

class LeftMenu:

	def __processSplit(self, notUsed = None):
		try:
			width = int(self.__widthInput.text)
			height = int(self.__heightInput.text)
			startX = int(self.__initialXInput.text)
			startY = int(self.__initialYInput.text)
			assert (width > 0 and height > 0)

		except:
			return

		self.__displayReference.updateDisplay(width, height, startX, startY)

	def __processRelativeSplit(self, notUsed = None):
		try:
			partitionOnX = int (self.__partitionOnXInput.text)
			partitionOnY = int (self.__partitionOnYInput.text)
			assert (partitionOnX > 0 and partitionOnY > 0)

		except:
			return

		self.__displayReference.updateDisplayRelative(partitionOnX, partitionOnY)

	def __reset(self, notUsed = None):
		self.__displayReference.showSingleBaseImage()
	
	def __export(self, notUsed = None):
		colorToAlpha = None
		if (self.__colorToAlphaCheckbox.active == True):
			colorToAlpha = self.__hexColor

		self.__exportPopup.dismiss()
		self.__dialog.dismiss()

		if(self.__displayReference.saveSelectedImages(self.__finalName + '.png', colorToAlpha, self.__divs) == False):
			self.__alert.setText('Error creating the message')
			self.__alert.open()

		self.__cancelExport()

	def __validateExportOptions(self, notUsed = None):
		
		self.__finalName = ''
		self.__divs = None

		baseName = self.__exportBaseNameInput.text
		if (baseName == ''):
			self.__alert.setText('You must give a base name')
			self.__alert.open()
			return

		try:
			xdivs = int (self.__exportXdivisions.text)
			ydivs = int (self.__exportYdivisions.text)

		except:
			self.__alert.setText('Invalid number of divsions.')
			self.__alert.open()
			return
		
		if ((xdivs != 0 and ydivs == 0) or (ydivs != 0 and xdivs == 0)):
			self.__alert.setText(
				'Invalid custom division, either both\n'\
				'or neither must be zero.\n'\
				'If both are zero the program will\n'\
				'automatically set their values.')
			self.__alert.open()
			return

		if (xdivs != 0 and ydivs != 0 and xdivs * ydivs < self.__displayReference.countSelectedImages()):
			self.__alert.setText(
				'Number of divisions is too low.\n'\
				'It must be bigger than the number\n'\
				'of images selected to be exported.\n'\
				'Current value: ' + str(xdivs * ydivs) + '.\n'\
				'Needed value: '+ str(self.__displayReference.countSelectedImages()) + '.'
				)
			self.__alert.open()
			return

		self.__divs = None
		if (xdivs != 0 and ydivs != 0):
			self.__divs = (xdivs, ydivs)
		
		
		if (baseName[-4:] in ['.png', '.opf']):
			baseName = baseName[:-4]

		self.__finalName = baseName
		pngFileExists = isfile(join(self.__exportFileChooser.path, baseName, '.png'))
		opfFileExists = isfile(join(self.__exportFileChooser.path, baseName, '.opf'))
		if (pngFileExists == True or opfFileExists == True):
			dialogText = 'The following files will be overwritten:\n'
			if (pngFileExists == True):
				dialogText += baseName + '.png\n'
			if (opfFileExists == True):
				dialogText += baseName + '.opf\n'

			dialogText += 'Continue?'
			
			self.__dialog.setText(dialogText)
			self.__dialog.open()

		else:
			self.__export()
			

	def __openExportOptions(self, notUsed = None):
		colorToAlpha = None
		if self.__colorToAlphaCheckbox.active == True:
			colorToAlpha = self.__hexColor
			self.__exportColorToAlphaImage.color = self.__whiteImage.color
			if (self.__exportColorToAlphaBox.parent == None):
				self.__exportRightPartBox.remove_widget(self.__exportBlankLabel)
				self.__exportRightPartBox.remove_widget(self.__exportButtonsBottomBar)
				self.__exportRightPartBox.add_widget(self.__exportColorToAlphaBox)
				self.__exportBlankLabel.size_hint = (1.0, 0.1)
				self.__exportRightPartBox.add_widget(self.__exportBlankLabel)
				self.__exportRightPartBox.add_widget(self.__exportButtonsBottomBar)
	
		else:
			self.__exportRightPartBox.remove_widget(self.__exportBlankLabel)
			self.__exportRightPartBox.remove_widget(self.__exportButtonsBottomBar)
			self.__exportRightPartBox.remove_widget(self.__exportColorToAlphaBox)
			self.__exportBlankLabel.size_hint = (1.0, 0.3)
			self.__exportRightPartBox.add_widget(self.__exportBlankLabel)
			self.__exportRightPartBox.add_widget(self.__exportButtonsBottomBar)


		self.__exportPopup.open()


	def __setAplhaColor(self, value):
		newColor = []
		
		self.__hexColor[0] = value[0]
		self.__hexColor[1] = value[1]
		self.__hexColor[2] = value[2]
		self.__hexColor[3] = value[3]
		
		for c in value:
			newColor.append(float(ord(c))/255.0)
		
		self.__whiteImage.color = newColor
	
	def __cancelExport(self, notUsed = None):
		if (self.__lastDisplayUsed == 'Absolute'):
			self.__showSplitLayout()
		else:
			self.__showRelativeSplitLayout()

		self.__displayReference.showSingleBaseImage()

	def __showExportLayoutIfPossible(self, notUsed = None):
		if (self.__displayReference.getState() == DisplayStates.showingSplitResult):
			self.__showExportLayout()

	def __createExportPopup(self):
		self.__exportPopup = Popup(title = 'Export options', auto_dismiss = False, size = (0.8, 0.8))
		
		exportBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 1.0))
		leftPartBox = BoxLayout(orientation = 'vertical', size_hint = (0.7, 1.0))
		self.__exportRightPartBox = BoxLayout(orientation = 'vertical', size_hint = (0.3, 1.0))
		
		self.__exportFileChooser = FileChooserIconView(size_hint = (1.0, 0.9), path = getcwd(), filters = ['*.png', '*.opf'])
		leftPartBox.add_widget(self.__exportFileChooser)
		
		self.__exportRightPartBox.add_widget(Label(text = 'Filename: ', size_hint = (1.0, 0.1)))
		self.__exportBaseNameInput = TextInput(multiline = False, size_hint = (1.0, 0.1))
		self.__exportRightPartBox.add_widget(self.__exportBaseNameInput)
		self.__exportRightPartBox.add_widget(Label(text = 'X divisions: ', size_hint = (1.0, 0.1)))
		self.__exportXdivisions = TextInput(multiline = False, text = '0', size_hint = (1.0, 0.1))
		self.__exportRightPartBox.add_widget(self.__exportXdivisions)
		self.__exportRightPartBox.add_widget(Label(text = 'Y divisions: ', size_hint = (1.0, 0.1)))
		self.__exportYdivisions = TextInput(multiline = False, text = '0', size_hint = (1.0, 0.1))
		self.__exportRightPartBox.add_widget(self.__exportYdivisions)
		
		self.__exportColorToAlphaBox = BoxLayout(orientation = 'vertical', size_hint = (1.0, 0.2))
		self.__exportColorToAlphaImage = self.__createWhiteImage()
		self.__exportColorToAlphaBox.add_widget(Label(text = 'Color to alpha:', size_hint = (1.0, 0.5)))
		self.__exportColorToAlphaBox.add_widget(self.__exportColorToAlphaImage)
		
		self.__exportBlankLabel = Label(text = '', size_hint = (1.0, 0.1))

		self.__exportRightPartBox.add_widget(self.__exportColorToAlphaBox)
		self.__exportRightPartBox.add_widget(self.__exportBlankLabel)

		self.__exportButtonsBottomBar = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		self.__exportButtonsBottomBar.add_widget(Button(text = 'Ok', on_release = self.__validateExportOptions))
		self.__exportButtonsBottomBar.add_widget(Button(text = 'Cancel', on_release = self.__exportPopup.dismiss))

		self.__exportRightPartBox.add_widget(self.__exportButtonsBottomBar)

		exportBox.add_widget(leftPartBox)
		exportBox.add_widget(self.__exportRightPartBox)

		self.__exportPopup.content = exportBox


	def __createWhiteImage(self):
		newTexture = Texture.create(size = (64, 64))
		size = 64 * 64 * 4
		i = 0
		buf = ''
		while i < size:
			buf += chr(0xFF)
			i += 1

		newTexture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
		
		return Image(size = (64, 64), texture = newTexture)
	
	def __createRelativeSplitLayout(self):
		self.__relativeSplitLayout = BoxLayout(orientation = 'vertical')
		self.__relativeSplitLayout.add_widget(Label(text = 'Partitions on x:'))
		self.__partitionOnXInput = TextInput(text = '12', multiline = False)
		self.__relativeSplitLayout.add_widget(self.__partitionOnXInput)
		self.__relativeSplitLayout.add_widget(Label(text = 'Partitions on y:'))
		self.__partitionOnYInput = TextInput(text = '8', multiline = False)
		self.__relativeSplitLayout.add_widget(self.__partitionOnYInput)
		
		self.__relativeSplitLayout.add_widget(Button(text = "Change Method", on_release = self.__showSplitLayout))
		self.__relativeSplitLayout.add_widget(Button(text = "Split!", on_release = self.__processRelativeSplit))
		self.__relativeSplitLayout.add_widget(Button(text = "Export", on_release = self.__showExportLayoutIfPossible))
		self.__relativeSplitLayout.add_widget(Button(text = "Reset", on_release = self.__reset))

	def __createSplitLayout(self):
		self.__splitLayout = BoxLayout(orientation = 'vertical')
		
		self.__splitLayout.add_widget(Label(text = 'Width:'))
		self.__widthInput = TextInput(text = '40', multiline = False)
		self.__splitLayout.add_widget(self.__widthInput)
		self.__splitLayout.add_widget(Label(text = 'Height:'))
		self.__heightInput = TextInput(text = '40', multiline = False)
		self.__splitLayout.add_widget(self.__heightInput)
		self.__splitLayout.add_widget(Label(text = 'Initial x:'))
		self.__initialXInput = TextInput(text = '0', multiline = False)
		self.__splitLayout.add_widget(self.__initialXInput)
		self.__splitLayout.add_widget(Label(text = 'Initial y:'))
		self.__initialYInput = TextInput(text = '-1', multiline = False)
		self.__splitLayout.add_widget(self.__initialYInput)

		self.__splitLayout.add_widget(Button(text = "Change Method", on_release = self.__showRelativeSplitLayout))
		self.__splitLayout.add_widget(Button(text = "Split!", on_release = self.__processSplit))
		self.__splitLayout.add_widget(Button(text = "Export", on_release = self.__showExportLayoutIfPossible))
		self.__splitLayout.add_widget(Button(text = "Reset", on_release = self.__reset))

	def __createExportLayout(self):
		self.__exportLayout = BoxLayout(orientation = 'vertical')
		self.__exportLayout.add_widget(Label(text = 'Color to alpha:'))
		self.__whiteImage = self.__createWhiteImage()
		self.__hexColor = [0xff, 0xff, 0xff, 0xff]
		self.__exportLayout.add_widget(self.__whiteImage)
		colorToAlphaConfirmationBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, None))
		self.__colorToAlphaCheckbox = CheckBox(active = False, size_hint = (0.2, 1.0))
		colorToAlphaConfirmationBox.add_widget(self.__colorToAlphaCheckbox)
		colorToAlphaConfirmationBox.add_widget(Label(text = 'Replace color to alpha 0'))

		self.__exportLayout.add_widget(colorToAlphaConfirmationBox)
		self.__exportLayout.add_widget(Button(text = 'Done', on_release = self.__openExportOptions))
		self.__exportLayout.add_widget(Button(text = 'Cancel', on_release = self.__cancelExport))

	def __showExportLayout(self, notUsed = None):
		self.__baseReference.clear_widgets()
		self.__whiteImage.color = [1.0, 1.0, 1.0, 1.0]
		self.__baseReference.add_widget(self.__exportLayout)
		self.__displayReference.showSplittedImagesList(self.__setAplhaColor)

	def __showSplitLayout(self, notUsed = None):
		self.__lastDisplayUsed = 'Absolute'
		self.__baseReference.clear_widgets()
		self.__baseReference.add_widget(self.__splitLayout)

	def __showRelativeSplitLayout(self, notUsed = None):
		self.__lastDisplayUsed = 'Relative'
		self.__baseReference.clear_widgets()
		self.__baseReference.add_widget(self.__relativeSplitLayout)

	def __createWarnings(self):
		self.__alert = AlertPopUp('Error', '', 'Ok')
		self.__dialog = Dialog(self.__export, 'Warning', '', 'Ok', 'Cancel')

	def __init__(self, base, display):
		self.__displayReference = display
		self.__baseReference = base
		
		self.__createRelativeSplitLayout()
		self.__createSplitLayout()
		self.__createExportLayout()
		self.__createExportPopup()
		self.__createWarnings()

		self.__showSplitLayout()

class DisplayStates:
	showingBaseImage = 1
	showingSplitResult = 2
	showingSplitList = 3

class Display:
	
	def __handleTouchOnSplittedImage(self, img, touch):
		if (self.__changeAlphaColorMethodReference != None and img.collide_point(*touch.pos) == True):
			point = img.to_local(touch.pos[0], touch.pos[1], True)
			adjY = img.texture_size[1] - int(point[1]) - 1
			pixelAddress = ((adjY * img.texture_size[0]) + int(point[0]) - 1) * 4
			self.__changeAlphaColorMethodReference(
				[img.texture.pixels[pixelAddress], img.texture.pixels[pixelAddress + 1], 
				img.texture.pixels[pixelAddress + 2], img.texture.pixels[pixelAddress + 3]]
			)


	def __init__(self, base, imageSrc, maxWidthProportion = 0.75, maxHeightProportion = 1.0):
		self.__imagesList = []
		self.__checkBoxList = []
		self.__maxWidthProportion = maxWidthProportion
		self.__maxHeightProportion = maxHeightProportion
		self.__maxWidthToShow = 400
		self.__maxHeightToShow = 400
		
		self.__changeAlphaColorMethodReference = None

		self.__baseImage = Image(source = imageSrc)
		
		self.__grid = GridLayout(cols = 1, rows = 1, size_hint = (None, None))

		self.__scrollView = ScrollView(size_hint = (None, None))
		self.__scrollView.add_widget(self.__grid)
		base.add_widget(self.__scrollView)

		self.showSingleBaseImage()
		self.updateLayoutSizes()

	def showSingleBaseImage(self):
		self.__state = DisplayStates.showingBaseImage
		self.__imagesList = []
		self.__checkBoxList = []
		self.__grid.clear_widgets()
		self.__baseImage.size = self.__baseImage.texture_size
		self.__grid.cols = 1
		self.__grid.rows = 1
		self.__grid.size = self.__baseImage.texture_size
		self.__grid.add_widget(self.__baseImage)

	def showSplittedImages(self):
		self.__state = DisplayStates.showingSplitResult
		self.__grid.clear_widgets()
		numberOfImages = len(self.__imagesList)
		if (numberOfImages != 0):
			dist = 1
			while (dist * dist < numberOfImages):
				dist += 1

			self.__grid.cols = dist
			self.__grid.rows = dist
			self.__grid.spacing = 10

			for img in self.__imagesList:
				self.__grid.add_widget(img)

	def showSplittedImagesList(self, changeAlphaColorByTouchReference):
		self.__state = DisplayStates.showingSplitList
		self.__grid.clear_widgets()
		self.__grid.spacing = 0
		numberOfImages = len(self.__imagesList)
		if (numberOfImages != 0):
			self.__grid.cols = 2
			self.__grid.rows = numberOfImages

			gridHeight = 0
			for img in self.__imagesList:
				x = Window.size[0] * self.__maxWidthProportion/2
				if (img.size[1] > self.__maxHeightToShow):
					y = self.__maxHeightToShow
				else:
					y = img.size[1]

				imgLayout = BoxLayout(orientation = 'vertical', size = (x, y))
				self.__changeAlphaColorMethodReference = changeAlphaColorByTouchReference
				
				checkbox = CheckBox(active = True, size_hint = (None, None), size = (x, y))
				imgLayout.add_widget(img)
				self.__checkBoxList.append(checkbox)
				self.__grid.add_widget(checkbox)
				self.__grid.add_widget(imgLayout)
				gridHeight += y

			
			self.__grid.size = (Window.size[0] * self.__maxWidthProportion, gridHeight)

	def updateDisplayRelative(self, partitionOnX, partitionOnY):
		width = self.__baseImage.texture_size[0] / partitionOnX
		height = self.__baseImage.texture_size[1] / partitionOnY

		self.updateDisplay(width, height, 0, 0)

	def updateDisplay(self, width, height, startX, startY):

		self.__changeAlphaColorMethodReference = None
		xList = range(startX, self.__baseImage.texture_size[0] + 1, width)
		yList = range(startY, self.__baseImage.texture_size[1] + 1, height)
		yList.reverse()

		self.__imagesList = []
		progressbar = None
		progressBarPopUp = None
		totalElements = len(xList) * len(yList)
		if (totalElements != 0):
			progressbar = ProgressBar(max = totalElements, value = 0)
			progressBarPopUp = Popup(title = 'Progress', size_hint = (0.3, 0.1), auto_dismiss = False, content = progressbar)
			progressBarPopUp.open()

		for y in yList:
			for x in xList:
				progressbar.value += 1
				newTexture = self.__baseImage.texture.get_region(x, y, width, height)
				formerColor = []
				isValid = False
				i= 0
				for pixel in newTexture.pixels:
					if (len(formerColor) != 4):
						formerColor.append(pixel)
					else:
						if (formerColor[i] != pixel):
							isValid = True
							break
						i = (i + 1) % 4

				if (isValid == True):
					self.__imagesList.append(
						Image(texture = newTexture, on_touch_up = self.__handleTouchOnSplittedImage,
						size = (width, height), size_hint = (None, None))
					)
				

		if (progressBarPopUp != None):
			progressBarPopUp.dismiss()
		
		self.showSplittedImages()

	def __setBufferRegion(self, buf, x, y, width, height, image, alphaToReplace):
		
		index = (y * width) + x
		i = 0
		j = 0
		rgbaList = []
		for p in image.texture.pixels:
			if (len(rgbaList) == 4):
				buf[index + i] = rgbaList[0]
				buf[index + i + 1] = rgbaList[1]
				buf[index + i + 2] = rgbaList[2]
				buf[index + i + 3] = rgbaList[3]
				i += 4

			if (i == (image.texture_size[x] * 4)):
				j += 1
				index = ((y+j) * width) + x

			rgbaList.append(p)
			
	def countSelectedImages(self):
		i = 0
		for check in self.__checkBoxList:
			if check.active == True:
				i += 1

		return i


	def saveSelectedImages(self, filename, colorToAlpha = None, dist = None):
		if (self.__state != DisplayStates.showingSplitList or len(self.__checkBoxList) == 0):
			return False

		imagesSelected = []
		i = 0
		for check in self.__checkBoxList:
			if check.active == True:
				imagesSelected.append(self.__imagesList[i])

			i += 1

		if (len(imagesSelected) == 0):
			return False

		if (dist == None or len(dist) != 2):
			x, y = 1, 1
			xTurn = True
			while x * y < len(imagesSelected):
				if (xTurn == True):
					x += 1
				else:
					y += 1
				xTurn = not xTurn

			dist = (x, y)

		newSize = (imagesSelected[0].texture_size[0] * dist[0], imagesSelected[1].texture_size[1] * dist[1])
		newTexture = Texture.create(size = newSize)
		newBuffer = ''
		k = 0
		for i in range(dist[1]):
			imagesToUse = []
			for j in range(dist[0]):
				if (k < len(imagesSelected)):
					imagesToUse.append(CacheImage(imagesSelected[k]))
				else:
					imagesToUse.append(None)
				k += 1
			
			for line in range(imagesSelected[0].texture_size[1]):
				for img in imagesToUse:
					newBuffer += self.__readLineFromImage(img, line, imagesSelected[0].texture_size[0], colorToAlpha) 
					

		newTexture.blit_buffer(newBuffer, colorfmt='rgba', bufferfmt='ubyte')
		newTexture.flip_vertical()
		newImage = Image (size = newSize,  texture = newTexture)
		#testpopup = Popup(title = 'text', auto_dismiss = True, content = newImage).open()
		newCoreImage = CoreImage(newTexture)
		newCoreImage.save(filename)

		return True
	
	def __readLineFromImage(self, img, line, xSize, colorToAlpha):
		buf = ''
		if (img == None):
			i = 0
			while i < xSize * 4:
				buf += chr(0xFF)
				i += 1
					
		else:
			address = line * xSize * 4
			i = 0
			pixels = img.getPixels()
			rgba = []
			while i < xSize * 4:
				rgba.append(pixels[address + i])
				i += 1
	
				if (len(rgba) == 4):
					if (colorToAlpha != None and rgba[0] == colorToAlpha[0] and rgba[1] == colorToAlpha[1] and 
							rgba[2] == colorToAlpha[2]):
						rgba[3] = chr(0x00);
					buf += chr(ord(rgba[0]))
					buf += chr(ord(rgba[1]))
					buf += chr(ord(rgba[2]))
					buf += chr(ord(rgba[3]))
					rgba = []
			
		
		return buf

	def updateLayoutSizes(self):
		wx, wy = Window.size
		
		xSize = wx * self.__maxWidthProportion
		ySize = wy * self.__maxHeightProportion
		
		self.__scrollView.size = (xSize, ySize)
	
	def getState(self):
		return self.__state

class CacheImage:
	def __init__(self, baseImage):
		self.__pixels = baseImage.texture.pixels

	def getPixels(self):
		return self.__pixels

class TileSplitter(App):
	
	def build_config(self, c):
		Config.set('graphics', 'width', 800)
		Config.set('graphics', 'height', 600)
		Config.set('graphics', 'fullscreen', 0)
		Config.set('input', 'mouse', 'mouse,disable_multitouch')
		Config.write()

	def build(self):

		self.root = BoxLayout(orientation='horizontal', padding = 0, spacing = 0, size_hint = (1.0, 1.0))

		self.leftMenuBase = BoxLayout(
			orientation='vertical', 
			padding = 0, 
			spacing = 0,
			size_hint = (0.25, 1.0)
		)

		self.rightScreen = BoxLayout(
			orientation = 'vertical',
			padding = 0, 
			spacing = 0,
			size_hint = (0.75, 1.0),
		)

		self.display = Display(self.rightScreen, 'top_ex.png')
		self.leftMenu = LeftMenu(self.leftMenuBase, self.display)

		self.root.add_widget(self.leftMenuBase)
		self.root.add_widget(self.rightScreen)

if __name__ == '__main__':
	TileSplitter().run()
