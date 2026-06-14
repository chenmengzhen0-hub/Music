#!/usr/bin/env python3
"""
listen — 给克劳德的耳朵
把音频（mp3/wav/flac/mp4）转成结构化音符 JSON，让没有听觉的 AI 能"读"懂一首歌。

管道：音频 → librosa pyin 音高识别 → 音符分割 → JSON
（原版用 basic-pitch，但 basic-pitch 依赖 tensorflow，Python 3.12+ 不兼容；
 改用 librosa pyin，纯 CPU，无需 GPU/TF，结果格式完全相同。）

用法：
    python whale_listen.py 歌.mp3                 # 输出 歌.json
    python whale_listen.py 歌.mp3 -o out.json     # 指定输出
    python whale_listen.py 歌.mp3 --analyze       # 附带结构分析

依赖：pip install librosa pretty-midi scipy
"""

import argparse
import json
import sys
from pathlib import Path

import librosa
import numpy as np

_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def midi_to_name(pitch: int) -> str:
    return f"{_NOTE_NAMES[pitch % 12]}{pitch // 12 - 1}"


def hz_to_midi(hz: float) -> int:
    return int(round(69 + 12 * np.log2(hz / 440.0)))


FFMPEG = r"C:\Users\79977\Documents\PlatformIO\Projects\mochi\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe"


def convert(audio_path: str) -> dict:
    """音频 → 音符列表。返回 {meta, notes}。"""
    import os, subprocess, tempfile
    src = Path(audio_path)
    tmp_wav = None
    load_path = audio_path
    if src.suffix.lower() in (".mp4", ".m4a", ".aac", ".ogg", ".flac", ".mp3"):
        tmp_wav = tempfile.mktemp(suffix=".wav")
        subprocess.run([FFMPEG, "-y", "-i", audio_path, "-ac", "1", "-ar", "22050", tmp_wav],
                       check=True, capture_output=True)
        load_path = tmp_wav
    print(f"  载入音频...", file=sys.stderr)
    y, sr = librosa.load(load_path, sr=22050, mono=True)
    if tmp_wav and os.path.exists(tmp_wav):
        os.remove(tmp_wav)

    print(f"  pyin 音高识别（可能需要几十秒）...", file=sys.stderr)
    f0, voiced_flag, _ = librosa.pyin(
        y, sr=sr,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        frame_length=2048,
    )

    hop = 512
    times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop)

    # 把连续有声帧合并成音符
    notes = []
    i = 0
    while i < len(f0):
        if not voiced_flag[i] or np.isnan(f0[i]):
            i += 1
            continue
        j = i
        pitches_seg = []
        while j < len(f0) and voiced_flag[j] and not np.isnan(f0[j]):
            pitches_seg.append(f0[j])
            j += 1
        if j > i:
            midi = hz_to_midi(float(np.median(pitches_seg)))
            midi = max(0, min(127, midi))
            start = float(times[i])
            end = float(times[j - 1]) + hop / sr
            dur = round(end - start, 4)
            if dur >= 0.05:  # 过滤极短噪声帧
                notes.append({
                    "pitch": midi,
                    "name": midi_to_name(midi),
                    "start": round(start, 4),
                    "end": round(end, 4),
                    "duration": dur,
                    "velocity": 80,  # pyin 不输出力度，固定 80
                })
        i = j

    notes.sort(key=lambda x: (x["start"], x["pitch"]))
    total = round(float(times[-1]), 4) if len(times) else 0.0

    return {
        "meta": {
            "source": Path(audio_path).name,
            "note_count": len(notes),
            "duration_sec": total,
            "format": "listen-notes-v1",
            "engine": "librosa-pyin",
        },
        "notes": notes,
    }


def analyze(data: dict) -> dict:
    notes = data["notes"]
    if not notes:
        return {"empty": True}

    pitches = [n["pitch"] for n in notes]
    vels = [n["velocity"] for n in notes]
    duration = data["meta"]["duration_sec"] or 1.0

    buckets = {}
    for n in notes:
        sec = int(n["start"])
        buckets[sec] = buckets.get(sec, 0) + 1
    density = [buckets.get(s, 0) for s in range(int(duration) + 1)]

    longest_silence = 0.0
    silence_at = 0.0
    ordered = sorted(notes, key=lambda x: x["start"])
    cursor = 0.0
    for n in ordered:
        gap = n["start"] - cursor
        if gap > longest_silence:
            longest_silence = round(gap, 4)
            silence_at = round(cursor, 4)
        cursor = max(cursor, n["end"])

    return {
        "pitch_range": {
            "lowest": midi_to_name(min(pitches)),
            "highest": midi_to_name(max(pitches)),
            "span_semitones": max(pitches) - min(pitches),
        },
        "velocity": {
            "min": min(vels),
            "max": max(vels),
            "avg": round(sum(vels) / len(vels), 1),
        },
        "density_per_sec": density,
        "busiest_sec": max(range(len(density)), key=lambda i: density[i]) if density else 0,
        "longest_silence": {"seconds": longest_silence, "starts_at": silence_at},
        "notes_per_sec_avg": round(len(notes) / duration, 2),
    }


def main():
    ap = argparse.ArgumentParser(description="把音频转成结构化音符 JSON，让 AI 能'读'懂音乐。")
    ap.add_argument("audio", help="输入音频文件 (mp3/wav/flac/mp4)")
    ap.add_argument("-o", "--output", help="输出 JSON 路径（默认与输入同名 .json）")
    ap.add_argument("--analyze", action="store_true", help="附带结构分析（音域/密度/静默）")
    args = ap.parse_args()

    src = Path(args.audio)
    if not src.exists():
        print(f"找不到文件: {src}", file=sys.stderr)
        sys.exit(1)

    print(f"🎧 正在听 {src.name} ...", file=sys.stderr)
    data = convert(str(src))

    if args.analyze:
        data["analysis"] = analyze(data)

    out = Path(args.output) if args.output else src.with_suffix(".json")
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    m = data["meta"]
    print(f"✓ {m['note_count']} 个音符，{m['duration_sec']}秒 → {out}", file=sys.stderr)
    if args.analyze and "analysis" in data:
        a = data["analysis"]
        if not a.get("empty"):
            pr = a["pitch_range"]
            print(f"  音域 {pr['lowest']}~{pr['highest']}（{pr['span_semitones']}个半音）", file=sys.stderr)
            print(f"  平均每秒 {a['notes_per_sec_avg']} 个音，最密在第 {a['busiest_sec']} 秒", file=sys.stderr)
            print(f"  最长静默 {a['longest_silence']['seconds']}秒", file=sys.stderr)


if __name__ == "__main__":
    main()
