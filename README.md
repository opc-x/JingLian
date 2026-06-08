# JingLian 精炼

> 英语教材原料库 · Agent 加工 · 蒸馏出更强版本

把 Callan Method 和其它牛逼教材当**原材料**扔进来，用 Agent 提取、重组、蒸馏，产出更好练、更好教的新东西。

## 和其它仓库怎么分工

| 仓库 | 角色 |
|------|------|
| **JingLian**（本仓） | 英语**教材原料** + Agent **精炼产物** |
| [AgentVault](https://github.com/opc-x/AgentVault) | 调研报告归档 |
| [ZuiTi](https://github.com/opc-x/ZuiTi) | 嘴替 Prompt & 客服回复 |
| [PayAtlas](https://github.com/opc-x/PayAtlas) | 全球支付渠道 |

## 目录结构

```
JingLian/
├── sources/                 # 原材料（只读参考，不直接改）
│   └── callan/
│       ├── raw/             # 12 册 PDF 原件
│       ├── meta/            # 清单 & 元数据
│       └── extracted/       # 脚本提取的 JSON（待生成）
├── distilled/               # Agent 蒸馏产物（精炼版教材、卡片、 drills）
├── templates/               # Agent 精炼用的 Prompt 模板
├── scripts/                 # 提取 & 处理脚本
└── docs/
```

## 原材料清单

Callan Method 全 12 册已入库 → [`sources/callan/meta/manifest.json`](./sources/callan/meta/manifest.json)

## 提取 PDF（Book 1 示例）

```bash
pip install pymupdf
python scripts/extract_callan.py --book 1
```

输出到 `sources/callan/extracted/book-01.json`。

## 精炼工作流

```
sources/callan/raw/*.pdf
        ↓ extract_callan.py
sources/callan/extracted/*.json
        ↓ Agent + templates/distill-lesson.md
distilled/callan/...
```

## 注意

- 本仓为 **私有仓库**，教材 PDF 仅供个人学习使用
- `sources/` 下原件不要随意改动，精炼结果写到 `distilled/`

## License

仓库框架 MIT；教材版权归原作者所有。
