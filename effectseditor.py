#!/usr/bin/python
from kivy import require
require('1.7.2')

from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.config import Config
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton

from os import execv, fork, chdir, rename
from shutil import copy

class EffectCurve:

	possibleNames = ("linear", "smooth", "smoother", "triangle", "square", "sine")
	def __init__(self):
		self.name = ""

	def setName(self, newName):
		assert (newName in self.possibleNames)
		self.name = newName
	
	def getPossibleNames(self):
		return self.possibleNames

class EffectType:
	
	possibleNames = ("alpha", "color", "scale", "rotation", "position", "speed")
	def __init__(self):
		self.name = ""

	def setName(self, newName):
		assert (newName in self.possibleNames)
		self.name = newName

	def getPossibleNames(self):
		return self.possibleNames

class Effect:
	
	def reset(self):
		self.effectType = EffectType()
		self.curve = EffectCurve()
		self.startTime = "0.0"
		self.endTime = "0.0"
		self.startValue = "0.0"
		self.endValue = "0.0"
		self.phase = "0.0"
		self.period = "0.0"
		self.absolute = False
		self.accelereation = "1.0"
		self.amplification = "1.0"
		self.power = "1.0"
		self.useRotation = False
		self.useScale = False
		self.activeEffect = False

	def __init__(self):
		self.reset()

	def setTypeByInstance(self, instance):
		self.effectType.setName(instance.text)

	def setCurveByInstance(self, instance):
		self.curve.setName(instance.text)

	def setStartTimeByInstance(self, instance, value):
		self.startTime = value

	def setEndTimeByInstance(self, instance, value):
		self.endTime = value

	def setStartValueByInstance(self, instance, value):
		self.startValue = value

	def setEndValueByInstance(self, instance, value):
		self.endValue = value

	def setPhaseByInstance(self, instance, value):
		self.phase = value

	def setPeriodByInstance(self, instance, value):
		self.period = value

	def setAccelerationByInstance(self, instance, value):
		self.accelereation = value

	def setAmplificationByInstance(self, instance, value):
		self.amplification = value

	def setPowerByInstance(self, instance, value):
		self.power = value

	def setAbsoluteByInstance(self, instance, value):
		self.absolute = value

	def setUseRotationByInstance(self, instance, value):
		self.useRotation = value
	
	def setUseScaleByInstance(self, instance, value):
		self.useScale = value
	
	def setActiveEffectByInstance(self, instance, value):
		self.activeEffect = value

	def __boolToStr(self, value):
		if (value == True):
			return "true"
		else:
			return "false"

	def convertToString(self):
		
		s = "Type = %s\n" \
			"Curve = %s\n" \
			"StartTime = %s\n" \
			"EndTime = %s\n" \
			"StartValue = %s\n" \
			"EndValue = %s\n" \
			"Phase = %s\n" \
			"Period = %s\n" \
			"Absolute = %s\n" \
			"Accelereation = %s\n" \
			"Amplification = %s\n" \
			"Pow           = %s\n" \
			"UseRotation   = %s\n" \
			"UseScale      = %s\n" % (self.effectType.name,
			self.curve.name,
			self.startTime,
			self.endTime,
			self.startValue,
			self.endValue,
			self.phase,
			self.period,
			self.__boolToStr(self.absolute), 
			self.accelereation,
			self.amplification,
			self.power,
			self.__boolToStr(self.useRotation),
			self.__boolToStr(self.useScale))

		return s

class FileUpdater:
	def __init__(self):
		self.path = 'bin/effect.ini'

	def updateFile(self, effectsList):
		base = """
[Character_Graphic]
Texture = light.png
TextureSize = (64, 64, 1.0)
Pivot = (32, 32, 1.0)

[Character_Graphic_Start@Character_Graphic]
TextureCorner = (0, 128, 1.0)

[MainObject]
Graphic = Character_Graphic_Start
Position = (0.0, 0.0, 1.0)
Scale = 1.0

[FireShield_Graphic]
Texture = fireshield.png

[EffectObject]
Graphic = FireShield_Graphic
Position = (-40, 0, 1)
"""
	
		anyActive = False
		effectStrings = []
		effectsNames = []
		i = 1
		for effect in effectsList:
			if (effect.activeEffect == True):
				anyActive = True
				effectStrings.append(effect.convertToString())
				effectsNames.append("EffectSlot"+str(i))

			i += 1

		if (anyActive == False):
			return
		
		base += 'FXList = SpecialEffect\n\n'

		base += '[SpecialEffect]\n'
		base += "SlotList = "

		for name in effectsNames:
			base += name
			if (name != effectsNames[-1]):
				base += " # "
		
		base += '\n'
		base += 'Loop = true\n'
		base += '\n'

		i = 0
		for name in effectsNames:
			base += '[' + name + ']\n'
			base += effectStrings[i] + '\n'
			i += 1

		f = open('tmpfile382749827492', 'w')
		f.write(base)
		f.close()

		rename('tmpfile382749827492', self.path)

class LeftMenu:

	def __clearEffets(self):
		pass

	def __test(self, instance):
		print instance

	def __addValueRow(self, labelText, value, method):
		line = BoxLayout(orientation = 'horizontal')
		line.add_widget(Label(text = labelText))
		ti = TextInput(text = value, multiline = False)
		ti.bind(text=method)
		line.add_widget(ti)
		line.add_widget(Label(text = ''))

		self.rightScreenRef.add_widget(line)
	
	def __addBoolRow(self, labelText, value, method):
		line = BoxLayout(orientation = 'horizontal')
		line.add_widget(Label(text = labelText))
		s = Switch(active = value)
		s.bind(active = method)
		line.add_widget(s)
		line.add_widget(Label(text = ''))

		self.rightScreenRef.add_widget(line)

	def __callUpdate(self, instance):
		self.fileUpdater.updateFile(self.effectsList)

	def renderEffectScreen(self, instance):
		index = int(instance.text[0]) - 1
		effect = self.effectsList[index]

		self.rightScreenRef.clear_widgets()
		
		typeLine = BoxLayout(orientation = 'horizontal')
		typeLine.add_widget(Label(text = 'Type:'))
		for name in effect.effectType.getPossibleNames():
			stateToUse = 'normal'
			if (effect.effectType.name == name):
				stateToUse = 'down'
			
			typeLine.add_widget(ToggleButton(text = name, group = 'type', state = stateToUse, 
				on_press = effect.setTypeByInstance))
			

		self.rightScreenRef.add_widget(typeLine)

		curveLine = BoxLayout(orientation = 'horizontal')
		curveLine.add_widget(Label(text = 'Curve:'))
		for name in effect.curve.getPossibleNames():
			stateToUse = 'normal'
			if (effect.curve.name == name):
				stateToUse = 'down'
			
			curveLine.add_widget(ToggleButton(text = name, group = 'curve', state = stateToUse,
				on_press = effect.setCurveByInstance))
		
		self.rightScreenRef.add_widget(curveLine)

		self.__addValueRow('Start Time:', effect.startTime, effect.setStartTimeByInstance)
		self.__addValueRow('End Time:', effect.endTime, effect.setEndTimeByInstance)
		self.__addValueRow('Start Value:', effect.startValue, effect.setStartValueByInstance)
		self.__addValueRow('End Value:', effect.endValue, effect.setEndValueByInstance)
		self.__addValueRow('Phase:', effect.phase, effect.setPhaseByInstance)
		self.__addValueRow('Period:', effect.period, effect.setPeriodByInstance)
		self.__addValueRow('Accelereation:', effect.accelereation, effect.setAccelerationByInstance)
		self.__addValueRow('Amplification:', effect.amplification, effect.setAmplificationByInstance)
		self.__addValueRow('Power:', effect.power, effect.setPowerByInstance)
		self.__addBoolRow('Absolute:', effect.absolute, effect.setAbsoluteByInstance)
		self.__addBoolRow('Use Rotation:', effect.useRotation, effect.setUseRotationByInstance)
		self.__addBoolRow('Use Scale:', effect.useScale, effect.setUseScaleByInstance)
		self.__addBoolRow('Is active:', effect.activeEffect, effect.setActiveEffectByInstance)

		finalLine = BoxLayout(orientation = 'horizontal', size_hint = (1.0, None))
		finalLine.add_widget(Label(text = '', size_hint = (0.7, None)))
		finalLine.add_widget(Button(text = 'Validate now.', size_hint = (0.3, None)))
		self.rightScreenRef.add_widget(finalLine)


	def __init__(self, leftMenuRef, rightScreenRef):

		self.leftMenuRef = leftMenuRef
		self.rightScreenRef = rightScreenRef
		self.fileUpdater = FileUpdater()
		self.effectsList = []
		for i in range(8):
			self.effectsList.append(Effect())

		leftMenuRef.add_widget(Button(text = 'MainObject'))
		leftMenuRef.add_widget(Button(text = 'EffectObjet'))
		leftMenuRef.add_widget(Button(text = '1st Effect', on_release = self.renderEffectScreen))
		leftMenuRef.add_widget(Button(text = '2nd Effect', on_release = self.renderEffectScreen))
		leftMenuRef.add_widget(Button(text = '3rd Effect', on_release = self.renderEffectScreen))
		leftMenuRef.add_widget(Button(text = '4th Effect', on_release = self.renderEffectScreen))
		leftMenuRef.add_widget(Button(text = '5th Effect', on_release = self.renderEffectScreen))
		leftMenuRef.add_widget(Button(text = '6th Effect', on_release = self.renderEffectScreen))
		leftMenuRef.add_widget(Button(text = '7th Effect', on_release = self.renderEffectScreen))
		leftMenuRef.add_widget(Button(text = '8th Effect', on_release = self.renderEffectScreen))
		leftMenuRef.add_widget(Label(text = ''))
		leftMenuRef.add_widget(Button(text = 'Clear Effects'))
		leftMenuRef.add_widget(Button(text = 'Clear All'))
		leftMenuRef.add_widget(Button(text = 'DONE', on_release = self.__callUpdate))

class EffectsEditor(App):
	
	def build_config(self, c):
		Config.set('graphics', 'width', 800)
		Config.set('graphics', 'height', 600)
		Config.set('graphics', 'fullscreen', 0)
		Config.set('input', 'mouse', 'mouse,disable_multitouch')
		Config.write()

	def build(self):

		self.root = BoxLayout(orientation='horizontal', padding = 0, spacing = 0, size_hint = (1.0, 1.0))

		self.leftMenuBase = BoxLayout(
			orientation='vertical', 
			padding = 0, 
			spacing = 0,
			size_hint = (0.20, 1.0)
		)

		self.rightScreen = BoxLayout(
			orientation = 'vertical',
			padding = 0, 
			spacing = 0,
			size_hint = (0.8, 1.0),
		)

		self.leftMenu = LeftMenu(self.leftMenuBase, self.rightScreen)

		self.root.add_widget(self.leftMenuBase)
		self.root.add_widget(self.rightScreen)



if __name__ == '__main__':
	if (fork() != 0):
		chdir('bin')
		copy('effect.ini.bkp','effect.ini') 
		execv('OrxEffectsRunner', ["OrxEffectsRunner"])
	else:
		EffectsEditor().run()
