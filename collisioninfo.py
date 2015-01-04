from singleton import Singleton

from operator import itemgetter

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
	def __startFlags(self):
		self.__id = 0
		self.__flagsDict = {}
	
	def __init__(self):
		self.__startFlags()

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

	def reset(self):
		self.__startFlags()

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

	def __assertPointsValue(self, form, points):
		assert (points is None) or (form == "box" and len(points) == 2) or (form == "sphere" and \
			len(points) == 2) or (form == "mesh" and len(points) >= 3),\
			"Number of points does not match the part form type."

	def __removeFlagFromList(self, listToUse, flag):
		flagObjectToRemove = None
		for flagObject in listToUse:
			if (flagObject == flag):
				flagObjectToRemove = flagObject
				break

		if (flagObjectToRemove is not None):
			listToUse.remove(flagObjectToRemove)

	def __compareFlagLists(self, firstList, secondList):
		if (len(firstList) != len(secondList)):
			return False
		else:
			for firstFlag in firstList:
				hasFlag == False
				for secondFlag in secondList:
					if (firstFlag.getName() == secondFlag.getName()):
						hasFlag = True
						break
				if (hasFlag == False):
					return False
		
		return True

	def __compareFormTypeAndPoints(self, part):
		if (self.__formType != part.getFormType()):
			return False

		otherPoints = part.getPoints() 
		if (self.__points is None and otherPoints is None):
			return True

		if (len(self.__points) != len(otherPoints)):
			return False

		for firstPartPoint in self.__points:
			hasPoint = False
			for secondPartPoint in otherPoints:
				if (firstPartPoint == secondPartPoint):
					hasPoint = True
					break

			if (hasPoint == False):
				return False

		return True

	def __init__(self, checkMask = [], selfFlags = [], solid = False, formType = "box", points = None):
		self.__assertPointsValue(formType, points)
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
		self.__points = None

	def setSolid(self, newValue):
		self.__solid = newValue

	def setPoints(self, newPoints):
		self.__assertPointsValue(self.__formType, newPoints)
		self.__points = newPoints

	def addFlagToSelfFlags(self, flag):
		assert (len(self.__selfFlags) <= 16)
		self.__selfFlags.append(flag)

	def removeFlagFromCheckMask(self, flag):
		self.__removeFlagFromList(self.__checkMask, flag)

	def removeFlagFromSelfFlags(self, flag):
		self.__removeFlagFromList(self.__selfFlags, flag)

	def getSolid(self):
		return self.__solid

	def getFormType(self):
		return self.__formType

	def getPoints(self):
		return self.__points

	def isEqual(self, part):
		assert isinstance(part, CollisionPartInformation), "Argument must be a CollisionPartInformation."
		if (self.__compareFlagLists(self.__checkMask, part.getCheckMask()) == True and
				self.__compareFlagLists(self.__selfFlags, part.getSelfFlags()) == True and
				self.__compareFormTypeAndPoints(part) == True and self.__solid == part.getSolid()):
			return True
		else:
			return False

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

	@staticmethod
	def isOnStartState(info):
		assert(isinstance(info, CollisionInformation))
		if (info.getDynamic() == True or info.getHighSpeed() == True or info.getFixedRotation() == True
					or info.getPartsList() != []):
			return False
		else:
			return True

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
