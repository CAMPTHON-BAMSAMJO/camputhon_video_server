from openai import OpenAI
import json
import re
from pydantic import BaseModel
import boto3
from PIL import Image
import requests 
import ex2copy

class ComponentRequest(BaseModel):
    id: int
    day: str
    sex: str
    start_time: str
    end_time: str
    activity: str
    location: str
    content: str

with open('./secret.json') as f:
    secrets = json.loads(f.read())
    
SECRET_KEY = secrets['API_Key']
CREDENTIALS_ACCESS_KEY = secrets['S3_ACCESS']
CREDENTIALS_SECRET_KEY = secrets['S3_SECRETE']
BUCKET_NAME = secrets['BUCKET_NAME']

client = OpenAI(
    api_key=SECRET_KEY,
)

# S3 연결 준비
client_s3 = boto3.client(
    's3',
    aws_access_key_id=CREDENTIALS_ACCESS_KEY,
    aws_secret_access_key=CREDENTIALS_SECRET_KEY
)


def generation_summary(request: ComponentRequest):
    
    gpt_version ='gpt-4-turbo'

    system = '내용을 정확히 3문장으로 일기에 쓰듯이 요약해줘. 요약할때 말투는 무조건 ~했다 와 같은 말투로 해. 결과물은 json 형식으로 {title : 제목, summary : 요약문}과 같은 형식으로 전달해줘'

    text = '나는 대학생 학교를 다니는 ' + request.sex + '인데, ' + request.day + '에 ' + request.start_time + '부터 ' + request.end_time + '까지 ' + request.location + '에서 ' +  request.activity + '를 했어.' + '그리고 ' + request.content

    response_sum = client.chat.completions.create(
        model=gpt_version,  # 또는 다른 모델을 사용
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
    )

    response = response_sum.json()
    response = json.loads(response)
    response = response["choices"][0]["message"]['content']

    print(response)

    return response

def generate_TTS(text, request_id, sentence_num):
    print("generate")
    try:
        response_tts = client.audio.speech.create(
            model="tts-1-hd",
            speed=1,
            voice="alloy",
            input=text,
        )
        print(response_tts)  # 응답 객체 전체 출력

        file_name = f'sentence_{sentence_num}.mp3'
        print(file_name)
        folder_name = str(request_id)
        print(folder_name)
        file_path = f'./resource/{file_name}'
        print(file_path)

        # 바이너리 데이터 추출
        audio_data = response_tts.read()
        if not audio_data:
            print("No audio data found in response.")
            return None
        
        print("Writing audio data to file.")
        with open(file_path, 'wb') as f:
            f.write(audio_data)

        # print("upload")
        # client_s3.upload_file(file_path, BUCKET_NAME, f'{folder_name}/{file_name}')
        # return response_tts
    except Exception as e:
        print(f"An error occurred during TTS generation: {e}")
        return None

def generate_image(text, request, sentence_num):
    print("generate image")
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"Illustration of {text} 참고로 나는 {request.sex}야",
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        
        print(image_url)  # 이미지 생성 응답 출력

        file_name = f'img_{sentence_num}.png'
        print(file_name)
        folder_name = str(request.id)
        print(folder_name)
        file_path = f'./resource/{file_name}'
        print(file_path)

        # 이미지 데이터 다운로드 및 저장
        image_data = requests.get(image_url).content
        if not image_data:
            print("No image data found in response.")
            return None

        print("Writing image data to file.")
        with open(file_path, 'wb') as f:
            f.write(image_data)

        with Image.open(file_path) as img:
            width, height = img.size
            target_width = 1024
            target_height = int(target_width * 12 / 9)

            # 새 캔버스를 생성하고, 원본 이미지를 중앙에 배치
            new_img = Image.new("RGB", (target_width, target_height), (255, 255, 255))
            new_img.paste(img, ((target_width - width) // 2, (target_height - height) // 2))
            new_img.save(file_path)

        print("upload image")
        # client_s3.upload_file(file_path, BUCKET_NAME, f'{folder_name}/{file_name}')
        return image_url
    except Exception as e:
        print(f"An error occurred during image generation: {e}")
        return None

def SeperateSentence(request: ComponentRequest):
    response = generation_summary(request)

    try:
        response = json.loads(response)

        summary_total = response['summary']
        summarys = re.sub(r'다\. ','다.\n',summary_total )
        summarys = summarys.split('\n')
        print(summarys)
        print(len(summarys))

        if len(summarys) != 3:
            raise
        summary_dic = {f'sentence_{i}' : summary for i,summary in enumerate(summarys)}

        summary_dic['sentence_total'] = summary_total

        tts = [generate_TTS(summary, request.id, i) for i, summary in enumerate(summarys)]

        images_url = [generate_image(summary, request, i) for i, summary in enumerate(summarys)]

        ex2copy.generate_video()

        client_s3.upload_file("./resource/final_output.mp4", BUCKET_NAME, f'{request.id}.mp4')
        print('upload mp3')

    except Exception as e:
        SeperateSentence(request)
        return None
        
    # return title, summary_dic, tts, images






