"""
Official Meta Instagram Graph API Publisher (v22.0)
Supports:
  - Reels publishing (REELS container -> poll status -> media_publish)
  - Multi-slide Carousel publishing (CAROUSEL children -> parent container -> media_publish)
Media Hosting:
  - Uses Cloudinary unsigned upload preset if CLOUDINARY_CLOUD_NAME + CLOUDINARY_UPLOAD_PRESET are set,
  - Otherwise falls back to temporary public staging via catbox.moe / tmpfiles.org so zero extra paid hosting is required.
"""
import os
import time
from pathlib import Path
import requests

GRAPH_BASE = "https://graph.facebook.com/v22.0"


def upload_public_media(file_path: Path, is_video: bool = False) -> str:
    """Uploads a local JPG or MP4 to a public HTTPS URL that Meta's servers can fetch."""
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
    upload_preset = os.getenv("CLOUDINARY_UPLOAD_PRESET", "").strip()

    if cloud_name and upload_preset:
        resource = "video" if is_video else "image"
        url = f"https://api.cloudinary.com/v1_1/{cloud_name}/{resource}/upload"
        with open(file_path, "rb") as fh:
            resp = requests.post(url, data={"upload_preset": upload_preset}, files={"file": fh}, timeout=120)
        resp.raise_for_status()
        public_url = resp.json()["secure_url"]
        print(f"[publisher] Uploaded to Cloudinary: {public_url}")
        return public_url

    # Zero-config fallback: catbox.moe (direct HTTPS URL compatible with Meta crawler)
    with open(file_path, "rb") as fh:
        resp = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (file_path.name, fh)},
            timeout=120,
        )
    resp.raise_for_status()
    public_url = resp.text.strip()
    if not public_url.startswith("https://"):
        raise RuntimeError(f"Unexpected upload host response: {public_url}")
    print(f"[publisher] Staged media at: {public_url}")
    return public_url


def _poll_container(container_id: str, token: str, max_wait_s: int = 180):
    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        r = requests.get(
            f"{GRAPH_BASE}/{container_id}",
            params={"fields": "status_code,status", "access_token": token},
            timeout=30,
        )
        r.raise_for_status()
        body = r.json()
        code = body.get("status_code")
        print(f"[publisher] Container {container_id} status: {code}")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram container failed: {body}")
        time.sleep(6)
    raise TimeoutError(f"Container {container_id} did not finish within {max_wait_s}s")


def publish_reel(video_path: Path, caption: str) -> str:
    ig_user_id = os.environ["IG_USER_ID"].strip()
    token = os.environ["IG_ACCESS_TOKEN"].strip()

    video_url = upload_public_media(video_path, is_video=True)
    r = requests.post(
        f"{GRAPH_BASE}/{ig_user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": token,
        },
        timeout=60,
    )
    r.raise_for_status()
    creation_id = r.json()["id"]
    print(f"[publisher] Created REELS container: {creation_id}")
    _poll_container(creation_id, token)

    pub = requests.post(
        f"{GRAPH_BASE}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
        timeout=60,
    )
    pub.raise_for_status()
    media_id = pub.json()["id"]
    print(f"[publisher] Published Reel successfully! IG Media ID: {media_id}")
    return media_id


def publish_carousel(slide_paths: list[Path], caption: str) -> str:
    ig_user_id = os.environ["IG_USER_ID"].strip()
    token = os.environ["IG_ACCESS_TOKEN"].strip()

    child_ids = []
    for sp in slide_paths:
        img_url = upload_public_media(sp, is_video=False)
        r = requests.post(
            f"{GRAPH_BASE}/{ig_user_id}/media",
            data={
                "image_url": img_url,
                "is_carousel_item": "true",
                "access_token": token,
            },
            timeout=60,
        )
        r.raise_for_status()
        cid = r.json()["id"]
        _poll_container(cid, token, max_wait_s=90)
        child_ids.append(cid)

    parent = requests.post(
        f"{GRAPH_BASE}/{ig_user_id}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
            "caption": caption,
            "access_token": token,
        },
        timeout=60,
    )
    parent.raise_for_status()
    parent_id = parent.json()["id"]
    _poll_container(parent_id, token, max_wait_s=90)

    pub = requests.post(
        f"{GRAPH_BASE}/{ig_user_id}/media_publish",
        data={"creation_id": parent_id, "access_token": token},
        timeout=60,
    )
    pub.raise_for_status()
    media_id = pub.json()["id"]
    print(f"[publisher] Published Carousel successfully! IG Media ID: {media_id}")
    return media_id
