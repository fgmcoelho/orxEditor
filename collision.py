from singleton import Singleton

from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.switch import Switch
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.togglebutton import ToggleButton

from string import letters, digits
from math import floor, ceil

from editorutils import Alert, Dialog, EmptyScrollEffect, CancelableButton, distance
from keyboard import KeyboardAccess, KeyboardGuardian
from collisioninfo import CollisionPartInformation, CollisionInformation
from collisionform import CollisionPartDisplay
from modulesaccess import ModulesAccess

class CollisionFlagEditorPopup(KeyboardAccess):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.close()

	def __reaplyFocus(self):
		flagsList = ModulesAccess.get('CollisionGuardian').getFlags()
		if (len(flagsList) != self.__maxCollisionFlags):
			self.__inputBar.clear_widgets()
			oldText = self.__flagNameInput.text
			self.__flagNameInput = TextInput(text = oldText, multiline = False, size_hint = (0.9, 1.0),
				on_text_validate = self.__processAddFlag, focus = True)
			self.__inputBar.add_widget(self.__flagNameInput)
			self.__inputBar.add_widget(self.__flagAddButton)

	def __render(self):
		self.__layout.clear_widgets()
		self.__layout.add_widget(Label(text = '', size_hint = (1.0, self.__baseHeight)))

		flagsList = ModulesAccess.get('CollisionGuardian').getFlags()
		for flag in flagsList:
			flagLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, self.__baseHeight))
			flagLine.add_widget(Label(text = flag.getName(), size_hint = (0.9, 1.0)))
			flagLine.add_widget(CancelableButton(text = 'Delete', size_hint = (0.1, 1.0), id = 'Delete#' + \
				flag.getName(),	on_release = self.__processRemoveFlag))
			self.__layout.add_widget(flagLine)
		self.__layout.add_widget(Label(text = '', size_hint = (1.0, 1.0 - ((len(flagsList) + 3) * self.__baseHeight))))

		if (len(flagsList) == self.__maxCollisionFlags):
			self.__layout.add_widget(Label(text = 'Maximum number of flags (%u) reached.' %
				(self.__maxCollisionFlags, ), size_hint = (1.0, self.__baseHeight)))
		else:
			self.__reaplyFocus()
			self.__layout.add_widget(self.__inputBar)

		self.__layout.add_widget(Label(text = '', size_hint = (1.0, self.__baseHeight)))
		self.__layout.add_widget(self.__bottomBar)

	def __removeFlagsFromPartsList(self, partsList):
		flagObject = ModulesAccess.get('CollisionGuardian').getFlagByName(self.__flagToRemove)
		for part in partsList:
			if (flagObject in part.getSelfFlags()):
				part.removeFlagFromSelfFlags(self.__flagToRemove)

			if (flagObject in part.getCheckMask()):
				part.removeFlagFromCheckMask(self.__flagToRemove)

	def __isPartsListAffected(self, partsList):
		flagObject = ModulesAccess.get('CollisionGuardian').getFlagByName(self.__flagToRemove)
		for part in partsList:
			if (flagObject in part.getSelfFlags() or flagObject in part.getCheckMask()):
				return 1
		return 0

	def __doRemoveFlag(self, *args):
		objectsList = ModulesAccess.get('SceneHandler').getAllObjects()
		for obj in objectsList:
			collisionInfo = obj.getCollisionInfo()
			if (collisionInfo is not None):
				self.__removeFlagsFromPartsList(collisionInfo.getPartsList())

		for collisionInfo in ModulesAccess.get('CollisionEditor').getCopiesDictAsList():
			self.__removeFlagsFromPartsList(collisionInfo.getPartsList())

		for partsList in ModulesAccess.get('CollisionEditor').getExtraPartsDictAsList():
			self.__removeFlagsFromPartsList(partsList)

		ModulesAccess.get('CollisionGuardian').removeFlag(self.__flagToRemove)
		self.__flagToRemove = None
		self.__render()

	def __processRemoveFlag(self, buttonPressed, touch):
		objectsList = ModulesAccess.get('SceneHandler').getAllObjects()
		existingObjectsCount = 0
		editingObjectsCount = 0
		self.__flagToRemove = buttonPressed.id.split('#')[1]
		for obj in objectsList:
			collisionInfo = obj.getCollisionInfo()
			if (collisionInfo is not None):
				existingObjectsCount += self.__isPartsListAffected(collisionInfo.getPartsList())

		for collisionInfo in ModulesAccess.get('CollisionEditor').getCopiesDictAsList():
		 	editingObjectsCount += self.__isPartsListAffected(collisionInfo.getPartsList())

		for partsList in ModulesAccess.get('CollisionEditor').getExtraPartsDictAsList():
			editingObjectsCount += self.__isPartsListAffected(partsList)

		if (existingObjectsCount == 0 and editingObjectsCount == 0):
			self.__flagRemoveWarning.setText(
				'Are you sure that you want to delete the\n'
				'%s flag?\n'
				'This operation can\'t be reverted.' %
				(self.__flagToRemove, )
			)

		elif (existingObjectsCount == 0 and editingObjectsCount != 0):
			self.__flagRemoveWarning.setText(
				'This will affect %d objects being edited.\n'
				'Are you sure you want to remove the\n'
				'%s flag?\n'
				'This operation can\'t be reverted.' %
				(editingObjectsCount, self.__flagToRemove)
			)

		elif (existingObjectsCount != 0 and editingObjectsCount == 0):
			self.__flagRemoveWarning.setText(
				'This will affect %d existing objects.\n'
				'Are you sure you want to remove the\n'
				'%s flag?\n'
				'This operation can\'t be reverted.' %
				(existingObjectsCount, self.__flagToRemove)
			)

		else:
			self.__flagRemoveWarning.setText(
				'This will affect %d existing objects and\n'
				'%d objects being edited.\n'
				'Are you sure you want to remove the\n'
				'%s flag?\n'
				'This operation can\'t be reverted.' %
				(existingObjectsCount, editingObjectsCount, self.__flagToRemove)
			)
		self.__flagRemoveWarning.open()

	def __processAddFlag(self, *args):
		if (self.__flagNameInput.text == ''):
			error = Alert('Error', 'Flag name can\'t be empty.', 'Ok', self.__reaplyFocus)
			error.open()
			return

		if (ModulesAccess.get('CollisionGuardian').getFlagByName(self.__flagNameInput.text) is not None):
			error = Alert('Error', 'This name has already been used.', 'Ok', self.__reaplyFocus)
			error.open()
			return

		invalidSet = []
		for char in self.__flagNameInput.text:
			if (char not in self.__validCharacters):
				invalidSet.append(char)

		if (invalidSet != []):
			error = Alert('Error', 'Found invalid characters in the name:\n ' + ''.join(invalidSet), 'Ok',
				self.__reaplyFocus)
			error.open()
			return

		ModulesAccess.get('CollisionGuardian').addNewFlag(self.__flagNameInput.text)
		self.__flagNameInput.text = ''
		self.__render()

	def __init__(self):
		ModulesAccess.add('CollisionFlagEditor', self)
		self.__layout = BoxLayout(orientation = 'vertical')
		self.__popup = Popup (title = 'Collision flags editor', auto_dismiss = False, content = self.__layout)

		self.__validCharacters = letters + digits
		self.__maxCollisionFlags = 16
		self.__baseHeight = 0.05

		emptyLabel = Label(text = '', size_hint = (0.9, 1.0))

		self.__inputBar = BoxLayout(orientation = 'horizontal', size_hint = (1.0, self.__baseHeight))
		self.__flagNameInput = TextInput(multiline = False, size_hint = (0.9, 1.0),
			on_text_validate = self.__processAddFlag, focus = False)
		self.__flagAddButton = CancelableButton(text = 'Add', size_hint = (0.1, 1.0),
			on_release = self.__processAddFlag)

		self.__inputBar.add_widget(self.__flagNameInput)
		self.__inputBar.add_widget(self.__flagAddButton)

		self.__bottomBar = BoxLayout(orientation = 'horizontal', size_hint = (1.0, self.__baseHeight))
		doneButton = CancelableButton(text = 'Done', size_hint = (0.1, 1.0), on_release = self.close)
		self.__bottomBar.add_widget(Label(text = '', size_hint = (0.9, 1.0)))
		self.__bottomBar.add_widget(doneButton)

		self.__layout.add_widget(self.__inputBar)
		self.__layout.add_widget(emptyLabel)
		self.__layout.add_widget(self.__bottomBar)

		self.__flagToRemove = None
		self.__flagRemoveWarning = Dialog(self.__doRemoveFlag, 'Confirmation',
			'This will affect existing objects.\nAre you sure you want to remove this flag?', 'Yes', 'No',
			self.__reaplyFocus, self.__reaplyFocus)

	def close(self, *args):
		self.__flagNameInput.focus = False
		KeyboardGuardian.Instance().dropKeyboard(self)
		ModulesAccess.get('CollisionEditor').updateLayout()
		self.__popup.dismiss()

	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__render()
		self.__popup.open()

class CollisionPartLayout:
	def __togglePartFlag(self, buttonObject):
		buttonInfo = buttonObject.id.split('#')
		if (buttonObject.state == 'normal'):
			if (buttonInfo[1] == 'selfflags'):
				self.__part.removeFlagFromSelfFlags(
					ModulesAccess.get('CollisionGuardian').getFlagByName(buttonInfo[2])
				)
			else:
				self.__part.removeFlagFromCheckMask(
					ModulesAccess.get('CollisionGuardian').getFlagByName(buttonInfo[2])
				)
		else:
			if (buttonInfo[1] == 'selfflags'):
				self.__part.addFlagToSelfFlags(
					ModulesAccess.get('CollisionGuardian').getFlagByName(buttonInfo[2])
				)
			else:
				self.__part.addFlagToCheckMask(
					ModulesAccess.get('CollisionGuardian').getFlagByName(buttonInfo[2])
				)

	def __doUpdateFormType(self):
		self.__part.setFormType(self.__formToSet)
		ModulesAccess.get('CollisionEditor').preview()

	def __restoreFormCheckbox(self):
		form = self.__part.getFormType()
		if (form == 'box'):
			self.__boxCheckBox.active = True
			self.__sphereCheckBox.active = False
			self.__meshCheckBox.active = False
		elif (form == 'sphere'):
			self.__boxCheckBox.active = False
			self.__sphereCheckBox.active = True
			self.__meshCheckBox.active = False
		else:
			self.__boxCheckBox.active = False
			self.__sphereCheckBox.active = False
			self.__meshCheckBox.active = True

	def __updateFormType(self, checkboxObject, newValue):
		if (newValue == True):
			checkboxInfo = checkboxObject.id.split('#')
			if (checkboxInfo[1] == self.__part.getFormType()):
				return

			self.__formToSet = checkboxInfo[1]
			if (self.__part.getPoints() is not None):
				dialog = Dialog(self.__doUpdateFormType, 'Confirmation',
					'This object have manually set collision form data,\n'\
					'if you set a new form, the former date will be lost!\n'
					'Do you wish to continue?', 'Yes', 'No', None, self.__restoreFormCheckbox)
				dialog.open()
			else:
				self.__doUpdateFormType()


	def __updateSolidFlag(self, instance, newValue):
			self.__part.setSolid(newValue)

	def __render(self, part, obj):
		self.__obj = obj
		self.__part = part
		flagsList = ModulesAccess.get('CollisionGuardian').getFlags()
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
					self.__selfFlagsGrid.add_widget(ToggleButton(text = name, size_hint = (0.25, 0.25),
						state = 'normal', on_release = self.__togglePartFlag, id = 'togglebutton#selfflags#' + name))
			else:
				self.__selfFlagsGrid.add_widget(Label(text = '', size_hint = (0.25, 0.25)))

		for i in range(16):
			if (i < numberOfFlags):
				name = flagsList[i].getName()
				if (name in partCheckMask):
					self.__checkMaskGrid.add_widget(ToggleButton(text = name, size_hint = (0.25, 0.25), state = 'down',
						on_release = self.__togglePartFlag, id = 'togglebutton#checkmask#' + name))
				else:
					self.__checkMaskGrid.add_widget(ToggleButton(text = name, size_hint = (0.25, 0.25),
						state = 'normal', on_release = self.__togglePartFlag, id = 'togglebutton#checkmask#' + name))
			else:
				self.__checkMaskGrid.add_widget(Label(text = '', size_hint = (0.25, 0.25)))

		if (part.getPoints() == None):
			self.__pointsText.text = 'Have collision points? No.'
		else:
			self.__pointsText.text = 'Have collision points? Yes.'

		self.__partSolidSwitch.active = part.getSolid()
		self.__partSolidSwitch.bind(active = self.__updateSolidFlag)

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

	def __callFormEditPopup(self, *args):
		ModulesAccess.get('CollisionFormEditor').open(self.__part, self.__obj)

	def __init__(self):
		self.__layout = BoxLayout(orientation = 'horizontal')
		self.__baseHeight = 0.1
		self.__part = None

		leftLayout = BoxLayout(orientation = 'vertical', size_hint = (0.5, 1.0))
		rightLayout = BoxLayout(orientation = 'vertical', size_hint = (0.5, 1.0))

		leftLayout.add_widget(Label(text = 'Self Flags:', size_hint = (1.0, self.__baseHeight)))
		self.__selfFlagsGrid = GridLayout(cols = 4, row = 4, size_hint = (1.0, 4 * self.__baseHeight))

		leftLayout.add_widget(self.__selfFlagsGrid)

		leftLayout.add_widget(Label(text = '', size_hint = (1.0, 1.0 - (self.__baseHeight * 7))))

		solidLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, self.__baseHeight))
		solidLine.add_widget(Label(text = 'Solid:'))
		self.__partSolidSwitch = Switch(active = False)
		solidLine.add_widget(self.__partSolidSwitch)
		leftLayout.add_widget(solidLine)

		pointsLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, self.__baseHeight))
		self.__pointsText = Label(text = 'Have collision points?')
		self.__pointsButton = CancelableButton(text = 'Edit points', on_release = self.__callFormEditPopup)
		pointsLine.add_widget(self.__pointsText)
		pointsLine.add_widget(self.__pointsButton)
		leftLayout.add_widget(pointsLine)

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

	def updateLayout(self, part, obj):
		assert (isinstance(part, CollisionPartInformation))
		self.__render(part, obj)

	def getPart(self):
		return self.__part

class CollisionEditorPopup(KeyboardAccess):
	def _processKeyUp(self, keyboard, keycode):
		if (keycode[1] == 'escape'):
			self.close()

	def __createTemporatyCopies(self):
		for obj in self.__objectsList:
			if (obj.getCollisionInfo() is not None):
				infoCopy = CollisionInformation.copy(obj.getCollisionInfo())
			else:
				infoCopy = CollisionInformation()

			extraParts = []
			for i in range (8 - len(infoCopy.getPartsList())):
				extraParts.append(CollisionPartInformation())

			self.__copiesDict[obj.getIdentifier()] = infoCopy
			self.__extraPartsDict[obj.getIdentifier()] = extraParts

	def __addPart(self, *args):
		assert self.__partsPanel.current_tab.text == 'Edit'
		currentId = self.__objectsList[self.__objectsListIndex].getIdentifier()
		newPart = self.__extraPartsDict[currentId].pop(0)
		self.__copiesDict[currentId].addPart(newPart)
		self.__render()
		self.preview()

	def __doDeleteCurrentPart(self, *args):
		currentId = self.__objectsList[self.__objectsListIndex].getIdentifier()
		index = int(self.__partsPanel.current_tab.text.split(' ')[1])
		partsList = self.__copiesDict[currentId].getPartsList()
		part = partsList[index - 1]
		self.__copiesDict[currentId].removePart(part)
		part = None
		self.__extraPartsDict[currentId].append(CollisionPartInformation())
		self.__render()

	def __deleteCurrentPart(self, *args):
		if (self.__partsPanel.current_tab.text == 'Edit'):
			errorPopup = Alert('Error', 'You can\'t delete the edit flag, it hasn\'t been added.', 'Ok')
			errorPopup.open()
		else:
			self.__warnDelete.open()

	def __doApplyChanges(self, *args):
		currentObj = self.__objectsList[self.__objectsListIndex]
		infoToCopy = self.__copiesDict[currentObj.getIdentifier()]
		for obj in self.__objectsList:
			if (obj != currentObj):
				infoCopy = CollisionInformation.copy(infoToCopy)
				self.__copiesDict[obj.getIdentifier()] = infoCopy
				numberOfParts = len(infoCopy.getPartsList())
				numberOfExtraParts = len(self.__extraPartsDict[obj.getIdentifier()])
				while (numberOfExtraParts + numberOfParts > 8):
					self.__extraPartsDict[obj.getIdentifier()].pop()
					numberOfExtraParts = len(self.__extraPartsDict[obj.getIdentifier()])
				while (numberOfExtraParts + numberOfParts < 8):
					self.__extraPartsDict[obj.getIdentifier()].append(CollisionPartInformation())
					numberOfExtraParts = len(self.__extraPartsDict[obj.getIdentifier()])

		self.__render()

	def __applyChangesToAll(self, *args):
		willEraseInfo = 0
		currentObj = self.__objectsList[self.__objectsListIndex]
		for obj in self.__objectsList:
			if (obj != currentObj):
				if (obj.getCollisionInfo() is not None or
							CollisionInformation.isOnStartState(self.__copiesDict[obj.getIdentifier()]) == False):
					willEraseInfo += 1

		if (willEraseInfo != 0):
			self.__warnApplyAll.setText('This will replace information of other ' + str(willEraseInfo) + ' objects.')
			self.__warnApplyAll.open()

		else:
			self.__doApplyChanges()

	def __selectNextObject(self, *args):
		self.__objectsListIndex = (self.__objectsListIndex + 1) % len(self.__objectsList)
		self.__render()
		self.preview()

	def __selectPreviousObject(self, *args):
		self.__objectsListIndex = (self.__objectsListIndex - 1) % len(self.__objectsList)
		self.__render()
		self.preview()

	def __reloadObjectsCollisionDisplay(self, expandLevel = 1.0):
		self.__objectsCollisionDisplay.clear_widgets()
		self.__partDisplay = CollisionPartDisplay(self.__objectsList[self.__objectsListIndex], expandLevel)
		self.__objectsCollisionDisplay.size = self.__partDisplay.getSize()
		self.__objectsCollisionDisplay.add_widget(self.__partDisplay)

	def __reloadUpperBoxes(self):
		self.__flagsAndPreviewBox.clear_widgets()
		self.__flagsAndPreviewBox.add_widget(self.__objectsCollisionDisplay)
		self.__flagsAndPreviewBox.add_widget(self.__bodyInfoBox)

	def __renderUpperPart(self, collisionInfo):
		self.__reloadObjectsCollisionDisplay()

		self.__dynamicSwitch.active = collisionInfo.getDynamic()
		self.__fixedRotationSwitch.active = collisionInfo.getFixedRotation()
		self.__highSpeedSwitch.active = collisionInfo.getHighSpeed()

		self.__reloadUpperBoxes()

	def __changeTabs(self, *args):
		self.__partDisplay.clearDrawnForm()
		self.__renderLowerPart(args[0].text)

	def __createPannedHeader(self, text, content, index):
		th = TabbedPanelHeader(text = text, on_press = self.__changeTabs, on_release = self.preview,
			id = 'tab#' + str(index))
		th.content = content
		return th

	def __renderTabbedPanel(self, obj, collisionInfo, extraParts):
		parts = collisionInfo.getPartsList()
		numberOfParts = len(parts)
		self.__partsPanel.clear_tabs()
		for i in range(numberOfParts):
			self.__partsLayoutList[i].updateLayout(parts[i], obj)
			self.__partsPanel.add_widget(self.__createPannedHeader('Part ' + str(i + 1),
				self.__partsLayoutList[i].getLayout(), i))

		if (extraParts != []):
			self.__partsLayoutList[numberOfParts].updateLayout(extraParts[0], obj)
			self.__partsPanel.add_widget(self.__createPannedHeader('Edit',
				self.__partsLayoutList[numberOfParts].getLayout(), numberOfParts))

		self.__partsPanel.switch_to(self.__partsPanel.tab_list[0])

	def __renderLowerPart(self, selectedTab = None):
		self.__lowerBox.clear_widgets()
		self.__lowerBox.add_widget(self.__editFlagsButton)
		if(selectedTab is None or selectedTab == 'Edit'):
			self.__lowerBox.add_widget(self.__addButton)
		else:
			self.__lowerBox.add_widget(self.__deleteCurrentButton)

		if (len (self.__objectsList) > 1):
			if (selectedTab is None or selectedTab == 'Edit'):
				self.__lowerBox.add_widget(Label(text = '', size_hint = (0.3, 1.0)))
			else:
				self.__lowerBox.add_widget(self.__applyToAllButton)
				self.__lowerBox.add_widget(Label(text = '', size_hint = (0.1, 1.0)))

			self.__lowerBox.add_widget(self.__previousObjectButton)
			self.__lowerBox.add_widget(self.__nextObjectButton)
		else:
			self.__lowerBox.add_widget(Label(text = '', size_hint = (0.4, 1.0)))

		self.__lowerBox.add_widget(self.__okButton)
		self.__lowerBox.add_widget(self.__cancelButton)

	def __render(self):
		currentObj = self.__objectsList[self.__objectsListIndex]
		currentId = currentObj.getIdentifier()
		collisionInfo = self.__copiesDict[currentId]
		extraParts = self.__extraPartsDict[currentId]

		self.__renderUpperPart(collisionInfo)
		self.__renderTabbedPanel(currentObj, collisionInfo, extraParts)
		self.__renderLowerPart()

	def __createOrEditCollisionInfo(self, *args):
		for obj in self.__objectsList:
			currentId = obj.getIdentifier()
			if (obj.getCollisionInfo() is None):
				copiedInfo = self.__copiesDict[currentId]
				if (copiedInfo.getPartsList() != [] or copiedInfo.getDynamic() == True or
						copiedInfo.getFixedRotation() == True or copiedInfo.getHighSpeed() == True):
					obj.setCollisionInfo(self.__copiesDict[currentId])
			else:
				obj.setCollisionInfo(self.__copiesDict[currentId])
		self.close()

	def __needToOversizePreview(self, part):
		overSizeNeeded = False
		points = part.getPoints()
		if (points != None):
			form = part.getFormType()
			limits = self.__objectsList[self.__objectsListIndex].getBaseSize()
			if form == 'box' or form == 'mesh':
				for point in points:
					if ((floor(point[0]) < 0 or floor(point[1]) < 0) or
							(ceil(point[0]) > limits[0] or ceil(point[1]) > limits[1])):
						overSizeNeeded = True
						break
			else:
				center = points[0]
				radius = distance(points[0], points[1])
				if ((floor(center[0] - radius) < 0 or floor(center[1] - radius) < 0) or
						(ceil(center[0] + radius) > limits[0] or ceil(center[1] + radius) > limits[1])):
					overSizeNeeded = True

		return overSizeNeeded

	def __updateDynamicFlag(self, instance, value):
		idToUse = self.__objectsList[self.__objectsListIndex].getIdentifier()
		self.__copiesDict[idToUse].setDynamic(value)

	def __updateFixedRotationFlag(self, instance, value):
		idToUse = self.__objectsList[self.__objectsListIndex].getIdentifier()
		self.__copiesDict[idToUse].setFixedRotation(value)

	def __updateHighSpeedFlag(self, instance, value):
		idToUse = self.__objectsList[self.__objectsListIndex].getIdentifier()
		self.__copiesDict[idToUse].setHighSpeed(value)

	def __init__(self):
		ModulesAccess.add('CollisionEditor', self)
		self.__baseHeight = 0.05

		self.__copiesDict = {}
		self.__extraPartsDict = {}
		self.__objectsList = []
		self.__objectsListIndex = 0

		self.__collisionPopUp = Popup (title = 'Collision configs', auto_dismiss = False)
		self.__mainLayout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))

		self.__flagsAndPreviewBox = BoxLayout(orientation = 'horizontal', size_hint= (1.0, 6 * self.__baseHeight))
		self.__objectsCollisionDisplay = ScrollView(effect_cls = EmptyScrollEffect)
		self.__flagsAndPreviewBox.add_widget(self.__objectsCollisionDisplay)

		self.__bodyInfoBox = GridLayout(orientation = 'vertical', size_hint = (0.5, 1.0), cols = 2, rows = 4)
		self.__bodyInfoBox.add_widget(Label(text = 'Dynamic', size_hint = (0.3, 0.15)))
		self.__dynamicSwitch = Switch(active = False, size_hint = (0.7, 0.15))
		self.__dynamicSwitch.bind(active = self.__updateDynamicFlag)
		self.__bodyInfoBox.add_widget(self.__dynamicSwitch)

		self.__bodyInfoBox.add_widget(Label(text = 'Fixed Rotation', size_hint = (0.3, 0.15)))
		self.__fixedRotationSwitch = Switch(active = False, size_hint = (0.7, 0.15))
		self.__fixedRotationSwitch.bind(active = self.__updateFixedRotationFlag)
		self.__bodyInfoBox.add_widget(self.__fixedRotationSwitch)

		self.__bodyInfoBox.add_widget(Label(text = 'High Speed', size_hint = (0.3, 0.15)))
		self.__highSpeedSwitch = Switch(active = False, size_hint = (0.7, 0.15))
		self.__highSpeedSwitch.bind(active = self.__updateHighSpeedFlag)
		self.__bodyInfoBox.add_widget(self.__highSpeedSwitch)

		self.__bodyInfoBox.add_widget(Label(text = '', size_hint = (0.5, 0.55)))
		self.__bodyInfoBox.add_widget(Label(text = '', size_hint = (0.5, 0.55)))

		self.__flagsAndPreviewBox.add_widget(self.__bodyInfoBox)

		self.__mainLayout.add_widget(self.__flagsAndPreviewBox)

		self.__mainLayout.add_widget(Label(text = '', size_hint = (1.0, self.__baseHeight)))

		self.__partsLayoutList = []
		for i in range(8):
			self.__partsLayoutList.append(CollisionPartLayout())

		self.__partsPanel = TabbedPanel(do_default_tab = False, size_hint = (1.0, 0.6))

		self.__mainLayout.add_widget(self.__partsPanel)

		self.__lowerBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, self.__baseHeight))

		self.__okButton = CancelableButton(text = 'Done', size_hint = (0.1, 1.0),
			on_release=self.__createOrEditCollisionInfo)
		self.__cancelButton = CancelableButton(text = 'Cancel', size_hint = (0.1, 1.0), on_release = self.close)
		self.__addButton = CancelableButton(text = 'Add', size_hint = (0.1, 1.0), on_release = self.__addPart)
		self.__applyToAllButton = CancelableButton(text = 'Copy info to all', size_hint = (0.2, 1.0),
			on_release = self.__applyChangesToAll)
		self.__deleteCurrentButton = CancelableButton(text = 'Delete', size_hint = (0.1, 1.0),
			on_release = self.__deleteCurrentPart)
		self.__previousObjectButton = CancelableButton(text = 'Previous', size_hint = (0.1, 1.0),
			on_release = self.__selectPreviousObject)
		self.__nextObjectButton = CancelableButton(text = 'Next', size_hint = (0.1, 1.0),
			on_release = self.__selectNextObject)
		self.__editFlagsButton = CancelableButton(text = 'Edit Flags', size_hint = (0.1, 1.0),
			on_release = ModulesAccess.get('CollisionFlagEditor').open)

		self.__mainLayout.add_widget(Label(text = '', size_hint = (1.0, self.__baseHeight)))
		self.__mainLayout.add_widget(self.__lowerBox)

		self.__collisionPopUp.content = self.__mainLayout
		self.__editingObject = None


		self.__warnDelete = Dialog(self.__doDeleteCurrentPart, 'Confirmation',
			'Are you sure you want to\ndelete this part?', 'Yes', 'No')
		self.__warnApplyAll = Dialog(self.__doApplyChanges, 'Confirmation',
			'This will replace information of other objects.', 'Yes', 'No')
		self.__errorPopUp = Alert('Error', 'No Object selected!\nYou need to select one object from the scene.',
			'Ok')

	def preview(self, *args):
		if (len(args) > 0 and isinstance(args[0], TabbedPanelHeader)):
			i = int(args[0].id.split('#')[1])
		else:
			i = int(self.__partsPanel.current_tab.id.split('#')[1])

		part = self.__partsLayoutList[i].getPart()
		self.__partsLayoutList[i].updateLayout(part, self.__objectsList[self.__objectsListIndex])
		needOversize = self.__needToOversizePreview(part)
		if (needOversize == True):
			expandLevel = 2
		else:
			expandLevel = 1

		self.__reloadObjectsCollisionDisplay(expandLevel)
		self.__reloadUpperBoxes()

		if (needOversize == True):
			transformedPoints = []
			partCopy = CollisionPartInformation.copy(part)
			for point in partCopy.getPoints():
				transformedPoints.append(self.__partDisplay.getImage().to_parent(point[0], point[1]))

			partCopy.setPoints(transformedPoints)
			partToRender = partCopy
		else:
			partToRender = part

		self.__partDisplay.drawPart(partToRender)

	def updateLayout(self):
		self.__render()

	def getCopiesDictAsList(self):
		return self.__copiesDict.values()

	def getExtraPartsDictAsList(self):
		return self.__extraPartsDict.values()

	def open(self, *args):
		objList = ModulesAccess.get('SceneHandler').getCurrentSelection()
		if (objList == []):
			self.__errorPopUp.setText('No object is selected!\nYou need to select at least one object from the scene.')
			self.__errorPopUp.open()
		else:
			firstSize = objList[0].getBaseSize()
			for obj in objList:
				sizeToCompare = obj.getBaseSize()
				if (firstSize[0] != sizeToCompare[0] or firstSize[1] != sizeToCompare[1]):
					self.__errorPopUp.setText(
						'Collision editor can only work on multiple\n'\
						'objects that have the same base size.'
					)
					self.__errorPopUp.open()
					return

			KeyboardGuardian.Instance().acquireKeyboard(self)
			self.__objectsList = objList
			self.__copiesDict = {}
			self.__extraPartsDict = {}
			self.__objectsListIndex = 0
			self.__createTemporatyCopies()
			self.__render()
			self.preview()
			self.__collisionPopUp.open()

	def close(self, *args):
		KeyboardGuardian.Instance().dropKeyboard(self)
		self.__collisionPopUp.dismiss()
