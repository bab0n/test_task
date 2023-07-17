from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import datetime
import asyncio

storage = MemoryStorage()
bot = Bot(token='')
dp = Dispatcher(bot, storage=storage)


class NotifyAprove(StatesGroup):
    text = State()
    date = State()
    send_time = State()
    answer_time = State()
    wait_aprove = State()


async def delete_mid(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    if "m_id" in data:
        await bot.delete_message(message.from_user.id, data["m_id"])


@dp.message_handler(commands=["notify"])
async def notify_cmd(message: types.Message, state: FSMContext):
    data = message.text.split()
    if len(data) <= 1:
        g = await message.answer(
            'Данная команда предназначена для отправки уведомления сотруднику,\
            формат использования:\n\
                /notify id\nДалее бот предложет вам заполнить оставшиеся данные'
        )
        await asyncio.sleep(30)
        await g.delete()
    else:
        g = await message.answer('Введите текст уведомления для сотрудника')
        await NotifyAprove.text.set()
        await state.update_data(empl=data[1])
        await state.update_data(m_id=g.message_id)
    await message.delete()


@dp.callback_query_handler(state=NotifyAprove.wait_aprove)
async def aprove(call: types.CallbackQuery, state: FSMContext):
    content = call.data.split("|")
    sendet = False
    if content[1] == 'ok':
        sendet = True
        data = await state.get_data()

        now_date = datetime.datetime.now()
        send_date = datetime.datetime.fromisoformat(
            f'{data["s_date"]} {data["s_time"]}'
        )
        to_wait = (send_date - now_date).total_seconds()
        await asyncio.sleep(to_wait)

        kb = types.InlineKeyboardMarkup(one_time_keyboard=True, row_width=1).add(
            types.InlineKeyboardButton(text='Выполнил', callback_data='make|ok'),
            types.InlineKeyboardButton(text='Не выполнил', callback_data='make|not'),
        )
        await bot.send_message(int(data['empl']), data['s_text'], reply_markup=kb)

    g = await call.message.answer(
        f'Уведомление успешно {"создано" if sendet else "отменено"}'
    )
    await call.message.delete()
    await asyncio.sleep(20)
    await g.delete()
    await state.finish()


@dp.message_handler(state=NotifyAprove.answer_time)
async def get_ans_time(message: types.Message, state: FSMContext):
    await delete_mid(message, state)
    data = await state.get_data()
    try:
        m = int(message.text)
        kb = types.InlineKeyboardMarkup(one_time_keyboard=True, row_width=1).add(
            types.InlineKeyboardButton(text='Отправить', callback_data='apr|ok'),
            types.InlineKeyboardButton(text='Отменить', callback_data='apr|cancel'),
        )
        g = await message.answer(
            f'Проверьте данные\n\
            Дата - {data["s_date"]}\n\
            Время - {data["s_time"]}\n\
            На ответ - {m} мин.\n\
            Текст:\n{data["s_text"]}',
            reply_markup=kb,
        )
        await NotifyAprove.wait_aprove.set()
    except Exception:
        g = await message.answer(
            'Не удалось получить время для ответа.\nНеобходимо отправить целое число - кол-во минут для ответа'
        )
        await state.update_data(m_id=g.message_id)
    return await message.delete()


@dp.message_handler(state=NotifyAprove.send_time)
async def get_time(message: types.Message, state: FSMContext):
    await delete_mid(message, state)
    try:
        t = datetime.time.fromisoformat(message.text)
        g = await message.answer(
            'Время отправки успешно сохранено!\nВведите целое кол-во минут для ответа на сообщение'
        )
        await NotifyAprove.answer_time.set()
        await state.update_data(m_id=g.message_id)
        await state.update_data(s_time=message.text)
    except Exception:
        g = await message.answer(
            f'Не удалось получить время, используйте формат:\n{datetime.time(9, 0)}'
        )
        await state.update_data(m_id=g.message_id)
    return await message.delete()


@dp.message_handler(state=NotifyAprove.date)
async def get_date(message: types.Message, state: FSMContext):
    await delete_mid(message, state)
    try:
        date = datetime.date.fromisoformat(message.text)
        g = await message.answer(
            f'Дата успешно сохранена, укажите в какое фремя должно быть отправлено напоминание\nФормат - {datetime.time(9, 0)}'
        )
        await NotifyAprove.send_time.set()
        await state.update_data(s_date=message.text)
        await state.update_data(m_id=g.message_id)
    except Exception:
        g = await message.answer(
            f'Не удалось преоброзовать дату, укажите дату в данном формате:\n{datetime.date.today().isoformat()}'
        )
        await state.update_data(m_id=g.message_id)
    return await message.delete()


@dp.message_handler(state=NotifyAprove.text)
async def get_text(message: types.Message, state: FSMContext):
    await delete_mid(message, state)
    g = await message.answer(
        f'Текст успешно сохранен, укажите дату отправки\nФормат: {datetime.date.today().isoformat()}'
    )
    await NotifyAprove.date.set()
    await state.update_data(s_text=message.text)
    await state.update_data(m_id=g.message_id)
    return await message.delete()


@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer(
        'Данный бот предназначен для отправки и получения уведомлений\nЕсли Вы явлетесь сотрудником то просто ожидайте сообщения от менеджера\nЕсли Вы являетесь менеджером, используйте /notify чтобы получить подробности отправки\n'
    )
    await message.answer(f'{datetime.time}')
    return await message.delete()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
