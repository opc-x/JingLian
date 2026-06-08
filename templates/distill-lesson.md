# Agent 精炼模板：Callan Lesson → 蒸馏版

## 输入

- 来源：`sources/callan/extracted/book-{NN}.json`
- 目标 Lesson ID：
- 精炼目标：（例：口语卡片 / 场景对话 / 错题本 / 极速复习版）

## 精炼原则

1. **保留 Callan 的快问快答节奏**，但去掉冗余重复
2. 词汇附带场景例句，不要干巴巴词表
3. 问答对按**场景**分组（购物、问路、工作…）
4. 标注难度与复习间隔建议
5. 输出必须可机器读取（JSON 或 Markdown 结构化）

## 输出格式

```json
{
  "source": "callan/book-01/lesson-03",
  "distilledAt": "YYYY-MM-DD",
  "title": "",
  "scenes": [
    {
      "name": "",
      "vocabulary": [{ "word": "", "meaningZh": "", "example": "" }],
      "drills": [{ "question": "", "answer": "", "tip": "" }]
    }
  ],
  "reviewNotes": ""
}
```

## 禁止

- 不要改动 `sources/` 原件
- 产物写入 `distilled/callan/book-{NN}/`
