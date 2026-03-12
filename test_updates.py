import asyncio
from aiogram import Bot, Dispatcher
from handlers import start, cookies, download, upload, myfiles, admin

async def main():
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(cookies.router)
    dp.include_router(download.router)
    dp.include_router(upload.router)
    dp.include_router(myfiles.router)
    dp.include_router(admin.router)
    print("Allowed Updates: ", dp.resolve_used_update_types())

asyncio.run(main())
