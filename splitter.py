#!/usr/bin/python
from kivy import require
require('1.7.2')

from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter
from kivy.config import Config
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.uix.switch import Switch
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.core.window import Window
from kivy.graphics.texture import Texture

from sys import argv, exit
from ConfigParser import ConfigParser
from os.path import isdir, isfile, join, exists
from os import listdir, getcwd, sep as pathSeparator


class LeftMenu:

	def __process(self, notUsed = None):
		try:
			width = int(self.__widthInput.text)
			height = int(self.__heightInput.text)
			startX = int(self.__initialXInput.text)
			startY = int(self.__initialYInput.text)
			assert (width > 0 and height > 0)

		except:
			return

		self.__displayReference.updateDisplay(width, height, startX, startY)

	def __export (self, notUsed = None):
		pass

	def __init__(self, base, display):
		base.add_widget(Label(text = 'Width:'))
		self.__widthInput = TextInput(text = '40', multiline = False)
		base.add_widget(self.__widthInput)
		base.add_widget(Label(text = 'Height:'))
		self.__heightInput = TextInput(text = '40', multiline = False)
		base.add_widget(self.__heightInput)
		base.add_widget(Label(text = 'Initial x:'))
		self.__initialXInput = TextInput(text = '0', multiline = False)
		base.add_widget(self.__initialXInput)
		base.add_widget(Label(text = 'Initial y:'))
		self.__initialYInput = TextInput(text = '-1', multiline = False)
		base.add_widget(self.__initialYInput)
		
		base.add_widget(Button(text = "Split!", on_press = self.__process))
		base.add_widget(Button(text = "Export", on_press = self.__export))
		
		self.__displayReference = display
		self.__layout = base

class Display:
	
	def __handleTouchOnSplittedImage(self, img, touch):
		if (img.collide_point(*touch.pos) == True):
			print img.to_local(touch.pos[0], touch.pos[1], True)

	def __init__(self, base, imageSrc):
		self.__grid = GridLayout(cols = 1, rows = 1, size_hint = (1.0, 1.0))
		self.__baseImage = Image(source = imageSrc)
		base.add_widget(self.__grid)
		self.__imagesList = []

	def showSingleBaseImage(serlf):
		self.__grid.clear_widgets()
		self.__grid.add_widget(self.__baseImage)

	def showSplittedImages(self):
		
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


	def updateDisplay(self, width, height, startX, startY):

		xList = range(startX, self.__baseImage.texture_size[0] + 1, width)
		yList = range(startY, self.__baseImage.texture_size[1] + 1, height)

		self.__imagesList = []

		for x in xList:
			for y in yList:
				newTexture = self.__baseImage.texture.get_region(x, y, width, height)
				formerColor = []
				isValid = False
				i = 0
				for pixel in newTexture.pixels:
					if (len(formerColor) != 4):
						formerColor.append(pixel)
					else:
						if (formerColor[i] != pixel):
							isValid = True
							break
						i = (i + 1) % 4


				if (isValid == True):
					self.__imagesList.append(Image(texture = newTexture, on_touch_up = self.__handleTouchOnSplittedImage, size = (width, height), size_hint = (None, None)))
		
		self.showSplittedImages()


class TileSplitter(App):
	
	def build_config(self, c):
		Config.set('graphics', 'width', 800)
		Config.set('graphics', 'height', 600)
		Config.set('graphics', 'fullscreen', 0)
		Config.set('input', 'mouse', 'mouse,disable_multitouch')
		Config.write()

	def build(self):

		self.root = BoxLayout(orientation='horizontal', padding = 0, spacing = 0, size = (800, 600))

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

		self.display = Display(self.rightScreen, '..\orxEditor\pave.png')
		self.leftMenu = LeftMenu(self.leftMenuBase, self.display)

		self.root.add_widget(self.leftMenuBase)
		self.root.add_widget(self.rightScreen)



if __name__ == '__main__':
	TileSplitter().run()
