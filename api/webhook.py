import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import settings
from handlers import start, cookies, download, upload, myfiles, admin

# Bot components
bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Include routers
dp.include_router(start.router)
dp.include_router(cookies.router)
dp.include_router(download.router)
dp.include_router(upload.router)
dp.include_router(myfiles.router)
dp.include_router(admin.router)

async def process_update(update_dict: dict):
    update = types.Update.model_validate(update_dict, context={"bot": bot})
    await dp.feed_update(bot, update)

# Vercel Serverless Function entry point
def handler(request):
    if request.method == 'POST':
        try:
            body = request.get_data().decode('utf-8')
            update_dict = json.loads(body)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_update(update_dict))
            
            return {
                'statusCode': 200,
                'body': 'ok'
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': str(e)
            }
    
    return {
        'statusCode': 200,
        'body': 'Bot webhook is active'
    }
