# prompts.py
from langchain_core.prompts import PromptTemplate

prompt_check = PromptTemplate(
    input_variables=["image_description"],
    template="""
You are an expert detective.
You can spot inconsistencies in an image description.
Say if there is an inconsistency or not and explain why.
Do not include any other text.

# Image description:
{image_description}

# Inconsistencies:
""",
)

prompt_fix_w_user_input = PromptTemplate(
    input_variables=["image_description", "user_feedback"],
    template="""
You are an expert image descriptor fixer.
You receive an image description which might have inconsistencies.
You also receive feedback from the user.
Improve the image description making changes incorporating the user feedback.
Do not include any other text.

# Image description:
{image_description}

# User feedback:
{feedback}

# Improved image description:
""",
)

prompt_fix_error = PromptTemplate(
    input_variables=["image_description", "inconsistencies"],
    template="""
You are an expert image descriptor fixer.
There is an image description which might have inconsistencies.
If there are no inconsistencies do not change the image description.
If there are inconsistencies, rewrite the image description without inconsistencies.
Do not include any other text.

# Image description:
{image_description}

# Inconsistencies:
{inconsistencies}

# Reconstructed image description:
""",
)

prompt_matching = PromptTemplate(
    input_variables=["characters", "names_and_descriptions"],
    template="""
You are an helpful assistant.
There is a list of characters.
There is a second list with the names and descriptions of the characters.
Combine the information and when there are inconsistencies follow the second list.
Do not include any other text.
One character per line.

# Characters:
{characters}

# Names and descriptions:
{names_and_descriptions}

# Match:
""",
)

prompt_characters = PromptTemplate(
    input_variables=["image_description"],
    template="""
You are an expert reader.
You can spot all the characters in a description.
Do not include any other text.
One character per line.

# Image description:
{image_description}

# Characters:
""",
)

prompt_story = PromptTemplate(
    input_variables=["image_description", "matching"],
    template="""
You recreate happy memories from image descriptions.
From the image description and the description of the characters write a short story of one paragraph.
Do not include any other text.
Use simple language.
Do not invent names or place names.


# Image description:
{image_description}

# Names and descriptions of characters:
{matching}

# Story:
""",
)

prompt_translator = PromptTemplate(
    input_variables=["story", "language"],
    template="""
You are an expert translator.
Translate the following story from English to the desired language.
Do not include any other text.

# Story:
{story}

# Language:
{language}

# Translation:
""",
)
