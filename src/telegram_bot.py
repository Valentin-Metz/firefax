import logging
import os.path
from datetime import datetime

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

import settings
from fax_parser import Fax
from mail_receiver import receive_fax

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def register_user(chat_id: int):
    user_database: [int] = get_registered_users()
    user_database.append(chat_id)
    user_database = list(dict.fromkeys(user_database))  # deduplicate
    user_database.sort()

    with open(settings.config['telegram']['database_file_path'], 'w') as f:
        for user in user_database:
            f.write(str(user) + '\n')


def get_registered_users() -> [int]:
    user_database: [int] = []
    if os.path.isfile(settings.config['telegram']['database_file_path']):
        with open(settings.config['telegram']['database_file_path'], 'r') as f:
            for line in f:
                user_database.append(int(line))
    return user_database


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Dieser Bot informiert dich über Einsätze "
                                        "der Freiwilligen Feuerwehr Pellheim.\n"
                                        "Nutze \"/register passwort\" um dich zu registrieren.")


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Bitte registriere dich mit Passwort.\n"
                                            "Beispiel: /register 123456")
        return

    if context.args[0] == settings.config['telegram']['user_password']:
        register_user(update.effective_chat.id)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Registrierung erfolgreich!\n"
                                            "Ab sofort erhältst du Einsatzbenachrichtigungen!")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Falsches Passwort!")


async def transmit_fax(context: ContextTypes.DEFAULT_TYPE, fax: Fax):
    for user in get_registered_users():
        if fax.einsatzort.koordinaten:
            await context.bot.send_location(chat_id=user,
                                            latitude=fax.einsatzort.koordinaten[0],
                                            longitude=fax.einsatzort.koordinaten[1])
        await context.bot.send_message(chat_id=user, text=str(fax), parse_mode="MarkdownV2")


def start_bot():
    application = ApplicationBuilder().token(settings.config['telegram']['api_token']).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('register', register))
    application.job_queue.run_repeating(receive_fax, interval=2, first=5)

    print(f"{datetime.now()}: Started FireFAX")
    application.run_polling()


if __name__ == '__main__':
    start_bot()
