from pathlib import Path
from openai import OpenAI
from pydub import AudioSegment
import os
import json
from moviepy.editor import ImageSequenceClip, AudioFileClip, concatenate_videoclips
import base64
from PIL import Image
import io

os.environ["OPENAI_API_KEY"] = '-'

def generate_audio(transcript_path, output_path="speech.mp3"):
    client = OpenAI()

    # Read the transcript from the file
    try:
        with open(transcript_path, 'r') as file:
            transcript = file.read()

        if not transcript:
            raise ValueError("Transcript file is empty.")

        speech_file_path = Path(output_path)
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=transcript
        )
        
        response.stream_to_file(speech_file_path)
        return transcript
    except FileNotFoundError:
        print(f"Error: File {transcript_path} not found.")
    except ValueError as ve:
        print(ve)
        
def get_audio_length(file_path):
    audio = AudioSegment.from_mp3(file_path)
    return len(audio) / 1000.0

def generate_transcript(prompt,approx_time):
    '''call gpt4'''
    return transcript

def timestamp_transcript(transcript):
    return

def generate_img_prompts(transcript, audio_time):
    client = OpenAI()
    prompt_list = client.chat.completions.create(
    model="gpt-4-1106-preview",
    response_format={ "type": "json_object" },
    seed=0,
    messages=[
        {"role": "system", "content": '''user will uplaod audio transcribe, after transcribing total audio lenght is {} seconds. generate a list of tuples
         (x,y) where x is detailed Dalle 3 image prompt relevant to the portion of the transcript , and y is the
         timestamp [a,b] where a is start time and b is end time during which that img relevant to transcript 
         shall be shown. make sure to consider start and end part of transcription as in initial title and ending
         images for video keep short time around 5s for them. make sure time intervals are lesser than total audio lenght.
         . output in json format '''.format(audio_time)},
        {"role": "user", "content": "{}".format(transcript)}
    ]
    )
    #print(prompt_list.choices[0].message.content)
    return prompt_list.choices[0].message.content

def generate_dalle_images(json_input):
    client = OpenAI()
    data = json_input
    key_name = list(data)[0]
    img_prompts = [item['prompt'] for item in data[key_name]]
    timestamps = [item['timestamp'] for item in data[key_name]]

    generated_images = []
    for prompt in img_prompts:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
            response_format='b64_json'
            )
        image_data = response.data[0].b64_json
        #print('img_res',type(image_data),image_data[:100])
        generated_images.append(image_data)

    return generated_images, timestamps

def create_video(image_b64s, audio_file, timestamps):
    clips = []
    for i, image_b64 in enumerate(image_b64s):
        # Convert base64 to image
        image_data = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_data))
        image_file = f'temp_image_{i}.png'
        image.save(image_file)

        # Create a clip for each image
        duration = timestamps[i][1] - timestamps[i][0]
        clip = ImageSequenceClip([image_file], durations=[duration])
        clips.append(clip)
    # Concatenate all clips and add audio
    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(audio_file)
    final_video = video.set_audio(audio)
    final_video.write_videofile("output_video.mp4", fps=24)
    

def get_transcript_string(path='transcript.txt'):
    with open(path, 'r') as file:
        transcript = file.read()
    if not transcript:
        raise ValueError("Transcript file is empty.")
    return transcript

def convert_json_string(json_string):
    try:
        json_object = json.loads(json_string)
        return json_object
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

if __name__=="__main__":
    generate_audio('transcript.txt')
    transcript = get_transcript_string()
    audio_time=get_audio_length('speech.mp3')
    prompt_list = generate_img_prompts(transcript,audio_time)
    img_json=convert_json_string(prompt_list)
    print(img_json)
    a,b = generate_dalle_images(img_json)
    print(b)
    create_video(a,'speech.mp3',b)
