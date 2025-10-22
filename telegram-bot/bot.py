import os
import httpx
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the bot token from an environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN set for the bot!")

# Define the FastAPI service URL
FASTAPI_URL = os.getenv("FASTAPI_SERVICE_URL", "http://fastapi-service:8000/products/")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message."""
    await update.message.reply_text(
        "Hi! I am a product bot. Use the /product <ID> command to get product details."
    )


async def get_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches product data from the FastAPI service."""
    try:
        product_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid product ID. Usage: /product <ID>")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_URL}{product_id}")

        if response.status_code == 200:
            product = response.json()
            message = (
                f"📦 *Product Details*\n\n"
                f"*ID:* `{product['id']}`\n"
                f"*Name:* {product['name']}\n"
                f"*Description:* {product['description']}\n"
                f"*Price:* `${product['price']:.2f}`\n"
                f"*Stock:* {product['stock']} units left"
            )
            await update.message.reply_text(message, parse_mode='Markdown')
        elif response.status_code == 404:
            await update.message.reply_text(f"Sorry, product with ID {product_id} was not found.")
        else:
            await update.message.reply_text("Error fetching product data from the service.")
            logger.error(f"API request failed with status code: {response.status_code}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        await update.message.reply_text("An internal error occurred. Please try again later.")


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("product", get_product))

    logger.info("Bot is starting...")
    application.run_polling()


if __name__ == "__main__":
    main()