from tempfile import TemporaryFile

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    PicklePersistence,
)

from telegram.helpers import escape_markdown
import random
import logging


from utils import read_and_rescale_image, get_image_description
from prompts import (
    prompt_check,
    prompt_fix_error,
    prompt_fix_w_user_input,
    prompt_characters,
    prompt_matching,
    prompt_story,
)
from prompts import prompt_translator
from constants import TELEGRAM_TOKEN, REPLICATE_API_KEY
from output_fun import base_to_PDF
from dataexport import export_pandas_df_to_sheets, create_sheet_and_drive

import os

os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_KEY

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

from constants import SHEETS_FILE_CREDENTIALS
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from constants import SAVE_TO_FOLDER_PATH


NAMES, PHOTO, FEEDBACK, STORY, ANALYZE, PREPHOTO, STORY_PDF, TRANSLATE_PDF = range(8)

# Create google sheet
credentials = service_account.Credentials.from_service_account_file(
    SHEETS_FILE_CREDENTIALS, scopes=SCOPES
)
spreadsheet_service = build("sheets", "v4", credentials=credentials)
drive_service = build("drive", "v3", credentials=credentials)

SHEET_ID = create_sheet_and_drive(spreadsheet_service, drive_service)

# Telegram functions


async def start_long(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation"""
    reply_keyboard = [["Single story", "Cancel"]]

    msg = """Hello My name is *Another Memory Photo Bot*, I can create stories from photos, reply _Single story_ to create a story from a single photo or _Cancel_ to stop"""
    await update.message.reply_markdown_v2(
        msg,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Continue?"
        ),
    )

    return PREPHOTO


async def prephoto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected type of story and asks for photo"""
    user = update.message.from_user
    story_type = update.message.text
    context.user_data["user_rnd_id"] = str(random.randint(1000, 9999))
    context.user_data["story_type"] = story_type
    logger.info("User %s selected %s", user.first_name, story_type)

    if story_type == "Single story":
        logger.info("Prephoto %s %s", user.first_name, update.message.text)
        await update.message.reply_text(
            "Please upload a photo.\n"
            "I will analyze it and I will ask you a couple of questions...",
            reply_markup=ReplyKeyboardRemove(),
        )
        return PHOTO
    return ConversationHandler.END


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the photo and asks for feedback"""

    await update.message.reply_text(
        "Receiving your photo...",
        allow_sending_without_reply=True,
    )

    user = update.message.from_user
    userid = (
        str(user.first_name)
        + "_"
        + str(user.id)[-3:-1]
        + "_"
        + context.user_data["user_rnd_id"]
    )
    photo_file = await update.message.photo[-1].get_file()
    path = SAVE_TO_FOLDER_PATH
    context.user_data["path"] = path

    logger.info("User %s uploaded a photo.", user.first_name)
    await photo_file.download_to_drive(path + "u_" + userid + "_photo")
    logger.info("Saved photo")

    with TemporaryFile() as custom_fobj:
        await photo_file.download_to_memory(custom_fobj)
        custom_fobj.seek(0)
        image = read_and_rescale_image(custom_fobj)
        logger.info("Read and scaled")

        await update.message.reply_markdown_v2(
            escape_markdown("I'm analyzing the photo, give me ", version=2)
            + "*1 minute*"
            + escape_markdown(" to complete ...", version=2),
            allow_sending_without_reply=True,
        )
        img_description = get_image_description(image)
        context.user_data["img_description"] = img_description
        logger.info("Description is:" + img_description)

        inconsistencies = chain_check.invoke({"image_description": img_description})
        context.user_data["inconsistencies"] = inconsistencies
        logger.info("Inconsistencies are:" + inconsistencies)

        fixed_inconsistencies = chain_fix_error.invoke(
            {"image_description": img_description, "inconsistencies": inconsistencies}
        )
        context.user_data["fixed_inconsistencies"] = fixed_inconsistencies
        logger.info("Fixed inconsistencies is:" + fixed_inconsistencies)

        msg = "Please answer with feedback about the description, for example:"
        ex1 = "The background is a garden not a forest"
        ex2 = "There are 3 people in the photo not 2"
        await update.message.reply_markdown_v2(
            "Here's a description of the image *"
            + escape_markdown(fixed_inconsistencies, version=2)
            + "* \n\n"
            + escape_markdown(msg, version=2)
            + "\n _*"
            + ex1
            + "*_ \n _*"
            + escape_markdown(ex2, version=2)
            + "*_",
            allow_sending_without_reply=True,
        )
        return FEEDBACK
    return ConversationHandler.END


async def names(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the names and asks for confirmation"""
    reply_keyboard = [["Yes", "/skip"]]

    user = update.message.from_user
    characters = context.user_data["characters"]
    namesanddescriptions = update.message.text

    await update.message.reply_text(
        "Ok, Thank you, let me add that information for the story...",
        allow_sending_without_reply=True,
    )

    context.user_data["namesanddescriptions"] = namesanddescriptions
    logger.info("Names of %s: %s", user.first_name, namesanddescriptions)

    matching = chain_matching.invoke(
        {"characters": characters, "names_and_descriptions": namesanddescriptions}
    )
    context.user_data["matching"] = matching
    logger.info("Matching of %s: %s", user.first_name, matching)

    await update.message.reply_text(
        "Let's generate the story or send /skip if you don't want to.",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Want to continue?",
        ),
    )

    return STORY


async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the feedback and asks for names"""
    feedback = update.message.text
    context.user_data["feedback"] = feedback

    await update.message.reply_text(
        "Ok, Thank you, let me pass that information... Now I'm going to check for people...",
        allow_sending_without_reply=True,
    )
    fixed_inconsistencies = context.user_data["fixed_inconsistencies"]
    image_description_w_feedback = chain_fix_w_user_input.invoke(
        {"image_description": fixed_inconsistencies, "feedback": feedback}
    )
    context.user_data["image_description_w_feedback"] = image_description_w_feedback
    logger.info("Feedback of %s: %s", update.message.from_user.first_name, feedback)

    characters = chain_characters.invoke(
        {"image_description": image_description_w_feedback, "feedback": feedback}
    )
    context.user_data["characters"] = characters
    logger.info("Characters of %s: %s", update.message.from_user.first_name, characters)

    msg = "I found some people in the photo:" + characters
    await update.message.reply_markdown_v2(
        escape_markdown(msg, version=2),
        allow_sending_without_reply=True,
    )

    msg = """Can you help me with additional information about the people I found?\n\n Example:"""
    ex1 = "The boy's name is ... and the man is his father named ..."
    await update.message.reply_markdown_v2(
        escape_markdown(msg, version=2) + " _" + escape_markdown(ex1, version=2) + "_",
    )

    return NAMES


async def story(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generates three versions of the stories and asks for a favourite"""

    chat_id = update.message.chat_id
    user = update.message.from_user

    await update.message.reply_text(
        "I'm working on it, please wait...",
        allow_sending_without_reply=True,
    )
    matching = context.user_data["matching"]
    image_description_w_feedback = context.user_data["image_description_w_feedback"]

    story = chain_story.invoke(
        {"image_description": image_description_w_feedback, "matching": matching}
    )
    context.user_data["story"] = story
    storyv2 = chain_storyv2.invoke(
        {"image_description": image_description_w_feedback, "matching": matching}
    )
    context.user_data["storyv2"] = storyv2
    storyv3 = chain_storyv3.invoke(
        {"image_description": image_description_w_feedback, "matching": matching}
    )
    context.user_data["storyv3"] = storyv3

    logger.info("Story of %s: %s", user.first_name, story)
    logger.info("Storyv2 of %s: %s", user.first_name, storyv2)
    logger.info("Storyv3 of %s: %s", user.first_name, storyv3)

    await update.message.reply_text(
        "These are your stories:", allow_sending_without_reply=True
    )

    await update.message.reply_markdown_v2(
        "1\. *" + escape_markdown(story, version=2) + "*",
        allow_sending_without_reply=True,
    )
    await update.message.reply_markdown_v2(
        "2\. *" + escape_markdown(storyv2, version=2) + "*",
        allow_sending_without_reply=True,
    )
    await update.message.reply_markdown_v2(
        "3\. *" + escape_markdown(storyv3, version=2) + "*",
        allow_sending_without_reply=True,
    )

    reply_keyboard = [["1", "2", "3"]]
    await update.message.reply_text(
        "Please, tell me which one you liked the most 1, 2 or 3",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, input_field_placeholder="Select an option"
        ),
    )

    return STORY_PDF


async def story_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generates a story in PDF"""
    user = update.message.from_user
    userid = (
        str(user.first_name)
        + "_"
        + str(user.id)[-3:-1]
        + "_"
        + context.user_data["user_rnd_id"]
    )
    chat_id = update.message.chat_id

    vselected = update.message.text
    photo_file = "u_" + userid + "_photo"
    path_photo = context.user_data["path"]
    path = SAVE_TO_FOLDER_PATH
    storiesnamefile = "story_u_" + userid + "_photo"
    if vselected == "1":
        story = context.user_data["story"]
        context.user_data["selected_story"] = "1"
    elif vselected == "2":
        story = context.user_data["storyv2"]
        context.user_data["selected_story"] = "2"
    elif vselected == "3":
        story = context.user_data["storyv3"]
        context.user_data["selected_story"] = "3"
    else:
        await update.message.reply_text("Something went wrong... Let's try again...")
        return STORY_PDF

    context.user_data["selected_story"] = story
    context.user_data["photo_file_final"] = photo_file

    base_to_PDF(path_photo, photo_file, story, path, storiesnamefile)
    logger.info("Saved PDF story")

    document = open(path + storiesnamefile + ".pdf", "rb")
    await context.bot.send_document(chat_id, document)

    reply_keyboard = [
        ["Cancel", "Spanish (Mexico)"],
        ["French", "Portuguese"],
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard)
    await update.message.reply_text(
        "Do you want to translate the story to another language?",
        reply_markup=markup,
    )

    return TRANSLATE_PDF


async def translate_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the info about the user and ends the conversation."""

    user = update.message.from_user
    userid = (
        str(user.first_name)
        + "_"
        + str(user.id)[-3:-1]
        + "_"
        + context.user_data["user_rnd_id"]
    )
    chat_id = update.message.chat_id
    vselected = update.message.text

    if vselected in ["Spanish (Mexico)", "Spanish", "French", "Portuguese"]:

        path_photo = context.user_data["path"]
        path = SAVE_TO_FOLDER_PATH
        logger.info("Selected language is:" + vselected)

        photo_file = context.user_data["photo_file_final"]
        storiesnamefile = "story_u_" + userid + "_photo"
        story = context.user_data["selected_story"]

        translation = chain_translator.invoke({"story": story, "language": vselected})
        logger.info("Translated story")

        base_to_PDF(path_photo, photo_file, translation, path, storiesnamefile)
        logger.info("Saved translated story")

        document = open(path + storiesnamefile + ".pdf", "rb")
        await context.bot.send_document(chat_id, document)

    await update.message.reply_text(
        "I hope you liked it! You can try again.",
        allow_sending_without_reply=True,
    )

    # create a dictionary selecting the following features of a list
    l = [
        "img_description",
        "matching",
        "story",
        "feedback",
        "storyv1",
        "storyv2",
        "storyv3",
        "selected_story",
        "selected_version",
        "namesanddescriptions",
        "inconsistencies",
        "photo_file_final",
    ]
    d = {}
    for i in l:
        if i in context.user_data.keys():
            d[i] = context.user_data[i]

    df = pd.DataFrame([d])
    export_pandas_df_to_sheets(spreadsheet_service, df, SHEET_ID)
    logger.info("Saved data to sheets")

    for i in l:
        if i in context.user_data.keys():
            del context.user_data[i]

    return ConversationHandler.END


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the photo and asks for a location."""
    user = update.message.from_user
    logger.info("User %s did not send a photo.", user.first_name)
    await update.message.reply_text("Without a photo I cannot do much. Sorry.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


from langchain.chains import LLMChain
from langchain_community.llms import Replicate
from langchain_core.prompts import PromptTemplate

llama8b = Replicate(
    model="meta/meta-llama-3-8b-instruct",
    model_kwargs={
        "temperature": 0.75,
        "min_tokens": 128,
        "max_tokens": 1024,
        "top_p": 0.9,
    },
)

llama8b_v2 = Replicate(
    model="meta/meta-llama-3-8b-instruct",
    model_kwargs={
        "temperature": 0.3,
        "min_tokens": 128,
        "max_tokens": 1024,
        "top_p": 0.9,
    },
)

llama8b_v4 = Replicate(
    model="meta/meta-llama-3-8b-instruct",
    model_kwargs={
        "temperature": 0.3,
        "min_tokens": 128,
        "max_tokens": 1024,
        "top_p": 0.7,
    },
)


llama70b = Replicate(
    model="meta/meta-llama-3-70b-instruct",
    model_kwargs={
        "temperature": 0.75,
        "min_tokens": 128,
        "max_tokens": 1024,
        "top_p": 0.9,
    },
)

# Create prompts with LLMs
chain_check = prompt_check | llama8b
chain_fix_error = prompt_fix_error | llama70b
chain_fix_w_user_input = prompt_fix_w_user_input | llama8b
chain_characters = prompt_characters | llama8b
chain_matching = prompt_matching | llama8b
chain_story = prompt_story | llama8b
chain_storyv2 = prompt_story | llama8b_v2
chain_storyv3 = prompt_story | llama8b_v4
chain_translator = prompt_translator | llama70b

# Enable data
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

persistence = PicklePersistence(filepath="conversationbot")
application = (
    Application.builder().token(TELEGRAM_TOKEN).persistence(persistence).build()
)

# Add conversation handler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_long)],
    states={
        PHOTO: [
            MessageHandler(filters.PHOTO, photo),
            CommandHandler("skip", skip_photo),
        ],
        NAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, names)],
        FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback)],
        STORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, story)],
        STORY_PDF: [MessageHandler(filters.TEXT & ~filters.COMMAND, story_pdf)],
        PREPHOTO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, prephoto),
            CommandHandler("Cancel", skip_photo),
        ],
        TRANSLATE_PDF: [MessageHandler(filters.TEXT & ~filters.COMMAND, translate_pdf)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(conv_handler)

application.run_polling(allowed_updates=Update.ALL_TYPES)
