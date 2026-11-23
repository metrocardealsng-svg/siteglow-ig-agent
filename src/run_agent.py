"""
SiteGlow NG Autonomous Instagram Agent Entrypoint
Runs daily via GitHub Actions (or manually with --dry-run / --mode reel|carousel).
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from src.content_engine import generate_content
from src.ig_publisher import publish_carousel, publish_reel
from src.media_renderer import render_carousel, render_reel

ROOT = Path(__file__).resolve().parent.parent
HISTORY_FILE = ROOT / "history.json"
OUT_ROOT = ROOT / "output"


def load_history() -> dict:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return {"posted_topics": [], "last_format": "carousel", "post_count": 0}


def save_history(history: dict):
    HISTORY_FILE.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")


def main():
    load_dotenv(ROOT / ".env")

    ap = argparse.ArgumentParser(description="SiteGlow NG Autonomous Instagram Posting Agent")
    ap.add_argument("--mode", choices=["auto", "reel", "carousel"],
                    default=os.getenv("CONTENT_MODE", "auto"))
    ap.add_argument("--dry-run", action="store_true",
                    default=os.getenv("DRY_RUN", "false").lower() == "true")
    args = ap.parse_args()

    history = load_history()
    if args.mode == "auto":
        fmt = "reel" if history.get("last_format") == "carousel" else "carousel"
    else:
        fmt = args.mode

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = OUT_ROOT / f"{run_stamp}_{fmt}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== SiteGlow NG Agent Run ({run_stamp}) | Format: {fmt.upper()} | Dry-Run: {args.dry_run} ===")
    content = generate_content(fmt, history)
    (run_dir / "post_plan.json").write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
    (run_dir / "caption.txt").write_text(content["caption"], encoding="utf-8")

    if fmt == "reel":
        media_out = render_reel(content, run_dir)
        print(f"[agent] Rendered Reel: {media_out}")
    else:
        media_out = render_carousel(content, run_dir)
        print(f"[agent] Rendered {len(media_out)} Carousel slides in {run_dir}")

    print("\n--- FINAL CAPTION ---\n" + content["caption"] + "\n---------------------\n")

    if args.dry_run:
        print("[agent] DRY_RUN enabled — skipping Instagram publish.")
        return

    if not os.getenv("IG_USER_ID") or not os.getenv("IG_ACCESS_TOKEN"):
        raise SystemExit(
            "Missing IG_USER_ID or IG_ACCESS_TOKEN. Set them in GitHub Secrets (or run with --dry-run)."
        )

    if fmt == "reel":
        media_id = publish_reel(media_out, content["caption"])
    else:
        media_id = publish_carousel(media_out, content["caption"])

    # Persist history so topics never repeat back-to-back and formats alternate cleanly
    posted = history.get("posted_topics", [])
    if content["topic_id"] not in posted:
        posted.append(content["topic_id"])
    if len(posted) >= 10:
        posted = posted[-3:]
    history["posted_topics"] = posted
    history["last_format"] = fmt
    history["post_count"] = history.get("post_count", 0) + 1
    history["last_media_id"] = media_id
    history["last_posted_utc"] = run_stamp
    save_history(history)
    print(f"[agent] Updated history.json (total posts: {history['post_count']})")


if __name__ == "__main__":
    main()
