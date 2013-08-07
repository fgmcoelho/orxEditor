from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.config import Config
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from ConfigParser import ConfigParser
from os.path import isdir, isfile, join

class SectionNames:
	BASE_SECTION = 'BASE'
	BASE_SECTION_CONFIGURED_SECTIONS_OPTION = 'configured_sections'

class PartedSprite:

	def __init__ (self, baseSprite, x, y):
		pass
		

class AssetsLoaded:

	def __loadInformationFromConfig(self):
		try:
 			sectionsToCheck = self.parser.getdefault(
				SectionNames.BASE_SECTION, 
				SectionNames.BASE_SECTION_CONFIGURED_SECTIONS_OPTION
			)

		# the file is empty, the is no information to load
		except:
			return

		for section in sectionsToCheck:
			pass		


	def __init__ (self, filename, load = False):
		self.parser = ConfigParser()		
		self.parser.read(filename)
		
		self.loadedBaseSprites = {}

		if (load == True):
			self.__loadInformationFromConfig()
		
		

class ButtonBindHandler:
	
	@staticmethod
	def callCustomAction(instance):
		instance.customAction()

	@staticmethod
	def bindButtonToAction(button, action):
		button.customAction = action
		button.bind(on_press = ButtonBindHandler.callCustomAction)

class DialogBox:

	def __init__(self, title, description='', closeText = 'Close'):
		self.dialogBoxLayout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.dialogBoxDescription = Label (text = description)
		self.dialogBoxCloseButton = Button(text = closeText, size_hint = (1.0, 0.1))
		self.dialogBoxLayout.add_widget(self.dialogBoxDescription)
		self.dialogBoxLayout.add_widget(self.dialogBoxCloseButton)
		self.dialogBox = Popup (title = title, content = self.dialogBoxLayout, size_hint = (0.5, 0.5), auto_dismiss = False)
		self.dialogBoxCloseButton.bind (on_press = self.dialogBox.dismiss)

	def setDescription(self, newDescription):
		self.dialogBoxDescription.text = newDescription

	def show(self):
		self.dialogBox.open()



class BaseHidableObject (object):

	def __addElementsToBase(self):
		for element in self.uiList:
			self.base.add_widget(element)

	def __removeElementsFromBase(self):
		for element in self.uiList:
			self.base.remove_widget(element)

	def __init__(self, base, hidden):
		self.uiList = []
		self.base = base
		self.hidden = hidden

	def hide(self):
		if (self.hidden == False):
			self.hidden = True
			self.__removeElementsFromBase()
	
	def show(self):
		if (self.hidden == True):
			self.hidden = False
			self.__addElementsToBase()


class SpriteDivisionLeftMenu(BaseHidableObject):

	def __createUIElements(self):
		self.widthLabel = Label(text='Width:')
		self.widthInput = TextInput(text='0', multiline=False)
		self.heightLabel = Label(text='Height:')
		self.heightInput = TextInput(text='0', multiline=False)
		self.applyButton = Button(text = 'Apply!')
		self.doneButton = Button(text = 'Done!')

		self.uiList.append(self.widthLabel)
		self.uiList.append(self.widthInput)
		self.uiList.append(self.heightLabel)
		self.uiList.append(self.heightInput)
		self.uiList.append(self.applyButton)
		self.uiList.append(self.doneButton)

	def __init__(self, base, hidden = True):
		super(SpriteDivisionLeftMenu, self).__init__(base, hidden)
		self.__createUIElements()
		if (self.hidden == False):
			super(SpriteDivisionLeftMenu, self).__addElementsToBase(base)

class SpriteDivisionView:

	#debugImage = 'top_worldmap-big.png'
	#debugImage = 'soldier_full.png'
	debugImage = 'top_ex.png'

	def splitImage(self, cutX, cutY):
		texX, texY = self.textureLoaded.texture_size


		xCoords = range(0, texX, cutX)
		yCoords = range(0, texY, cutY)
	
		cols = len (xCoords)
		rows = len (yCoords)
		yCoords.reverse()

		print (cols, rows)
		self.grid = GridLayout (
			cols = cols, 
			rows = rows,
			spacing = 1,
			size_hint = (None, None),
			width = (cols * cutX) + cols,
			height = (rows * cutY) + rows,
		)

		texture = self.textureLoaded.texture
		for y in yCoords:
			for x in xCoords:
				region = texture.get_region(x, y, cutX-1, cutY-1)
				self.grid.add_widget(Image(texture = region))

		self.view.remove_widget(self.textureLoaded)
		self.view.add_widget(self.grid)

	def restoreImage(self):
		if (self.grid == None):
			return

		else:
			self.view.remove_widget(self.grid)
			self.view.add_widget(self.textureLoaded)

	def __init__(self, base, imageToShow = None):
		self.grid = None
		self.view = ScrollView(size_hint=(1.0, 1.0))

		self.textureLoaded = Image (
			source = self.debugImage, 
		)
		x, y = self.textureLoaded.texture_size
		self.textureLoaded.size_hint = (None, None)
		self.textureLoaded.width = x
		self.textureLoaded.height = y
		
		self.textureLoaded.allow_stretch = True
		self.textureLoaded.keep_ratio = False
		
		
		self.view.add_widget(self.textureLoaded)
		base.add_widget(self.view)

class StartWorkingLeftMenu(BaseHidableObject):

	def bindNewAnnimationButton(self, action):
		ButtonBindHandler.bindButtonToAction(self.newAnimationButton, action)

	def bindLoadAnnimationButton(self, action):
		ButtonBindHandler.bindButtonToAction(self.loadAnnimationButton, action)	

	def __createUIElements(self):
		self.newAnimationButton = Button(text = 'New Annimation', size_hint = (1.0, 0.1))
		self.loadAnnimationButton = Button (text = 'Load Annimation', size_hint = (1.0, 0.1))
		
		self.uiList.append(self.newAnimationButton)
		self.uiList.append(self.loadAnnimationButton)

	def __init__(self, base, hidden = True):
		super(StartWorkingLeftMenu, self).__init__(base, hidden)
		self.__createUIElements()
		if (self.hidden == False):
			super(SpriteDivisionLeftMenu, self).__addElementsToBase(base)

class StartWorkingScreen(BaseHidableObject):

	@staticmethod
	def callChooserAction(instance, *args):
		instance.submitAction()

	def __createUIElements(self):
		# Upper screen part
		self.filenameLabel = Label(text = 'Filename:', size_hint = (1.0, 0.1))
		self.filenameInput = TextInput(readonly = True, multiline = False, size_hint = (1.0, 0.1))
		self.fileChooser = FileChooserIconView(size_hint = (1.0, 0.7))

		# Bottom Bar Code
		self.bottomBar = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		self.okButton = Button (text = 'Done')
		self.cancelButton = Button (text = 'Cancel')
		self.bottomBar.add_widget(self.okButton)
		self.bottomBar.add_widget(self.cancelButton)

		# Error popup
		self.errorPopup = DialogBox('Error')

		self.uiList.append(self.filenameLabel)
		self.uiList.append(self.filenameInput)
		self.uiList.append(self.fileChooser)
		self.uiList.append(self.bottomBar)

	def __createInternalBinds(self):
		ButtonBindHandler.bindButtonToAction(self.cancelButton, self.hide)
		ButtonBindHandler.bindButtonToAction(self.okButton, self.__validateAndAdvance)
		self.fileChooser.submitAction = self.__validateAndAdvance
		self.fileChooser.bind(on_submit=StartWorkingScreen.callChooserAction)

	def __validateAndAdvance(self):

		if (self.creatingNewFile == True):
			if (self.filenameInput.text == ''):
				self.errorPopup.setDescription('Empty filename.')
				self.errorPopup.show()
				return

			newFilename = join(self.fileChooser.path, self.filenameInput.text)
			if (len(newFilename) <= 6 or newFilename[:-6] != '.orxsa'):
				newFilename = newFilename + '.orxsa'


			print 'Testing filename: ' + newFilename
			if (isfile(newFilename) == True):
				self.errorPopup.setDescription('File already exists!')
				self.errorPopup.show()
				return


			self.stateChangeAction(self.nextState)

			

	def __init__(self, stateChangeAction, nextState, base, hidden = True):
		super(StartWorkingScreen, self).__init__(base, hidden)
		self.stateChangeAction = stateChangeAction
		self.nextState = nextState
		self.__createUIElements()
		self.__createInternalBinds()

	# This UI element is not automatically shown.
	def show(self):
		pass

	def dirFilter(self, currentDirectory, listedFile):
		return isdir(listedFile)

	def selectNewFile(self):
		self.creatingNewFile = True
		self.fileChooser.filters = [self.dirFilter]
		self.filenameLabel.text = 'Enter the name of the file and select the directory to save it.'
		self.filenameInput.text = ''
		self.filenameInput.readonly = False
		super(StartWorkingScreen, self).show()
	
	def selectExistingFile(self):
		self.creatingNewFile = False
		self.fileChooser.filters = ['*.orxsa']
		self.filenameInput.text = ''
		self.filenameInput.readonly = True
		self.filenameLabel.text = 'Select the new file.'
		super(StartWorkingScreen, self).show()


class ApplicationUiStates:
	STARTING_SCREEN = 1
	SPRITE_DIVISION = 2

class AnimationController:

	def __bindStartingScreenEvents(self):
		self.startWorkingLeftMenu.bindNewAnnimationButton(self.startWorkingView.selectNewFile)	
		self.startWorkingLeftMenu.bindLoadAnnimationButton(self.startWorkingView.selectExistingFile)

	def __bindEvents(self):
		self.__bindStartingScreenEvents()

	def __createControllers(self):

		self.spriteDivisionLeftMenu = SpriteDivisionLeftMenu(self.leftMenu)
	  	#self.spriteDivisionView = SpriteDivisionView(self.rightScreen)
		self.startWorkingLeftMenu = StartWorkingLeftMenu(self.leftMenu)
		self.startWorkingView = StartWorkingScreen(self.changeState, ApplicationUiStates.SPRITE_DIVISION, self.rightScreen)

	def __init__(self, leftMenu, rightScreen):
		self.state = ApplicationUiStates.STARTING_SCREEN
		self.leftMenu = leftMenu
		self.rightScreen = rightScreen

		self.__createControllers()
		self.__bindEvents()
		
		self.startWorkingLeftMenu.show()

		self.currentLeftMenu = self.startWorkingLeftMenu
		self.currentRightView = self.startWorkingView

	def changeState(self, nextState):
		self.currentLeftMenu.hide()
		self.currentRightView.hide()

		if (nextState == ApplicationUiStates.STARTING_SCREEN):
			self.currentLeftMenu = self.startWorkingLeftMenu
			self.currentRightView = self.startWorkingView
		
		elif (nextState == ApplicationUiStates.SPRITE_DIVISION):
			self.currentLeftMenu = self.spriteDivisionLeftMenu
			#self.currentRightView = self.spriteDivisionView

		self.currentLeftMenu.show()
		self.currentRightView.show()


class AnimationEditor(App):
	
	def build_config(self, c):
		Config.set('graphics', 'width', 800)
        Config.set('graphics', 'height', 600)
        Config.set('graphics', 'fullscreen', 0)
        Config.write()

	def build(self):

		self.root = BoxLayout(orientation='horizontal', padding = 0, spacing = 0)

		leftMenuBase = BoxLayout(
			orientation='vertical', 
			padding = 0, 
			spacing = 0,
			size_hint = (0.25, 1.0)
		)

		rightScreen = BoxLayout(
			orientation = 'vertical',
			padding = 0, 
			spacing = 0,
			size_hint = (0.75, 1.0),
		)

		self.root.add_widget(leftMenuBase)
		self.root.add_widget(rightScreen)

		AnimationController(leftMenuBase, rightScreen)

		return self.root


if __name__ == '__main__':
	AnimationEditor().run()
