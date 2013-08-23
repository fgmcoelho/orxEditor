from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

class BasePopUpMethods:

	def open(self):
		self.mainPopUp.open()

	def setTitle(self, value):
		self.mainPopUp.title = value

	def setText(self, value):
		self.mainPopUpText.text = value

	def dismiss(self):
		self.mainPopUp.dismiss()


class Dialog (BasePopUpMethods):

	def __doNothing(self, notUsed = None):
		return None

	def __init__(self, okMethod = None, dialogTitle = '', dialogText = '', dialogOkButtonText = '', dialogCancelButtonText = ''):
		
		self.mainPopUp = Popup(title = dialogTitle, auto_dismiss = False, size_hint = (0.7, 0.5))
		self.mainPopUpText = Label(text = dialogText)
		popUpLayout = BoxLayout(orientation = 'vertical')
		yesNoLayout = BoxLayout(orientation = 'horizontal', size_hint = (1.0, 0.3))
		
		if (okMethod == None):
			self.__okMethod = self.__doNothing
		else:
			self.__okMethod = okMethod
		
		self.__dialogOkButton = Button(text = dialogOkButtonText, on_release = self.__okMethod)
		popUpLayout.add_widget(self.mainPopUpText)
		yesNoLayout.add_widget(self.__dialogOkButton)
		yesNoLayout.add_widget(Button(text = dialogCancelButtonText, on_release = self.mainPopUp.dismiss))
		popUpLayout.add_widget(yesNoLayout)
		self.mainPopUp.content = popUpLayout

class AlertPopUp (BasePopUpMethods):
	
	def __init__(self, alertTitle = '', alertText = '', closeButtonText = ''):
		self.mainPopUp = Popup(
			title = alertTitle, 
			auto_dismiss = False,
			size_hint = (0.5, 0.5)
		)
		mainPopUpBox = BoxLayout(orientation = 'vertical')
		self.mainPopUpText = Label(
			text = alertText, size_hint = (1.0, 0.7)
		)
		mainPopUpBox.add_widget(self.mainPopUpText)
		mainPopUpBox.add_widget(Button(text = closeButtonText, size_hint = (1.0, 0.3), on_release = self.mainPopUp.dismiss))
		self.mainPopUp.content = mainPopUpBox

