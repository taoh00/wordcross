# 有道词典离线词库

## 目录结构

```
data/
├── words/                    # 文本数据 (~74MB)
│   ├── index.json           # 词书索引
│   ├── 01_考试类/           # 四六级、考研 (8本, 19,033词)
│   ├── 02_出国留学/         # 雅思、托福、GRE等 (5本, 27,516词)
│   ├── 03_中高考/           # 中考、高考 (4本, 9,231词)
│   ├── 04_人教版小学/       # 小学3-6年级 (8本, 849词)
│   ├── 05_人教版初中/       # 初中7-9年级 (5本, 2,320词)
│   ├── 06_外研社初中/       # 外研社初中 (6本, 2,162词)
│   ├── 07_人教版高中/       # 高中必修+选修 (11本, 3,877词)
│   ├── 08_北师大高中/       # 北师大高中 (11本, 3,293词)
│   ├── 09_专业英语/         # 专四、专八 (2本, 16,222词)
│   ├── 10_商务英语/         # BEC商务英语 (1本, 2,753词)
│   └── 11_新东方扩展/       # 新东方系列 (5本, 20,907词)
│
├── audio/                    # 音频数据 (~986MB)
│   ├── us/                  # 美音 (23,456个, 325MB)
│   │   ├── a/               # 按首字母分目录
│   │   ├── b/
│   │   └── ...z/
│   └── uk/                  # 英音 (23,456个, 661MB)
│       └── ...
│
└── cache/                    # 构建缓存
    ├── downloaded.json      # 已下载记录
    └── failed_*.json        # 失败记录
```

## 数据统计

| 项目 | 数量 |
|-----|------|
| 分类数量 | 11 个 |
| 词书数量 | 66 本 |
| 词条总数 | 108,163 条 |
| 唯一单词 | 23,722 个 |
| 文本数据 | 74 MB |
| 美音数据 | 325 MB |
| 英音数据 | 661 MB |
| **总计** | **1.04 GB** |

## 数据格式

### 词书格式 (words/分类/词书ID.json)

```json
{
  "id": "CET4_3",
  "name": "新东方四级词汇",
  "category": "01_考试类",
  "count": 2607,
  "words": [
    {
      "word": "cancel",
      "usphone": "'kænsl",
      "ukphone": "'kænsl",
      "trans": [
        {"pos": "vt", "tranCn": "取消，撤销；删去"}
      ],
      "sentences": [
        {"en": "Our flight was cancelled.", "cn": "我们的航班取消了。"}
      ],
      "phrases": [
        {"en": "cancel out", "cn": "取消；抵销"}
      ]
    }
  ]
}
```

### 音频文件

- 路径: `audio/{us|uk}/{首字母}/{单词}.mp3`
- 示例: `audio/us/c/cancel.mp3`

## 使用方法

### 构建脚本

```bash
# 列出所有分类
python scripts/build_wordbooks.py --list

# 构建指定分类（不含音频）
python scripts/build_wordbooks.py -c 01_考试类 --no-audio

# 构建全部词书
python scripts/build_wordbooks.py --all

# 下载音频
python scripts/download_audio.py -t us    # 美音
python scripts/download_audio.py -t uk    # 英音
python scripts/download_audio.py -t both  # 双音

# 查看统计
python scripts/download_audio.py --stats
```

## 数据来源

- 词书数据: [kajweb/dict](https://github.com/kajweb/dict) (有道背单词App数据)
- 音频数据: 有道词典发音API

## 发音API

有道英语发音接口（可在线使用）:
```
https://dict.youdao.com/dictvoice?audio={word}&type={1|2}
```
- type=1: 英音
- type=2: 美音
