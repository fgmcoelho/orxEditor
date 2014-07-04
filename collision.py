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

from editorutils import AlertPopUp, Dialog
from communicationobjects import CollisionToSceneCommunication, CollisionToMainLayoutCommunication


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
		return self.__flagsDict[name][1]


class CollisionPartInformation:

	@staticmethod
	def copy(part):
		assert (isinstance(part, CollisionPartInformation))
		return CollisionPartInformation(
			part.getCheckMask(),
			part.getSelfFlags(),
			part.getSolid(),
			part.getFormType(),
			part.getPoints()
		)

	def __init__(self, checkMask = [], selfFlags = [], solid = False, formType = "box", points = None):
		assert ((points == None) or (formType == "box" and len(points) == 2) or (formType == "sphere" and
			len(points) == 2) or (formType == "mesh" and len(points) >= 3))

		self.__checkMask = checkMask[:]
		self.__selfFlags = selfFlags[:]
		self.__solid = solid
		self.__formType = formType
		self.__points = points

	def getCheckMask(self):
		return self.__checkMask
		
	def getSelfFlags(self):
		return self.__selfFlags

	def addFlagToCheckMask(self, flag):
		assert (len(self.__checkMask) <= 16)
		self.__checkMask.append(flag)
		
	def setFormType(self, newForm):
		assert (newForm in ['box', 'sphere', 'mesh'])
		self.__formType = newForm
			
	def addFlagToSelfFlags(self, flag):
		assert (len(self.__selfFlags) <= 16)
		self.__selfFlags.append(flag)

	def removeFlagFromCheckMask(self, flag):
		self.__checkMask.remove(flag)
	
	def removeFlagFromSelfFlags(self, flag):
		self.__selfFlags.remove(flag)

	def getSolid(self):
		return self.__solid
		
	def getFormType(self):
		return self.__formType
	
	def getPoints(self):
		return self.__points

class CollisionInformation:

	@staticmethod
	def copy(info):
		assert(isinstance(info, CollisionInformation))
		newInfo = CollisionInformation(
			info.getDynamic(),
			info.getHighSpeed(),
			info.getFixedRotation()
		)
		for part in info.getPartsList():
			newInfo.addPart(CollisionPartInformation.copy(part))
			
		return newInfo

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
		
	def getPartsList(self):
		return self.__partsList

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
		
		CollisionInformationPopup.Instance().updateLayout()
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
	
	def __togglePartFlag(self, buttonObject):
		buttonInfo = buttonObject.id.split('#')
		if (buttonObject.state == 'normal'):
			if (buttonInfo[1] == 'selfflags'):
				self.__part.removeFlagFromSelfFlags(CollisionGuardian.Instance().getFlagByName(buttonInfo[2]))
			else:
				self.__part.removeFlagFromCheckMask(CollisionGuardian.Instance().getFlagByName(buttonInfo[2]))

		else:
			if (buttonInfo[1] == 'selfflags'):
				self.__part.addFlagToSelfFlags(CollisionGuardian.Instance().getFlagByName(buttonInfo[2]))
			else:
				self.__part.addFlagToCheckMask(CollisionGuardian.Instance().getFlagByName(buttonInfo[2]))


	def __updateFormType(self, checkboxObject, newValue):
		if (newValue == True):
			#TODO: Warn that points data will be lost.
			checkboxInfo = checkboxObject.id.split('#')
			self.__part.setFormType(checkboxInfo[1])
				
	def __render(self, part):

		self.__part = part
		flagsList = CollisionGuardian.Instance().getFlags()
		numberOfFlags = len(flagsList)
		
		partSelfFlags = []
		for flag in part.getSelfFlags():
			partSelfFlags.append(flag.getName())

		partCheckMask = []
		for flag in part.getCheckMask():
			partCheckMask.append(flag.getName())
		
		self.__selfFlagsGrid.clear_widgets()
		self.__checkMaskGrid.clear_widgets()

		for i in range(16):
			if (i <  numberOfFlags):
				name = flagsList[i].getName()
				if (name in partSelfFlags):
					self.__selfFlagsGrid.add_widget(ToggleButton(text = name, size_hint = (0.25, 0.25), state = 'down', 
						on_release = self.__togglePartFlag, id = 'togglebutton#selfflags#' + name))
				else:
					self.__selfFlagsGrid.add_widget(ToggleButton(text = name, size_hint = (0.25, 0.25), state = 'normal',
						on_release = self.__togglePartFlag, id = 'togglebutton#selfflags#' + name))
			else:
				self.__selfFlagsGrid.add_widget(Label(text = '', size_hint = (0.25, 0.25)))

		for i in range(16):
			if (i < numberOfFlags):
				name = flagsList[i].getName()
				if (name in partCheckMask):
					self.__checkMaskGrid.add_widget(ToggleButton(text = name, size_hint = (0.25, 0.25), state = 'down',
						on_release = self.__togglePartFlag, id = 'togglebutton#checkmask#' + name))
				else:
					self.__checkMaskGrid.add_widget(ToggleButton(text = name, size_hint = (0.25, 0.25), state = 'normal',
						on_release = self.__togglePartFlag, id = 'togglebutton#checkmask#' + name))
			else:
				self.__checkMaskGrid.add_widget(Label(text = '', size_hint = (0.25, 0.25)))

		self.__typeLine.clear_widgets()
		self.__boxCheckBox = CheckBox(group = 'part_type' + str(id(self)), id = 'checkbox#box')
		self.__sphereCheckBox = CheckBox(group = 'part_type' + str(id(self)), id = 'checkbox#sphere')
		self.__meshCheckBox = CheckBox(group = 'part_type' + str(id(self)), id = 'checkbox#mesh')
		
		formType = part.getFormType()
		if (formType == "box"):
			self.__boxCheckBox.active = True
		elif (formType == "sphere"):
			self.__sphereCheckBox.active = True
		else:
			self.__meshCheckBox.active = True		
		
		self.__boxCheckBox.bind (active = self.__updateFormType)
		self.__sphereCheckBox.bind(active = self.__updateFormType)
		self.__meshCheckBox.bind(active = self.__updateFormType)

		self.__typeLine.add_widget(self.__boxCheckBox)
		self.__typeLine.add_widget(Label(text = 'Box'))
		self.__typeLine.add_widget(self.__sphereCheckBox)
		self.__typeLine.add_widget(Label(text ='Sphere'))
		self.__typeLine.add_widget(self.__meshCheckBox)
		self.__typeLine.add_widget(Label(text = 'Mesh'))


	def __init__(self):
		self.__layout = BoxLayout(orientation = 'horizontal')
		self.__baseHeight = 0.1
		self.__part = None
		
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
		self.__typeLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, self.__baseHeight))
		
		rightLayout.add_widget(self.__typeLine)

		self.__layout.add_widget(rightLayout)

	def getLayout(self):
		return self.__layout
		
	def updateLayout(self, part):
		assert (isinstance(part, CollisionPartInformation))
		self.__render(part)		

@Singleton
class CollisionInformationPopup:

	def __createTemporatyCopies(self):
		
		for obj in self.__objectsList:
			if (obj.getCollisionInfo() != None):
				infoCopy = CollisionInformation.copy(obj.getCollisionInfo())
			else:
				infoCopy = CollisionInformation()

			extraParts = []
			for i in range (8 - len(infoCopy.getPartsList())):
				extraParts.append(CollisionPartInformation())				
							
			self.__copiesDict[obj.getIdentifier()] = infoCopy
			self.__extraPartsDict[obj.getIdentifier()] = extraParts
			
	def __applyChanges(self, notUsed = None):
		currentId = self.__objectsList[self.__objectsListIndex].getIdentifier()
		if(self.__partsPanel.current_tab.text == 'Edit'):
			newPart = self.__extraPartsDict[currentId].pop(0)
			self.__copiesDict[currentId].addPart(newPart)
			self.__render()

	def __doDeleteCurrentPart(self, notUsed = None):
		currentId = self.__objectsList[self.__objectsListIndex].getIdentifier()
		index = int(self.__partsPanel.current_tab.text.split(' ')[1])
		partsList = self.__copiesDict[currentId].getPartsList()
		part = partsList[index - 1]
		self.__copiesDict[currentId].removePart(part)
		part = None
		self.__extraPartsDict[currentId].append(CollisionPartInformation())
		self.__warnDelete.dismiss()
		self.__render()

	def __deleteCurrentPart(self, notUsed = None):
		currentId = self.__objectsList[self.__objectsListIndex].getIdentifier()
		if (self.__partsPanel.current_tab.text == 'Edit'):
			errorPopup = AlertPopUp('Error', 'You can\'t delete the edit flag, it hasn\'t been added.', 'Ok')
			errorPopup.open()
		else:
			self.__warnDelete.open()

	def __doApplyChanges(self, notUsed = None):

		currentObj = self.__objectsList[self.__objectsListIndex]
		infoToCopy = currentObj.getCollisionInfo()
		for obj in self.__objectsList:
			if (obj != currentObj):
				infoCopy = CollisionInformation.copy(infoToCopy)
				self.__copiesDict[obj.getIdentifier()] = infoCopy
				numberOfParts = len(infoCopy.getPartsList)
				numberOfExtraParts = len(self.__extraPartsDict[obj.getIdentifier()])
				while (numberOfExtraParts + numberOfParts > 8):
					self.__extraPartsDict[obj.getIdentifier()].pop()
				while (numberOfExtraParts + numberOfParts < 8):
					self.__extraPartsDict[obj.getIdentifier()].append(CollisionPartInformation())

		self.__warnApplyAll.dismiss()
		self.__render()

	def __applyChangesToAll(self, notUsed = None):
		
		willEraseInfo = 0
		currentObj = self.__objectsList[self.__objectsListIndex]
		for obj in self.__objectsList:
			if (obj != currentObj):
				if (obj.getCollisionInfo() == None):
					willEraseInfo += 1
		
		if (willEraseInfo == 0):
			self.__warnApplyAll.setText('This will replace information of other ' + str(willEraseInfo) + ' objects.')
			self.__warnApplyAll.open()
		

	def __selectNextObject(self, notUsed = None):
		self.__objectsListIndex = (self.__objectsListIndex + 1) % len(self.__objectsList)
		self.__render()
		
	def __selectPreviousObject(self, notUsed = None):
		self.__objectsListIndex = (self.__objectsListIndex - 1) % len(self.__objectsList)
		self.__render()
			
	def __render(self):
		
		currentId = self.__objectsList[self.__objectsListIndex].getIdentifier()
		collisionInfo = self.__copiesDict[currentId]
		extraParts = self.__extraPartsDict[currentId]
		
		self.__dynamicSwitch.active = collisionInfo.getDynamic()
		self.__fixedRotationSwitch.active = collisionInfo.getFixedRotation()
		self.__highSpeedSwitch.active = collisionInfo.getHighSpeed()
		
		parts = collisionInfo.getPartsList()
		numberOfParts = len(parts)
		
		self.__partsPanel.clear_tabs()
			
		for i in range(numberOfParts):
			self.__partsLayoutList[i].updateLayout(parts[i])
			if (i == 0):
				self.__partsPanel.default_tab_content = self.__partsLayoutList[i].getLayout()
				self.__partsPanel.default_tab_text = 'Part 1'
			
			else:
				th = TabbedPanelHeader(text = 'Part ' + str(i + 1))
				th.content = self.__partsLayoutList[i].getLayout()
				self.__partsPanel.add_widget(th)
				if (i == 7):
					self.__partsPanel.switch_to(th)
	
		if (extraParts != []):
			self.__partsLayoutList[numberOfParts].updateLayout(extraParts[0])
			if (numberOfParts == 0):
				self.__partsPanel.default_tab_text = 'Edit'
				self.__partsPanel.default_tab_content = self.__partsLayoutList[numberOfParts].getLayout()
			else:
				th = TabbedPanelHeader(text = 'Edit')
				th.content = self.__partsLayoutList[numberOfParts].getLayout()
				self.__partsPanel.add_widget(th)
				self.__partsPanel.switch_to(th)
				
		self.__lowerBox.clear_widgets()
		self.__lowerBox.add_widget(self.__editFlagsButton)
		self.__lowerBox.add_widget(self.__applyButton)
		self.__lowerBox.add_widget(self.__deleteCurrentButton)
		if (len (self.__objectsList) > 1):
			self.__lowerBox.add_widget(self.__applyToAllButton)
			self.__lowerBox.add_widget(Label(text = '', size_hint = (0.2, 1.0)))
			self.__lowerBox.add_widget(self.__previousObjectButton)
			self.__lowerBox.add_widget(self.__nextObjectButton)
		else:
			self.__lowerBox.add_widget(Label(text = '', size_hint = (0.5, 1.0)))

		self.__lowerBox.add_widget(self.__okButton)
		self.__lowerBox.add_widget(self.__cancelButton)
		
	def __createOrEditCollisionInfo(self, useless):
		CollisionToMainLayoutCommunication.Instance().giveBackKeyboard()
		
		for obj in self.__objectsList:
			currentId = obj.getIdentifier()
			if (obj.getCollisionInfo() == None):
				if (self.__copiesDict[currentId].getPartsList() != []):
					obj.setCollisionInfo(self.__copiesDict[currentId])
			else:
				obj.setCollisionInfo(self.__copiesDict[currentId])
		
		self.__collisionPopUp.dismiss()

	def __init__(self):
		self.__baseHeight = 0.05

		self.__copiesDict = {}
		self.__extraPartsDict = {}
		self.__objectsList = []
		self.__objectsListIndex = 0
		
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

		self.__partsLayoutList = []
		for i in range(8):
			self.__partsLayoutList.append(CollisionPartLayout())

		self.__partsPanel = TabbedPanel(default_tab_text = 'Part 1', size_hint = (1.0, 0.6), 
				default_tab_content = self.__partsLayoutList[0].getLayout())

		self.__mainLayout.add_widget(self.__partsPanel)

		self.__lowerBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, self.__baseHeight))
		
		self.__okButton = Button(text = 'Done', size_hint = (0.1, 1.0))
		self.__cancelButton = Button (text = 'Cancel', size_hint = (0.1, 1.0))
		self.__applyButton = Button (text = 'Apply', size_hint = (0.1, 1.0))
		self.__applyToAllButton = Button (text = 'Apply to all', size_hint = (0.1, 1.0))
		self.__deleteCurrentButton = Button (text = 'Delete', size_hint = (0.1, 1.0))
		self.__previousObjectButton = Button (text = 'Previous', size_hint = (0.1, 1.0))
		self.__nextObjectButton = Button (text = 'Next', size_hint = (0.1, 1.0))
		self.__editFlagsButton = Button (text = 'Edit Flags', size_hint = (0.1, 1.0))
		
		self.__okButton.bind(on_release=self.__createOrEditCollisionInfo)
		self.__cancelButton.bind(on_release = self.__collisionPopUp.dismiss)
		self.__applyButton.bind(on_release = self.__applyChanges)
		# TODO: Code the apply to all button method and bind it
		self.__deleteCurrentButton.bind(on_release = self.__deleteCurrentPart)
		self.__previousObjectButton.bind(on_release = self.__selectPreviousObject)
		self.__nextObjectButton.bind(on_release = self.__selectNextObject)
		self.__editFlagsButton.bind(on_release = CollisionFlagsEditor.Instance().showPopUp)
		
		self.__mainLayout.add_widget(Label(text = '', size_hint = (1.0, self.__baseHeight)))
		self.__mainLayout.add_widget(self.__lowerBox)
		
		self.__collisionPopUp.content = self.__mainLayout
		self.__editingObject = None
			
		
		self.__warnDelete = Dialog(self.__doDeleteCurrentPart, 'Confirmation', 'Are you sure you want to\ndelete this part?',
				'Yes', 'No')
		self.__warnApplyAll = Dialog(self.__doApplyChanges, 'Confirmation', 'This will replace information of other objects.',
				'Yes', 'No')
		self.__errorPopUp = AlertPopUp('Error', 'No Object selected!\nYou need to select one object from the scene.', 'Ok')

	def updateLayout(self):
		self.__render()

	def showPopUp(self):
		
		objList = CollisionToSceneCommunication.Instance().getSelectedObjects()
		if (objList == []):
			self.__errorPopUp.setText('No object(s) selected!\nYou need to select at least one object from the scene.')
			self.__errorPopUp.open()
		
		else:
			self.__objectsList = objList
			self.__copiesDict = {}
			self.__extraPartsDict = {}
			self.__objectsListIndex = 0
			self.__createTemporatyCopies()
			self.__render()
			self.__collisionPopUp.open()

