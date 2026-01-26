#!/usr/bin/env python3
"""
估算有道词典所有词库的存储空间需求
基于 kajweb/dict 的81本词书数据
"""

# 有道词典官方分类词库（来自kajweb/dict）
YOUDAO_WORDBOOKS = {
    # ========== 考试类 ==========
    "四级真题核心词 (CET4luan_1)": 1162,
    "六级真题核心词 (CET6luan_1)": 1228,
    "考研必考词汇 (KaoYanluan_1)": 1341,
    "四级英语词汇 (CET4luan_2)": 3739,
    "六级英语词汇 (CET6_2)": 2078,
    "考研英语词汇 (KaoYan_2)": 4533,
    "新东方四级词汇 (CET4_3)": 2607,
    "新东方六级词汇 (CET6_3)": 2345,
    
    # ========== 出国留学 ==========
    "雅思词汇 (IELTSluan_2)": 3427,
    "TOEFL词汇 (TOEFL_2)": 9213,
    "GRE词汇 (GRE_2)": 7199,
    "SAT词汇 (SAT_2)": 4423,
    "GMAT词汇 (GMATluan_2)": 3254,
    
    # ========== 中高考 ==========
    "中考必备词汇 (ChuZhongluan_2)": 1420,
    "高考必备词汇 (GaoZhongluan_2)": 3668,
    "新东方初中词汇 (ChuZhong_3)": 1803,
    "新东方高中词汇 (GaoZhong_3)": 2340,
    
    # ========== 人教版小学 ==========
    "人教版小学三年级上 (PEPXiaoXue3_1)": 64,
    "人教版小学三年级下 (PEPXiaoXue3_2)": 68,
    "人教版小学四年级上 (PEPXiaoXue4_1)": 84,
    "人教版小学四年级下 (PEPXiaoXue4_2)": 78,
    "人教版小学五年级上 (PEPXiaoXue5_1)": 131,
    "人教版小学五年级下 (PEPXiaoXue5_2)": 110,
    "人教版小学六年级上 (PEPXiaoXue6_1)": 130,
    "人教版小学六年级下 (PEPXiaoXue6_2)": 156,
    
    # ========== 人教版初中 ==========
    "人教版初中七年级上 (PEPChuZhong7_1)": 392,
    "人教版初中七年级下 (PEPChuZhong7_2)": 335,
    "人教版初中八年级上 (PEPChuZhong8_1)": 419,
    "人教版初中八年级下 (PEPChuZhong8_2)": 404,
    "人教版初中九年级全册 (PEPChuZhong9_1)": 551,
    
    # ========== 外研社版初中 ==========
    "外研社初中七年级上 (WaiYanSheChuZhong_1)": 420,
    "外研社初中七年级下 (WaiYanSheChuZhong_2)": 380,
    "外研社初中八年级上 (WaiYanSheChuZhong_3)": 450,
    "外研社初中八年级下 (WaiYanSheChuZhong_4)": 420,
    "外研社初中九年级上 (WaiYanSheChuZhong_5)": 380,
    "外研社初中九年级下 (WaiYanSheChuZhong_6)": 350,
    
    # ========== 人教版高中 ==========
    "人教版高中必修1 (PEPGaoZhong_1)": 380,
    "人教版高中必修2 (PEPGaoZhong_2)": 350,
    "人教版高中必修3 (PEPGaoZhong_3)": 420,
    "人教版高中必修4 (PEPGaoZhong_4)": 380,
    "人教版高中必修5 (PEPGaoZhong_5)": 357,
    "人教版高中选修6 (PEPGaoZhong_6)": 307,
    "人教版高中选修7 (PEPGaoZhong_7)": 340,
    "人教版高中选修8 (PEPGaoZhong_8)": 360,
    "人教版高中选修9 (PEPGaoZhong_9)": 320,
    "人教版高中选修10 (PEPGaoZhong_10)": 300,
    "人教版高中选修11 (PEPGaoZhong_11)": 280,
    
    # ========== 北师大版高中 ==========
    "北师大高中必修1 (BeiShiGaoZhong_1)": 320,
    "北师大高中必修2 (BeiShiGaoZhong_2)": 300,
    "北师大高中必修3 (BeiShiGaoZhong_3)": 340,
    "北师大高中必修4 (BeiShiGaoZhong_4)": 320,
    "北师大高中必修5 (BeiShiGaoZhong_5)": 300,
    "北师大高中选修6 (BeiShiGaoZhong_6)": 280,
    "北师大高中选修7 (BeiShiGaoZhong_7)": 290,
    "北师大高中选修8 (BeiShiGaoZhong_8)": 300,
    "北师大高中选修9 (BeiShiGaoZhong_9)": 260,
    "北师大高中选修10 (BeiShiGaoZhong_10)": 240,
    "北师大高中选修11 (BeiShiGaoZhong_11)": 226,
    
    # ========== 专业英语 ==========
    "专四词汇 (TEM4)": 4025,
    "专八词汇 (TEM8)": 12197,
    
    # ========== 商务英语 ==========
    "商务英语词汇 (BEC_2)": 2753,
    
    # ========== 剑桥英语 ==========
    "KET词汇 (A2)": 1500,
    "PET词汇 (B1)": 3500,
    "FCE词汇 (B2)": 5000,
    
    # ========== 其他 ==========
    "COCA词频20000": 20000,
}

def estimate_storage():
    """估算存储空间"""
    
    # 统计总词数
    total_words = sum(YOUDAO_WORDBOOKS.values())
    total_books = len(YOUDAO_WORDBOOKS)
    
    # 估算去重后的唯一单词数（很多词库有重复）
    # 根据经验，实际唯一单词约为总数的40-50%
    unique_words_ratio = 0.45
    unique_words = int(total_words * unique_words_ratio)
    
    print("=" * 60)
    print("有道词典词库存储空间估算")
    print("=" * 60)
    
    print(f"\n📚 词库统计:")
    print(f"   - 词书数量: {total_books} 本")
    print(f"   - 词条总数: {total_words:,} 条")
    print(f"   - 估计唯一单词数: ~{unique_words:,} 个")
    
    # ========== 文本数据估算 ==========
    print(f"\n📄 文本数据估算:")
    
    # 每个单词的JSON数据大小（包含释义、例句、音标、同义词等）
    # 根据kajweb/dict的实际数据格式，每个完整词条约1.5-3KB
    bytes_per_word_full = 2.5 * 1024  # 2.5KB平均
    bytes_per_word_simple = 0.5 * 1024  # 0.5KB精简版
    
    text_size_full = total_words * bytes_per_word_full
    text_size_simple = total_words * bytes_per_word_simple
    
    print(f"   - 完整版(含例句/同义词): {text_size_full / (1024*1024):.1f} MB")
    print(f"   - 精简版(仅释义/音标): {text_size_simple / (1024*1024):.1f} MB")
    
    # ========== 音频数据估算 ==========
    print(f"\n🔊 音频数据估算:")
    
    # 有道发音API返回的MP3，单词发音通常2-8秒
    # 短单词(如cat): ~3KB
    # 中等单词(如beautiful): ~5KB  
    # 长单词(如congratulations): ~10KB
    # 平均约5KB每个单词
    
    avg_audio_size = 5 * 1024  # 5KB平均
    
    # 只存唯一单词的音频
    audio_us_only = unique_words * avg_audio_size
    audio_uk_only = unique_words * avg_audio_size
    audio_both = unique_words * avg_audio_size * 2
    
    print(f"   - 仅美音: {audio_us_only / (1024*1024):.1f} MB ({unique_words:,} 个文件)")
    print(f"   - 仅英音: {audio_uk_only / (1024*1024):.1f} MB ({unique_words:,} 个文件)")
    print(f"   - 英美双音: {audio_both / (1024*1024):.1f} MB ({unique_words*2:,} 个文件)")
    
    # ========== 总计 ==========
    print(f"\n📊 总存储空间估算:")
    
    scenarios = [
        ("精简方案 (精简文本+美音)", text_size_simple + audio_us_only),
        ("标准方案 (完整文本+美音)", text_size_full + audio_us_only),
        ("完整方案 (完整文本+双音)", text_size_full + audio_both),
    ]
    
    for name, size in scenarios:
        mb = size / (1024 * 1024)
        gb = size / (1024 * 1024 * 1024)
        print(f"   - {name}: {mb:.1f} MB ({gb:.2f} GB)")
    
    # ========== 分类汇总 ==========
    print(f"\n📋 各分类词汇数量:")
    
    categories = {
        "考试类(四六级/考研)": ["四级", "六级", "考研", "新东方"],
        "出国留学(雅思/托福/GRE等)": ["雅思", "TOEFL", "GRE", "SAT", "GMAT"],
        "中高考": ["中考", "高考"],
        "人教版小学": ["人教版小学"],
        "人教版初中": ["人教版初中"],
        "人教版高中": ["人教版高中"],
        "外研社初中": ["外研社"],
        "北师大高中": ["北师大"],
        "专业英语(专四/专八)": ["专四", "专八"],
        "商务英语": ["商务"],
        "剑桥英语(KET/PET/FCE)": ["KET", "PET", "FCE"],
        "COCA词频": ["COCA"],
    }
    
    for cat_name, keywords in categories.items():
        cat_words = sum(
            count for name, count in YOUDAO_WORDBOOKS.items()
            if any(kw in name for kw in keywords)
        )
        print(f"   - {cat_name}: {cat_words:,} 词")
    
    # ========== 建议 ==========
    print(f"\n💡 建议方案:")
    print("   1. 文本数据: 本地存储JSON文件 (~50-200MB)")
    print("   2. 音频数据: 推荐使用在线API，按需加载")
    print("      - 有道API: https://dict.youdao.com/dictvoice?audio={word}&type=2")
    print("      - 完全免费，无需存储")
    print("   3. 如需离线: 可只下载常用词库的音频 (约200-300MB)")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    estimate_storage()
