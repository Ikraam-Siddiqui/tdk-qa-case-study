import asyncio
import json
import time
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/v1/models")
async def list_models():
    return {"object": "list", "data": [{"id": "mock-gpt", "object": "model"}]}

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    stream = body.get("stream", False)
    tokens = ["Hello", " from", " the", " local", " mock", " AI", " server", " for", " TDK", " load", " testing."]

    if not stream:
        return {
            "id": "chatcmpl-mock",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "mock-gpt",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "".join(tokens)}, "finish_reason": "stop"}],
        }

    async def event_stream():
        for tok in tokens:
            chunk = {
                "id": "chatcmpl-mock",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "mock-gpt",
                "choices": [{"index": 0, "delta": {"content": tok}, "finish_reason": None}],
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.02)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")