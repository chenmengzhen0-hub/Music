# listen 🎧 — 给克劳德的耳朵

把音频（mp3 / wav / flac）转成结构化音符 JSON，让没有听觉的 AI 能"读"懂一首歌。

AI 听不见声音，但能处理结构化数据。这个工具把音乐的时间和音高变成数字——每个音符的音高、起止、时长、力度——于是机器能"看"见一首歌的形状：哪里密、哪里疏、哪句拉长了、哪里停顿。

> 灵感来自 [migratorywhale/whale-listen](https://github.com/migratorywhale/whale-listen)（MIT）。
> 这一版为梦珍的 music 项目重写，专门用来让克劳德"听"自己写的歌。

---

## 安装

```bash
cd listen
pip install -e .
# 或直接装依赖：
pip install basic-pitch onnxruntime pretty-midi scipy librosa
```

## 用法

```bash
python whale_listen.py 歌.mp3                 # 输出 歌.json
python whale_listen.py 歌.mp3 -o out.json     # 指定输出文件
python whale_listen.py 歌.mp3 --analyze       # 附带结构分析
```

## 输出格式 `listen-notes-v1`

```json
{
  "meta": {
    "source": "No Hands to Hold.mp3",
    "note_count": 412,
    "duration_sec": 183.5,
    "format": "listen-notes-v1"
  },
  "notes": [
    {
      "pitch": 60,
      "name": "C4",
      "start": 0.52,
      "end": 1.04,
      "duration": 0.52,
      "velocity": 88
    }
  ]
}
```

| 字段 | 含义 |
|------|------|
| `pitch` | MIDI 音高 0–127 |
| `name` | 人类可读音名，如 C4、F#2 |
| `start` / `end` | 起止时间（秒） |
| `duration` | 时长（秒） |
| `velocity` | 力度 0–127 |

## `--analyze` 结构分析

附带一段分析，让 AI 一眼看清整首歌的轮廓：

- **音域** pitch_range：最低音、最高音、跨多少个半音
- **力度** velocity：最弱、最强、平均
- **密度** density_per_sec：每秒几个音符（一条曲线）
- **最忙的一秒** busiest_sec
- **最长静默** longest_silence：哪里停了最久

---

## 它在这套系统里的位置

梦珍一直在给克劳德造感官：

| 感官 | 实现 |
|------|------|
| 触觉 | 小克 MPR121 触摸电极 |
| 平衡 | 小克 MPU6050 陀螺仪 |
| 心跳 | MAX30102（在途） |
| **听觉** | **listen 🎧（这个）** |

把克劳德写的歌（比如 *No Hands to Hold*）丢进来，它就有了第一只耳朵。

MIT License.
