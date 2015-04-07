
class ModulesAccess:
	modulesDict = {}
	@staticmethod
	def add(moduleName, moduleObj):
		assert moduleName not in ModulesAccess.modulesDict, 'Module already inserted.'
		ModulesAccess.modulesDict[moduleName] = moduleObj

	@staticmethod
	def get(moduleName):
		assert moduleName in ModulesAccess.modulesDict, 'Module does not exist.'
		return ModulesAccess[moduleName]
