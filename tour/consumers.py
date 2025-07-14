import json
from channels.generic.websocket import AsyncWebsocketConsumer
from config.celery import app
from config.settings import PUBLIC_DATA_PORTAL_API_KEY, APP_LOGGER
from services.tour_api import *
import urllib.parse
import logging
logger = logging.getLogger(APP_LOGGER)

class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        ##query_string##
          - user_id: string (required)
          - areaCode: string (required)
          - sigunguName: string (optional)
          - categoryName: string (comma-separated, required)
          - unique_code: string (optional)
        """
        query_string = self.scope['query_string'].decode()
        params = urllib.parse.parse_qs(query_string)
        self.user_id = params.pop('user_id', [None])[0]
        self.unique_code = params.pop('unique_code', [""])[0]
        self.user_id = self.user_id + '_' + self.unique_code if self.unique_code else self.user_id

        if self.user_id is None:
            await self.close()
            return

        # 그룹 가입
        logger.info(f'channel_id: {self.user_id} 웹소켓 가입')
        await self.channel_layer.group_add(self.user_id, self.channel_name)
        await self.accept()

        # 파라미터 파싱
        areaCode = params.pop('areaCode', [None])[0]
        sigunguName = params.pop('sigunguName', [None])[0]
        categoryName = params.pop('categoryName', [None])[0]

        if areaCode is None or categoryName is None:
            await self.send(text_data=json.dumps({
                'state': 'ERROR',
                'Message': '필수 파라미터 중 일부가 없습니다.'
            }, ensure_ascii=False))
            return

        # 시군구 코드 파싱
        tour = TourApi(MobileOS=MobileOS.ANDROID, MobileApp='AlphaProject2025', service_key=PUBLIC_DATA_PORTAL_API_KEY)
        sigunguCodes = None
        if sigunguName:
            sigunguNames = sigunguName.split(',')
            sigunguCodes = []
            for each in sigunguNames:
                sigunguCode = tour.get_sigungu_code(areaCode, each)
                if sigunguCode is None:
                    await self.send(text_data=json.dumps({
                        'state': 'ERROR',
                        'Message': '해당 시군구 이름에 대응되는 코드를 가져올 수 없습니다. 시군구 이름을 다시 한번 확인 바랍니다.'
                    }, ensure_ascii=False))
                    return
                sigunguCodes.append(sigunguCode)

        # categoryName → 리스트로 변환 후 task 호출
        categoryNames = categoryName.split(',')
        task_result = app.send_task(
            'tour.tasks.get_recommended_place_by_category_task',
            args=[self.user_id, areaCode, categoryNames, sigunguCodes, Arrange.TITLE_IMAGE.value, self.user_id]  # ← 추가됨
        )

        await self.send(text_data=json.dumps({
            'state': 'OK',
            'Message': {
                'task_id': task_result.task_id,
            }
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.user_id, self.channel_name)

    async def task_update(self, event):
        # celery 컨테이너에서 보낸 메시지를 클라이언트로 전송
        await self.send(text_data=json.dumps(event["message"], ensure_ascii=False))

    async def receive(self, text_data=None, bytes_data=None):
        """
        재시도를 위한 메시지입니다.
        """
        data = json.loads(text_data)
        user_id = data.get("user_id", None)
        areaCode = data.get("areaCode", None)
        sigunguName = data.get("sigunguName", None)
        unique_code = data.get("unique_code", "")  # 웹소켓 통신을 위한 고유 번호를 가져옵니다.
        categoryName = data.get("categoryName", None)
        user_id = user_id + '_' + unique_code if unique_code else user_id

        if user_id is None or areaCode is None or categoryName is None:
            await self.send(text_data=json.dumps({
                'state': 'ERROR',
                'Message': '필수 파라미터 중 일부가 없거나 잘못되었습니다.'
            }, ensure_ascii=False))
            return

        # 시군구 코드 파싱
        tour = TourApi(MobileOS=MobileOS.ANDROID, MobileApp='AlphaProject2025', service_key=PUBLIC_DATA_PORTAL_API_KEY)
        sigunguCodes = None
        if sigunguName:
            sigunguNames = sigunguName.split(',')
            sigunguCodes = []
            for each in sigunguNames:
                sigunguCode = tour.get_sigungu_code(areaCode, each)
                if sigunguCode is None:
                    await self.send(text_data=json.dumps({
                        'state': 'ERROR',
                        'Message': '해당 시군구 이름에 대응되는 코드를 가져올 수 없습니다. 시군구 이름을 다시 한번 확인 바랍니다.'
                    }, ensure_ascii=False))
                    return
                sigunguCodes.append(sigunguCode)

        # 카테고리 파라미터를 리스트로 변환
        categoryNames = categoryName.split(',')

        task_result = app.send_task(
            'tour.tasks.get_recommended_place_by_category_task',
            args=[user_id, areaCode, categoryNames, sigunguCodes, Arrange.TITLE_IMAGE.value, user_id]  # ← 추가됨
        )

        await self.send(text_data=json.dumps({
            'state': 'OK',
            'Message': {
                'task_id': task_result.task_id,
            }
        }))
