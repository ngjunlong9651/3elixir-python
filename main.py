from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from datetime import datetime
import pytz
import requests
import os
import logging
from dotenv import load_dotenv

# Set up logging to a file
logging.basicConfig(
    level=logging.INFO
    )

logger = logging.getLogger(__name__)

# Conversation states
START_ROUTES, CATALOG, ORDERS,  ORDER_OPTIONS = range(4)


# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋 👋 Welcome to 3elixir bot! You can use me to: \n1️⃣ Manage your catalogs or \n2️⃣ Manage orders!",
        reply_markup=path_keyboard(),
    )
    return START_ROUTES


async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋👋 Hey there, you have selected to manage some orders!📦📦. \n\nYou can choose to \n1️⃣ View order  \n2️⃣ Create a new order:",
        reply_markup=order_management_keyboard(),
    )
    return ORDER_OPTIONS


async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋👋 Hey there, you have selected to manage the catalog!🍷🍻. \n\nYou can choose to \n1️⃣ View catalog  \n2️⃣ List a new catalog:",
        reply_markup=catalog_management_keyboard(),
    )
    return CATALOG

async def reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        logger.info("Fetching orders due today.")
        
        # Define Singapore timezone
        singapore_timezone = pytz.timezone('Asia/Singapore')
        today = datetime.now(singapore_timezone).date()
        logger.info(f"Current Date time (Singapore): {today}")
        
        prod_url = os.environ.get("PROD_URL")
        if prod_url is None:
            logger.error("Prod URL is not set in the environment variables.")
            await update.message.reply_text("PROD_URL is not set in the environment variables.")
            return
        
        # Initialize variables for pagination
        all_orders = []
        start = 0
        limit = 100

        # Fetch all pages of orders
        while True:
            response = requests.get(f"{prod_url}/api/orders/?populate=*&pagination[limit]={limit}&pagination[start]={start}", headers={
                'Authorization': f"Bearer {os.getenv('API_TOKEN')}"
            })
            response.raise_for_status()
            data = response.json().get('data', [])
            if not data:
                break
            all_orders.extend(data)
            start += limit

        logger.info(f"Fetched a total of {len(all_orders)} orders from API")
        if not all_orders:
            await update.message.reply_text("No orders found.")
            return START_ROUTES
        
        for order in all_orders:
            if order['attributes']['fulfilmentEnd'] is None:
                order['attributes']['fulfilmentEnd'] = order['attributes']['fulfilmentStart']
        
        active_orders = [
            order for order in all_orders
            if order['attributes']['order_status']['data']['attributes']['orderStatus'] not in ['Completed', 'Cancelled', 'Out For Delivery']
        ]
        logger.info(f"Filtered {len(active_orders)} active orders")

        due_today_orders = [
            order for order in active_orders
            if (
                datetime.strptime(order['attributes']['fulfilmentStart'], "%Y-%m-%dT%H:%M:%S.%fZ").astimezone(singapore_timezone).date() <= today <= 
                (datetime.strptime(order['attributes']['fulfilmentEnd'], "%Y-%m-%dT%H:%M:%S.%fZ").astimezone(singapore_timezone).date())
            ) 
        ]
        
        logger.info(f"Found {len(due_today_orders)} orders due today")

        if due_today_orders:
            total_orders = len(due_today_orders)
            order_message = f"Orders Due Today:  {today.strftime('%d-%m-%Y')}. {today.strftime('%A')}\n"
            order_message += f"Total Orders: {total_orders}\n"
            order_message += "--------------------------------------\n"
            
            for order in due_today_orders:
                attributes = order['attributes']
                order_message += f"<b> 📋 Order ID:</b> {order['id']}\n"
                order_message += f"<b> ⌛ Order Status:</b> {attributes['order_status']['data']['attributes']['orderStatus']}\n"
                order_message += f"<b> 💼 Customer Name: {attributes['customerName']}</b>\n"
                order_message += f"<b> 👤 Attn: {attributes['attention']}</b>\n"
                order_message += f"<b> 📍 Delivery Address:</b> {attributes['customerAddress']}\n"
                order_message += f"<b> ⏰ Delivery Time:</b> {datetime.strptime(attributes['fulfilmentStart'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%d-%m-%Y %I:%M %p')}\n"
                order_message += f"<b> 📞 Contact Number:</b> {attributes['customerContact']}\n"
                order_message += "<b> 📦 Products:</b>\n"
                for product in attributes['orderProducts']:
                    order_message += (
                        f"  {product['quantity']} x {product['name']} "
                        f"@ ${product['price']}/Btl\n"
                    )
                ## Optional Remarks:
                if attributes.get('remarks'):
                    order_message += f"<b>Remarks:</b> {attributes['remarks']}\n\n"
                    
                ## Divider between the orders:
                order_message += "--------------------------------------\n"
            
            await update.message.reply_text(order_message, parse_mode=ParseMode.HTML)
            logger.info("Sent reminder with due today orders.")
        else:
            logger.info("No orders due today")
            await update.message.reply_text("No orders due today.")
    
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        await update.message.reply_text("An error occurred while fetching orders.")
    
    return START_ROUTES



                
            
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id  
    await update.message.reply_text(
        f"""Hey there, you have selected to register! 🎉🎉 \n\nFollow these steps to get registered immediately!\n\nStep 1️⃣: Copy your telegram {user_id} \n\nStep 2️⃣: Go to strapi backend Create a new authenticated user with the telegram user id as both the username and password"""
        )
    print(update.effective_user)
    
# Function to generate the inline keyboard for initial path selection
def path_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                " 🍷🍷 Catalog management 🍷🍷", callback_data="catalog_management"
            )
        ],
        [
            InlineKeyboardButton(
                " 📦📦 Order management 📦📦 ", callback_data="order_management"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# Function to generate the inline keyboard for order management options
def order_management_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "1️⃣ View orders",
                web_app=WebAppInfo(url="https://3elixir-order-management-tma.vercel.app/orders"),
            )
        ],
        [
            InlineKeyboardButton(
                "2️⃣ Create order",
                web_app=WebAppInfo(
                    url="https://3elixir-order-management-tma.vercel.app/orders/create-step1"
                ),
            )
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")
        ],  # Added back button
    ]
    return InlineKeyboardMarkup(keyboard)


# Function to generate the inline keyboard for catalog management options
def catalog_management_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "1️⃣ View catalogs",
                web_app=WebAppInfo(url="https://3elixir-order-management-tma.vercel.app/products"),
            )
        ],
        [
            InlineKeyboardButton(
                "2️⃣ Add a new product",
                web_app=WebAppInfo(
                    url="https://3elixir-order-management-tma.vercel.app/products/create"
                ),
            )
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")
        ],  # Added back button
    ]
    return InlineKeyboardMarkup(keyboard)


# Function to handle the button click for initial path selection
async def path_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "catalog_management":
        await query.edit_message_text(
            text="👋👋 Hey there, you have selected to manage the catalog!🍷🍻. \n\nYou can choose to \n1️⃣ View catalog  \n2️⃣ List a new catalog:",
            reply_markup=catalog_management_keyboard(),
        )
        return CATALOG
    elif query.data == "order_management":
        await query.edit_message_text(
            text="👋👋 Hey there, you have selected to manage some orders!📦📦. \n\nYou can choose to \n1️⃣ View order  \n2️⃣ Create a new order:",
            reply_markup=order_management_keyboard(),
        )
        return ORDER_OPTIONS
    elif query.data == "back_to_start":  # Handle back button click
        await query.edit_message_text(
            text="👋 👋 Welcome to 3elixir bot! You can use me to: \n1️⃣ Manage your catalogs or \n2️⃣ Manage orders!",
            reply_markup=path_keyboard(),
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
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("orders", orders),
            CommandHandler("catalog", catalog),
            CommandHandler("register", register),
            CommandHandler("reminder", reminder),
        ],
        states={
            START_ROUTES: [
                CallbackQueryHandler(
                    path_select,
                    pattern="^(catalog_management|order_management|back_to_start)$",
                ),  # Added back_to_start pattern
            ],
            CATALOG: [
                CallbackQueryHandler(
                    path_select, pattern="^back_to_start$"
                ),  # Handle back to start from catalog
            ],
            ORDER_OPTIONS: [
                CallbackQueryHandler(
                    path_select, pattern="^back_to_start$"
                ),  # Handle back to start from orders
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("orders", orders),
            CommandHandler("catalog", catalog),
            CommandHandler("register", register),
            CommandHandler("reminder", reminder),
        ],
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


if __name__ == "__main__":
    main()
