"""reversi - 黑白棋 (Othello/Reversi) 人机对战.

标准 8x8 黑白棋: 你执黑 ● 先手, AI 执白 ○.
输入坐标如 D3 落子; AI 使用位置权重贪心 + 1 层展望.

用法:
    python -m reversi            # 人机对战
    python -m reversi --demo     # AI 自走演示(随机开局)
    python -m reversi --selfplay # AI 对 AI 自弈
"""
from __future__ import annotations

import argparse
import random
import sys

N = 8
EMPTY, BLACK, WHITE = 0, 1, 2
DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# 位置权重: 角部巨大(100), 角邻位为负(送角风险), 边为正.
# 来源: 经典 Othello 启发式权重表(简化版), 文档见 README.
def _weights() -> list[list[int]]:
    return [
        [100, -20,  10,   5,   5,  10, -20, 100],
        [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
        [ 10,  -2,   5,   1,   1,   5,  -2,  10],
        [  5,  -2,   1,   1,   1,   1,  -2,   5],
        [  5,  -2,   1,   1,   1,   1,  -2,   5],
        [ 10,  -2,   5,   1,   1,   5,  -2,  10],
        [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
        [100, -20,  10,   5,   5,  10, -20, 100],
    ]


WEIGHTS = _weights()


def new_board() -> list[list[int]]:
    b = [[EMPTY] * N for _ in range(N)]
    b[3][3] = b[4][4] = WHITE
    b[3][4] = b[4][3] = BLACK
    return b


def opponent(p: int) -> int:
    return WHITE if p == BLACK else BLACK


def flips_for(b: list[list[int]], r: int, c: int, p: int) -> list[tuple[int, int]]:
    """返回在 (r,c) 落子 p 会翻转的棋子列表; 空列表表示非法."""
    if not (0 <= r < N and 0 <= c < N) or b[r][c] != EMPTY:
        return []
    o = opponent(p)
    out: list[tuple[int, int]] = []
    for dr, dc in DIRS:
        line: list[tuple[int, int]] = []
        rr, cc = r + dr, c + dc
        while 0 <= rr < N and 0 <= cc < N and b[rr][cc] == o:
            line.append((rr, cc))
            rr += dr
            cc += dc
        if line and 0 <= rr < N and 0 <= cc < N and b[rr][cc] == p:
            out.extend(line)
    return out


def legal_moves(b: list[list[int]], p: int) -> list[tuple[int, int]]:
    return [(r, c) for r in range(N) for c in range(N) if flips_for(b, r, c, p)]


def apply_move(b: list[list[int]], r: int, c: int, p: int) -> int:
    fl = flips_for(b, r, c, p)
    b[r][c] = p
    for rr, cc in fl:
        b[rr][cc] = p
    return len(fl)


def count(b: list[list[int]]) -> tuple[int, int]:
    bl = sum(row.count(BLACK) for row in b)
    wh = sum(row.count(WHITE) for row in b)
    return bl, wh


def ai_choose(b: list[list[int]], p: int, rng: random.Random) -> tuple[int, int] | None:
    """位置权重贪心 + 1 层展望: 选择 (权重和 + 翻子数) - 对手最佳反击价值 最大的走法."""
    moves = legal_moves(b, p)
    if not moves:
        return None
    o = opponent(p)
    best: tuple[int, int] | None = None
    best_val = float("-inf")
    order = moves[:]
    rng.shuffle(order)
    for r, c in order:
        fl = flips_for(b, r, c, p)
        gain = WEIGHTS[r][c] + len(fl)
        # 1 层展望: 模拟后对手的最佳反击
        nb = [row[:] for row in b]
        apply_move(nb, r, c, p)
        reply = 0
        for rr, cc in legal_moves(nb, o):
            v = WEIGHTS[rr][cc] + len(flips_for(nb, rr, cc, o))
            if v > reply:
                reply = v
        val = gain - 0.9 * reply
        if val > best_val:
            best_val = val
            best = (r, c)
    return best


COLS = "ABCDEFGH"


def parse_coord(s: str) -> tuple[int, int] | None:
    s = s.strip().upper()
    if len(s) < 2 or len(s) > 3:
        return None
    col_s, row_s = s[0], s[1:]
    if col_s not in COLS or not row_s.isdigit():
        return None
    r, c = int(row_s) - 1, COLS.index(col_s)
    if not (0 <= r < N and 0 <= c < N):
        return None
    return r, c


def render(b: list[list[int]]) -> str:
    sym = {EMPTY: "·", BLACK: "●", WHITE: "○"}
    lines = ["   " + " ".join(COLS)]
    for r in range(N):
        lines.append(f"{r + 1:>2} " + " ".join(sym[b[r][c]] for c in range(N)))
    return "\n".join(lines)


def play_game(ai_black: bool = False, ai_white: bool = True,
              verbose: bool = True, seed: int | None = None,
              human_moves: list[str] | None = None) -> tuple[int, int, int]:
    """返回 (黑子数, 白子数, 胜者 0=平). human_moves 用于测试时喂招."""
    rng = random.Random(seed)
    b = new_board()
    p = BLACK
    passes = 0
    feed = list(human_moves or [])
    while True:
        moves = legal_moves(b, p)
        if not moves:
            passes += 1
            if passes == 2:
                break
            p = opponent(p)
            continue
        passes = 0
        is_ai = (p == BLACK and ai_black) or (p == WHITE and ai_white)
        if is_ai:
            mv = ai_choose(b, p, rng)
            assert mv is not None
            r, c = mv
            if verbose:
                print(f"{'黑' if p == BLACK else '白'} AI 落子 {COLS[c]}{r + 1}")
        else:
            while True:
                if feed:
                    s = feed.pop(0)
                    if verbose:
                        print(f"> {s}")
                else:
                    try:
                        s = input(f"你执{'黑 ●' if p == BLACK else '白 ○'}, 落子 (如 D3, q 退出): ")
                    except (EOFError, KeyboardInterrupt):
                        print("\n再见!")
                        sys.exit(0)
                if s.strip().lower() in ("q", "quit", "exit"):
                    print("再见!")
                    sys.exit(0)
                pc = parse_coord(s)
                if pc is None:
                    print("坐标格式不对, 请输入如 D3 (A-H + 1-8)。")
                    continue
                r, c = pc
                if not flips_for(b, r, c, p):
                    print("非法落子: 必须至少翻转一枚对方棋子, 请重下。")
                    continue
                break
        n = apply_move(b, r, c, p)
        if verbose:
            print(render(b))
            bl, wh = count(b)
            print(f"翻转 {n} 子 | 黑 ● {bl} : 白 ○ {wh}\n")
        p = opponent(p)
    bl, wh = count(b)
    winner = BLACK if bl > wh else (WHITE if wh > bl else 0)
    if verbose:
        print(render(b))
        print(f"终局: 黑 ● {bl} - 白 ○ {wh}")
        print("黑胜!" if winner == BLACK else ("白胜!" if winner == WHITE else "平局!"))
    return bl, wh, winner


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="reversi", description="黑白棋 (Othello) 人机对战")
    ap.add_argument("--demo", action="store_true", help="AI 自走演示(随机种子)")
    ap.add_argument("--selfplay", action="store_true", help="AI 对 AI 自弈")
    ap.add_argument("--seed", type=int, default=None, help="随机种子")
    args = ap.parse_args(argv)
    print("黑白棋 Reversi | 你执黑 ● 先手")
    if args.demo:
        play_game(ai_black=True, ai_white=True, seed=args.seed if args.seed is not None else random.randrange(10**6))
    elif args.selfplay:
        bl, wh, w = play_game(ai_black=True, ai_white=True, verbose=False, seed=args.seed)
        print(f"自弈终局: 黑 {bl} - 白 {wh}, " + ("黑胜" if w == BLACK else ("白胜" if w == WHITE else "平局")))
    else:
        play_game()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
