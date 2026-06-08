# JingLian 架构

## 两层资产

```
sources/     原材料（PDF、提取 JSON）— 只读
distilled/   精炼产物 — Agent 可反复迭代
```

## 流水线

1. **Import**：PDF 入库 `sources/*/raw/`
2. **Extract**：脚本把 PDF → 结构化 JSON（问答、词汇）
3. **Distill**：Agent 按模板重组 → `distilled/`
4. **Consume**：TalkFlow / App / Anki 等下游消费 `distilled/`

## 扩展新教材

```
sources/
├── callan/
├── other-method-x/    # 以后加
└── ...
```

每种教材：`raw/` + `meta/manifest.json` + `extracted/` + 对应 `distilled/` 子目录。
