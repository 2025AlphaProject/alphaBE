import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync

class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.task_id = self.scope["url_route"]["kwargs"]["task_id"]
        self.group_name = f"task_{self.task_id}"

        # 웹소켓 그룹에 가입
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Celery 작업 실행 (B 컨테이너에서 실행됨)
        # async_to_sync(celery_app.send_task)("your_app.tasks.long_running_task", args=[self.task_id])

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def task_update(self, event):
        # celery 컨테이너에서 보낸 메시지를 클라이언트로 전송
        await self.send(text_data=json.dumps(event["message"]))