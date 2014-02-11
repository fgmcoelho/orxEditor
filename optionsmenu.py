from singleton import Singleton

from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.accordion import Accordion, AccordionItem
from editorutils import Dialog, AlertPopUp
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserIconView

from os import listdir, getcwd

class BaseObjectDescriptor:
	
	def __init__(self, accordionItem):
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__pathLabel = Label(text = 'Path: ', size_hint = (1.0, 0.5))
		self.__sizeLabel = Label(text = 'Size: ', size_hint = (1.0, 0.5))
		self.__layout.add_widget(self.__pathLabel)
		self.__layout.add_widget(self.__sizeLabel)
		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)

	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False

	def setValues(self, path = '', size=''):
		self.__pathLabel.text = 'Path: ' + str(path)
		self.__sizeLabel.text = 'Size: ' + str(size)
		self.setActive()

class RenderedObjectDescriptor:
	def __init__(self, accordionItem, popUpMethod):
		self.__layout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__pathLabel = Label(text = 'Path: ', size_hint = (1.0, 0.2))

		self.__nameLabel = Label(text = 'Name: ', size_hint = (1.0, 0.2))

		self.__flipBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__flipxLabel = Label(text = 'Flipped on X: ', size_hint = (0.5, 1.0))
		self.__flipyLabel = Label(text = 'Flipped on Y: ', size_hint = (0.5, 1.0))
		self.__flipBox.add_widget(self.__flipxLabel)
		self.__flipBox.add_widget(self.__flipyLabel)

		self.__sizeScaleLayerBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__sizeLabel = Label(text = 'Size: ', size_hint = (0.333, 1.0))
		self.__scaleLabel = Label(text = 'Scale: ', size_hint = (0.333, 1.0))
		self.__layerLabel = Label(text = 'Layer: ', size_hint = (0.3334, 1.0))
		
		self.__sizeScaleLayerBox.add_widget(self.__sizeLabel)
		self.__sizeScaleLayerBox.add_widget(self.__scaleLabel)
		self.__sizeScaleLayerBox.add_widget(self.__layerLabel)

		self.__collisionBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.2))
		self.__collisionInfoLabel = Label(text = 'Has collision info: ')
		self.__collisionHandler = Button(text = 'Edit Collision', size_hint = (0.3, 1.0))
		self.__collisionHandler.bind(on_release=popUpMethod)
		
		self.__collisionBox.add_widget(self.__collisionInfoLabel)
		self.__collisionBox.add_widget(self.__collisionHandler)

		self.__layout.add_widget(self.__pathLabel)
		self.__layout.add_widget(self.__nameLabel)
		self.__layout.add_widget(self.__flipBox)
		self.__layout.add_widget(self.__sizeScaleLayerBox)
		self.__layout.add_widget(self.__collisionBox)

		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)
	
	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False

	def setValues(self, path = '', size = '', scale = '', layer = '', name = '', flipX = '', flipY = '', collisionInfo = None):
		self.__setValues(path, size, scale, layer, name, flipX, flipY, collisionInfo)
		self.setActive()

	def setValueNoActive(self, path = '', size = '', scale = '', layer = '', name = '', flipX = '', flipY = '', 
			collisionInfo = None):
		self.__setValues(path, size, scale, layer, name, flipX, flipY, collisionInfo)

	def __setValues(self, path, size, scale, layer, name, flipX, flipY, collisionInfo):
		self.__pathLabel.text = 'Path: ' + str(path)
		self.__sizeLabel.text = 'Size: ' + str(size)
		self.__scaleLabel.text = 'Scale: ' + str(scale)
		self.__layerLabel.text = 'Layer: ' + str(layer)
		self.__nameLabel.text = 'Name: ' + str(name)
		self.__flipxLabel.text = 'Flipped on X: ' + str(flipX)
		self.__flipyLabel.text = 'Flipped on Y: ' + str(flipY)
		if (collisionInfo == None):
			self.__collisionInfoLabel.text = 'Has collision info: None'
		else:
			self.__collisionInfoLabel.text = 'Has collision info: Available'
		

class OptionsMenu:
	
	def __newSceneFinish(self, notUsed = None):
		self.__newSceneMethodReference(notUsed)
		self.__newSceneDialog.dismiss()

	def __newScene(self, notUsed = None):
		self.__newSceneDialog.open()

	def __saveSceneFinish(self, notUsed = None):
		self.__saveSceneMethodReference(join(self.__fileChooser.path, self.__fileChooserInput.text))
		self.__fileChooserPopUp.dismiss()
		self.__saveSceneDialog.dismiss()
		self.__lastPath = self.__fileChooser.path

	def __validateSelectedOsf(self, entry, notUsed = None):
		if (isfile(entry[0]) == True):
			sepIndex = entry[0].rfind(pathSeparator)
			if (sepIndex != -1):
				self.__fileChooserInput.text = entry[0][sepIndex+1:]
			else:
				self.__fileChooserInput.text = entry[0]
		else:
			self.__errorPopUp.setText('Invalid file selected.')
			self.__errorPopUp.open()

	def __validateAndContinueToSave(self, notUsed = None):
		if (self.__fileChooserInput.text == ''):
			self.__errorPopUp.setText('No file selected.')
			self.__errorPopUp.open()
			return

		if (isfile(join(self.__fileChooser.path, self.__fileChooserInput.text)) == True):
			self.__saveSceneDialog.open()
		else:
			self.__saveSceneFinish()

	def __saveScene(self, notUsed = None):
		self.__fileChooser.path = self.__lastPath
		self.__fileChooser.filters = ['*.osf']
		self.__fileChooser.on_submit = self.__validateSelectedOsf
		self.__fileChooserOkButton.on_release = self.__validateAndContinueToSave
		self.__fileChooserPopUp.open()

	def __loadSceneFinish(self, notUsed = None):
		self.__loadSceneMethodReference(join(self.__fileChooser.path, self.__fileChooserInput.text))
		self.__fileChooserPopUp.dismiss()
		self.__lastPath = self.__fileChooser.path

	def __validateAndContinueToLoad(self, notUsed = None):
		if (self.__fileChooserInput.text == ''):
			self.__errorPopUp.setText('No file selected.')
			self.__errorPopUp.open()
			return

		if (isfile(join(self.__fileChooser.path, self.__fileChooserInput.text)) == True):
			self.__loadSceneFinish()
		else:
			self.__errorPopUp.setText("Selected file doesn't exist.")
			self.__errorPopUp.open()

	def __loadScene(self, notUsed = None):
		self.__fileChooser.path = self.__lastPath
		self.__fileChooser.filters = ['*.osf']
		self.__fileChooser.on_submit = self.__validateSelectedOsf
		self.__fileChooserOkButton.on_release = self.__validateAndContinueToLoad
		self.__fileChooserPopUp.open()

	def __startBasicButtonsLayout(self):
		self.__layout = GridLayout(rows = 4, cols = 1, size_hint = (1.0, 1.0))
		self.__newButton = Button(text = 'New Scene', size_hint = (1.0, 0.25), on_release = self.__newScene)
		self.__loadButton = Button(text = 'Load Scene', size_hint = (1.0, 0.25), on_release = self.__loadScene)
		self.__saveButton = Button(text = 'Save Scene', size_hint = (1.0, 0.25), on_release = self.__saveScene)
		self.__exportButton = Button(text = 'Export Scene', size_hint = (1.0, 0.25))
		
		self.__layout.add_widget(self.__newButton)
		self.__layout.add_widget(self.__loadButton)
		self.__layout.add_widget(self.__saveButton)
		self.__layout.add_widget(self.__exportButton)

	def __startConfirmationPopUp(self):
		self.__newSceneDialog = Dialog(
			self.__newSceneFinish, 'Confirmation', 
			'Starting a new scene will remove all the\nnon saved changes.\nAre you sure?', 'Ok', 'Cancel'
		)
		self.__saveSceneDialog = Dialog(
			self.__saveSceneFinish, 'Confirmation',
			'This will override the selected file.\nContinue?', 'Ok', 'Cancel'
		)

	def __startFileChooser(self):
		
		self.__fileChooserLayout = BoxLayout(orientation = 'vertical')
		self.__fileChooserPopUp = Popup(auto_dismiss = False, title = 'Select the file:')
		self.__fileChooserInputLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		filenameLabel = Label(text = 'File:', size_hint = (0.3, 1.0))
		self.__fileChooserInput = TextInput(multiline = False, size_hint = (0.7, 1.0))
		self.__fileChooserInputLayout.add_widget(filenameLabel)
		self.__fileChooserInputLayout.add_widget(self.__fileChooserInput)
		self.__fileChooser = FileChooserIconView(size_hint = (1.0, 0.9))

		self.__fileChooserYesNoLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.1))
		self.__fileChooserOkButton = Button(text = 'Ok')
		self.__fileChooserCancelButton = Button(text = 'Cancel', on_release = self.__fileChooserPopUp.dismiss)
		self.__fileChooserYesNoLayout.add_widget(self.__fileChooserOkButton)
		self.__fileChooserYesNoLayout.add_widget(self.__fileChooserCancelButton)

		self.__fileChooserLayout.add_widget(self.__fileChooserInputLayout)
		self.__fileChooserLayout.add_widget(self.__fileChooser)
		self.__fileChooserLayout.add_widget(self.__fileChooserYesNoLayout)
		self.__fileChooserPopUp.content = self.__fileChooserLayout
		self.__lastPath = getcwd()


	def __init__(self, accordionItem, newSceneMethod, saveSceneMethod, loadSceneMethod):

		self.__newSceneMethodReference = newSceneMethod
		self.__saveSceneMethodReference = saveSceneMethod
		self.__loadSceneMethodReference = loadSceneMethod

		self.__startBasicButtonsLayout()	
		self.__startConfirmationPopUp()	
		self.__startFileChooser()
		self.__errorPopUp = AlertPopUp('Error', '', 'Ok')

		self.__accordionItemReference = accordionItem
		self.__accordionItemReference.add_widget(self.__layout)

	def getLayout(self):
		return self.__layout

	def setActive(self):
		self.__accordionItemReference.collapse = False

@Singleton
class ObjectDescriptor:
	
	def updateObjectDescriptors(self):
		self.setObject(self.__currentObject)

	def openCollisionPopUp(self, ignore):
		
		self.__collisionPopUpReference.showPopUp(self.__currentObject)
		
		if (self.__currentObject != None):
			self.setObject(self.__currentObject)

	def __init__(self, rightScreen, collisionPopUp, maxWidthProportion = 1.0, maxHeightProportion = 0.333):
		
		self.__collisionPopUpReference = collisionPopUp
		self.__collisionPopUpReference.setPostCreateOrEditMethod(self.updateObjectDescriptors)
		self.__currentObject = None
		self.__maxWidthProportion = maxWidthProportion
		self.__maxHeightProportion = maxHeightProportion

		self.__layout = Accordion(orientation = 'horizontal', size_hint = (maxWidthProportion, maxHeightProportion))

		self.__accordionItems = {
			'BaseObject' : AccordionItem(title = 'Base Objects'),
			'RenderedObject' : AccordionItem (title = 'Rendered Object'),
			'Options' : AccordionItem(title = 'Options'),
		}

		self.__baseObjectDescriptor = BaseObjectDescriptor(self.__accordionItems['BaseObject'])
		self.__renderedObjectDescriptor = RenderedObjectDescriptor(self.__accordionItems['RenderedObject'], self.openCollisionPopUp)
		self.__optionsMenu = OptionsMenu(self.__accordionItems['Options'], None, None, None)

		self.__layout.add_widget(self.__accordionItems['BaseObject'])
		self.__layout.add_widget(self.__accordionItems['RenderedObject'])
		self.__layout.add_widget(self.__accordionItems['Options'])

		self.__baseObjectDescriptor.setActive()

		rightScreen.add_widget(self.__layout)

	def resetAllWidgets(self):
		self.__baseObjectDescriptor.setValues()
		self.__renderedObjectDescriptor.setValueNoActive()
			
	def setOrDrawObject(self, obj):
		if (self.__currentObject == obj):
			self.__drawObject(obj)
		else:
			self.setObject(obj)

	def __drawObject(self, obj):
		self.__sceneHandlerReference.draw(obj)

	def setObject(self, obj):

		if (self.__currentObject != None and self.__currentObject.getType() == ObjectTypes.renderedObject):
			self.__currentObject.unsetMarked()

		path = obj.getPath()
		size = obj.getSize()
		cwd = getcwd() + '/'
		if (cwd == path[:len(cwd)]):
			path = path[len(cwd):]

		if (obj.getType() == ObjectTypes.renderedObject):
			self.__renderedObjectDescriptor.setValues(path, size, obj.getScale(), obj.getLayer(), obj.getName(), obj.getFlipX(),
				obj.getFlipY(), obj.getCollisionInfo())
			obj.setMarked()
		
		else:
			self.__baseObjectDescriptor.setValues(path, size)

		self.__currentObject = obj

	def getCurrentObject(self):
		return self.__currentObject

	def clearCurrentObject(self):
		if (self.__currentObject == None):
			return
		
		if (self.__currentObject.getType() == ObjectTypes.renderedObject):
			self.__currentObject.unsetMarked()
			self.__renderedObjectDescriptor.setValues()
			self.__baseObjectDescriptor.setValues()
		else:
			self.__baseObjectDescriptor.setValues()
			self.__renderedObjectDescriptor.setValues()
		
		self.__currentObject = None
