from django.test import TestCase
from mission.models import Mission

# Create your tests here.


class TestMission(TestCase):
    def setUp(self):
        # 임의로 미션을 생성합니다.
        Mission.objects.create(
            content='예시 사진과 유사하게 사진찍기'
        )
        Mission.objects.create(
            content='손 하트 만든 상태로 사진찍기'
        )
    def test_mission(self):
        """
        Performs the necessary actions to test a mission within the context of a
        given functionality or implementation. This method is typically used to
        validate the proper behavior and operation of a mission as part of broader
        testing routines.

        Raises:
            Exception: If any issue or state failure occurs during the testing of
            the mission.
        """
        end_point = '/mission/list/'
        # get Test
        response = self.client.get(end_point)
        self.assertEqual(response.status_code, 200)
        print(response.json())
