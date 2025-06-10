from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from bot.logic.commands import *
from config.settings import bot_token

def main():
    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("weather", weather))
    app.add_handler(CommandHandler("movie", movie))
    app.add_handler(CommandHandler("map", map_command))
    app.add_handler(CommandHandler("affirmation", random_affirmations))
    app.add_handler(CommandHandler("translate", translate_user_msg))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("most_wanted", most_wanted))
    app.add_handler(CallbackQueryHandler(most_wanted_callback, pattern="^most_wanted_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.run_polling()

if __name__ == "__main__":
    main()