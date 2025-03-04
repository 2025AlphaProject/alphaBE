import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from config.celery import app
from config.settings import PUBLIC_DATA_PORTAL_API_KEY
from .modules.tour_api import *
import urllib.parse

class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        ##query_string##
          - user_id: string (required)
          - areaCode: string (required)
          - sigunguName: string (required)
          - contentTypeId: string (required)
        """
        query_string = self.scope['query_string'].decode() # 쿼리 스트링을 불러들입니다.
        params = urllib.parse.parse_qs(query_string) # 쿼리 스트링을 파라미터로 변환합니다.
        self.user_id = params.pop('user_id', [None])[0] # user 고유 sub를 가져옵니다.

        if self.user_id is None:
            await self.close()
            return

        # 웹소켓 그룹에 가입
        await self.channel_layer.group_add(self.user_id, self.channel_name) # user_id를 그룹 이름으로 하고 웹소켓에 가입합니다.
        await self.accept() # 웹소켓 연결

        # 요청을 celery task로 보냅니다.
        areaCode = params.pop('areaCode', [None])[0] # area_code 가져옴
        sigunguName = params.pop('sigunguName', [None])[0] # 시군구 이름 가져옴
        contentTypeId = params.pop('contentTypeId', [None])[0] # 컨텐츠 유형 아이디 가져옴
        if areaCode is None or sigunguName is None or contentTypeId is None:
            await self.send(text_data=json.dumps({
                'state': 'ERROR',
                'Message': '필수 파라미터 중 일부가 없습니다.'
            }))
            return
        tour = TourApi(MobileOS=MobileOS.ANDROID, MobileApp='AlphaProject2025', service_key=PUBLIC_DATA_PORTAL_API_KEY)
        sigunguCode = tour.get_sigungu_code(areaCode, sigunguName) # 시군구 이름에 대응되는 코드를 가져옵니다.
        if sigunguCode is None: # 시군구 코드가 없다면
            await self.send(text_data=json.dumps({
                'state': 'ERROR',
                'Message': '해당 시군구 이름에 대응되는 코드를 가져올 수 없습니다. 시군구 이름을 다시 한번 확인 바랍니다.'
            }))
            return

        task_result = app.send_task('tour.tasks.get_recommended_tour_based_area', args=[self.user_id, # 채널 레이어 그룹 특정을 위해 보냅니다.
                                                                                        areaCode, contentTypeId, Arrange.TITLE_IMAGE.value, sigunguCode])
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