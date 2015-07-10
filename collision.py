from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.switch import Switch
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.clock import Clock

from math import floor, ceil

from editorheritage import SeparatorLabel, AutoFocusInputUser
from editorutils import Alert, Dialog, EmptyScrollEffect, CancelableButton, distance, AlignedLabel, AlignedToggleButton
from keyboard import KeyboardAccess, KeyboardGuardian
from collisioninfo import CollisionPartInformation, CollisionInformation
from collisionform import CollisionPartDisplay
from modulesaccess import ModulesAccess
from uisizes import defaultSmallButtonSize, defaultLineSize, defaultInputSize, defaultLabelSize, defaultCheckboxSize,\
	defaultFontSize, defaultSwitchSize, defaultLargeButtonSize, collisionBodyInfoSize, collisionTabbedSize

class CollisionConfig(object):
	def __init__(self):
		super(CollisionConfig, self).__init__()
		self._switchLineSize = defaultLineSize.copy()
		self._switchLineSize['height'] = defaultSwitchSize['height']

class CollisionFlagEditorPopup(AutoFocusInputUser, SeparatorLabel, KeyboardAccess):
	def __reaplyFocus(self):
		flagsList = ModulesAccess.get('CollisionGuardian').getFlags()
		if (len(flagsList) != self.__maxCollisionFlags):
			self.__inputBar.clear_widgets()
			self.__inputBar.add_widget(self._autoFocusInput)
			self.__inputBar.add_widget(self.__flagAddButton)
			Clock.schedule_once(self._delayedFocus, 0)

	def __render(self):
		self.__layout.clear_widgets()
		self.__layout.add_widget(AlignedLabel(text = '', **defaultLineSize))

		flagsList = ModulesAccess.get('CollisionGuardian').getFlags()
		for flag in flagsList:
			flagLine = BoxLayout(orientation = 'horizontal', **defaultLineSize)
			flagLine.add_widget(AlignedLabel(text = flag.getName(), **defaultLabelSize))
			flagLine.add_widget(CancelableButton(text = 'Delete', id = 'Delete#' + flag.getName(),
				on_release = self.__processRemoveFlag, **defaultSmallButtonSize))
			self.__layout.add_widget(flagLine)
		self.__layout.add_widget(self.getSeparator())

		if (len(flagsList) == self.__maxCollisionFlags):
			self.__layout.add_widget(AlignedLabel(text = 'Maximum number of flags (%u) reached.' %
				(self.__maxCollisionFlags, ), **defaultLabelSize))
		else:
			self.__reaplyFocus()
			self.__layout.add_widget(self.__inputBar)

		self.__layout.add_widget(AlignedLabel(text = '', **defaultLineSize))
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
		if (self._autoFocusInput.text == ''):
			error = Alert('Error', 'Flag name can\'t be empty.', 'Ok', self.__reaplyFocus)
			error.open()
			return

		if (ModulesAccess.get('CollisionGuardian').getFlagByName(self._autoFocusInput.text) is not None):
			error = Alert('Error', 'This name has already been used.', 'Ok', self.__reaplyFocus)
			error.open()
			return

		invalidSet = []
		for char in self._autoFocusInput.text:
			if (char not in self._validCharacters):
				invalidSet.append(char)

		if (invalidSet != []):
			error = Alert('Error', 'Found invalid characters in the name:\n ' + ''.join(invalidSet), 'Ok',
				self.__reaplyFocus)
			error.open()
			return

		ModulesAccess.get('CollisionGuardian').addNewFlag(self._autoFocusInput.text)
		self._autoFocusInput.text = ''
		self.__render()

	def __init__(self):
		ModulesAccess.add('CollisionFlagEditor', self)
		super(CollisionFlagEditorPopup, self).__init__()
		self._autoFocusInput.bind(on_text_validate = self.__processAddFlag)
		self.__layout = BoxLayout(orientation = 'vertical')
		self.__popup = Popup (title = 'Collision flags editor', auto_dismiss = False, content = self.__layout)

		self.__maxCollisionFlags = 16
		self.__inputBar = BoxLayout(orientation = 'horizontal', **defaultInputSize)
		self.__flagAddButton = CancelableButton(text = 'Add', on_release = self.__processAddFlag,
			**self._addButtonSize)

		self.__inputBar.add_widget(self._autoFocusInput)
		self.__inputBar.add_widget(self.__flagAddButton)

		self.__bottomBar = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		doneButton = CancelableButton(text = 'Done', on_release = self.close, **defaultSmallButtonSize)
		self.__bottomBar.add_widget(self.getSeparator())
		self.__bottomBar.add_widget(doneButton)

		self.__layout.add_widget(self.__inputBar)
		self.__layout.add_widget(self.getSeparator())
		self.__layout.add_widget(self.__bottomBar)

		self.__flagToRemove = None
		self.__flagRemoveWarning = Dialog(self.__doRemoveFlag, 'Confirmation',
			'This will affect existing objects.\nAre you sure you want to remove this flag?', 'Yes', 'No',
			self.__reaplyFocus, self.__reaplyFocus)

	def close(self, *args):
		self._autoFocusInput.focus = False
		KeyboardGuardian.Instance().dropKeyboard(self)
		ModulesAccess.get('CollisionEditor').updateLayout()
		self.__popup.dismiss()

	def open(self, *args):
		KeyboardGuardian.Instance().acquireKeyboard(self)
		self.__render()
		self.__popup.open()

class CollisionPartLayout(SeparatorLabel, CollisionConfig):
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
					self.__selfFlagsGrid.add_widget(
						AlignedToggleButton(
							text = name, state = 'down', on_release = self.__togglePartFlag,
							id = 'togglebutton#selfflags#' + name, **defaultLabelSize
						)
					)
				else:
					self.__selfFlagsGrid.add_widget(
						AlignedToggleButton(
							text = name, state = 'normal', on_release = self.__togglePartFlag,
							id = 'togglebutton#selfflags#' + name, **defaultLabelSize
						)
					)
			else:
				self.__selfFlagsGrid.add_widget(AlignedLabel(text = '', **defaultLabelSize))

		for i in range(16):
			if (i < numberOfFlags):
				name = flagsList[i].getName()
				if (name in partCheckMask):
					self.__checkMaskGrid.add_widget(
						AlignedToggleButton(
							text = name, state = 'down', on_release = self.__togglePartFlag,
							id = 'togglebutton#checkmask#' + name, **defaultLabelSize
						)
					)
				else:
					self.__checkMaskGrid.add_widget(
						AlignedToggleButton(
							text = name, state = 'normal', on_release = self.__togglePartFlag,
							id = 'togglebutton#checkmask#' + name, **defaultLabelSize
						)
					)
			else:
				self.__checkMaskGrid.add_widget(AlignedLabel(text = '', **defaultLabelSize))

		if (part.getPoints() == None):
			self.__pointsText.text = 'Have collision points? No.'
		else:
			self.__pointsText.text = 'Have collision points? Yes.'

		self.__partSolidSwitch.active = part.getSolid()
		self.__partSolidSwitch.bind(active = self.__updateSolidFlag)

		self.__typeLine.clear_widgets()
		self.__boxCheckBox = CheckBox(group = 'part_type' + str(id(self)), id = 'checkbox#box',
			allow_no_selection = False, **defaultCheckboxSize)
		self.__sphereCheckBox = CheckBox(group = 'part_type' + str(id(self)), id = 'checkbox#sphere',
			allow_no_selection = False, **defaultCheckboxSize)
		self.__meshCheckBox = CheckBox(group = 'part_type' + str(id(self)), id = 'checkbox#mesh',
			allow_no_selection = False, **defaultCheckboxSize)

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
		self.__typeLine.add_widget(AlignedLabel(text = 'Box'))
		self.__typeLine.add_widget(self.__sphereCheckBox)
		self.__typeLine.add_widget(AlignedLabel(text ='Sphere'))
		self.__typeLine.add_widget(self.__meshCheckBox)
		self.__typeLine.add_widget(AlignedLabel(text = 'Mesh'))

	def __callFormEditPopup(self, *args):
		ModulesAccess.get('CollisionFormEditor').open(self.__part, self.__obj)

	def __init__(self):
		super(CollisionPartLayout, self).__init__()
		self.__layout = BoxLayout(orientation = 'horizontal')
		self.__part = None

		gridSize = {
			'height' : 4 * defaultFontSize,
			'size_hint' : (1.0, None),
		}

		# left side layout
		leftLayout = BoxLayout(orientation = 'vertical', size_hint = (0.5, 1.0))

		leftLayout.add_widget(AlignedLabel(text = 'Self Flags:', **defaultLabelSize))
		self.__selfFlagsGrid = GridLayout(cols = 4, row = 4, **gridSize)
		leftLayout.add_widget(self.__selfFlagsGrid)
		leftLayout.add_widget(self.getSeparator())

		solidLine = BoxLayout(orientation = 'horizontal', **self._switchLineSize)
		solidLine.add_widget(AlignedLabel(text = 'Solid:', **defaultLabelSize))
		self.__partSolidSwitch = Switch(active = False, **defaultSwitchSize)
		solidLine.add_widget(self.__partSolidSwitch)
		leftLayout.add_widget(solidLine)

		pointsLine = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		self.__pointsText = AlignedLabel(text = 'Have collision points?', **defaultLabelSize)
		self.__pointsButton = CancelableButton(text = 'Edit points', on_release = self.__callFormEditPopup,
			**defaultSmallButtonSize)
		pointsLine.add_widget(self.__pointsText)
		pointsLine.add_widget(self.__pointsButton)
		leftLayout.add_widget(pointsLine)

		# right side layout
		rightLayout = BoxLayout(orientation = 'vertical', size_hint = (0.5, 1.0))

		rightLayout.add_widget(AlignedLabel(text = 'Check Mask:', **defaultLabelSize))
		self.__checkMaskGrid = GridLayout(cols = 4, row = 4, **gridSize)
		rightLayout.add_widget(self.__checkMaskGrid)
		rightLayout.add_widget(self.getSeparator())
		rightLayout.add_widget(AlignedLabel(text = 'Type', **defaultLineSize))
		self.__typeLine = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		rightLayout.add_widget(self.__typeLine)

		self.__layout.add_widget(leftLayout)
		self.__layout.add_widget(rightLayout)

	def getLayout(self):
		return self.__layout

	def updateLayout(self, part, obj):
		assert (isinstance(part, CollisionPartInformation))
		self.__render(part, obj)

	def getPart(self):
		return self.__part

class CollisionEditorPopup(KeyboardAccess, SeparatorLabel, CollisionConfig):
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
				self.__lowerBox.add_widget(self.getSeparator())
			else:
				self.__lowerBox.add_widget(self.__applyToAllButton)
				self.__lowerBox.add_widget(self.getSeparator())

			self.__lowerBox.add_widget(self.__previousObjectButton)
			self.__lowerBox.add_widget(self.__nextObjectButton)
		else:
			self.__lowerBox.add_widget(self.getSeparator())

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

	# Body properties layout:
	def __startBodyPropertiesLayout(self):
		self.__bodyInfoBox = BoxLayout(orientation = 'vertical', **collisionBodyInfoSize)

		dynamicInfo = BoxLayout(orientation = 'horizontal', **self._switchLineSize)
		dynamicInfo.add_widget(AlignedLabel(text = 'Dynamic', **defaultLabelSize))
		self.__dynamicSwitch = Switch(active = False, **defaultSwitchSize)
		self.__dynamicSwitch.bind(active = self.__updateDynamicFlag)
		dynamicInfo.add_widget(self.__dynamicSwitch)

		fixedRotationInfo = BoxLayout(orientation = 'horizontal', **self._switchLineSize)
		fixedRotationInfo.add_widget(AlignedLabel(text = 'Fixed Rotation', **defaultLabelSize))
		self.__fixedRotationSwitch = Switch(active = False, **defaultSwitchSize)
		self.__fixedRotationSwitch.bind(active = self.__updateFixedRotationFlag)
		fixedRotationInfo.add_widget(self.__fixedRotationSwitch)

		highSpeedInfo = BoxLayout(orientation = 'horizontal', **self._switchLineSize)
		highSpeedInfo.add_widget(AlignedLabel(text = 'High Speed', **defaultLabelSize))
		self.__highSpeedSwitch = Switch(active = False, **defaultSwitchSize)
		self.__highSpeedSwitch.bind(active = self.__updateHighSpeedFlag)
		highSpeedInfo.add_widget(self.__highSpeedSwitch)

		self.__bodyInfoBox.add_widget(dynamicInfo)
		self.__bodyInfoBox.add_widget(fixedRotationInfo)
		self.__bodyInfoBox.add_widget(highSpeedInfo)
		self.__bodyInfoBox.add_widget(self.getSeparator())

	def __updateDynamicFlag(self, instance, value):
		idToUse = self.__objectsList[self.__objectsListIndex].getIdentifier()
		self.__copiesDict[idToUse].setDynamic(value)

	def __updateFixedRotationFlag(self, instance, value):
		idToUse = self.__objectsList[self.__objectsListIndex].getIdentifier()
		self.__copiesDict[idToUse].setFixedRotation(value)

	def __updateHighSpeedFlag(self, instance, value):
		idToUse = self.__objectsList[self.__objectsListIndex].getIdentifier()
		self.__copiesDict[idToUse].setHighSpeed(value)

	# Part preview and body layout:
	def __startPreviewAndBodyLayout(self):
		self.__flagsAndPreviewBox = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 1.0))
		self.__objectsCollisionDisplay = ScrollView(effect_cls = EmptyScrollEffect, size_hint = (1.0, 1.0))
		self.__flagsAndPreviewBox.add_widget(self.__objectsCollisionDisplay)
		self.__startBodyPropertiesLayout()
		self.__flagsAndPreviewBox.add_widget(self.__bodyInfoBox)

	# TabbedPanel layout:
	def __startTabbedPartLayout(self):
		self.__partsLayoutList = []
		for i in range(8):
			self.__partsLayoutList.append(CollisionPartLayout())
		self.__partsPanel = TabbedPanel(do_default_tab = False, **collisionTabbedSize)

	# Start lower box layout
	def __startLowerBoxLayout(self):
		self.__lowerBox = BoxLayout(orientation = 'horizontal', **defaultLineSize)
		self.__okButton = CancelableButton(text = 'Done', on_release=self.__createOrEditCollisionInfo,
			**defaultSmallButtonSize)
		self.__cancelButton = CancelableButton(text = 'Cancel', on_release = self.close,
			**defaultSmallButtonSize)
		self.__addButton = CancelableButton(text = 'Add', on_release = self.__addPart,
			**defaultSmallButtonSize)
		self.__applyToAllButton = CancelableButton(text = 'Copy info to all', on_release = self.__applyChangesToAll,
			**defaultLargeButtonSize)
		self.__deleteCurrentButton = CancelableButton(text = 'Delete', on_release = self.__deleteCurrentPart,
			**defaultSmallButtonSize)
		self.__previousObjectButton = CancelableButton(text = 'Previous', on_release = self.__selectPreviousObject,
			**defaultSmallButtonSize)
		self.__nextObjectButton = CancelableButton(text = 'Next', on_release = self.__selectNextObject,
			**defaultSmallButtonSize)
		self.__editFlagsButton = CancelableButton(text = 'Edit Flags',
			on_release = ModulesAccess.get('CollisionFlagEditor').open, **defaultSmallButtonSize)

	def __init__(self):
		super(CollisionEditorPopup, self).__init__()
		ModulesAccess.add('CollisionEditor', self)

		self.__copiesDict = {}
		self.__extraPartsDict = {}
		self.__objectsList = []
		self.__objectsListIndex = 0
		self.__editingObject = None

		self.__startPreviewAndBodyLayout()
		self.__startTabbedPartLayout()
		self.__startLowerBoxLayout()

		self.__mainLayout = BoxLayout(orientation = 'vertical', size_hint = (1.0, 1.0))
		self.__mainLayout.add_widget(self.__flagsAndPreviewBox)
		self.__mainLayout.add_widget(AlignedLabel(**defaultLineSize))
		self.__mainLayout.add_widget(self.__partsPanel)
		self.__mainLayout.add_widget(AlignedLabel(**defaultLineSize))
		self.__mainLayout.add_widget(self.__lowerBox)
		self.__collisionPopUp = Popup (title = 'Collision configs', auto_dismiss = False, content = self.__mainLayout)

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
