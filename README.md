
# Another Telegram Photo Story bot

A lightweight bot that uses (MiniGPT-4)[https://arxiv.org/abs/2304.10592] and Llama LLMs to generate a story from a photo using user feedback.
It uses Google sheets to keep track of prompts and generated data.

## Code

- `constants.py` To set paths and API keys.
- `dataexport.py` Create a google sheet to keep track of the prompts and generation.
- `output_fun.py` Uses reportlab library to generate a PDF with the image and story.
- `prompts.py` Prompts for generating story and add feedback from the user.
- `utils.py` Call image description (MiniGPT-4 or ChatGPT).
- `main.py` Use functionality with a telegram bot.


## Usage

You need to add some API_KEYS in `constants.py`

Then you can run `main.py`


## Requirements

- `functions-framework==3.5.0`
- `python-telegram-bot==21.1.1`
- `replicate==0.28.0`
- `langchain==0.2.7`
- `langchain_community==0.2.7`
- `reportlab==4.2.2`
- `google-api-python-client==2.84.0`
- `google-auth-httplib2==0.1.1`
- `google-auth-oauthlib==1.2.0`
- `pandas==2.0.0`
- `testresources==2.0.1`
- `openai==1.35.13`
