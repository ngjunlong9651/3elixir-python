import os
import logging
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

# Load environment variables
load_dotenv()

# Set up logging to a file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Conversation states
START_ROUTES, CATALOG, ORDERS, ORDER_OPTIONS = range(4)

# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        '👋 👋 Welcome to 3elixir bot! You can use me to: \n1️⃣ Manage your catalogs or \n2️⃣ Manage orders!',
        reply_markup=path_keyboard()
    )
    return START_ROUTES

async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        '👋👋 Hey there, you have selected to manage some orders!📦📦. \n\nYou can choose to \n1️⃣ View order  \n2️⃣ Create a new order:',
        reply_markup=order_management_keyboard()
    )
    return ORDER_OPTIONS

async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        '👋👋 Hey there, you have selected to manage the catalog!🍷🍻. \n\nYou can choose to \n1️⃣ View catalog  \n2️⃣ List a new catalog:',
        reply_markup=catalog_management_keyboard()
    )
    return CATALOG

# Function to generate the inline keyboard for initial path selection
def path_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(" 🍷🍷 Catalog management 🍷🍷", callback_data='catalog_management')],
        [InlineKeyboardButton(" 📦📦 Order management 📦📦 ", callback_data='order_management')],
    ]
    return InlineKeyboardMarkup(keyboard)

# Function to generate the inline keyboard for order management options
def order_management_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("1️⃣ View orders", web_app=WebAppInfo(url="https://3elixir-tma-web.vercel.app/orders"))],
        [InlineKeyboardButton("2️⃣ Create order", web_app=WebAppInfo(url="https://3elixir-tma-web.vercel.app/orders/create-step1"))],
        [InlineKeyboardButton("⬅️ Back", callback_data='back_to_start')],  # Added back button
    ]
    return InlineKeyboardMarkup(keyboard)

# Function to generate the inline keyboard for catalog management options
def catalog_management_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("1️⃣ View catalogs", web_app=WebAppInfo(url="https://3elixir-tma-web.vercel.app/products"))],
        [InlineKeyboardButton("2️⃣ Add a new product", web_app=WebAppInfo(url="https://3elixir-tma-web.vercel.app/products/create-step1"))],
        [InlineKeyboardButton("⬅️ Back", callback_data='back_to_start')],  # Added back button
    ]
    return InlineKeyboardMarkup(keyboard)

# Function to handle the button click for initial path selection
async def path_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "catalog_management":
        await query.edit_message_text(
            text="👋👋 Hey there, you have selected to manage the catalog!🍷🍻. \n\nYou can choose to \n1️⃣ View catalog  \n2️⃣ List a new catalog:",
            reply_markup=catalog_management_keyboard()
        )
        return CATALOG
    elif query.data == "order_management":
        await query.edit_message_text(
            text="👋👋 Hey there, you have selected to manage some orders!📦📦. \n\nYou can choose to \n1️⃣ View order  \n2️⃣ Create a new order:",
            reply_markup=order_management_keyboard()
        )
        return ORDER_OPTIONS
    elif query.data == 'back_to_start':  # Handle back button click
        await query.edit_message_text(
            text='👋 👋 Welcome to 3elixir bot! You can use me to: \n1️⃣ Manage your catalogs or \n2️⃣ Manage orders!',
            reply_markup=path_keyboard()
        )
        return START_ROUTES

def main() -> None:
    # Retrieve the bot token from an environment variable
    # Create the Application and pass it your bot's token.
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN_PROD")
    if TELEGRAM_BOT_TOKEN is None:
        logger.error("No TELEGRAM_BOT_TOKEN set in environment variables.")
        return
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers go here
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start),
                      CommandHandler("orders", orders),
                      CommandHandler("catalog", catalog)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(path_select, pattern='^(catalog_management|order_management|back_to_start)$'),  # Added back_to_start pattern
            ],
            CATALOG: [
                CallbackQueryHandler(path_select, pattern='^back_to_start$'),  # Handle back to start from catalog
            ],
            ORDER_OPTIONS: [
                CallbackQueryHandler(path_select, pattern='^back_to_start$'),  # Handle back to start from orders
            ],
        },
        fallbacks=[CommandHandler("start", start),
                      CommandHandler("orders", orders),
                      CommandHandler("catalog", catalog)]
    )
    
    # Add ConversationHandler to the application
    application.add_handler(conv_handler)

    PRODUCTION = os.environ.get("PRODUCTION") == "True"
    if PRODUCTION:
        # Ensure the TELEGRAM_WEBHOOK_URL is set in the environment variables
        TELEGRAM_WEBHOOK_URL = os.environ.get("TELEGRAM_WEBHOOK_URL")
        if TELEGRAM_WEBHOOK_URL is None:
            logger.error("No TELEGRAM_WEBHOOK_URL set in environment variables.")
            return

        # * Run the bot in production mode with webhook enabled
        logger.info("Running in production mode, with webhook enabled.")
        logger.info(f"Webhook URL: {TELEGRAM_WEBHOOK_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 8443)),
            secret_token=os.environ.get("TELEGRAM_WEBHOOK_SECRET", "NotSoSecret"),
            webhook_url=TELEGRAM_WEBHOOK_URL,
        )
    else:
        # * Run the bot in development mode with polling enabled
        logger.info("Running in development mode, with polling enabled.")
        

if __name__ == '__main__':
    main()
