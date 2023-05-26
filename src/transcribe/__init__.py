import os
import sys
from pathlib import Path

from datetime import datetime
import whisper

import os
import openai

from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

user_profile = os.environ['USERPROFILE']
SEP = os.path.sep


def summarize_txt(txt):

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="Summarize the following text with one paragraph having not more than 50 words:\n\n" + txt,
        temperature=0,
        max_tokens=64,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

    return response.choices[0].text


def extract_txt(audio_path):
    # Transcribe the audio using OpenAI Whisper API
    model_opts = [
        "tiny",
        "base",
        "small",
        "medium",
        "large"
    ]

    model = whisper.load_model(
        name=model_opts[2]
    )
    result = model.transcribe(audio_path, verbose=False)
    txt = result['text']
    return txt


def save_transcription(audio_path, txt, summarize = False):
    
    if summarize:
        txt = summarize_txt(txt)
    
    # Save the transcription
    file_name = audio_path.split(SEP)[-1].split(".")[0] + ".txt"
    
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(txt)
        
    return file_name


def main():
    """This method extract the audio from a video
    The transcriptions API takes as input the audio file you want to transcribe and the desired output file format 
    for the transcription of the audio. They currently support multiple input and output file formats.
    """

    audio_path = sys.argv[1] or input("Enter the audio file path: ")
    txt = extract_txt(audio_path)
    file_name = save_transcription(audio_path, txt)
    
    print(
        f"---------------------------------------------------------------------------------------------------------\n"
        f"Transcribed: {audio_path} to {file_name}"
        f"\n---------------------------------------------------------------------------------------------------------\n"
    )


if __name__ == '__main__':
    main()
