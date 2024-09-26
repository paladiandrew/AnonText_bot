import asyncio

from enum import Enum
from aiogram import Bot, types, Dispatcher
from aiogram.utils import executor
from collections import deque

from data.config import TOKEN
from data.config import ADMIN_ID1
from data.config import ADMIN_ID2
from data.config import Advert


async def two_users_to_room(id1, id2):
    status[id1], status[id2] = users.virting_user, users.virting_user
    if len(stack) == 0:
        stackLen += 1
        stack.append(stackLen)
    room = stack.pop()
    await bot.send_message(
        id1, "Собеседник найден, нажмите /stop чтобы остановить вирт."
    )
    await bot.send_message(
        id2, "Собеседник найден, нажмите /stop чтобы остановить вирт."
    )
    connections[id1] = [id2, room]
    connections[id2] = [id1, room]


async def queue_users_to_chats():
    await asyncio.sleep(0.5)
    loop = asyncio.get_event_loop()
    while len(queue) > 0:
        work_queue.append(queue.popleft())
    while len(work_queue) > 1:
        id1, id2 = work_queue.popleft(), work_queue.popleft()
        if id1 == id2:
            work_queue.append(id1)
            continue
        loop.create_task(two_users_to_room(id1, id2))


async def stop_chatting(id1):
    id2 = connections[id1][0]
    room = connections[id1][1]
    stack.append(room)
    status[id1] = users.active_user
    status[id2] = users.active_user
    del connections[id1]
    del connections[id2]
    await bot.send_message(id1, "Подключение разорвано")
    await bot.send_message(id2, "Подключение разорвано")


async def stop_searching(id1):
    try:
        status[id1] = users.active_user
        work_queue.remove(id1)
        await bot.send_message(id1, "Поиск приостановлен")
    except:
        pass


async def max_connections_fn():
    global max_connections
    if len(connections) > max_connections:
        max_connections = len(connections)


class users(Enum):
    active_user = 0
    waiting_user = 1
    virting_user = 2


class admin_advertStatus(Enum):
    noAdvert = 0
    waitForSendChatId = 1
    waitForSendAdvert = 2
    needToSendAdvert = 3


bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

adminID1, adminID2, adminDict = ADMIN_ID1, ADMIN_ID2, dict()
advert = Advert()

adminDict[adminID1] = admin_advertStatus.noAdvert
adminDict[adminID2] = admin_advertStatus.noAdvert
advert.__init__()

stack, stackLen = deque(), 100
queue = deque()
work_queue = deque()
max_connections = 0
connections, status = dict(), dict()


for i in range(1, 101):
    stack.append(i)


@dp.message_handler(commands="start")
async def start(message: types.Message):
    status[message.from_user.id] = users.active_user
    await bot.send_message(
        message.from_user.id,
        "Приветствуем в нашем боте, он предназначен для анонимного текстового вирта, рады всем кто пришёл для ролевых переписок любого формата. Другие виды файлов, кроме текста, не отправляются собеседникам, приятного общения.",
    )
    await asyncio.sleep(3)
    await message.answer("Нажмите /virt чтобы найти незнакомца для вирта")


@dp.message_handler(commands="virt")
async def virt(message: types.Message):
    loop = asyncio.get_event_loop()
    loop.create_task(max_connections_fn())
    if not message.from_user.id in status:
        status[message.from_user.id] = users.active_user
    if adminDict[adminID1] == admin_advertStatus.needToSendAdvert:
        chat_member = await bot.get_chat_member(
            advert.get_chat_id(), int(message.from_user.id)
        )
        if str(chat_member.status) != "left":
            advert.set_watch_status(message.from_user.id, True)
        else:
            advert.set_watch_status(message.from_user.id, False)

    match status[message.from_user.id]:
        case users.active_user:
            if (
                advert.get_watch_status(message.from_user.id) == True
                and adminDict[adminID1] == admin_advertStatus.needToSendAdvert
            ) or (adminDict[adminID1] != admin_advertStatus.needToSendAdvert):
                loop = asyncio.get_event_loop()
                status[message.from_user.id] = users.waiting_user
                await bot.send_message(
                    message.from_user.id, "Начинаем поиск собеседника"
                )
                await asyncio.sleep(0.5)
                queue.append(message.from_user.id)
                loop.create_task(queue_users_to_chats())
            else:
                await bot.send_message(message.from_user.id, advert.get_Advert())
        case users.waiting_user:
            await bot.send_message(message.from_user.id, "Ожидаем подключения")
        case _:
            await bot.send_message(message.from_user.id, "У вас уже есть активный чат")


@dp.message_handler(commands="stop")
async def stop(message: types.Message):
    loop = asyncio.get_event_loop()
    loop.create_task(max_connections_fn())
    if not message.from_user.id in status:
        status[message.from_user.id] = users.active_user
    match status[message.from_user.id]:
        case users.virting_user:
            loop = asyncio.get_event_loop()
            loop.create_task(stop_chatting(message.from_user.id))
        case users.waiting_user:
            loop = asyncio.get_event_loop()
            loop.create_task(stop_searching(message.from_user.id))
        case _:
            await bot.send_message(message.from_user.id, "У вас нет активного чата")


@dp.message_handler(commands="setAdvert")
async def stop(message: types.Message):
    if (
        (message.from_user.id == adminID1 or message.from_user.id == adminID2)
        and message.from_user.id in status
        and status[message.from_user.id] != users.virting_user
    ):
        if adminDict[adminID1] == admin_advertStatus.noAdvert:
            await bot.send_message(message.from_user.id, "Присылайте id чата")
            adminDict[adminID1] = admin_advertStatus.waitForSendChatId
            adminDict[adminID2] = admin_advertStatus.waitForSendChatId


@dp.message_handler(commands="del")
async def stop(message: types.Message):
    if message.from_user.id == adminID1 or message.from_user.id == adminID2:
        if adminDict[adminID1] == admin_advertStatus.needToSendAdvert:
            advert.del_advert()
            adminDict[adminID1] = admin_advertStatus.noAdvert
            adminDict[adminID2] = admin_advertStatus.noAdvert
            await bot.send_message(message.from_user.id, "Реклама удалена")


@dp.message_handler(commands="stat")
async def stop(message: types.Message):
    if message.from_user.id == adminID1 or message.from_user.id == adminID2:
        await bot.send_message(
            message.from_user.id, f"Онлайн максимум - {max_connections}"
        )


@dp.message_handler(content_types=["text"])
async def echo_message(message: types.Message):
    await asyncio.sleep(0.5)
    if (
        (message.from_user.id == adminID1 or message.from_user.id == adminID2)
        and message.from_user.id in status
        and status[message.from_user.id] != users.virting_user
    ):
        if adminDict[adminID1] == admin_advertStatus.waitForSendChatId:
            advert.set_chat_id(message.text)
            await bot.send_message(
                message.from_user.id, "Отлично! Теперь присылайте текст рекламы"
            )
            adminDict[adminID1] = admin_advertStatus.waitForSendAdvert
            adminDict[adminID2] = admin_advertStatus.waitForSendAdvert

        elif adminDict[adminID1] == admin_advertStatus.waitForSendAdvert:
            advert.set_Advert(message.text)
            await bot.send_message(message.from_user.id, "Отлично! Реклама сохранена")
            adminDict[adminID1] = admin_advertStatus.needToSendAdvert
            adminDict[adminID2] = admin_advertStatus.needToSendAdvert
    else:
        if (
            message.from_user.id in status
            and status[message.from_user.id] == users.virting_user
        ):
            id = connections[message.from_user.id][0]
            await bot.send_message(id, message.text)


if __name__ == "__main__":
    executor.start_polling(dp)
