from kivy import require
require('1.8.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.codeinput import CodeInput
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window

# lexer related
from pygments.lexers import IniLexer, GLShaderLexer
from pygments.lexer import using, bygroups, RegexLexer
from pygments.token import Number, Text, Name
import re

from os.path import join
from ConfigParser import SafeConfigParser

class OrxConfigLexer(RegexLexer):

	name = 'OrxConfigLexer'
	aliases = ['ini']
	filenames = ['*.ini']

	flags = re.DOTALL

	tokens = {
		'root': [
			(r'^Code[\s]*=[\s]*"', Name.Tag, ('shader-content', ))
		],
		'shader-content': [
			(r'(.*)\"', bygroups(using(GLShaderLexer))),
		]
	}

class OrxValueType:
	validTypes = set([
		'Template',
		'Vector',
		'Float',
		'Int',
		'Bool',
		'String',
		'Specific',
		'Path'
	])

	def _validateTemplate(self, value):
		# TODO: Improve this
		return True

	def _validateVector(self, value):
		if (value[0] == '(' and value[-1] == ')') or (value[0] == '{' and value[-1] == '}'):
			if ((value.count('(') != value.count(')')) or (value.count('{') != value.count('}'))):
				return False
			return True

		return False

	def _validateFloat(self, value):
		try:
			float(value)
		except:
			return False
		else:
			return True

	def _validateInteger(self, value):
		if (len(value) > 2):
			base = None
			if (value.startswith('0x') == True):
				base = 16
			elif (value.startswith('0b') == True):
				base = 2
			elif (value[0] == '0'):
				base = 8
			else:
				base = 10

			if (base is not None):
				try:
					int(value, base)
				except:
					return False
				else:
					return True

	def _validateBool(self, value):
		if value == 'true' or value == 'false':
			return True
		else:
			return False

	def _validateString(self, value):
		if (value[0] == '"' and value[-1] == '"'):
			return True
		return False


	def _validateSpecific(self, value):
		if value in self.specificValues:
			return True
		return False

	def _validatePath(self, value):
		# TODO: this needs to be better implemented
		return self._validateString(value)

	def validate(self, realValue):
		if (self.single == True):
			tempValidate = realValue.split('#')
		else:
			tempValidate = [ realValue ]

		valuesToValidate = []
		for value in tempValidate:
			for item in value.split('~'):
				valuesToValidate.append(item.strip())

		validateMap = {
			'Template': self._validateTemplate,
			'Vector': self._validateVector,
			'Float': self._validateFloat,
			'Int': self._validateInteger,
			'Bool': self._validateBool,
			'String': self._validateString,
			'Specific': self._validateSpecific,
			'Path': self._validatePath
		}

		for value in valuesToValidate:
			for validType in self.validTypes:
				if validateMap[validType](value) == True:
					break
			else:
				return False

		return True


	def identifyType(self, value):
		value = value.strip()

		if ('...' in value):
			return

		if ('Int' in value or 'Float' in value or 'Vector' in value or 'String' in value):
			validate = value.lstrip('[').rstrip(']')
			if (validate in OrxValueType.validTypes):
				self.acceptedTypes.add(validate)
				return

		if ('Template' in value):
			self.acceptedTypes.add('Template')
			self.templateTypes.add(value.split('Template')[0])

		elif (value in ['true', 'false']):
			self.acceptedTypes.add('Bool')

		elif (value.startswith('path/') == True):
			self.acceptedTypes.add('Path')

		elif (value[0] == '"' and value[-1] == '"'):
			self.acceptedTypes.add('String')

		else:
			self.acceptedTypes.add('Specific')
			self.specificValues.add(value)

	def __init__(self, value, hint):
		self.single = True
		self.acceptedTypes = set()
		self.templateTypes = set()
		self.specificValues = set()
		self.hint = hint

		if ('|' in value):
			valuesToValidate = value.split('|')
		elif ('#' in value):
			self.single = False
			valuesToValidate = value.split('#')
		else:
			valuesToValidate = [value]

		for validate in valuesToValidate:
			self.identifyType(validate)

class OrxConfigType:
	def __init__(self, name):
		self.name = name
		self.validArguments = {}
		self.keys = set()
		self.exclusiveSet = None

	def addArgument(self, name, value):
		if ';' in value:
			lineParts = value.split(';')
			value = lineParts[0]
			hint = '\n'.join(lineParts[1:])
		else:
			hint = None

		valueType = OrxValueType(value, hint)
		self.validArguments[name] = valueType
		self.keys.add(name)

	def processExclusivity(self, other):
		if (self.exclusiveSet is None):
			self.exclusiveSet = self.keys.copy()

		self.exclusiveSet = self.exclusiveSet - other

class ParsedSection:
	def __init__(self, name, inherits = False):
		self.name = name
		self.inherits = inherits
		self.raw_values = {}
		self.values = {}
		self.inherited_values = {}
		self.validators = {}
		self.inherits_name = ''
		self.inherit_solved = False
		self._configType = None

	def addValues(self, key, value):
		self.values[key] = value

	def setValidator(self, configType):
		self._configType = configType
		self.callValidator()

	def callValidator(self):
		if self._configType is not None:
			for key, value in self.values.iteritems():
				if key in self._configType.validArguments:
					if self._configType.validArguments[key].validate(value):
						print key, 'is valid!'
					else:
						print key, 'is not valid!'
				else:
					print key, 'is unknown.'

class OrxConfigClassifier(object):
	def _start_expressions(self):
		self.comment_exp = re.compile(r'^[\s]*;.*$')
		self.include_exp = re.compile(r'^[\s]*(@.+@)[\s]*$')
		self.section_exp = re.compile(r'^[\s]*(\[.+\])[\s]*$')
		self.value_exp = re.compile(r'^[\s]*(.+?)[\s]*=[\s]*(.+)[\s]*')

	def __init__(self):
		super(OrxConfigClassifier, self).__init__()
		self.types = {}
		settingsFiles = ['CreationTemplate.ini', 'SettingsTemplate.ini']
		for name in settingsFiles:
			full_name = join('templates', name)
			parser = SafeConfigParser()
			parser.optionxform = str
			parser.read(full_name)

			for section in parser.sections():
				configType = OrxConfigType(section)
				for option in parser.options(section):
					configType.addArgument(option, parser.get(section, option))

				self.types[section] = configType

		for x in self.types.itervalues():
			for y in self.types.itervalues():
				if x is not y:
					x.processExclusivity(y.keys)

		self.files_parsed = []
		self._start_expressions()

	def parse_content(self, content):
		currentSection = None
		currentKey = None
		parsedSections = []
		inString = False
		valueStack = []
		for line in content.split('\n'):
			if (inString == True):
				valueStack.append(line)
				validLine = line.rstrip()
				if len(validLine) == 0:
					continue

				if validLine.rstrip()[-1] == '"' and line.replace('\\"', '').count('"') == 1:
					currentSection.addValues(currentKey, '\n'.join(valueStack))
					inString = False
					currentKey = None
					valueStack = []
					continue

			if self.comment_exp.match(line) is not None:
				continue

			result = self.value_exp.match(line)
			if result is not None:
				key = result.group(1).strip()
				value = result.group(2).strip()
				if value[0] == '"' and value[-1] != '"':
					inString = True
					valueStack.append(value)
					currentKey = key
				else:
					currentSection.addValues(key, value)
				continue

			result = self.section_exp.match(line)
			if result is not None:
				currentSection = ParsedSection(result.group(1))
				parsedSections.append(currentSection)
				continue

			result = self.include_exp.match(line)
			if result is not None:
				continue

		if inString == True:
			print 'Invalid file!'
			return

		for section in parsedSections:
			for parsedType in self.types.itervalues():
				found = False
				for key in section.values.iterkeys():
					if key in parsedType.exclusiveSet:
						print 'Found type as', parsedType.name
						section.setValidator(parsedType)
						found = True
						break
				if (found == True):
					break


class OrxCodeInput(CodeInput):
	def insert_text(self, s, from_undo=False):
		return super(self.__class__, self).insert_text(s, from_undo=from_undo)

	def __init__(self, **kwargs):
		self.complete = False
		kwargs['lexer'] = IniLexer()
		super(OrxCodeInput, self).__init__(**kwargs)
		self.input_type = 'text'
		self.hint_text_color = [1.0, 0, 0, 1.0]
		self.complete = True

class OrxCodeReader(App):
	def build(self):
		self.layout = BoxLayout(orientation = 'horizontal')
		f = open('/home/fcoelho/sandbox/ASJ_proj/bin/Debug/ASJ_proj.ini')
		content = f.read()
		f.close()
		codeinput = OrxCodeInput(text=content)
		self.layout.add_widget(codeinput)
		self.classifier = OrxConfigClassifier()
		self.classifier.parse_content(content)

		return self.layout

if __name__ == '__main__':
	ocr = OrxCodeReader()
	try:
		Window.maximize()
	except:
		# maximize may not be supported
		pass

	ocr.run()

