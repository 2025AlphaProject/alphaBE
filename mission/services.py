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
from tour.models import PlaceImages, TravelDaysAndPlaces, Place # 모델을 가져옵니다.

import cv2
import numpy as np
import requests
from skimage.metrics import structural_similarity as ssim
from tour.models import PlaceImages, TravelDaysAndPlaces, Place


class ImageSimilarity:
    def __init__(self, travel_id, place_id, mission_id):
        self.travel_id = travel_id
        self.place_id = place_id
        self.mission_id = mission_id
        self.img1 = self.get_user_image()
        self.img2 = self.get_reference_image()

    def get_user_image(self):
        """ 사용자가 촬영한 미션 이미지를 가져옵니다. """
        try:
            image_obj = TravelDaysAndPlaces.objects.get(id=self.travel_id, mission=self.mission_id)
            return cv2.imread(image_obj.image.path)
        except TravelDaysAndPlaces.DoesNotExist:
            print("사용자 이미지 조회 실패")
            return None

    def get_reference_image(self):
        """ 장소의 예시 이미지를 가져옵니다. """
        try:
            place_obj = Place.objects.get(id=self.place_id)
            image_obj = PlaceImages.objects.get(place=place_obj)
            return cv2.imread(image_obj.image.path)
        except (Place.DoesNotExist, PlaceImages.DoesNotExist):
            print("참고 이미지 조회 실패")
            return None

    def calculate_histogram_similarity(self):
        """ RGB 히스토그램 유사도 계산 """
        if self.img1 is None or self.img2 is None:
            return 0

        hist1 = cv2.calcHist([self.img1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([self.img2], [0], None, [256], [0, 256])

        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()

        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    def calculate_ssim(self):
        """ SSIM 유사도 계산 """
        if self.img1 is None or self.img2 is None:
            return 0

        gray1 = cv2.cvtColor(self.img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(self.img2, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))

        similarity_index, _ = ssim(gray1, gray2, full=True)
        return similarity_index

    def get_combined_similarity(self, weight_hist=0.5, weight_ssim=0.5):
        """ 히스토그램과 SSIM의 가중 평균 유사도 """
        hist_similarity = self.calculate_histogram_similarity()
        ssim_similarity = self.calculate_ssim()

        return (weight_hist * hist_similarity) + (weight_ssim * ssim_similarity)

    def get_similarity_score(self):
        """ 최종 유사도 점수 반환 """
        score = self.get_combined_similarity()
        return round(score * 100, 2)  # 0~100 범위로 변환

    def check_mission_success(self):
        """ 유사도 40% 이상이면 미션 성공, 이하면 실패 """
        score = self.get_similarity_score()
        return 1 if score >= 40 else 0  # 성공이면 1, 실패면 0 반환