"""
    ISSUE - #36, ASSIGNEE - dbsthf04
    이 파일에 CV 코드를 작성합니다.
    함수 혹은 클래스 형태로 코드를 작성하여 Views.py에서 클래스나 함수 형태로 사용하여 결과값을 받을 수 있도록 해주시기 바랍니다.

    <주의 사항>
        1. 모듈 설치시 'pip install <모듈 이름>'으로 설치 후 반드시 'pip freeze > requirements.txt' 명령어를 입력하여 주시기 바랍니다.
        2. 파이참 IDE 사용시 가상환경이 자동으로 설정되나, vscode와 같은 IDE를 사용하신다면 반드시 초기에 가상환경 설정 후
        'pip install -r requirements.txt'를 해주시기 바랍니다.
        3. 반드시 git flow 전략을 따르도록 하며, feature/#<이슈 번호>-<브랜치 이름> 형식의 브랜치를 파서 진행해주세요
        4. 풀 리퀘스트를 생성할 때 source branch를 develop, target branch를 작업 브랜치로 해서 풀리퀘 생성해주세요.
        5. 반드시 코드 리뷰어는 PM으로 해놓습니다.
    TODO pip freeze > requirements.txt 명령어 반드시 입력

    <추가 인지 사항>
        1. 미션에 해당하는, 개인이 촬영한 이미지는 TravelDaysAndPlaces.objects.get(id='여행 번호', mission='미션 번호')로 가져옵니다.
        2. 장소 예시 이미지는 PlaceImages.objects.get(place=Place.objects.get(id='여행 장소 번호'))
        3. 여행 장소 번호, 여행 번호, 미션 번호는 함수나 클래스의 '입력값' 즉, 인수로 사용됩니다.
"""
# from tour.models import PlaceImages, TravelDaysAndPlaces, Place # 모델을 가져옵니다.

import cv2
import os
from ultralytics import YOLO
import numpy as np
import requests
from skimage.metrics import structural_similarity as ssim
from tour.models import PlaceImages, TravelDaysAndPlaces, Place
import logging
from config.settings import APP_LOGGER
from django.conf import settings

logger = logging.getLogger(APP_LOGGER)


class ImageSimilarity:
    def __init__(self, travel_id, place_id, mission_id):
        self.travel_id = travel_id
        self.place_id = place_id
        self.mission_id = mission_id
        self.img1 = self.get_user_image()
        self.img2 = self.get_reference_image()

    @staticmethod
    def get_image_from_url(url):
        """ URL로부터 이미지를 가져옵니다. """
        try:
            # 이미지 URL로부터 데이터 가져오기
            response = requests.get(url)
            # 응답이 정상적이면 이미지 데이터를 NumPy 배열로 변환
            if response.status_code == 200:
                img_array = np.array(bytearray(response.content), dtype=np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)  # 이미지 디코딩
                return img
            else:
                logger.error("Failed Image Request")
                return None
        except Exception as e:
            logger.error(f"Image Download Error {e}")
            return None

    def get_user_image(self):
        """ 사용자가 촬영한 미션 이미지를 가져옵니다. """
        try:
            # TravelDaysAndPlaces에서 이미지 객체를 찾고 이미지 경로를 가져옵니다.
            image_obj = TravelDaysAndPlaces.objects.get(id=self.travel_id, mission=self.mission_id)
            # 이미지가 실제로 존재한다면, cv2를 사용하여 이미지 파일을 읽어들입니다.
            if image_obj.mission_image:
                image_path = image_obj.mission_image.url
                return cv2.imread(image_path)
            else:
                logger.warning("There is no mission image")
                return None
        except TravelDaysAndPlaces.DoesNotExist:
            logger.error("Failed to get user image. Mission image does not exist.")
            return None

    def get_reference_image(self):
        """ 장소의 예시 이미지를 가져옵니다. """
        try:
            place_obj = Place.objects.get(id=self.place_id)
            image_obj = PlaceImages.objects.get(place=place_obj)
            image_url = image_obj.image_url  # 이미지 URL 가져오기
            return self.get_image_from_url(image_url)
        except (Place.DoesNotExist, PlaceImages.DoesNotExist):
            logger.error("Failed to get reference image.")
            return None

    def calculate_histogram_similarity(self):
        """ RGB 히스토그램 유사도 계산 """
        if self.img1 is None or self.img2 is None: # 이미지가 None인 경우, 유사도 0 반환
            return 0

       # 두 이미지의 RGB 히스토그램을 계산
        hist1 = cv2.calcHist([self.img1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([self.img2], [0], None, [256], [0, 256])

        # 히스토그램 정규화
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()

        # 두 히스토그램의 유사도를 비교하고, 상관계수를 반환
        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    @property
    def calculate_ssim(self):
        """ SSIM 유사도 계산 """
        if self.img1 is None or self.img2 is None:
            return 0

        # 이미지를 그레이스케일로 변환하여 구조적 유사도를 계산
        gray1 = cv2.cvtColor(self.img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(self.img2, cv2.COLOR_BGR2GRAY)

        # 두 이미지의 크기를 맞추기 위해  첫 번째 이미지(유저)를 두 번째 이미지(예시사진)의 크기로 리사이즈
        gray1 = cv2.resize(gray1, (gray2.shape[1], gray2.shape[0]))

        # ssim 함수는 두 이미지를 비교하여 구조적 유사도를 계산합니다.
        similarity_index, _ = ssim(gray1, gray2, full=True)
        return similarity_index

    def get_similarity_score(self, weight_hist=0.5, weight_ssim=0.5):
        """ 히스토그램과 SSIM의 가중 평균 유사도 """
        hist_similarity = self.calculate_histogram_similarity()
        ssim_similarity = self.calculate_ssim

        # 가중 평균 유사도 계산
        score = (weight_hist * hist_similarity) + (weight_ssim * ssim_similarity)

        return round(score * 100, 2) # 최종 유사도 반환(0~100 범위로 변환)

    def check_mission_success(self):
        """ 유사도 40% 이상이면 미션 성공, 이하면 실패 """
        score = self.get_similarity_score()
        return 1 if score >= 20 else 0  # 성공이면 1, 실패면 0 반환

"""테스트용 코드 """
# if __name__ == "__main__":
#     similarity_checker = ImageSimilarity()
#     print(f"유사도 점수: {similarity_checker.get_similarity_score()}%")

#     print("미션 성공 여부:", "성공" if similarity_checker.check_mission_success() else "실패")

"""

위 테스트용 코드를 기반으로 이름을 정한다고 가정
자세한 기능은 코드 참조

similarity_checker = ImageSimilarity()
'similarity_checker.check_mission_success()' 이거 실행하면 알아서 됨

1.  클래스의 객체가 생성되면서 
    self.img1은 'get_user_image()' 호출
    self.img2는 get_reference_image() 호출
2.  get_user_image() 호출
    • 사용자가 올린 이미지를 가져오는 함수
3.  get_reference_image() 호출
	• 장소의 예시사진 url을 받아오는 함수
	• get_image_from_url()을 호출
4.  get_image_from_url() 호출
    • get_reference_image()에서의 url로 이미지를 다운하는 함수
    
similarity_checker.check_mission_success()을 실행시 차례대로 함수 호출하고 반환됨

5.  check_mission_success() 호출
    • 사진 유사도 점수를 보고 미션 성공 여부 판단
    • get_similarity_score() 호출
6.  get_similarity_score() 호출
    • 최종 유사도 반환
    • 히스토그램과 ssim 방식의 각 유사도를 평균으로 합한 유사도 계산
    •  calculate_histogram_similarity() 호출
    •  calculate_ssim() 호출

7.  calculate_histogram_similarity() 호출
    •  두 이미지의 히스토그램을 계산하여 유사도 측정
8.  calculate_ssim() 호출
    •  두 이미지를 전처리 후 구조적 유사도 측정
저 역순으로 다시 값 return 하여 유사도 구함 
     
"""

class ObjectDetection:
    """
    - 커스텀 학습한 best.pt 모델로 handheart, peace, smile 인식
    - COCO pretrained yolov8n.pt 모델로 person 인식
    - 주어진 미션 문구에 따라 객체 검출 성공 여부를 판단
    """
    def __init__(self):
        # 모델 경로 설정
        custom_model_path = os.path.join(settings.MODEL_DIR, "best.pt")
        person_model_path = os.path.join(settings.MODEL_DIR, "yolov8n.pt")

        # YOLO 모델 로드
        self.model_custom = YOLO(custom_model_path)
        self.model_person = YOLO(person_model_path)

        # 커스텀 모델 클래스 이름
        self.class_names_custom = ['handheart', 'peace', 'smile']

    def detect_and_check(self, image_path, mission_content):
        """
        :param image_path: 검증할 이미지 파일 경로 (절대경로 또는 MEDIA 경로 기반)
        :param mission_content: 미션 문구 (ex: '손가락 하트를 하고 사진을 찍어보세요')
        :return: 성공 여부 (True/False)
        """

        # 이미지 읽기
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"이미지를 열 수 없습니다: {image_path}")

        # 객체 카운트 초기화
        counts = {name: 0 for name in self.class_names_custom}
        counts['person'] = 0

        # 커스텀 모델로 handheart, peace, smile 탐지
        results_custom = self.model_custom(image, conf=0.5)
        for result in results_custom:
            for box in result.boxes:
                cls_idx = int(box.cls.item())
                if 0 <= cls_idx < len(self.class_names_custom):
                    cls_name = self.class_names_custom[cls_idx]
                    counts[cls_name] += 1

        # 기본 모델로 person 탐지
        results_person = self.model_person(image, conf=0.5, classes=[0])  # 0번 class = person
        for result in results_person:
            for box in result.boxes:
                counts['person'] += 1

        # 미션에 맞게 성공 여부 판정
        return self.check_mission(mission_content, counts)

    def check_mission(self, mission_content, counts):
        """
        미션 내용에 따라 필요한 객체가 검출되었는지 판단
        """

        mission_requirements = {
            "손가락 하트를 하고 사진을 찍어보세요": ["handheart"],
            "브이 포즈로 사진을 찍어보세요": ["peace"],
            "여러분이 사진에 꼭 등장해야 해요!": ["person"],
        }
        required_objects = mission_requirements.get(mission_content, [])

        return all(counts.get(obj, 0) >= 1 for obj in required_objects)