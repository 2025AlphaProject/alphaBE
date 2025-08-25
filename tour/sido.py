from django.conf import settings

s3_base_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}"

SIDO_LIST = [
    {
        "rnum": 1, 
        "code": "1", 
        "name": "서울", 
        "image": f"{s3_base_url}/image_82.png"
    },
    {
        "rnum": 2, 
        "code": "2", 
        "name": "인천", 
        "image": f"{s3_base_url}/image_83.png"
    },
    {
        "rnum": 3, 
        "code": "3", 
        "name": "대전", 
        "image": f"{s3_base_url}/image_84.png"
    },
    {
        "rnum": 4, 
        "code": "4", 
        "name": "대구", 
        "image": f"{s3_base_url}/image_85.png"
    },
    {
        "rnum": 5, 
        "code": "5", 
        "name": "광주", 
        "image": f"{s3_base_url}/image_86.png"
    },
    {
        "rnum": 6, 
        "code": "6", 
        "name": "부산", 
        "image": f"{s3_base_url}/image_87.png"
    },
    {
        "rnum": 7, 
        "code": "7", 
        "name": "울산", 
        "image": f"{s3_base_url}/image_88.png"
    },
    {
        "rnum": 8, 
        "code": "8", 
        "name": "세종",
        "image": f"{s3_base_url}/image_89.png"
    },
    {
        "rnum": 9, 
        "code": "31", 
        "name": "경기",
        "image": f"{s3_base_url}/image_90.png"
    },
    {
        "rnum": 10, 
        "code": "32", 
        "name": "강원",
        "image": f"{s3_base_url}/image_91.png"
    },
    {
        "rnum": 11, 
        "code": "33", 
        "name": "충북",
        "image": f"{s3_base_url}/image_92.png"
    },
    {
        "rnum": 12, 
        "code": "34", 
        "name": "충남",
        "image": f"{s3_base_url}/image_93.png"
    },
    {
        "rnum": 13, 
        "code": "35", 
        "name": "경북",
        "image": f"{s3_base_url}/image_94.png"
    },
    {
        "rnum": 14, 
        "code": "36", 
        "name": "경남",
        "image": f"{s3_base_url}/image_95.png"
    },
    {
        "rnum": 15, 
        "code": "37", 
        "name": "전북",
        "image": f"{s3_base_url}/image_96.png"
    },
    {
        "rnum": 16, 
        "code": "38", 
        "name": "전남",
        "image": f"{s3_base_url}/image_97.png"
    },
    {
        "rnum": 17, 
        "code": "39", 
        "name": "제주",
        "image": f"{s3_base_url}/image_98.png"
    },
]