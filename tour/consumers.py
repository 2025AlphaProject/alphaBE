import json
from channels.generic.websocket import AsyncWebsocketConsumer
from config.celery import app
from config.settings import PUBLIC_DATA_PORTAL_API_KEY, APP_LOGGER
from services.tour_api import *
import urllib.parse
import logging
from django.core.cache import cache
logger = logging.getLogger(APP_LOGGER)

class TaskConsumer(AsyncWebsocketConsumer):
    needCachingCategories = []
    sigunguName = ''
    areaCode = 1
    result_dic = dict()
    """
        '관광지': '12',
        '문화시설': '14',
        '축제공연행사': '15',
        '레포츠': '28',
        '숙박': '32',
        '쇼핑': '38',
        '음식점': '39'
        {
            "12": [
                {
                    "address": "서울특별시 종로구 사직로 161 (세종로)",
                    "areaCode": "1",
                },
            ]
        }
    """
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
        self.areaCode = areaCode
        sigunguName = params.pop('sigunguName', [None])[0]
        self.sigunguName = sigunguName
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
        self.needCachingCategories = []
        self.result_dic = dict()
        # 캐싱된 데이터는 미리 빼놓고, 캐싱되지 않은 데이터만 AI 요청을 보냅니다.
        # celery 코드를 보아하니 카테고리별로 장소들을 가지고 오는 행태를 보이므로 최소한의 카테고리만 보내는 것이 효율적일 것으로 보임
        for each in categoryNames:
            value = cache.get(f"{self.areaCode}&{self.sigunguName}&{each}")
            if value is None:
                self.needCachingCategories.append(each)
            else:
                logger.debug('key: ' + f'{self.areaCode}&{self.sigunguName}&{each}\n' +
                             f'value: {value}\ncache 사용됨')
                self.result_dic[each] = value
        logger.debug('Need AI list: ' + str(self.needCachingCategories))
        if len(self.needCachingCategories) != 0:
            task_result = app.send_task(
                'tour.tasks.get_recommended_place_by_category_task',
                args=[self.user_id, areaCode, categoryNames, sigunguCodes, Arrange.TITLE_IMAGE.value, self.user_id]  # ← 추가됨
            )

            await self.send(text_data=json.dumps({
                'state': 'OK',
                'Message': {
                    'task_id': task_result.task_id,
                }
            }, ensure_ascii=False))
        else:
            await self.send(text_data=json.dumps({
                'state': 'CACHE_HIT',
                'result': self.result_dic,
            }, ensure_ascii=False))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.user_id, self.channel_name)

    async def task_update(self, event):

        data = event["message"]
        # cache에 데이터를 저장합니다.
        for each in self.needCachingCategories:
            cache.set(
                f'{self.areaCode}&{self.sigunguName}&{each}',
                data['result'][each]
            )
            self.result_dic[each] = data['result'][each]
            logger.debug('key: ' + f'{self.areaCode}&{self.sigunguName}&{each}\n' +
                         f'value: {self.result_dic[each]}\n이 cache에 저장됨')
        data['result'] = self.result_dic
        # celery 컨테이너에서 보낸 메시지를 클라이언트로 전송
        await self.send(text_data=json.dumps(data, ensure_ascii=False))

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
