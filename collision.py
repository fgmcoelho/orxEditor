from singleton import Singleton

from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.switch import Switch
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.togglebutton import ToggleButton

from operator import itemgetter
from string import letters, digits

from editorutils import AlertPopUp
from editorobjects import ObjectTypes
from communicationobjects import CollisionToSceneCommunication


class CollisionFlag:
	def __init__(self, name):
		self.__name = name
		self.__isDeleted = False

	def getName(self):
		return self.__name
	
	def setDeleted (self):
		self.__isDeleted = True

	def getDeleted (self):
		return self.__isDeleted

@Singleton
class CollisionGuardian:
	def __init__(self):
		self.__id = 0
		self.__flagsDict = {}

	def addNewFlag(self, name):
		if (name not in self.__flagsDict):
			flag = CollisionFlag(name)
			self.__flagsDict[name] = (self.__id, flag)
			self.__id += 1
	
	def removeFlag(self, name):
		if (name in self.__flagsDict):
			del self.__flagsDict[name]

	def getFlags(self):
		flagsList = []
		for flag in self.__flagsDict.values():
			if (flag[1].getDeleted() == False):
				flagsList.append(flag)
		
		flagsOrderedList = sorted(flagsList, key=itemgetter(0))

		listToReturn = []
		for flag in flagsOrderedList:
			listToReturn.append(flag[1])

		return listToReturn

	def getFlagByName(self, name):
		if (name not in self.__flagsDict):
			return None
		return self.__flagsDict[name]


class CollisionPartInformation:

	def __init__(self, checkMask = [], selfFlags = [], solid = False, formType = "box", points = None):
		assert ((points == None) or (formType == "box" and len(points) == 2) or (formType == "sphere" and
			len(points) == 2) or (formType == "mesh" and len(points) != 0))

		self.__checkMask = checkMask
		self.__selfFlags = selfFlags
		self.__solid = solid
		self.__formType = formType
		self.__points = points

	def getCheckMask(self):
		return self.__checkMask
		
	def getSelfFlags(self):
		return self.__selfFlags

	def getSolid(self):
		return self.__solid
		
	def getFormType(self):
		return self.__formType
	
	def getPoints(self):
		return self.__points

class CollisionInformation:

	def __init__(self, dynamic = False, highSpeed = False, fixedRotation = False):
		self.__dynamic = dynamic
		self.__highSpeed = highSpeed
		self.__fixedRotation = fixedRotation
		self.__partsList = []

	def getDynamic(self):
		return self.__dynamic
	
	def getHighSpeed(self):
		return self.__highSpeed

	def getFixedRotation(self):
		return self.__fixedRotation

	def setDynamic(self, value):
		self.__dynamic = value
	
	def setHighSpeed(self, value):
		self.__highSpeed = value

	def setFixedRotation(self, value):
		self.__fixedRotation = value

	def addPart(self, newPart):
		self.__partsList.append(newPart)

	def removePart(self, partToRemove):
		self.__partsList.remove(partToRemove)


@Singleton
class CollisionFlagsEditor:

	def __render(self):
		
		self.__layout.clear_widgets()

		self.__layout.add_widget(Label(text = '', size_hint = (1.0, self.__baseHeight)))

		flagsList = CollisionGuardian.Instance().getFlags()
		for flag in flagsList:
			flagLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, self.__baseHeight))
			flagLine.add_widget(Label(text = flag.getName(), size_hint = (0.9, 1.0)))
			flagLine.add_widget(Button(text = 'Delete', size_hint = (0.1, 1.0), id = 'Delete#' + flag.getName(),
				on_release = self.__processRemoveFlag))
			self.__layout.add_widget(flagLine)
		

		self.__layout.add_widget(Label(text = '', size_hint = (1.0, 1.0 - ((len(flagsList) + 3) * self.__baseHeight))))
		
		if (len(flagsList) == self.__maxCollisionFlags):
			self.__layout.add_widget(Label(text = 'Maximum number of flags (%u) reached.' % (self.__maxCollisionFlags, ), 
				size_hint = (1.0, self.__baseHeight)))
		else:
			self.__inputBar.clear_widgets()
			oldText = self.__flagNameInput.text
			self.__flagNameInput = TextInput(text = oldText, multiline = False, size_hint = (0.9, 1.0), 
					on_text_validate = self.__processAddFlag, focus = True)
			self.__inputBar.add_widget(self.__flagNameInput)
			self.__inputBar.add_widget(self.__flagAddButton)

			self.__layout.add_widget(self.__inputBar)
		
		self.__layout.add_widget(Label(text = '', size_hint = (1.0, self.__baseHeight)))
		
		self.__layout.add_widget(self.__bottomBar)
	
	# TODO: MUST UPDATE OBJECTS FLAGS ON THE SCENE HERE
	# Only possible after the communication objects implementaion
	def __processRemoveFlag(self, buttonPressed):
		flagToRemove = buttonPressed.id.split('#')[1]
		CollisionGuardian.Instance().removeFlag(flagToRemove)
		self.__render()

	def __processAddFlag(self, notUsed = None):
		if (self.__flagNameInput.text == ''):
			error = AlertPopUp('Error', 'Flag name can\'t be empty.', 'Ok')
			error.open()
			return
		
		if (CollisionGuardian.Instance().getFlagByName(self.__flagNameInput.text) != None):
			error = AlertPopUp('Error', 'This name has already been used.', 'Ok')
			error.open()
			return
		
		invalidSet = []
		for char in self.__flagNameInput.text:
			if (char not in self.__validCharacters):
				invalidSet.append(char)

		if (invalidSet != []):
			error = AlertPopUp('Error', 'Found invalid characters in the name:\n ' + ''.join(invalidSet), 'Ok')
			error.open()
			return

		CollisionGuardian.Instance().addNewFlag(self.__flagNameInput.text)
		self.__flagNameInput.text = ''
		self.__render()

	def __processClose(self, notUsed = None):
		self.__flagNameInput.focus = False
		self.__popup.dismiss()

	def __init__(self):
		self.__layout = BoxLayout(orientation = 'vertical')
		self.__popup = Popup (title = 'Collision flags editor', auto_dismiss = False, content = self.__layout)

		self.__validCharacters = letters + digits
		self.__maxCollisionFlags = 16
		self.__baseHeight = 0.05
		
		emptyLabel = Label(text = '', size_hint = (0.9, 1.0))

		self.__inputBar = BoxLayout(orientation = 'horizontal', size_hint = (1.0, self.__baseHeight))
		self.__flagNameInput = TextInput(multiline = False, size_hint = (0.9, 1.0), on_text_validate = self.__processAddFlag,
			focus = True)
		self.__flagAddButton = Button(text = 'Add', size_hint = (0.1, 1.0))
		self.__flagAddButton.bind(on_release = self.__processAddFlag)

		self.__inputBar.add_widget(self.__flagNameInput)
		self.__inputBar.add_widget(self.__flagAddButton)

		self.__bottomBar = BoxLayout(orientation = 'horizontal', size_hint = (1.0, self.__baseHeight))
		doneButton = Button (text = 'Done', size_hint = (0.1, 1.0))
		doneButton.bind(on_release = self.__processClose)
		self.__bottomBar.add_widget(Label(text = '', size_hint = (0.9, 1.0)))
		self.__bottomBar.add_widget(doneButton)
		
		self.__layout.add_widget(self.__inputBar)
		self.__layout.add_widget(emptyLabel)
		self.__layout.add_widget(self.__bottomBar)

	def showPopUp(self, notUsed = None):
		self.__render()
		self.__popup.open()


class CollisionPartLayout:
	
	def __render(self, part):
		flagsList = CollisionGuardian.Instance().getFlags()
		numberOfFlags = len(flagsList)

		self.__selfFlagsGrid.clear_widgets()
		self.__checkMaskGrid.clear_widgets()

		for i in range(16):
			if (i <  numberOfFlags):
				self.__selfFlagsGrid.add_widget(ToggleButton(text = flagsList[i].getName(), size_hint = (0.25, 0.25)))
			else:
				self.__selfFlagsGrid.add_widget(Label(text = '', size_hint = (0.25, 0.25)))

		for i in range(16):
			if (i < numberOfFlags):
				self.__checkMaskGrid.add_widget(ToggleButton(text = flagsList[i].getName(), size_hint = (0.25, 0.25)))
			else:
				self.__checkMaskGrid.add_widget(Label(text = '', size_hint = (0.25, 0.25)))

	def getLayout(self):
		self.__render(None)
		return self.__layout

	def __init__(self):
		self.__layout = BoxLayout(orientation = 'horizontal')
		self.__baseHeight = 0.1

		leftLayout = BoxLayout(orientation = 'vertical', size_hint = (0.5, 1.0))
		rightLayout = BoxLayout(orientation = 'vertical', size_hint = (0.5, 1.0))

		leftLayout.add_widget(Label(text = 'Self Flags:', size_hint = (1.0, self.__baseHeight)))
		self.__selfFlagsGrid = GridLayout(cols = 4, row = 4, size_hint = (1.0, 4 * self.__baseHeight))

		leftLayout.add_widget(self.__selfFlagsGrid)
		
		leftLayout.add_widget(Label(text = '', size_hint = (1.0, 1.0 - (self.__baseHeight * 6))))

		solidLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, self.__baseHeight))
		solidLine.add_widget(Label(text = 'Solid:'))
		self.__partSolidSwitch = Switch(active = False)
		solidLine.add_widget(self.__partSolidSwitch)
		leftLayout.add_widget(solidLine)
		
		self.__layout.add_widget(leftLayout)
		
		rightLayout.add_widget(Label(text = 'Check Mask:', size_hint = (1.0, self.__baseHeight)))
		self.__checkMaskGrid = GridLayout(cols = 4, row = 4, size_hint = (1.0, 4 * self.__baseHeight))

		rightLayout.add_widget(self.__checkMaskGrid)
		
		rightLayout.add_widget(Label(text = '', size_hint = (1.0, 1.0 - (self.__baseHeight * 7))))

		rightLayout.add_widget(Label(text = 'Type', size_hint = (1.0, self.__baseHeight)))
		typeLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, self.__baseHeight))
		self.__boxButton = ToggleButton(text='Box', group='part_type', state='down')
		self.__sphereButton = ToggleButton(text='Sphere', group='part_type')
		self.__meshButton = ToggleButton(text='Mesh', group='part_type')
		typeLine.add_widget(self.__boxButton)
		typeLine.add_widget(self.__sphereButton)
		typeLine.add_widget(self.__meshButton)
		rightLayout.add_widget(typeLine)

		self.__layout.add_widget(rightLayout)

@Singleton
class CollisionInformationPopup:

	def __render(self):
		pass

	def __init__(self):
		self.__baseHeight = 0.05

		self.__collisionPopUp = Popup (title = 'Collision configs', auto_dismiss = False)
		self.__mainLayout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		
		self.__flagsAndPreviewBox = BoxLayout(orientation = 'horizontal', size_hint= (1.0, 6 * self.__baseHeight))
		self.__flagsAndPreviewBox.add_widget(Label(text = 'WIP', size_hint = (0.5, 1.0)))

		self.__bodyInfoBox = GridLayout(orientation = 'vertical', size_hint = (0.5, 1.0), cols = 2, rows = 4)
		self.__bodyInfoBox.add_widget(Label(text = 'Dynamic', size_hint = (0.3, 0.15)))
		self.__dynamicSwitch = Switch(active = False, size_hint = (0.7, 0.15))
		self.__bodyInfoBox.add_widget(self.__dynamicSwitch)

		self.__bodyInfoBox.add_widget(Label(text = 'Fixed Rotation', size_hint = (0.3, 0.15)))
		self.__fixedRotationSwitch = Switch(active = False, size_hint = (0.7, 0.15))
		self.__bodyInfoBox.add_widget(self.__fixedRotationSwitch)

		self.__bodyInfoBox.add_widget(Label(text = 'High Speed', size_hint = (0.3, 0.15)))
		self.__highSpeedSwitch = Switch(active = False, size_hint = (0.7, 0.15))
		self.__bodyInfoBox.add_widget(self.__highSpeedSwitch)
		
		self.__bodyInfoBox.add_widget(Label(text = '', size_hint = (0.5, 0.55)))
		self.__bodyInfoBox.add_widget(Label(text = '', size_hint = (0.5, 0.55)))
		
		self.__flagsAndPreviewBox.add_widget(self.__bodyInfoBox)

		self.__mainLayout.add_widget(self.__flagsAndPreviewBox)

		self.__mainLayout.add_widget(Label(text = '', size_hint = (1.0, self.__baseHeight)))

		self.__partLayout = CollisionPartLayout()

		self.__partsPanel = TabbedPanel(default_tab_text = 'Part 1', size_hint = (1.0, 0.6), 
				default_tab_content = self.__partLayout.getLayout())
		self.__mainLayout.add_widget(self.__partsPanel)

		lowerBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, self.__baseHeight))
		self.__okButton = Button(text = 'Done', size_hint = (0.10, 1.0))
		self.__okButton.bind(on_release=self.__createOrEditCollisionInfo)
		self.__cancelButton = Button (text = 'Cancel', size_hint = (0.10, 1.0))
		self.__cancelButton.bind(on_release = self.__collisionPopUp.dismiss)
		self.__previousObjectButton = Button (text = 'Previous', size_hint = (0.1, 1.0))
		self.__nextObjectButton = Button (text = 'Next', size_hint = (0.1, 1.0))
		self.__editFlagsButton = Button (text = 'Edit Flags', size_hint = (0.1, 1.0))
		self.__editFlagsButton.bind(on_release = CollisionFlagsEditor.Instance().showPopUp)
		
		lowerBox.add_widget(self.__editFlagsButton)
		lowerBox.add_widget(Label(text = '', size_hint = (0.5, 1.0)))
		lowerBox.add_widget(self.__previousObjectButton)
		lowerBox.add_widget(self.__nextObjectButton)
		lowerBox.add_widget(self.__okButton)
		lowerBox.add_widget(self.__cancelButton)
		
		self.__mainLayout.add_widget(Label(text = '', size_hint = (1.0, self.__baseHeight)))
		self.__mainLayout.add_widget(lowerBox)
		
		self.__collisionPopUp.content = self.__mainLayout
		self.__editingObject = None
	
	
		self.__errorPopUp = AlertPopUp('Error', 'No Object selected!\nYou need to select one object from the scene.', 'Ok')
		
	def __createOrEditCollisionInfo(self, useless):
		
		self.__collisionPopUp.dismiss()

	def showPopUp(self):
		
		objList = CollisionToSceneCommunication.Instance().getSelectedObjects()
		if (objList == []):
			self.__errorPopUp.setText('No object(s) selected!\nYou need to select at least one object from the scene.')
			self.__errorPopUp.open()
		
		else:
			#self.__editingObject = obj
			#self.__reloadValues()
			self.__partLayout.getLayout()
			self.__collisionPopUp.open()
			

