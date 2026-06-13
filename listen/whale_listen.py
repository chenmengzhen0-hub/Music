#!/usr/bin/env python3
"""
listen — 给克劳德的耳朵
把音频（mp3/wav/flac）转成结构化音符 JSON，让没有听觉的 AI 能"读"懂一首歌。

管道：音频 → basic-pitch 音高识别 → pretty_midi → JSON
灵感来自 migratorywhale/whale-listen（MIT）。本实现为梦珍的 music 项目重写。

用法：
    python whale_listen.py 歌.mp3                 # 输出 歌.json
    python whale_listen.py 歌.mp3 -o out.json     # 指定输出
    python whale_listen.py 歌.mp3 --analyze       # 附带结构分析

依赖：pip install basic-pitch onnxruntime pretty-midi scipy librosa
"""

import argparse
import json
import sys
from pathlib import Path


# MIDI 音高 → 音名（C4 = 中央C = 60）
_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def midi_to_name(pitch: int) -> str:
    """60 → 'C4'，61 → 'C#4'"""
    return f"{_NOTE_NAMES[pitch % 12]}{pitch // 12 - 1}"


def convert(audio_path: str) -> dict:
    """音频 → 音符列表。返回 {meta, notes}。"""
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH

    # basic-pitch 返回 (model_output, midi_data, note_events)
    _, midi_data, _ = predict(audio_path, ICASSP_2022_MODEL_PATH)

    notes = []
    for inst in midi_data.instruments:
        for n in inst.notes:
            notes.append({
                "pitch": int(n.pitch),
                "name": midi_to_name(int(n.pitch)),
                "start": round(float(n.start), 4),
                "end": round(float(n.end), 4),
                "duration": round(float(n.end - n.start), 4),
                "velocity": int(n.velocity),
            })

    # 按起始时间排序，方便阅读
    notes.sort(key=lambda x: (x["start"], x["pitch"]))

    total = round(midi_data.get_end_time(), 4) if notes else 0.0
    return {
        "meta": {
            "source": Path(audio_path).name,
            "note_count": len(notes),
            "duration_sec": total,
            "format": "listen-notes-v1",
        },
        "notes": notes,
    }


def analyze(data: dict) -> dict:
    """对音符数据做结构分析：音域、密度、力度、最长静默。"""
    notes = data["notes"]
    if not notes:
        return {"empty": True}

    pitches = [n["pitch"] for n in notes]
    vels = [n["velocity"] for n in notes]
    duration = data["meta"]["duration_sec"] or 1.0

    # 每秒音符密度（density map）
    buckets = {}
    for n in notes:
        sec = int(n["start"])
        buckets[sec] = buckets.get(sec, 0) + 1
    density = [buckets.get(s, 0) for s in range(int(duration) + 1)]

    # 最长静默：相邻音符之间的最大空隙
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
    ap.add_argument("audio", help="输入音频文件 (mp3/wav/flac)")
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
    if args.analyze:
        a = data["analysis"]
        if not a.get("empty"):
            pr = a["pitch_range"]
            print(f"  音域 {pr['lowest']}~{pr['highest']}（{pr['span_semitones']}个半音）", file=sys.stderr)
            print(f"  平均每秒 {a['notes_per_sec_avg']} 个音，最密在第 {a['busiest_sec']} 秒", file=sys.stderr)
            print(f"  最长静默 {a['longest_silence']['seconds']}秒", file=sys.stderr)


if __name__ == "__main__":
    main()
