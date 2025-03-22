import json

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from aiogram import F

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, types
from random import sample

from questions import QUESTIONS, ANIMALS

router = Router()


class Quiz(StatesGroup):
    quest = State()
    feadback = State()
    text_to_stuff = State()

    quiz_rezult = State()
    questions = State()


@router.message(Quiz.quest)
async def make_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    quiz_rezult, questions = data['quiz_rezult'], data['questions']

    if message.text.strip().lower() not in ['1', '2', '3', '4', 'начать']:
        await message.answer(f'Я Вас не понял \nОтветом могут быть только цифры от 1 до 4')
        return

    if message.text in ['1', '2', '3', '4']:
        if message.text == '1':
            quiz_rezult['amphibian'] += 1
        elif message.text == '2':
            quiz_rezult['reptile'] += 1
        elif message.text == '3':
            quiz_rezult['mammal'] += 1
        elif message.text == '4':
            quiz_rezult['bird'] += 1
        await state.update_data({'quiz_rezult': quiz_rezult})

    if not questions:
        await state.clear()
        win_category = max(quiz_rezult, key=quiz_rezult.get)
        for category, animals in ANIMALS.items():
            if category == win_category:
                win_animal = sample(animals, 1)[0]

                rezult_message = f'🫧 Вы можете стать опекуном этого милого создания и частью большого круга друзей Московского зоопарка\n' \
                                 f'🐾 Ваш возможный подопечный: <a href="{win_animal["url"]}">{win_animal["name"]}</a> 🐾 \n\n' \
                                 f'🫧 Подробнее о программе опекунства: ' \
                                 f'<a href="https://moscowzoo.ru/about/guardianship">«Клуб друзей зоопарка»</a>'

                await state.set_data({'rezult_name': win_animal['name']})
                kb = [
                        [InlineKeyboardButton(text='Попробовать ещё раз?', callback_data='replay')],
                        [InlineKeyboardButton(text='Связаться с сотрудником Зоопарка', callback_data='contact')],
                        [InlineKeyboardButton(text='Поделиться в VK', callback_data='replay',
                                              url=f'https://vk.com/share.php?url={win_animal["url"]}'
                                                  f'&title=@totem_zoo_bot\nВаше тотемное животное: {win_animal["name"]}'
                                                  f'&image={win_animal["photo"]}',)],
                        [InlineKeyboardButton(text='Оставить отзыв', callback_data='feadback')]
                ]
                inlinekb = InlineKeyboardMarkup(inline_keyboard=kb)

                await message.answer(f'Вы завершили викторину \n'
                                     f'Ваше тотемное животное: {win_animal["name"]}',
                                     reply_markup=types.ReplyKeyboardRemove())
                await message.answer_photo(photo=win_animal['photo'])

                await message.answer(rezult_message, parse_mode='HTML', reply_markup=inlinekb)

                return

    question = sample(questions, 1)[0]
    questions.pop(questions.index(question))
    answers = question['answers']
    await state. update_data({'questions': questions})
    builder = ReplyKeyboardBuilder()
    num = ['1', '2', '3', '4']
    for _ in num:
        builder.add(types.KeyboardButton(text=_))
    builder.adjust(4)

    await message.answer(
        f"{question['question']} \n"
        f"1) {answers[0]}\n"
        f"2) {answers[1]}\n"
        f"3) {answers[2]}\n"
        f"4) {answers[3]}\n",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )


@router.callback_query(F.data == 'replay')
async def replay(callback: types.CallbackQuery, state: FSMContext):
    await state.set_data(
        {'quiz_rezult': {
            'amphibian': 0,
            'reptile': 0,
            'mammal': 0,
            'bird': 0},
            'questions': QUESTIONS.copy()
        }
    )

    await state.set_state(Quiz.quest.state)
    kb = [[types.KeyboardButton(text='Начать')]]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    await callback.message.answer(f'Начнём?', reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == 'contact')
async def contact(callback: types.CallbackQuery, state: FSMContext):
    rezult_name = await state.get_data()
    buttons = [[types.KeyboardButton(text=f'🦉 Чат с сотрудником 🦉\n Результат викторины: \n{rezult_name["rezult_name"]}')]]
    kb = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    await callback.message.answer(f'Чтобы узнать больше о программе опекунства, '
                                  f'Вы можете связаться с нашим сотрудником Любовью: \n\n'
                                  f'✏   Telegram: @liubashai\n'
                                  f'✉   E-mail: lovella1202@mail.ru\n'
                                  f'📞   +7-9хх-ххх-хх-хх', reply_markup=kb)
    await state.set_state(Quiz.text_to_stuff.state)
    await callback.answer()


@router.message(Quiz.text_to_stuff)
async def text_to_stuff(message: types.Message, state: FSMContext):
    await message.copy_to(chat_id=1875707606, reply_markup=types.ReplyKeyboardRemove())
    await state.clear()


@router.callback_query(F.data == 'feadback')
async def feadback_state(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Quiz.feadback.state)
    await callback.message.answer(
        f'🫧 Напишите свои впечатления о нашем боте или свои предложения по его улучшению. \n\n'
        f'А мы постараемся сделать его удобнее для Вас 🐻‍❄')
    await callback.answer()


@router.message(Quiz.feadback)
async def feadback_add(message: types.Message, state: FSMContext):
    with open('feadbacks.json', 'r', encoding='utf8') as fb_file:
        fb = json.load(fb_file)
        with open('feadbacks.json', 'w', encoding='utf8') as new_fb_file:
            new = {
                'feadback': message.text,
                'user': message.from_user.username
            }
            fb.append(new)
            new_data = json.dumps(fb, indent=4, ensure_ascii=False)
            new_fb_file.write(new_data)

    await message.answer(f'Спасибо за Ваш отзыв! 🦉')
    await state.clear()