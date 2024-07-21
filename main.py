import os
import sys
from fastapi import FastAPI
from pydantic import BaseModel

import boto3

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import Generate

# AWS S3 설정
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = "kkm-shortform-resource"

class ComponentRequest(BaseModel):
    id: int
    day: str
    sex: str
    start_time: str
    end_time: str
    activity: str
    location: str
    content: str

# S3 클라이언트 생성
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

app = FastAPI()

@app.get("/ttest")
async def test(request: ComponentRequest):
    print("generate ai resource")
    Generate.SeperateSentence(request)


@app.get("/test")
async def health_check():
    return {"code": 200, "message": "success", "data": None}

# 메인 함수
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# 스프링에서 값을 받아 아이디 생성하고 아이디랑 같이 여기로 요청 보냄