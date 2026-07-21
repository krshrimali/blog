#!/usr/bin/env python3
"""Fetch the latest videos and live-stream replays from YouTube via yt-dlp
and write them to data/youtube.json for Hugo's Videos / Live Streams pages.

Run manually with: python3 scripts/fetch_youtube_data.py
Requires yt-dlp to be installed and on PATH.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "youtube.json"

# (data key, source URL, how many most-recent entries to keep)
SOURCES = {
    "videos": (
        "https://www.youtube.com/playlist?list=PLfjzHJeA53gR5FSHWhkMgRAlcj9UCyqoU",
        30,
    ),
    "livestreams": (
        "https://www.youtube.com/@buffetCodes/streams",
        20,
    ),
}


def format_duration(seconds):
    if not seconds:
        return None
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def fetch(url, limit):
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-single-json",
        "--playlist-end", str(limit),
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        print(f"yt-dlp failed for {url}:\n{result.stderr}", file=sys.stderr)
        return []

    data = json.loads(result.stdout)
    entries = []
    for entry in data.get("entries") or []:
        video_id = entry.get("id")
        if not video_id:
            continue
        entries.append({
            "id": video_id,
            "title": (entry.get("title") or "Untitled").strip(),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            "duration": format_duration(entry.get("duration")),
        })
    return entries


def main():
    payload = {}
    for key, (url, limit) in SOURCES.items():
        payload[key] = fetch(url, limit)
        print(f"{key}: fetched {len(payload[key])} entries", file=sys.stderr)

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
