# MuAPI Media Generation (Open Generative AI integration)

`tools/muapi_client.py` integrates [MuAPI](https://muapi.ai) — the media engine
behind [Open Generative AI](https://github.com/Anil-matcha/Open-Generative-AI)
(200+ image/video models: Flux, Nano Banana, Kling, Seedance, Veo) — as a backend
tool. Use it as a Python library or a CLI to generate images and short videos.

## Setup

Requires `requests` (already in `requirements.txt`). Set the key in the
environment — never hard-code it:

```bash
export MUAPI_KEY=<your MuAPI key>          # get one at https://muapi.ai
export MUAPI_BASE_URL=https://api.muapi.ai # optional override
```

## Library

```python
from tools.muapi_client import MuapiClient

client = MuapiClient()  # reads MUAPI_KEY

# text -> image (default flux-dev)
img = client.generate_image(prompt="a cozy reading nook, warm light", aspect_ratio="1:1")
print(img["url"])

# image -> image / edit (image_url switches to nano-banana)
edit = client.generate_image(prompt="make it night, neon signs", image_url="https://.../in.png")

# text -> video (default seedance-lite-t2v)
vid = client.generate_video(prompt="slow dolly across a misty forest", duration=5)
print(vid["url"])

# image -> video (image_url switches to wan2.1-image-to-video)
anim = client.generate_video(prompt="gentle wind", image_url="https://.../still.png")

# any endpoint + raw params
custom = client.generate("kling-v2.5-turbo-pro-t2v", {"prompt": "city flythrough", "duration": 10})

# balance
print(client.get_balance())
```

`generate_*` return a dict: `{request_id, status, url, outputs, raw}` where `url`
is the hosted output asset.

## CLI

```bash
python tools/muapi_client.py balance
python tools/muapi_client.py image --prompt "a calm lake at dawn" --aspect-ratio 1:1
python tools/muapi_client.py image --prompt "night look" --image-url https://.../in.png
python tools/muapi_client.py video --prompt "slow pan across a forest" --duration 5
python tools/muapi_client.py video --prompt "drifting clouds" --image-url https://.../still.png
python tools/muapi_client.py generate --model kling-v2.5-turbo-pro-t2v --prompt "..." --duration 10

# preview a request without sending it
python tools/muapi_client.py image --prompt "test" --dry-run
# submit only (no polling), then fetch later
python tools/muapi_client.py video --prompt "..." --no-wait
python tools/muapi_client.py result --id <request_id>
```

CLI output is JSON. `--help` and `--dry-run` work without a key; only commands
that call the API require `MUAPI_KEY`.

## Default model endpoints

| Task | Default |
|------|---------|
| Text → image | `flux-dev` |
| Image → image / edit | `nano-banana` |
| Text → video | `seedance-lite-t2v` |
| Image → video | `wan2.1-image-to-video` |

Pass `--model` / `model=` to use any MuAPI endpoint (e.g. `flux-schnell`,
`bytedance-seedream-v4`, `veo3-fast-text-to-video`, `runway-image-to-video`).

## Protocol

| Action | Request |
|--------|---------|
| Submit | `POST {base}/api/v1/{model}`, header `x-api-key` → `{ request_id }` |
| Poll | `GET {base}/api/v1/predictions/{request_id}/result` → `{ status, outputs[] }` |
| Balance | `GET {base}/api/v1/account/balance` → `{ balance }` |

The client polls until `completed` (video: up to ~30 min), tolerates transient
network errors during the poll, and raises `MuapiError` on terminal failure or
timeout — the `request_id` is included so a long job can be recovered via
`result --id`.
