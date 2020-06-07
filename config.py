from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, WipeTransition

import DBConnection, classes
# from flashcards_test.main import *

Builder.load_file("main.kv")
Builder.load_file("learningWindows.kv")
sm = ScreenManager()
sm.transition = WipeTransition(clearcolor=(1, 1, 1, 1))

mail = ""
flashcard_set = classes.Set("1", "a")
current_sets = {}

db_x = DBConnection.DBConnection()
