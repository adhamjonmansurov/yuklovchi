import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from yt_dlp import YoutubeDL
from shazamio import Shazam
from pydub import AudioSegment

# ================== SOZLAMALAR ==================
TOKEN = "8307673011:AAGdw_6moCNUsD_sVDUSUgDUUVPFdA8kxbA"

BASE_DIR = r"D:\Bot"
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

FFMPEG_PATH = r"C:\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe"
AudioSegment.converter = FFMPEG_PATH
AudioSegment.ffmpeg = FFMPEG_PATH

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
# ===============================================

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ================== STATE ==================
class UserState(StatesGroup):
    WAIT_INPUT = State()
    WAIT_CHOICE = State()
# ==========================================

# ================== /start ==================
@dp.message_handler(commands=["start"])
async def start(message: types.Message, state: FSMContext):
    await state.set_state(UserState.WAIT_INPUT)
    await message.answer(
        "👋 Salom!\n\n"
        "🎥 Video yoki 🔗 YouTube / Instagram link tashla.\n"
        "Keyin nima qilishni tanlaysan 👇"
    )

# ================== INPUT ==================
@dp.message_handler(
    content_types=[types.ContentType.TEXT],
    state=UserState.WAIT_INPUT
)
async def get_input(message: types.Message, state: FSMContext):
    await state.update_data(source=message.text)

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🎥 Video yuklash", callback_data="video"),
        types.InlineKeyboardButton("🎵 Musiqa (MP3)", callback_data="audio"),
        types.InlineKeyboardButton("🎧 Shazam", callback_data="shazam"),
    )

    await state.set_state(UserState.WAIT_CHOICE)
    await message.answer("Nimani qilamiz?", reply_markup=kb)

# ================== CALLBACK ==================
@dp.callback_query_handler(state=UserState.WAIT_CHOICE)
async def process_choice(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    source = data.get("source")

    await callback.message.edit_text("⏳ Iltimos kuting...")

    # -------- VIDEO --------
    if callback.data == "video":
        ydl_opts = {
            "outtmpl": os.path.join(DOWNLOAD_DIR, "video.mp4"),
            "format": "best"
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([source])

        await callback.message.answer_video(
            open(os.path.join(DOWNLOAD_DIR, "video.mp4"), "rb"),
            supports_streaming=True
        )
        os.remove(os.path.join(DOWNLOAD_DIR, "video.mp4"))

    # -------- AUDIO --------
    elif callback.data == "audio":
        ydl_opts = {
            "outtmpl": os.path.join(DOWNLOAD_DIR, "audio.%(ext)s"),
            "format": "bestaudio",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([source])

        await callback.message.answer_audio(
            open(os.path.join(DOWNLOAD_DIR, "audio.mp3"), "rb")
        )
        os.remove(os.path.join(DOWNLOAD_DIR, "audio.mp3"))

    # -------- SHAZAM --------
    elif callback.data == "shazam":
        audio_path = os.path.join(DOWNLOAD_DIR, "shazam.mp3")

        ydl_opts = {
            "outtmpl": os.path.join(DOWNLOAD_DIR, "shazam.%(ext)s"),
            "format": "bestaudio",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([source])

        shazam = Shazam()
        result = await shazam.recognize_song(audio_path)

        if not result or "track" not in result:
            await callback.message.answer("❌ Qo‘shiq topilmadi")
        else:
            track = result["track"]
            await callback.message.answer(
                f"🎵 {track.get('title', 'Nomaʼlum')}\n"
                f"👤 {track.get('subtitle', 'Nomaʼlum')}"
            )

        if os.path.exists(audio_path):
            os.remove(audio_path)

    await state.set_state(UserState.WAIT_INPUT)

# ================== RUN ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
