import random

import editdistance
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.uix.togglebutton import ToggleButton

# from flashcards_test.config import *
from flashcards_test.config import sm
from flashcards_test import config


class LearningWindow(Screen):
    def __init__(self, **kwargs):
        super(LearningWindow, self).__init__(**kwargs)

    def browse_sets(self):
        self.reset()
        sm.current = "searchSet"

    def learningMethod(self):
        sm.current = "learningMethod"
        self.reset()

    def allSets(self):
        global current_sets
        current_sets.clear()
        current_sets = db_x.all_sets()
        self.reset()
        sm.current = "availableSets"


class ReviewWindow(LearningWindow):
    def __init__(self, **kwargs):
        super(ReviewWindow, self).__init__(**kwargs)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.card_button_texts = dict()

    def on_enter(self, *args):
        for card in config.flashcard_set.Flashcards:
            texts = (card.Question, card.Answer)
            button_term = ToggleButton(text=texts[0], halign='center', valign='middle')
            button_term.size_hint = (0.65, 0.35)
            button_term.bind(on_press=self.switched)
            self.card_button_texts[button_term] = texts
            self.ids.grid.add_widget(button_term)

    def switched(self, instance):
        texts = self.card_button_texts[instance]
        if instance.text == texts[0]:
            instance.text = texts[1]
        else:
            instance.text = texts[0]

    def reset(self):
        for button in self.card_button_texts.keys():
            self.ids.grid.remove_widget(button)


class TestWindow(LearningWindow):
    def __init__(self, **kwargs):
        super(TestWindow, self).__init__(**kwargs)
        self.question_ids = None
        self.current_question = None

    def on_enter(self, *args):
        self.question_ids = set(range(len(config.flashcard_set.Flashcards)))
        self.next_question()

    def validate(self):
        user_answer = self.ids.answer.text
        correct_answer = config.flashcard_set.Flashcards[self.current_question].Answer
        editdist = editdistance.eval(user_answer, correct_answer)
        if editdist == 0:
            self.send_message('Correct!')
            self.question_ids.remove(self.current_question)
            Clock.schedule_once(lambda dt: self.next_question(), 0.8)
        elif editdist == 1:
            self.ids.result.text = 'You had a typo, correct answer: \'{}\''.format(correct_answer)
            self.question_ids.remove(self.current_question)
            Clock.schedule_once(lambda dt: self.next_question(), 2)
        else:
            self.ids.result.text = 'Wrong! Correct answer: \'{}\''.format(correct_answer)
            Clock.schedule_once(lambda dt: self.next_question(), 2.5)

    def send_message(self, message):
        self.ids.result.text = message

    def next_question(self):
        self.reset()
        if len(self.question_ids) != 0:
            self.current_question = random.choice(tuple(self.question_ids))
            self.ids.question.text = config.flashcard_set.Flashcards[self.current_question].Question
        else:
            self.reset()
            self.ids.result.text = 'Congratulations, you finished this set!'

    def reset(self, *args):
        self.ids.question.text = ""
        self.ids.answer.text = ""
        self.ids.result.text = ""


class QuizWindow(LearningWindow):
    def __init__(self, **kwargs):
        super(QuizWindow, self).__init__(**kwargs)
        self.question_ids = None
        self.current_question = None
        self.buttons = [self.ids.but1, self.ids.but2, self.ids.but3, self.ids.but4]
        for button in self.buttons:
            button.background_normal = ''

    def on_enter(self, *args):
        self.question_ids = set(range(len(config.flashcard_set.Flashcards)))
        self.next_question()

    def validate(self, instance):
        user_answer = instance.text
        correct_answer = config.flashcard_set.Flashcards[self.current_question].Answer
        if user_answer == correct_answer:
            instance.background_color = (0.133, 0.545, 0.133, 1.0)
            self.question_ids.remove(self.current_question)
            Clock.schedule_once(lambda dt: self.next_question(), 0.8)
        else:
            instance.background_color = (0.698, 0.133, 0.133, 1.0)
            for button in self.buttons:
                if button.text == correct_answer:
                    button.background_color = (0.133, 0.545, 0.133, 1.0)
                    break
            Clock.schedule_once(lambda dt: self.next_question(), 2.5)

    def next_question(self):
        self.reset()
        if len(self.question_ids) != 0:
            self.current_question = random.choice(tuple(self.question_ids))
            self.ids.question.text = config.flashcard_set.Flashcards[self.current_question].Question
            current_flashcard = config.flashcard_set.Flashcards[self.current_question]
            answers = [f.Answer for f in config.flashcard_set.Flashcards if f != current_flashcard]
            answers = random.sample(answers, 3)
            answers.append(current_flashcard.Answer)
            random.shuffle(answers)
            for button, answer in zip(self.buttons, answers):
                button.text = answer
        else:
            self.ids.question.text = 'Congratulations, you finished this set!'
            self.reset()

    def reset(self, *args):
        for button in self.buttons:
            button.text = ""
            button.background_color = (0.4, 0.4, 0.4, 1.0)