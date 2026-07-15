"""
MuAPI Client — generate images and videos through MuAPI (https://muapi.ai),
the media engine behind Open Generative AI (200+ models: Flux, Nano Banana,
Kling, Seedance, Veo). Usable as a library or a CLI.

Auth: set the MUAPI_KEY environment variable (never hard-code the key).
Optional: MUAPI_BASE_URL to override the endpoint.

Protocol (mirrors Open-Generative-AI's studio client):
    submit   POST {base}/api/v1/{model-endpoint}        -> { request_id }
    poll     GET  {base}/api/v1/predictions/{id}/result  -> { status, outputs[] }
    balance  GET  {base}/api/v1/account/balance          -> { balance }

Library:
    from tools.muapi_client import MuapiClient
    client = MuapiClient()                       # reads MUAPI_KEY
    result = client.generate_image(prompt="a calm lake at dawn")
    print(result["url"])

CLI:
    python tools/muapi_client.py balance
    python tools/muapi_client.py image --prompt "a calm lake at dawn" --aspect-ratio 1:1
    python tools/muapi_client.py video --prompt "slow pan across a forest" --duration 5
    python tools/muapi_client.py generate --model kling-v2.5-turbo-pro-t2v --prompt "..." --duration 10
    python tools/muapi_client.py image --prompt "test" --dry-run       # preview only
    python tools/muapi_client.py video --prompt "..." --no-wait        # submit, return request_id
    python tools/muapi_client.py result --id <request_id>
"""

import argparse
import json
import os
import sys
import time

import requests

DEFAULT_BASE_URL = "https://api.muapi.ai"

# Sensible default model endpoints (any MuAPI endpoint id is accepted).
DEFAULT_MODELS = {
    "text_to_image": "flux-dev",
    "image_to_image": "nano-banana",
    "text_to_video": "seedance-lite-t2v",
    "image_to_video": "wan2.1-image-to-video",
}

# Statuses reported by MuAPI's poll endpoint.
_DONE = {"completed", "succeeded", "success"}
_FAILED = {"failed", "error"}


class MuapiError(Exception):
    """Raised for MuAPI request/generation failures."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class MuapiClient:
    def __init__(
        self,
        api_key=None,
        base_url=None,
        poll_interval=2.0,
        max_poll_attempts=900,
    ):
        # The key is validated lazily (see _headers), not here, so importing or
        # constructing the client without a key never crashes — only an actual
        # request does.
        self.api_key = api_key or os.environ.get("MUAPI_KEY", "")
        self.base_url = (base_url or os.environ.get("MUAPI_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.poll_interval = poll_interval
        self.max_poll_attempts = max_poll_attempts

    def _headers(self):
        if not self.api_key:
            raise MuapiError("MUAPI_KEY environment variable (or api_key) is required")
        return {"Content-Type": "application/json", "x-api-key": self.api_key}

    def get_balance(self):
        """Return the account's remaining MuAPI credit balance."""
        res = requests.get(f"{self.base_url}/api/v1/account/balance", headers=self._headers())
        if not res.ok:
            raise MuapiError(f"Failed to fetch balance: {res.status_code} {res.text[:200]}", res.status_code)
        return res.json()

    def generate(self, model_endpoint, payload, max_poll_attempts=None):
        """Submit a generation request and poll until the output is ready.

        `payload` is passed through to MuAPI verbatim (prompt, aspect_ratio, ...).
        Returns a normalized dict: {request_id, status, url, outputs, raw}.
        """
        res = requests.post(
            f"{self.base_url}/api/v1/{model_endpoint}",
            headers=self._headers(),
            data=json.dumps(payload),
        )
        if not res.ok:
            raise MuapiError(f"MuAPI request failed: {res.status_code} {res.text[:200]}", res.status_code)
        submit = res.json()
        request_id = submit.get("request_id") or submit.get("id")
        if not request_id:
            return self._normalize(None, submit)
        result = self._poll_for_result(request_id, max_poll_attempts or self.max_poll_attempts)
        return self._normalize(request_id, result)

    def generate_image(self, prompt, model=None, aspect_ratio=None, resolution=None,
                       quality=None, image_url=None, images_list=None, seed=None):
        """Text-to-image, or image-to-image when image_url/images_list is given."""
        if model is None:
            model = DEFAULT_MODELS["image_to_image"] if (image_url or images_list) else DEFAULT_MODELS["text_to_image"]
        payload = {"prompt": prompt}
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if resolution:
            payload["resolution"] = resolution
        if quality:
            payload["quality"] = quality
        if images_list:
            payload["images_list"] = images_list
        elif image_url:
            payload["image_url"] = image_url
        if seed is not None and seed != -1:
            payload["seed"] = seed
        return self.generate(model, payload, max_poll_attempts=120)

    def generate_video(self, prompt=None, model=None, aspect_ratio=None, resolution=None,
                       quality=None, duration=None, mode=None, image_url=None, images_list=None):
        """Text-to-video, or image-to-video when image_url is given."""
        if model is None:
            model = DEFAULT_MODELS["image_to_video"] if image_url else DEFAULT_MODELS["text_to_video"]
        payload = {}
        if prompt:
            payload["prompt"] = prompt
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if resolution:
            payload["resolution"] = resolution
        if quality:
            payload["quality"] = quality
        if duration:
            payload["duration"] = duration
        if mode:
            payload["mode"] = mode
        if image_url:
            payload["image_url"] = image_url
        if images_list:
            payload["images_list"] = images_list
        return self.generate(model, payload)

    def get_result(self, request_id):
        """Fetch the current result for a submitted request (single check)."""
        res = requests.get(
            f"{self.base_url}/api/v1/predictions/{request_id}/result",
            headers=self._headers(),
        )
        if not res.ok:
            raise MuapiError(f"Failed to fetch result: {res.status_code} {res.text[:200]}", res.status_code)
        return res.json()

    def _poll_for_result(self, request_id, max_attempts):
        url = f"{self.base_url}/api/v1/predictions/{request_id}/result"
        for attempt in range(1, max_attempts + 1):
            time.sleep(self.poll_interval)
            try:
                res = requests.get(url, headers=self._headers())
                if not res.ok:
                    if res.status_code >= 500:
                        continue  # transient upstream error, keep polling
                    raise MuapiError(f"Poll failed: {res.status_code} {res.text[:200]}", res.status_code)
                data = res.json()
                status = str(data.get("status", "")).lower()
                if status in _DONE:
                    return data
                if status in _FAILED:
                    raise MuapiError(f"Generation failed: {data.get('error') or 'unknown error'}")
            except MuapiError:
                # Terminal MuAPI errors (auth failure, generation failed, non-5xx
                # poll failure) propagate immediately.
                raise
            except requests.RequestException as err:
                # Transient network errors are tolerated during the long poll so a
                # brief outage doesn't abort a multi-minute video job.
                if attempt == max_attempts:
                    raise MuapiError(f"Poll failed: {err}") from err
        raise MuapiError(f"Generation timed out while polling (request_id: {request_id})")

    @staticmethod
    def _normalize(request_id, raw):
        # Upstream models vary: outputs (array), output (string or array), or a
        # top-level url. Normalize them all.
        outputs_raw = raw.get("outputs")
        if outputs_raw is None:
            outputs_raw = raw.get("output") if isinstance(raw.get("output"), list) else []
        outputs = [o for o in outputs_raw if isinstance(o, str)] if isinstance(outputs_raw, list) else []
        single = None
        if outputs:
            single = outputs[0]
        elif raw.get("url"):
            single = raw["url"]
        elif isinstance(raw.get("output"), str):
            single = raw["output"]
        elif isinstance(raw.get("output"), dict):
            single = raw["output"].get("url")
        return {
            "request_id": request_id,
            "status": str(raw.get("status") or ("completed" if single else "unknown")),
            "url": single,
            "outputs": [single] if (single and not outputs) else outputs,
            "raw": raw,
        }


def _build_parser():
    p = argparse.ArgumentParser(description="Generate images/videos via MuAPI (Open Generative AI).")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("balance", help="show remaining MuAPI credit")

    def add_common(sp):
        sp.add_argument("--model", help="MuAPI model endpoint (overrides default)")
        sp.add_argument("--aspect-ratio", dest="aspect_ratio")
        sp.add_argument("--resolution")
        sp.add_argument("--quality")
        sp.add_argument("--image-url", dest="image_url")
        sp.add_argument("--dry-run", action="store_true", help="preview the request without sending it")
        sp.add_argument("--no-wait", action="store_true", help="submit only, return the request_id")

    img = sub.add_parser("image", help="text->image, or image->image with --image-url")
    img.add_argument("--prompt", required=True)
    img.add_argument("--seed", type=int)
    add_common(img)

    vid = sub.add_parser("video", help="text->video, or image->video with --image-url")
    vid.add_argument("--prompt")
    vid.add_argument("--duration", type=int)
    vid.add_argument("--mode")
    add_common(vid)

    # `generate` defines --model itself (required), so it can't reuse add_common.
    gen = sub.add_parser("generate", help="any model endpoint with raw params")
    gen.add_argument("--model", required=True)
    gen.add_argument("--prompt")
    gen.add_argument("--duration", type=int)
    gen.add_argument("--seed", type=int)
    gen.add_argument("--aspect-ratio", dest="aspect_ratio")
    gen.add_argument("--image-url", dest="image_url")
    gen.add_argument("--dry-run", action="store_true")
    gen.add_argument("--no-wait", action="store_true")

    res = sub.add_parser("result", help="fetch the result of a submitted request")
    res.add_argument("--id", required=True, dest="request_id")

    return p


def _dry_run_payload(base_url, model, payload):
    return {
        "_dry_run": True,
        "method": "POST",
        "url": f"{base_url}/api/v1/{model}",
        "headers": {"x-api-key": "***"},
        "body": payload,
    }


def main(argv=None):
    args = _build_parser().parse_args(argv)
    client = MuapiClient()

    if args.command == "balance":
        print(json.dumps(client.get_balance(), indent=2))
        return

    if args.command in ("image", "video", "generate"):
        if args.command == "image":
            model = args.model or (DEFAULT_MODELS["image_to_image"] if args.image_url else DEFAULT_MODELS["text_to_image"])
            payload = {"prompt": args.prompt}
            if args.seed is not None:
                payload["seed"] = args.seed
            max_attempts = 120
        elif args.command == "video":
            model = args.model or (DEFAULT_MODELS["image_to_video"] if args.image_url else DEFAULT_MODELS["text_to_video"])
            payload = {}
            if args.prompt:
                payload["prompt"] = args.prompt
            if args.duration:
                payload["duration"] = args.duration
            if getattr(args, "mode", None):
                payload["mode"] = args.mode
            if not args.prompt and not args.image_url:
                print(json.dumps({"error": "video requires --prompt or --image-url"}))
                sys.exit(1)
            max_attempts = 900
        else:  # generate
            model = args.model
            payload = {}
            if args.prompt:
                payload["prompt"] = args.prompt
            if args.duration:
                payload["duration"] = args.duration
            if args.seed is not None:
                payload["seed"] = args.seed
            max_attempts = 900

        if args.aspect_ratio:
            payload["aspect_ratio"] = args.aspect_ratio
        if getattr(args, "resolution", None):
            payload["resolution"] = args.resolution
        if getattr(args, "quality", None):
            payload["quality"] = args.quality
        if args.image_url:
            payload["image_url"] = args.image_url

        if args.dry_run:
            print(json.dumps(_dry_run_payload(client.base_url, model, payload), indent=2))
            return

        # Submit; optionally return without polling.
        res = requests.post(f"{client.base_url}/api/v1/{model}", headers=client._headers(), data=json.dumps(payload))
        if not res.ok:
            raise MuapiError(f"MuAPI request failed: {res.status_code} {res.text[:200]}", res.status_code)
        submit = res.json()
        request_id = submit.get("request_id") or submit.get("id")
        if not request_id:
            print(json.dumps(client._normalize(None, submit), indent=2))
            return
        if args.no_wait:
            print(json.dumps({"request_id": request_id, "status": "submitted"}, indent=2))
            return
        try:
            result = client._poll_for_result(request_id, max_attempts)
        except MuapiError as err:
            raise MuapiError(f"{err} (request_id: {request_id}; retry with: result --id {request_id})")
        out = client._normalize(request_id, result)
        print(json.dumps({k: out[k] for k in ("request_id", "status", "url", "outputs")}, indent=2))
        return

    if args.command == "result":
        print(json.dumps(client.get_result(args.request_id), indent=2))
        return

    _build_parser().print_help()


if __name__ == "__main__":
    try:
        main()
    except MuapiError as err:
        print(json.dumps({"error": str(err)}), file=sys.stderr)
        sys.exit(1)
