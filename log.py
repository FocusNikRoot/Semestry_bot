import logging
from telegram import Update

def setup_user_logger(user_id):
    logger = logging.getLogger(str(user_id))
    logger.setLevel(logging.INFO)
    log_file = logging.FileHandler(f"logs/{user_id}.log", encoding='utf-8')
    log_file.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    if not logger.handlers:
        logger.addHandler(log_file)
    return logger

async def log_message(update: Update, message: str):
    user_id = update.effective_user.id
    logger = setup_user_logger(user_id)
    logger.info(f"[user_id: {user_id}]:{message}")