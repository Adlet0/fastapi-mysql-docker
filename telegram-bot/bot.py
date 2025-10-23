import os
import httpx
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FASTAPI_BASE_URL = os.getenv("FASTAPI_SERVICE_URL", "http://fastapi-service:8000/products/")

# --- Функции-помощники ---
def format_product_message(product: dict) -> str:
    """Форматирует данные о продукте в красивое сообщение."""
    return (
        f"*Продукт найден!*\n\n"
        f"*ID:* `{product['id']}`\n"
        f"*Название:* {product['name']}\n"
        f"*Описание:* {product['description']}\n"
        f"*Цена:* `${product['price']:.2f}`\n"
        f"*Остаток на складе:* {product['stock']} шт."
    )

# --- Обработчики команд ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение и справку."""
    await update.message.reply_text(
        "Привет! Я бот для управления каталогом товаров. "
        "Используйте /help, чтобы увидеть список команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает справку по командам."""
    help_text = (
        "*Список доступных команд:*\n\n"
        "*/help* - Показать это сообщение.\n\n"
        "*/all* - Показать все товары в каталоге.\n\n" 
        "*/product <ID>* - Получить информацию о товаре.\n"
        "*Пример:* `/product 1`\n\n"
        "*/add <Название>; <Описание>; <Цена>; <Кол-во>* - Добавить новый товар.\n"
        "*Пример:* `/add Чайник; Электрический; 25.50; 100`\n\n"
        "*/update <ID>; <Название>; <Описание>; <Цена>; <Кол-во>* - Обновить товар.\n"
        "*Пример:* `/update 1; Чайник; Бесшумный; 30.0; 80`\n\n"
        "*/delete <ID>* - Удалить товар.\n"
        "*Пример:* `/delete 2`"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def get_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """READ: Получает товар по ID."""
    try:
        product_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Ошибка: Укажите корректный ID. \nПример: `/product 1`")
        return

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{FASTAPI_BASE_URL}{product_id}")
            if response.status_code == 200:
                message = format_product_message(response.json())
                await update.message.reply_text(message, parse_mode='Markdown')
            elif response.status_code == 404:
                await update.message.reply_text(f"❌ Товар с ID {product_id} не найден.")
            else:
                await update.message.reply_text("Произошла ошибка на сервере.")
        except httpx.RequestError as e:
            await update.message.reply_text(f"Не удалось подключиться к сервису продуктов: {e}")

async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """CREATE: Добавляет новый товар."""
    try:
        args_str = " ".join(context.args)
        name, description, price_str, stock_str = [arg.strip() for arg in args_str.split(';')]
        price = float(price_str)
        stock = int(stock_str)
        
        product_data = {
            "name": name, 
            "description": description, 
            "price": price, 
            "stock": stock
        }
    except (ValueError, IndexError):
        await update.message.reply_text(
            "*Ошибка формата.*\nИспользуйте: `/add <Название>; <Описание>; <Цена>; <Кол-во>`",
            parse_mode='Markdown'
        )
        return

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(FASTAPI_BASE_URL, json=product_data)
            if response.status_code == 200:
                new_product = response.json()
                await update.message.reply_text(f"Товар '{new_product['name']}' успешно добавлен с ID: `{new_product['id']}`", parse_mode='Markdown')
            else:
                await update.message.reply_text(f"Ошибка при добавлении: {response.text}")
        except httpx.RequestError as e:
            await update.message.reply_text(f"Не удалось подключиться к сервису продуктов: {e}")

async def update_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """UPDATE: Обновляет существующий товар."""
    try:
        args_str = " ".join(context.args)
        product_id_str, name, description, price_str, stock_str = [arg.strip() for arg in args_str.split(';')]
        product_id = int(product_id_str)
        price = float(price_str)
        stock = int(stock_str)
        
        product_data = {
            "name": name, 
            "description": description, 
            "price": price, 
            "stock": stock
        }
    except (ValueError, IndexError):
        await update.message.reply_text(
            "*Ошибка формата.*\nИспользуйте: `/update <ID>; <Название>; <Описание>; <Цена>; <Кол-во>`",
            parse_mode='Markdown'
        )
        return

    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(f"{FASTAPI_BASE_URL}{product_id}", json=product_data)
            if response.status_code == 200:
                updated_product = response.json()
                await update.message.reply_text(f"Товар с ID `{updated_product['id']}` успешно обновлен.")
            elif response.status_code == 404:
                await update.message.reply_text(f"Товар с ID {product_id} не найден.")
            else:
                await update.message.reply_text(f"Ошибка при обновлении: {response.text}")
        except httpx.RequestError as e:
            await update.message.reply_text(f"Не удалось подключиться к сервису продуктов: {e}")
            
async def delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """DELETE: Удаляет товар по ID."""
    try:
        product_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Ошибка: Укажите корректный ID. \nПример: `/delete 1`")
        return

    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(f"{FASTAPI_BASE_URL}{product_id}")
            if response.status_code == 200:
                await update.message.reply_text(f"Товар с ID {product_id} был успешно удален.")
            elif response.status_code == 404:
                await update.message.reply_text(f"Товар с ID {product_id} не найден.")
            else:
                await update.message.reply_text(f"Ошибка при удалении: {response.text}")
        except httpx.RequestError as e:
            await update.message.reply_text(f"Не удалось подключиться к сервису продуктов: {e}")


async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """READ ALL: Показывает список всех товаров."""
    async with httpx.AsyncClient() as client:
        try:
            # Обращаемся к эндпоинту, который мы создали в FastAPI
            response = await client.get(FASTAPI_BASE_URL)

            if response.status_code == 200:
                products = response.json()
                if not products:
                    await update.message.reply_text("Каталог товаров пуст.")
                    return

                # Формируем сообщение из списка товаров
                message = "*Вот список всех товаров:*\n\n"
                for p in products:
                    message += (
                        f"*ID:* `{p['id']}`\n"
                        f"*Название:* {p['name']}\n"
                        f"*Цена:* ${p['price']:.2f}\n"
                        f"---------------------\n"
                    )
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"Произошла ошибка на сервере: {response.text}")
        except httpx.RequestError as e:
            await update.message.reply_text(f"Не удалось подключиться к сервису продуктов: {e}")


def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(TOKEN).build()

    # Добавляем все обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("all", list_products)) 
    application.add_handler(CommandHandler("product", get_product))
    application.add_handler(CommandHandler("add", add_product))
    application.add_handler(CommandHandler("update", update_product))
    application.add_handler(CommandHandler("delete", delete_product))

    logger.info("Бот запускается...")
    application.run_polling()


if __name__ == "__main__":
    main()