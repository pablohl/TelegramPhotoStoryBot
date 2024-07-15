# utils.py
import base64
from io import BytesIO
import replicate
from openai import OpenAI
from constants import OPENAI_API_KEY

MODEL = "gpt-4o"


# Get description of an image
def get_image_description(image, chatGPT=False):

    if chatGPT:  # We can use CahatGPT
        client = OpenAI(api_key=OPENAI_API_KEY)
        image.seek(0)
        base64_image = base64.b64encode(image.read()).decode("utf-8")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Give a short description of the image.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ],
                },
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content
    else:  # We can use MiniGPT
        output = replicate.run(
            "daanelson/minigpt-4:e447a8583cffd86ce3b93f9c2cd24f2eae603d99ace6afa94b33a08e94a3cd06",
            input={
                "image": image,
                "top_p": 0.5,
                "prompt": "Describe the image as detailed as possible",
                "num_beams": 5,
                "max_length": 2000,
                "temperature": 1,
                "max_new_tokens": 1500,
                "repetition_penalty": 1,
            },
        )
    return output

    # Let's read an image get the dimensions


def read_and_rescale_image(path):
    from PIL import Image

    image = Image.open(path)
    width, height = image.size
    # rescale to fit within a page
    if width > 768 or height > 1024:
        scale = min(768 / width, 1024 / height)
        width = int(width * scale)
        height = int(height * scale)
        image = image.resize((width, height))
    # Create a data uri of base64
    afile = BytesIO()
    image.save(afile, "JPEG")
    return afile
