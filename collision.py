from singleton import Singleton

from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.switch import Switch
from editorutils import AlertPopUp

from editorobjects import ObjectTypes


class CollisionTypes:
	box = 1
	sphere = 2

class CollisionFlag:
	def __init__(self, name):
		self.__name = name
		self.__count = 0
		self.__isDeleted = False

	def getName(self):
		return self.__name
	
	def increaseCounter(self):
		self.__count += 1

	def getCounter (self):
		return self.__count

	def setDeleted (self):
		self.__isDeleted = True

	def getDeleted (self):
		return self.__isDeleted

@Singleton
class CollisionGuardian:
	def __init__(self):
		self.__flagsDict = {}

	def addNewFlag(self, name):
		if (name not in self.__flagsDict):
			flag = CollisionFlag(name)
			self.__flagsDict[name] = flag

	def assignFlag (self, name):
		assert (name in self.__flagsDict)
		self.__flagsDict[name].increaseCounter()

class CollisionInformation:

	def __init__(self, selfFlag, checkMask, isSolid, isDynamic, allowSleep, collisionType):
		self.__selfFlag = selfFlag
		self.__checkMask = checkMask
		self.__isSolid = isSolid
		self.__isDynamic = isDynamic
		self.__allowSleep = allowSleep
		self.__collisionType = collisionType

	def getSelfFlag(self):
		return self.__selfFlag

	def getCheckMask(self):
		return self.__checkMask

	def getIsSolid(self):
		return self.__isSolid

	def getIsDynamic(self):
		return self.__isDynamic

	def getAllowSleep(self):
		return self.__allowSleep

	def getCollisionType(self):
		return self.__collisionType
	
	def setSelfFlag(self, value):
		self.__selfFlag = value

	def setCheckMask(self, value):
		self.__checkMask = value

	def setIsSolid(self, value):
		self.__isSolid = value

	def setIsDynamic(self, value):
		self.__isDynamic = value

	def setAllowSleep(self, value):
		self.__allowSleep = value

	def setCollisionType(self, value):
		self.__collisionType = value

	def copy(self):
		return CollisionInformation(self.getSelfFlag(), self.getCheckMask(), self.getIsSolid(), self.getIsDynamic(),
			self.getAllowSleep(), self.getCollisionType())

	def isEquals(self, other):
		return (self.getSelfFlag() == other.getSelfFlag() & 
			self.getCheckMask() == other.getCheckMask() &
			self.getIsSolid() == other.getIsSolid() &
			self.getIsDynamic() == other.getIsDynamic() &
			self.getAllowSleep() == other.getAllowSleep() &
			self.getCollisionType() == other.getCollisionType())

def validateMask(inputReference):
	value = inputReference.text
	valid = True
	
	if (value == ''):
		valid = False

	else:
		value = value.strip()
		base = 10
		if (value[0:2] == '0x' or value[0:2] == '0X'):
			base = 16
		
		elif (value[0:2] == '0b' or value[0:2] == '0B'):
			base = 2

		elif (value[0] == '0'):
			base = 8

		try:
			x = int (value, base)
			valid = True
			if (x < 0 or x > 0xFFFF):
				valid = False
		except:
			valid = False

	if (valid == False):
		inputReference.background_color = [1, 0, 0, 1]
	else:
		inputReference.background_color = [1, 1, 1, 1]



@Singleton
class CollisionInformationPopup:

	def __setDefaultValues(self):
		self.__selfFlagInput.text = '0xFFFF'
		self.__checkMaskInput.text = '0xFFFF'
		self.__solidSwitch.active = False
		self.__dynamicSwitch.active = False
		self.__allowSleepSwitch.active = False
		self.__typeBoxSelect.active = True
		self.__typeSphereSelect.active = False

	def __setObjectValues(self, obj):
		self.__selfFlagInput.text = obj.getSelfFlag()
		self.__checkMaskInput.text = obj.getCheckMask()
		self.__solidSwitch.active = obj.getIsSolid()
		self.__dynamicSwitch.active = obj.getIsDynamic()
		self.__allowSleepSwitch.active = obj.getAllowSleep()
		if (obj.getCollisionType() == CollisionTypes.box):
			self.__typeBoxSelect.active = True
			self.__typeSphereSelect.active = False
		else:
			self.__typeBoxSelect.active = False
			self.__typeSphereSelect.active = True

	def __reloadValues(self):
		if (self.__editingObject == None):
			self.__setDefaultValues()

		else:
			collisionInfo = self.__editingObject.getCollisionInfo()
			if (collisionInfo == None):
				self.__setDefaultValues()
			else:
				self.__setObjectValues(collisionInfo)

	def __init__(self):
		self.__collisionPopUp = Popup (title = 'Collision configs', auto_dismiss = False)
		self.__collisionGrid = GridLayout(cols = 2, rows = 7, size_hint = (1.0, 1.0))
		
		self.__collisionGrid.add_widget(Label(text = 'SelfFlag:'))
		self.__selfFlagInput = TextInput(text='0xFFFF', multiline = False)
		self.__selfFlagInput.bind(on_text_validate=validateMask)
		self.__collisionGrid.add_widget(self.__selfFlagInput)

		self.__collisionGrid.add_widget(Label(text = 'Check Mask:'))
		self.__checkMaskInput = TextInput(text='0xFFFF', multiline = False, on_text_validate=validateMask)
		self.__collisionGrid.add_widget(self.__checkMaskInput)
		
		self.__collisionGrid.add_widget(Label(text = 'Solid?'))
		self.__solidSwitch = Switch(active = False)
		self.__collisionGrid.add_widget(self.__solidSwitch)

		self.__collisionGrid.add_widget(Label(text = 'Dynamic?'))
		self.__dynamicSwitch = Switch(active = False)
		self.__collisionGrid.add_widget(self.__dynamicSwitch)

		self.__collisionGrid.add_widget(Label(text = 'Allow sleep?'))
		self.__allowSleepSwitch = Switch(active = False)
		self.__collisionGrid.add_widget(self.__allowSleepSwitch)
		
		self.__collisionGrid.add_widget(Label(text = 'Type:'))
		self.__typesGrid = GridLayout (cols = 2, rows = 2)
		self.__typeBoxSelect = CheckBox(active = True, group = 'collision_type')
		self.__typesGrid.add_widget(self.__typeBoxSelect)
		self.__typesGrid.add_widget(Label(text = 'Box'))
		self.__typeSphereSelect = CheckBox(active = False, group = 'collision_type')
		self.__typesGrid.add_widget(self.__typeSphereSelect)
		self.__typesGrid.add_widget(Label(text = 'Sphere'))
		self.__collisionGrid.add_widget(self.__typesGrid)

		self.__okButton = Button(text = 'Done')
		self.__okButton.bind(on_release=self.__createOrEditCollisionInfo)
		self.__cancelButton = Button (text = 'Cancel')
		self.__cancelButton.bind(on_release=self.__collisionPopUp.dismiss)
		self.__collisionGrid.add_widget(self.__okButton)
		self.__collisionGrid.add_widget(self.__cancelButton)
		
		self.__collisionPopUp.content = self.__collisionGrid
		self.__editingObject = None
	
	
		self.__errorPopUp = AlertPopUp('Error', 'No Object selected!\nYou need to select one object from the scene', 'Ok')
		self.__postCreateOrEditMethod = None
		
	def __createOrEditCollisionInfo(self, useless):
		if (self.__editingObject != None):
			if (self.__selfFlagInput.background_color==[1, 0, 0, 1] or self.__checkMaskInput.background_color==[1, 0, 0, 1]):
				self.__errorPopUp.setText('Invalid flag input.')
				self.__errorPopUp.open()
				return
			
			if (self.__typeBoxSelect.active == True):
				collisionType = CollisionTypes.box
			else:
				collisionType = CollisionTypes.sphere

			if (self.__editingObject.getCollisionInfo() == None):

				newCollisionInfo = CollisionInformation(
					self.__selfFlagInput.text, 
					self.__checkMaskInput.text, 
					self.__solidSwitch.active, 
					self.__dynamicSwitch.active, 
					self.__allowSleepSwitch.active, 
					collisionType
				)
				self.__editingObject.setCollisionInfo(newCollisionInfo)
			
			else:
				collisionObject = self.__editingObject.getCollisionInfo()
				collisionObject.setSelfFlag(self.__selfFlagInput.text)
				collisionObject.setCheckMask(self.__checkMaskInput.text)
				collisionObject.setIsSolid(self.__solidSwitch.active)
				collisionObject.setIsDynamic(self.__dynamicSwitch.active)
				collisionObject.setAllowSleep(self.__allowSleepSwitch.active)
				collisionObject.setCollisionType(collisionType)

		self.__editingObject = None
		self.getPopUp().dismiss()

		if (self.__postCreateOrEditMethod != None):
			self.__postCreateOrEditMethod()
				
	def getPopUp(self):
		return self.__collisionPopUp

	def showPopUp(self, obj):
		
		if (obj == None or (obj != None and obj.getType() != ObjectTypes.renderedObject)):
			self.__errorPopUp.setText('No Object selected!\nYou need to select one object from the scene')
			self.__errorPopUp.open()
		
		else:
			self.__editingObject = obj
			self.__reloadValues()
			self.__collisionPopUp.open()
			

