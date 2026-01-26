# 词汇资源整理文档

> 更新日期: 2026-01-24  
> 用途: 为"我爱填单词"项目整理权威词汇分类和资源

---

## 一、词库分类体系

### 1.1 推荐的权威分类结构

| 分类代码 | 名称 | 词汇数量 | 适用人群 | 来源依据 |
|---------|------|---------|---------|---------|
| **基础教育阶段** |
| primary_3 | 小学三年级 | ~64个 | 8-9岁 | 人教版教材 |
| primary_4 | 小学四年级 | ~84个 | 9-10岁 | 人教版教材 |
| primary_5 | 小学五年级 | ~131个 | 10-11岁 | 人教版教材 |
| primary_6 | 小学六年级 | ~130个 | 11-12岁 | 人教版教材 |
| junior_7 | 初一/七年级 | ~392个 | 12-13岁 | 人教版教材 |
| junior_8 | 初二/八年级 | ~419个 | 13-14岁 | 人教版教材 |
| junior_9 | 初三/九年级 | ~551个 | 14-15岁 | 人教版教材 |
| zhongkao | 中考必备 | ~1420个 | 初三 | 有道词典 |
| **高中阶段** |
| senior_1 | 高一必修 | ~630个 | 15-16岁 | 人教版必修1-2 |
| senior_2 | 高二必修 | ~673个 | 16-17岁 | 人教版必修3-4 |
| senior_3 | 高三选修 | ~357个 | 17-18岁 | 人教版必修5 |
| gaokao | 高考3500词 | ~3668个 | 高三 | 高考大纲 |
| **大学阶段** |
| cet4 | 大学四级 | ~3739个 | 大一大二 | 四级大纲2016版 |
| cet6 | 大学六级 | ~2078个 | 大二大三 | 六级大纲2016版 |
| postgrad | 考研英语 | ~4533个 | 大四/考研 | 考研大纲 |
| **专业英语** |
| tem4 | 专四 | ~4025个 | 英语专业大二 | 专四大纲 |
| tem8 | 专八 | ~12197个 | 英语专业大四 | 专八大纲 |
| **剑桥英语** |
| ket | KET(A2) | ~1500个 | 对应中考水平 | 剑桥官方词汇表 |
| pet | PET(B1) | ~3500个 | 对应高考水平 | 剑桥官方词汇表 |
| fce | FCE(B2) | ~5000个 | 对应大学水平 | 剑桥官方 |
| **留学考试** |
| ielts | 雅思 | ~3427个 | 出国留学 | 有道/新东方 |
| toefl | 托福 | ~9213个 | 出国留学 | 有道/新东方 |
| gre | GRE | ~7199个 | 北美研究生 | 有道/新东方 |
| sat | SAT | ~4423个 | 美国高考 | 有道/新东方 |
| gmat | GMAT | ~3254个 | 商学院 | 有道/新东方 |
| **其他** |
| bec | 商务英语 | ~2753个 | 职场人士 | BEC考试 |
| coca | COCA词频 | ~20000个 | 通用 | 美国语料库 |

---

## 二、开源词库资源

### 2.1 kajweb/dict（推荐⭐⭐⭐⭐⭐）

**地址**: https://github.com/kajweb/dict  
**Stars**: 2,984 ⭐  
**数据来源**: 有道背单词APP  
**特点**: 数据最全，包含例句、音标、发音、同义词等

#### 词库列表（81本词书）

| 序号 | 名称 | 单词数 | ID |
|-----|------|-------|-----|
| 1 | 四级真题核心词 | 1162 | CET4luan_1 |
| 2 | 六级真题核心词 | 1228 | CET6luan_1 |
| 3 | 考研必考词汇 | 1341 | KaoYanluan_1 |
| 6 | 四级英语词汇 | 3739 | CET4luan_2 |
| 7 | 六级英语词汇 | 2078 | CET6_2 |
| 8 | 考研英语词汇 | 4533 | KaoYan_2 |
| 11 | 新东方四级词汇 | 2607 | CET4_3 |
| 12 | 新东方六级词汇 | 2345 | CET6_3 |
| 21 | 雅思词汇 | 3427 | IELTSluan_2 |
| 22 | TOEFL词汇 | 9213 | TOEFL_2 |
| 23 | GRE词汇 | 7199 | GRE_2 |
| 24 | SAT词汇 | 4423 | SAT_2 |
| 25 | GMAT词汇 | 3254 | GMATluan_2 |
| 33 | 中考必备词汇 | 1420 | ChuZhongluan_2 |
| 34 | 高考必备词汇 | 3668 | GaoZhongluan_2 |
| 35 | 新东方初中词汇 | 1803 | ChuZhong_3 |
| 36 | 新东方高中词汇 | 2340 | GaoZhong_3 |
| 37-44 | 人教版小学3-6年级 | 64-156 | PEPXiaoXue3_1~6_2 |
| 45-49 | 人教版初中7-9年级 | 392-551 | PEPChuZhong7_1~9_1 |
| 50-55 | 外研社版初中7-9年级 | 128-629 | WaiYanSheChuZhong_1~6 |
| 56-66 | 人教版高中必修/选修 | 307-420 | PEPGaoZhong_1~11 |
| 71-81 | 北师大版高中 | 226-364 | BeiShiGaoZhong_1~11 |
| 69 | 商务英语词汇 | 2753 | BEC_2 |

#### JSON数据格式

```json
{
  "wordRank": 1,
  "headWord": "cancel",
  "content": {
    "word": {
      "wordHead": "cancel",
      "wordId": "CET4_3_1",
      "content": {
        "usphone": "'kænsl",
        "ukphone": "'kænsl",
        "usspeech": "cancel&type=2",
        "ukspeech": "cancel&type=1",
        "trans": [
          {"tranCn": "取消，撤销；删去", "pos": "vt", "tranOther": "英英释义..."}
        ],
        "sentence": {
          "sentences": [
            {"sContent": "Our flight was cancelled.", "sCn": "我们的航班取消了。"}
          ]
        },
        "phrase": {
          "phrases": [
            {"pContent": "cancel out", "pCn": "取消；抵销"}
          ]
        },
        "syno": {
          "synos": [
            {"pos": "vt", "tran": "取消", "hwds": [{"w": "recall"}, {"w": "call it off"}]}
          ]
        },
        "relWord": {
          "rels": [
            {"pos": "n", "words": [{"hwd": "cancellation", "tran": "取消"}]}
          ]
        }
      }
    }
  }
}
```

---

### 2.2 mahavivo/english-wordlists

**地址**: https://github.com/mahavivo/english-wordlists  
**Stars**: 2,223 ⭐  
**特点**: 纯文本词汇表，适合快速导入

#### 主要文件

| 文件名 | 说明 |
|-------|------|
| CET4_edited.txt | 四级词汇(已校对) |
| CET6_edited.txt | 六级词汇(已校对) |
| CET_4+6_edited.txt | 四六级综合词汇(2016大纲) |
| Highschool_edited.txt | 高中词汇 |
| TOEFL.txt | 托福词汇 |
| GRE_8000_Words.txt | GRE 8000词 |
| COCA_20000.txt | COCA词频20000 |
| COCA_with_translation.txt | COCA带中文翻译 |
| 小学英语大纲词汇.txt | 小学词汇大纲 |
| 中考英语词汇表.txt | 中考词汇 |
| 上海市初中英语词汇表（2020年版）.pdf | 上海中考官方 |
| 红宝书 GRE词汇精选.csv | GRE红宝书 |

**官方来源**:
- 四六级词汇来自: http://www.cet.edu.cn/file_2016_1.pdf (全国大学英语四、六级考试大纲2016版)

---

### 2.3 RealKai42/qwerty-learner

**地址**: https://github.com/RealKai42/qwerty-learner  
**Stars**: 21,371 ⭐  
**特点**: 热门打字背单词项目，词库数据来自kajweb/dict

#### 内置词库

- CET-4/6, GMAT, GRE, IELTS, SAT, TOEFL
- 考研英语、专四、专八
- 高考3500词、中考
- 商务英语、BEC
- 人教版3-9年级英语
- 新概念英语1-4册
- 日语N1~N5
- 程序员常用词、各语言API

---

## 三、剑桥官方词汇表（KET/PET/FCE）

### 3.1 官方资源

| 考试 | CEFR级别 | 词汇表链接 | 词汇数量 |
|-----|---------|-----------|---------|
| KET | A2 | Cambridge官网 | ~1500 |
| PET | B1 | [84669-pet-vocabulary-list.pdf](https://www.cambridgeenglish.org/Images/84669-pet-vocabulary-list.pdf) | ~3500 |
| FCE | B2 | Cambridge官网 | ~5000+ |

### 3.2 PET词汇表结构（B1级别）

根据剑桥官方PDF，PET词汇表包含：

**按主题分类**:
- Clothes and Accessories（服装配饰）
- Colours（颜色）
- Communications and Technology（通讯技术）
- Education（教育）
- Entertainment and Media（娱乐媒体）
- Environment（环境）
- Food and Drink（饮食）
- Health, Medicine and Exercise（健康医疗）
- Hobbies and Leisure（兴趣休闲）
- House and Home（家居）
- Language（语言）
- Personal Feelings, Opinions and Experiences（情感观点）
- Places: Buildings（建筑）
- Places: Countryside（乡村）
- Places: Town and City（城镇）
- Services（服务）
- Shopping（购物）
- Sport（体育）
- The Natural World（自然）
- Time（时间）
- Travel and Transport（旅行交通）
- Weather（天气）
- Work and Jobs（工作职业）

---

## 四、发音资源

### 4.1 有道词典API（推荐）

```
https://dict.youdao.com/dictvoice?audio={word}&type={1|2}
```

- `type=1`: 英音
- `type=2`: 美音

**优点**: 免费、稳定、音质好

### 4.2 Forvo

**地址**: https://forvo.com/  
**特点**: 真人发音，多种口音  
**用途**: 验证发音，获取小众单词发音

### 4.3 其他TTS方案

| 服务 | 说明 |
|-----|------|
| Google TTS | 需要API Key |
| Microsoft Azure TTS | 高质量，付费 |
| Amazon Polly | 付费 |
| 百度TTS | 国内可用 |

---

## 五、数据获取方案

### 5.1 方案A: 使用kajweb/dict（推荐）

```bash
# 克隆仓库
git clone https://github.com/kajweb/dict.git

# 词库数据在 book/ 目录下
# 每个词库是一个zip文件，解压后是JSON格式
```

**数据处理脚本示例**:

```python
import json
import zipfile

def extract_vocabulary(zip_path):
    """从kajweb/dict的zip文件提取词汇"""
    words = []
    with zipfile.ZipFile(zip_path, 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.json'):
                with z.open(filename) as f:
                    data = json.load(f)
                    for item in data:
                        word_info = {
                            'word': item['headWord'],
                            'definition': '',
                            'phonetic_us': '',
                            'phonetic_uk': '',
                        }
                        content = item.get('content', {}).get('word', {}).get('content', {})
                        if content:
                            # 提取释义
                            trans = content.get('trans', [])
                            if trans:
                                word_info['definition'] = trans[0].get('tranCn', '')
                            # 提取音标
                            word_info['phonetic_us'] = content.get('usphone', '')
                            word_info['phonetic_uk'] = content.get('ukphone', '')
                        words.append(word_info)
    return words
```

### 5.2 方案B: 爬取官方词汇表

对于KET/PET等剑桥官方词汇，可以从官方PDF提取。

### 5.3 发音下载

```python
import requests
import os

def download_pronunciation(word, output_dir, accent='us'):
    """下载有道发音"""
    type_code = 2 if accent == 'us' else 1
    url = f"https://dict.youdao.com/dictvoice?audio={word}&type={type_code}"
    
    response = requests.get(url)
    if response.status_code == 200:
        filepath = os.path.join(output_dir, f"{word}_{accent}.mp3")
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
    return None
```

---

## 六、项目词库结构建议

### 6.1 基础教育（小学+初中+高中）

```
vocabulary/
├── primary/
│   ├── grade3_上.json  # 人教版三年级上
│   ├── grade3_下.json
│   ├── grade4_上.json
│   ├── grade4_下.json
│   ├── grade5_上.json
│   ├── grade5_下.json
│   ├── grade6_上.json
│   └── grade6_下.json
├── junior/
│   ├── grade7_上.json
│   ├── grade7_下.json
│   ├── grade8_上.json
│   ├── grade8_下.json
│   └── grade9_全.json
├── senior/
│   ├── 必修1.json
│   ├── 必修2.json
│   ├── 必修3.json
│   ├── 必修4.json
│   └── 必修5.json
└── exam/
    ├── zhongkao.json     # 中考词汇
    └── gaokao.json       # 高考词汇
```

### 6.2 大学+考试

```
vocabulary/
├── college/
│   ├── cet4.json
│   ├── cet6.json
│   └── postgrad.json
├── cambridge/
│   ├── ket.json
│   └── pet.json
└── abroad/
    ├── ielts.json
    ├── toefl.json
    └── gre.json
```

### 6.3 JSON格式建议

```json
{
  "meta": {
    "name": "人教版小学英语-三年级上册",
    "code": "primary_3_1",
    "level": "primary",
    "grade": 3,
    "semester": 1,
    "word_count": 64,
    "source": "kajweb/dict",
    "updated": "2026-01-24"
  },
  "words": [
    {
      "word": "hello",
      "definition": "你好",
      "phonetic_us": "/həˈloʊ/",
      "phonetic_uk": "/həˈləʊ/",
      "difficulty": 1,
      "audio_us": "hello&type=2",
      "audio_uk": "hello&type=1",
      "examples": [
        {"en": "Hello, how are you?", "zh": "你好，你好吗？"}
      ]
    }
  ]
}
```

---

## 七、下一步行动

### 7.1 数据准备

1. [ ] 克隆 kajweb/dict 仓库
2. [ ] 编写数据转换脚本，将词库转为项目所需格式
3. [ ] 下载剑桥KET/PET官方词汇表PDF并提取数据
4. [ ] 生成各级别词库JSON文件

### 7.2 发音处理

1. [ ] 使用有道API批量下载发音文件
2. [ ] 或在前端使用在线发音API（节省存储）

### 7.3 词库验证

1. [ ] 检查词汇去重
2. [ ] 验证中文释义准确性
3. [ ] 确保发音可用

---

## 八、参考链接

| 资源 | 地址 |
|-----|------|
| kajweb/dict | https://github.com/kajweb/dict |
| mahavivo/english-wordlists | https://github.com/mahavivo/english-wordlists |
| qwerty-learner | https://github.com/RealKai42/qwerty-learner |
| 剑桥PET词汇表 | https://www.cambridgeenglish.org/Images/84669-pet-vocabulary-list.pdf |
| 四六级大纲2016 | http://www.cet.edu.cn/file_2016_1.pdf |
| 有道发音API | https://dict.youdao.com/dictvoice?audio={word}&type={1\|2} |
| Forvo发音词典 | https://forvo.com/ |

---

*文档结束*
