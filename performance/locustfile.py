import time
import uuid
from locust import HttpUser, task, between, events

EMAIL = "userb@test.com"       # Replace with your UserB email
PASSWORD = "Test@123" # Replace with your UserB password


class LibreChatUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        """Log in once per virtual user and store the Bearer token."""
        res = self.client.post(
            "/api/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
            name="1_Login",
        )
        if res.status_code == 200:
            self.token = res.json().get("token", "")
            self.headers = {
    "Authorization": f"Bearer {self.token}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
}
        else:
            self.token = ""
            self.headers = {}

    @task(3)
    def api_flow_list_and_search(self):
        """Flow 1: Non-AI API flow (list conversations, load messages, search)."""
        if not self.token:
            return

        # 1. List conversations
        convos_res = self.client.get(
            "/api/convos?pageNumber=1",
            headers=self.headers,
            name="2_List_Conversations",
        )

        # 2. Load messages from the first conversation if available
        if convos_res.status_code == 200:
            convos = convos_res.json().get("conversations", [])
            if convos:
                convo_id = convos[0].get("conversationId")
                self.client.get(
                    f"/api/messages/{convo_id}",
                    headers=self.headers,
                    name="3_Load_Messages",
                )

        # 3. Search conversations via Meilisearch
        self.client.get(
            "/api/convos?search=Hello",
            headers=self.headers,
            name="4_Search_Conversations",
        )

    @task(1)
    def chat_streaming_flow(self):
        """Flow 2: LibreChat v0.8.7 2-step streaming chat (Init + SSE Stream)."""
        if not self.token:
            return

        payload = {
            "text": "Hello load test",
            "sender": "User",
            "clientTimestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "isCreatedByUser": True,
            "parentMessageId": "00000000-0000-0000-0000-000000000000",
            "conversationId": None,
            "messageId": str(uuid.uuid4()),
            "endpoint": "MockAI",
            "endpointType": "custom",
            "model": "mock-gpt",
        }

        start_time = time.perf_counter()

        # Step 1: Initiate chat generation
        init_res = self.client.post(
            "/api/agents/chat/MockAI",
            json=payload,
            headers=self.headers,
            name="5a_Chat_Init",
        )
        if init_res.status_code != 200:
            return

        stream_id = init_res.json().get("streamId")
        if not stream_id:
            return

        # Step 2: Subscribe to SSE stream and measure TTFT + Total Time
        ttft_recorded = False
        stream_headers = {**self.headers, "Accept": "text/event-stream"}

        with self.client.get(
            f"/api/agents/chat/stream/{stream_id}",
            headers=stream_headers,
            stream=True,
            catch_response=True,
            name="5b_Chat_Stream_Total",
        ) as response:
            if response.status_code != 200:
                response.failure(f"HTTP {response.status_code}")
                return

            for chunk in response.iter_content(chunk_size=None):
                if chunk and not ttft_recorded:
                    ttft_ms = (time.perf_counter() - start_time) * 1000
                    events.request.fire(
                        request_type="SSE",
                        name="5c_Chat_Time_To_First_Token",
                        response_time=ttft_ms,
                        response_length=len(chunk),
                        exception=None,
                    )
                    ttft_recorded = True
            response.success()