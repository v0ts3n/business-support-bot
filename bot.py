import logging
import asyncio
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import exceptions
import telethon
import requests
import random
from aiogram import *
import datetime
from config import token, ADMIN_IDS
logging.basicConfig(level=logging.INFO)

router = Router()



already_answered = {}
urgent_cooldowns = {}

is_online = True


async def already_answered_poller():
    for i in ADMIN_IDS:
        try:await bot.send_message(i, "👌 Запустили бота")
        except:pass
    while True:
        now = datetime.datetime.now()

        for user_id in list(already_answered):
            if (now - already_answered[user_id]).total_seconds() > 3600:
                already_answered.pop(user_id)
                print(f"Removed {user_id}")

        for user_id in list(urgent_cooldowns):
            if (now - urgent_cooldowns[user_id]).total_seconds() > 7200:
                urgent_cooldowns.pop(user_id)
                print(f"Urgent cooldown cleared {user_id}")

        await asyncio.sleep(10)



@router.callback_query(F.data.startswith("support:urgent"))
async def support_urgent(callback: types.CallbackQuery):
    now = datetime.datetime.now()
    user_id = callback.from_user.id
    last_press = urgent_cooldowns.get(user_id)

    if last_press is not None and (now - last_press).total_seconds() < 7200:
        remaining = 7200 - (now - last_press).total_seconds()
        minutes = int(remaining // 60) + 1
        await callback.answer(
            f"Вы уже нажимали кнопку 'Это срочно'. Повторно можно через {minutes} мин.",
            show_alert=True
        )
        return

    urgent_cooldowns[user_id] = now

    await callback.answer("👌 Оповестили агента поддержки", show_alert=True)
    for i in ADMIN_IDS:
        try:
            await bot.send_message(i, f"👌 Пользователь {callback.from_user.id} нажал на кнопку 'Это срочно'")
        except:
            pass


@router.business_message()
async def business_message(message: types.Message):
    global is_online
    if message.chat.id != message.from_user.id:
        return

    now = datetime.datetime.now()
    last_time = already_answered.get(message.from_user.id)
    if last_time is not None and (now - last_time).total_seconds() < 3600:
        return

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🤖 Конвертор", url="https://t.me/instamarket_conv_bot")
    keyboard.button(text="‼️ Это срочно", callback_data="support:urgent")
    await message.reply(
        f"""Здравствуйте, это чат поддержки InstaMarket.
На данный момент поддержка {"🟢 Онлайн" if is_online else "🔴 Оффлайн"}

Вы можете отправить нам вашу проблему и мы решим ее как можно быстрее! Или если проблема срочная, нажмите на кнопку
Бота-автоконвертора вы можете найти по кнопке ниже""",
        reply_markup=keyboard.as_markup()
    )
    already_answered[message.from_user.id] = now

@router.message(Command("online"))
async def online(message: types.Message):
    global is_online
    is_online = not is_online
    await message.reply(f"Поддержка {'🟢 Онлайн' if is_online else '🔴 Оффлайн'}")
    return

bot = Bot(token=token)
dp = Dispatcher()
dp.include_router(router)


async def main():
    
    asyncio.create_task(already_answered_poller())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
