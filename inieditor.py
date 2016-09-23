from kivy import require
require('1.8.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.codeinput import CodeInput
from kivy.uix.button import Button
from pygments.lexers import IniLexer

from os.path import join
from ConfigParser import ConfigParser

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

    def identifyType(self, value):
        value = value.strip()

        if ('...' in value):
            return

        if ('Int' in value or 'Float' in value or 'Vector' in value or
                'String' in value):
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
            hint = lineParts[1]
        else:
            hint = None

        valueType = OrxValueType(value, hint)
        self.validArguments[name] = valueType
        self.keys.add(name)

    def processExclusivity(self, other):
        if (self.exclusiveSet is None):
            self.exclusiveSet = self.keys.copy()

        self.exclusiveSet = self.exclusiveSet - other

class OrxConfigClassifier(object):
    def __init__(self):
        super(OrxConfigClassifier, self).__init__()
        self.types = {}
        settingsFiles = ['CreationTemplate.ini', 'SettingsTemplate.ini']
        for name in settingsFiles:
            full_name = join('templates', name)
            parser = ConfigParser()
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

            print x.exclusiveSet



class OrxCodeInput(CodeInput):
    def insert_text(self, s, from_undo=False):
        return super(self.__class__, self).insert_text(s, from_undo=from_undo)

    def __init__(self, **kwargs):
        kwargs['lexer'] = IniLexer()
        super(OrxCodeInput, self).__init__(**kwargs)
        self.input_type = 'text'
        self.hint_text_color = [1.0, 0, 0, 1.0]

class OrxCodeReader(App):
    def build(self):
        self.layout = BoxLayout(orientation = 'horizontal')
        f = open('/home/fcoelho/sandbox/ASJ_proj/bin/Debug/ASJ_proj.ini')
        content = f.read()
        f.close()
        codeinput = OrxCodeInput(text=content)
        self.layout.add_widget(codeinput)
        self.classifier = OrxConfigClassifier()

        return self.layout

if __name__ == '__main__':
	ocr = OrxCodeReader()
	try:
		Window.maximize()
	except:
		# maximize may not be supported
		pass

	ocr.run()

