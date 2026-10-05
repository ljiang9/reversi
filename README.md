# reversi 黑白棋

标准 8×8 黑白棋 (Othello/Reversi) 终端人机对战。纯 Python 标准库，单文件。

## 玩法

```bash
python -m reversi            # 人机对战: 你执黑 ● 先手
python -m reversi --demo     # AI 自走演示
python -m reversi --selfplay # AI 对 AI 自弈
python -m reversi --selfplay --seed 42
```

落子输入坐标如 `D3`（列 A–H + 行 1–8），输入 `q` 退出。
非法落子（不能翻转任何对方棋子）会被拒绝并要求重下。

## AI 说明（诚实版）

AI = **位置权重贪心 + 1 层展望**，不是深度搜索：

- 每个格子有权重：**角 = 100**（最大，拿下基本不亏）、
  角相邻格 = −20 ~ −50（容易送角，避开）、边 = 5 ~ 10、
  中央 = 1。
- 每步选择 `(权重 + 翻子数) − 0.9 × 对手最佳反击价值` 最大的走法，
  即只看自己走一步、对手回一步。
- 权重表是经典 Othello 启发式表的简化版（对称 8×8），
  见 `reversi.py` 顶部 `WEIGHTS`。

已知局限：贪心 AI 中盘后容易陷入固定模式，对"让子抢角"类
陷阱无长远规划；人类玩家熟悉角部战术后胜率会明显上升。
想要更强对手可以把 `ai_choose` 换成 minimax + alpha-beta，
权重表可直接复用为评估函数。

## 规则

标准黑白棋规则：落子必须夹住至少一枚对方棋子并翻转；
无棋可下时跳过（pass），双方连续跳过则终局，
子多者胜。

## License

MIT, Copyright (c) 2026 ljiang9
