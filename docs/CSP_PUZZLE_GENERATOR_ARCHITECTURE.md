# CSP 填字游戏生成器架构设计

## 概述

本文档描述了使用**约束满足问题 (CSP)** 方法重构的填字游戏关卡生成器。该生成器参考了纽约时报 Mini Crossword 的设计理念，实现了高质量、每个格子都有用的填字游戏生成。

## 设计目标

1. **每个格子都有用** - 横向和纵向的单词槽位都有效填充
2. **交叉约束满足** - 所有交叉点的字母必须一致
3. **支持多种网格大小** - 6x6 到 10x10
4. **高效生成** - 使用模板+CSP混合策略确保快速生成

## 核心架构

### 1. 模块结构

```
src/backend/
├── csp_puzzle_generator.py   # CSP生成器主模块
├── puzzle_generator.py       # 原有传统生成器
├── vocabulary.py             # 词汇管理器
└── main.py                   # FastAPI服务
```

### 2. 类图

```
┌─────────────────────────┐
│    CSPPuzzleGenerator   │
├─────────────────────────┤
│ - _answer_cache         │
│ - _word_id_counter      │
├─────────────────────────┤
│ + generate_campaign_level()  │
│ + generate_random_puzzle()   │
│ + generate_template_puzzle() │
│ + verify_answer()            │
└─────────────────────────┘
            │
            ▼
┌─────────────────────────┐
│   TemplateCSPSolver     │
├─────────────────────────┤
│ - word_index            │
│ - grid_size             │
│ - template              │
├─────────────────────────┤
│ + solve()               │
│ - _backtrack_template() │
│ - _find_intersection()  │
│ - _is_consistent_template() │
└─────────────────────────┘
            │
            ▼
┌─────────────────────────┐
│       WordIndex         │
├─────────────────────────┤
│ - by_length             │
│ - position_letter_index │
│ - word_to_info          │
├─────────────────────────┤
│ + get_words_by_length() │
│ + get_compatible_words()│
│ + get_word_info()       │
└─────────────────────────┘
```

## CSP 建模

### 变量 (Variables)
- 每个单词槽位是一个变量
- 6x6 模板通常有 6-8 个变量

### 域 (Domain)
- 每个变量的域是符合长度要求的所有单词
- 域在求解过程中会被约束传播削减

### 约束 (Constraints)
- **交叉约束**: 如果槽位 A 和槽位 B 相交于某个格子，则：
  - A 中单词在交叉位置的字母 = B 中单词在交叉位置的字母

## 算法流程

### 1. 模板选择
```python
# 预定义的高质量填字模板
TEMPLATES_6X6 = [
    # 模板定义 (row, col, direction, length)
    [(0, 0, "across", 6), (2, 0, "across", 3), ...],
    ...
]
```

### 2. 约束构建
```python
def _find_intersection(slot1, slot2):
    """找出两个槽位的交叉点"""
    # 返回 (pos_in_slot1, pos_in_slot2) 或 None
```

### 3. 回溯搜索 + MRV 启发式
```python
def _backtrack_template(slots, constraints, assignment):
    if len(assignment) == len(slots):
        return assignment  # 找到解
    
    var = select_mrv_variable(slots, assignment)  # 最少剩余值
    
    for word in slots[var].domain:
        if is_consistent(var, word, assignment):
            assignment[var] = word
            result = backtrack_template(...)
            if result:
                return result
            del assignment[var]
    
    return None  # 回溯
```

## 模板设计

### 6x6 模板示例

```
模板1 (经典对称):
┌─┬─┬─┬─┬─┬─┐
│A│A│A│A│A│A│  <- 横向6字母
├─┼─┼─┼─┼─┼─┤
│D│ │D│ │D│ │
├─┼─┼─┼─┼─┼─┤
│A│A│A│A│A│A│  <- 横向3+3字母
├─┼─┼─┼─┼─┼─┤
│D│ │D│ │D│ │
├─┼─┼─┼─┼─┼─┤
│A│A│A│A│A│A│  <- 横向6字母
├─┼─┼─┼─┼─┼─┤
│ │ │ │ │ │ │
└─┴─┴─┴─┴─┴─┘

A = Across (横向)
D = Down (纵向)
```

### 支持的网格大小
- **6x6**: 入门级 (easy)
- **7x7**: 中级 (medium)
- **8x8**: 困难 (hard)
- **9x9**: 专家 (expert)
- **10x10**: 大师 (master)

## API 使用

### 生成关卡

```python
from csp_puzzle_generator import CSPPuzzleGenerator
from vocabulary import VocabularyManager

vocab_manager = VocabularyManager()
generator = CSPPuzzleGenerator()

# 生成闯关关卡
puzzle = generator.generate_campaign_level(
    level=1,
    group="junior",
    vocab_manager=vocab_manager
)

# 生成随机关卡
puzzle = generator.generate_random_puzzle(
    group="cet4",
    difficulty="medium",
    vocab_manager=vocab_manager
)
```

### REST API

```
GET /api/campaign/level/{level}?group=junior&mode=csp
GET /api/endless/puzzle?group=cet4&difficulty=medium&mode=csp
```

## 性能特点

- **生成速度**: 通常 < 500ms
- **成功率**: > 95%（使用合并词库）
- **内存占用**: 适中（单词索引预计算）

## 与纽约时报 Mini Crossword 的区别

| 特性 | NYT Mini | 本实现 |
|------|----------|--------|
| 网格大小 | 固定 5x5 | 6x6 到 10x10 |
| 格子利用率 | 100% 密集 | 模板决定（~60-80%）|
| 单词来源 | 精心策划 | 教育词库 |
| 生成方式 | 人工设计 | CSP 自动生成 |

## 未来优化方向

1. **更多模板**: 添加更多高质量模板增加多样性
2. **密集填字**: 对于特定词库，尝试完全密集填字
3. **难度调节**: 根据单词难度动态调整预填提示
4. **主题关卡**: 按主题分类单词生成关联关卡

## 文件列表

- `csp_puzzle_generator.py` - CSP 生成器实现
- `vocabulary.py` - 词汇管理（含 `get_all_words_for_csp` 方法）
- `main.py` - FastAPI 服务（支持 `mode=csp` 参数）
