import json
import os
from urllib import request

GLM_API_KEY = os.getenv("GLM_API_KEY")
assert GLM_API_KEY, "GLM_API_KEY not set"

url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

payload = {
    "model": "glm-4.7",
    "messages": [
        {"role": "system", "content": "你是一个测试助手"},
        {"role": "user", "content": "只回复：你好"},
    ],
    "temperature": 0.1,
}

data = json.dumps(payload).encode("utf-8")

req = request.Request(
    url,
    data=data,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GLM_API_KEY}",
    },
)

print(">>> Sending request to GLM...")

with request.urlopen(req, timeout=30) as resp:
    body = resp.read().decode("utf-8")
    print(">>> Response received:")
    print(body)
