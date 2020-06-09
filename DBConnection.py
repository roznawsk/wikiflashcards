from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import classes


class AuthenticationException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class AddValueException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class DatabaseException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class DBConnection:
    def __init__(self):
        client = MongoClient(
            "mongodb+srv://Developer:TrustMe99@flipcardsdb-k8zdx.mongodb.net/test?retryWrites=true&w=majority")
        self.db = client["FlipcardsDB"]

    def list_users(self):
        users = self.db["users"]
        for user in users.find():
            print(user)

    def get_user(self, email):
        users = self.db["users"]
        amount = users.count_documents({"email": email})
        if amount == 0:
            return 0
        else:
            return users.find({"email": email})

    def get_id(self, email):
        users = self.db["users"]
        user = users.find_one({"email": email})
        id = user.get("_id")
        return id

    def get_set(self, set_id):
        result_cards = []
        if self.db["cardssets"].count_documents({"_id": ObjectId(set_id)}) == 0:
            return -1
            # raise DatabaseException("No such set")
        cards_set = self.db["cardssets"].find({"_id": ObjectId(set_id)})
        for card_id in cards_set["cards"]:
            card = self.db["flashcards"].findOne({"_id": ObjectId(card_id)})
            result_cards.append(classes.Flashcard(card["Question"], card["Answer"], card["Set"], card["User"]))
        return classes.Set(cards_set["Creator"], result_cards, set_id)

    def add_user(self, user_name, user_email, user_password):
        if len(user_password) < 8:
            return -1
            # raise AddValueException("Too short password")
        already_exists = self.db["users"].count_documents({"email": user_email})
        if already_exists > 0:
            return -2
            # raise (DatabaseException("User already exists"))
        users = self.db["users"]
        users.insert_one({"UserName": user_name, "password": user_password, "email": user_email, "cardsCreated": 0})
        return 1

    def user_auth(self, email, given_password):
        user = self.get_user(email)
        if user == 0:
            return -1
            # raise AuthenticationException("No such user")
        result = self.db["users"].count_documents({'email': email, 'password': given_password})
        if result == 0:
            return -2
            # raise AuthenticationException("Password incorrect")
        return 1

    def add_flashcard(self, question, answer, creator_id, set_id):
        flashcards = self.db["flashcards"]
        if self.db["users"].count_documents({"_id": ObjectId(creator_id)}) == 0:
            # raise DatabaseException("No such user")
            return -1
        query = {"Question": question, "Answer": answer, "User": creator_id, "Set": set_id}
        if self.db["flashcards"].count_documents(query) != 0:
            # raise DatabaseException("You have already created such flashcard")
            return -2
        flash_card_id = flashcards.insert_one(
            {"Question": question, "Answer": answer, "User": creator_id, "Set": set_id}).inserted_id
        self.db["cardssets"].update_one({"_id": ObjectId(set_id)}, {"$addToSet": {"cards": flash_card_id}})
        return 1

    def add_rating(self, mark, description, creator_id, set_id):
        rate = self.db["rating"]
        query = {"Creator_ID": creator_id, "Set_ID": set_id}
        if self.db["rating"].count_documents(query) != 0:
            return -1  # already rated
        if not mark.isdigit():
            return -2  # mark isn't an intiger
        if int(mark) < 0 or int(mark) > 5:
            return -2
        rate.insert_one({"Creator_ID": creator_id, "Set_ID": set_id, "Mark": mark, "Description": description})
        self.update_average_mark(set_id)
        return 1

    def add_flashcard_mark(self, card_id, user_id, mark):
        if self.db["flashcards"].count_documents({"_id": ObjectId(card_id)}) == 0:
            return -1
            # raise DatabaseException("No such card")
        card = self.db["flashcards"].find_one({"_id": ObjectId(card_id)})
        already_exists = self.db["ratings"].count_documents({"User": user_id, "Card": card_id})
        if already_exists == 0:
            self.db["ratings"].insert_one({"User": user_id, "Card": card_id, "Date": datetime.now(), "Mark": mark})
        else:
            self.db["ratings"].update_one({"User": user_id, "Card": card_id}, {"Date": datetime.now(), "Mark": mark})
        self.update_avarege_mark(card["_id"])
        return 1

    def update_average_mark(self, set_id):
        ratings = self.db["rating"].find({"Set_ID": set_id})
        marks_sum = 0
        marks_amount = 0
        for rating in ratings:
            marks_sum += int(rating["Mark"])
            marks_amount += 1
        self.db["cardssets"].update_one({"_id": set_id}, {"$set": {"avg_mark": round(marks_sum / marks_amount, 2)}})

    def get_set_average_mark(self, set_id):
        return (self.db["cardssets"].find_one({"_id": set_id}))["avg_mark"]

    def get_all_ratings(self, set_id):
        ratings = []
        if self.db['rating'].count_documents({"Set_ID": set_id}) == 0:
            return -1
        cursor = self.db["rating"].find({"Set_ID": set_id})
        count=self.db["rating"].count_documents({"Set_ID":set_id})
        for index in range(count):
            ratings.append(classes.Rating(cursor[index]["Creator_ID"], cursor[index]["Set_ID"], cursor[index]["Mark"], cursor[index]["Description"]))

        return ratings


    def upload_set(self, cards_set):
        if cards_set.ID is None:
            set_id = self.db["cardssets"].insert_one({"Description": cards_set.description,
                                                      "Creator": cards_set.Creator,
                                                      }).inserted_id
            for flashcard in cards_set.Flashcards:
                self.add_flashcard(flashcard.Question, flashcard.Answer, flashcard.User, set_id)
        else:
            # TODO
            pass

    def sets_list_for_selection(self, search_word):
        result_sets = {}
        for cards_set in self.db["cardssets"].find({"Description": {"$exists": "true"}}):
            if search_word in cards_set["Description"]:
                cur_set = classes.Set(cards_set["Creator"], cards_set["Description"], cards_set["_id"])
                for cardID in cards_set["cards"]:
                    card = self.db["flashcards"].find_one({"_id": cardID})
                    cur_set.addFlashcard(classes.Flashcard(card["Question"],
                                                           card["Answer"],
                                                           card["User"],
                                                           cards_set["_id"],
                                                           cardID))
                result_sets.update({cur_set.ID: cur_set})
                del cur_set

        return result_sets

    def all_sets(self):
        result_sets = {}
        for cards_set in self.db["cardssets"].find({"Description": {"$exists": "true"}}):
            cur_set = classes.Set(cards_set["Creator"], cards_set["Description"], cards_set["_id"])
            for cardID in cards_set["cards"]:
                card = self.db["flashcards"].find_one({"_id": cardID})
                cur_set.addFlashcard(classes.Flashcard(card["Question"],
                                                       card["Answer"],
                                                       card["User"],
                                                       cards_set["_id"],
                                                       cardID))
            result_sets.update({cur_set.ID: cur_set})
            del cur_set

        return result_sets

# db = DBConnection()
# print("Users list:")
# db.list_users()
# print("User 1:")
# db.get_user("usr1")
# db.add_user("userFromPython3", "user3@email.com", "passwordVeryStrong")
# print("User from python:")
# for user in db.get_user("userFromPython"):
# print(user)
# db.add_flashcard("czy bazy2 to najlepszy przedmiotyyyyyyyyyyyyy3333", "no chyba raczej a jak",
#                 "5eb6bf2bac666a10cbe7b395",
#                 "5eb746d292763182cc3c8362")
# print(db.user_auth("userFromPython", "passwordVeryStrong"))
# print(db.user_auth("userFromPython", "veryWrongPassword"))
# db.add_flashcard_mark("5eb807df9217647fbe7ab1bb", 5)
# db.add_flashcard_mark("5eb807df9217647fbe7ab1bb", 3)
# print(db.get_flashcard_average_mark("5eb807df9217647fbe7ab1bb"))
# db = DBConnection()
# setsList = db.sets_list_for_selection("set")
# for set in setsList:
#     print(set.description)
