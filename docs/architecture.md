# JingLian 架构

## 品牌分层

```
JingLian（引擎）          JingYu 精语（网站）
     │                          │
 sources/ ──► distilled/ ──► jingyu/public/
  原材料        精炼 JSON        学习 UI
```

| 层 | 路径 | 说明 |
|----|------|------|
| 原料 | `sources/*/raw/` | Callan 等 PDF，只读 |
| 提取 | `sources/*/extracted/` | 脚本结构化 JSON |
| 蒸馏 | `distilled/` | AI/规则精炼后的学习内容 |
| 呈现 | `jingyu/` | 精语网站，消费 `distilled/` |

## 流水线

1. **Import** — PDF 入库 `sources/`
2. **Extract** — `extract_callan.py` → 问答、词汇 JSON
3. **Distill** — `distill_callan.py` → 场景化精炼 JSON
4. **Publish** — `jingyu/scripts/sync-data.mjs` → 网站静态数据
5. **Learn** — 用户在 **JingYu** 浏览、练习、验收

## 扩展新教材

```
sources/
├── callan/
├── other-method/     # 以后加
└── ...
distilled/
├── callan/
└── other-method/
```

精语网站按 `distilled/index.json` 聚合展示多教材。
