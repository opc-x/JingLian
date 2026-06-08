# JingLian 精炼

> 英语教材原料库 · Agent 加工 · 蒸馏出更强版本

**JingLian** 是蒸馏管线（仓库/引擎）；**[精语 JingYu](./jingyu/)** 是对外学习网站。

| 名称 | 角色 |
|------|------|
| **JingLian**（本仓） | 教材原料 + 提取/蒸馏脚本 + `distilled/` 产物 |
| **JingYu 精语**（`jingyu/`） | 学习网站：浏览 AI 精炼后的内容 |
| [AgentVault](https://github.com/opc-x/AgentVault) | 调研报告归档 |
| [ZuiTi](https://github.com/opc-x/ZuiTi) | 嘴替 Prompt |
| [PayAtlas](https://github.com/opc-x/PayAtlas) | 全球支付渠道 |

## 目录结构

```
JingLian/
├── sources/          # 原材料（Callan PDF 等）
├── distilled/        # 蒸馏产物 JSON
├── scripts/          # 提取 & 蒸馏管线
├── jingyu/           # 精语学习网站 ← 用户看这个
└── docs/
```

## 全稿流水线

```bash
./scripts/run_all.sh          # 提取 + 蒸馏 12 册 + 同步网站数据
cd jingyu && npm install && npm run dev
```

打开 **http://localhost:5174** → **精语 JingYu**

## 品牌 Slogan

**多教材 · AI 精炼 · 学了就更会讲**

## 注意

- 本仓为 **私有仓库**，教材 PDF 仅供个人学习
- `sources/` 原件勿改，精炼结果写 `distilled/`

## License

仓库框架 MIT；教材版权归原作者所有。
