import telebot


class TelegramBot(object):
    def __init__(self, api_token, chat_id):
        self.chat_id = chat_id
        self.api_token = api_token
        self.bot = self.create_bot()

    def create_bot(self):
        return telebot.TeleBot(self.api_token)

    def send_message(self, message):
        self.bot.send_message(self.chat_id, message)
