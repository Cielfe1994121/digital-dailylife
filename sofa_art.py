import pygame
import numpy as np
import sys
import math

# --- 設定パラメータ ---
WINDOW_W, WINDOW_H = 800, 600
HAIR_COUNT = 10000  # 毛の本数
GRID_SIZE = 40  # 物理計算の粗さ
HAIR_LENGTH = 15  # 毛の長さ

# 【新設】ブラシの設定
BRUSH_RADIUS = 80  # 手の大きさ（半径ピクセル）。ここを変えると手の大きさが変わります。
BRUSH_STRENGTH = 0.4  # なでる強さ（0.0 ~ 1.0）。大きいとくっきり跡がつきます。

# 色の設定 (RGB)
COLOR_DARK = np.array([20, 40, 60], dtype=np.float32)  # 寝ている時
COLOR_LIGHT = np.array([200, 220, 240], dtype=np.float32)  # 逆立っている時

# --- 初期化 ---
pygame.init()
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
pygame.display.set_caption("Python Velvet Simulator - Soft Brush")
clock = pygame.time.Clock()

# --- データ準備 ---
cols = math.ceil(WINDOW_W / GRID_SIZE)
rows = math.ceil(WINDOW_H / GRID_SIZE)

# グリッドの角度（初期化）
grid_angles = (np.random.rand(cols, rows) * 0.5 - 0.25).astype(np.float32)

# 毛のデータ
hair_pos = np.random.rand(HAIR_COUNT, 2).astype(np.float32)
hair_pos[:, 0] *= WINDOW_W
hair_pos[:, 1] *= WINDOW_H

hair_props = np.random.rand(HAIR_COUNT, 2).astype(np.float32)
hair_lengths = (hair_props[:, 0] * 0.4 + 0.8) * HAIR_LENGTH
hair_color_vars = (hair_props[:, 1] - 0.5) * 40.0

# 計算用バッファ
end_pos = np.zeros((HAIR_COUNT, 2), dtype=np.float32)


# --- 【重要】ここが修正された関数です ---
def update_grid_soft(mouse_pos, pmouse_pos):
    """マウス操作でグリッドの角度を更新（柔らかい円形ブラシ）"""
    mx, my = mouse_pos
    pmx, pmy = pmouse_pos
    dx, dy = mx - pmx, my - pmy
    speed = math.hypot(dx, dy)

    if speed < 1.0:
        return

    move_angle = math.atan2(dy, dx)

    # 影響範囲のバウンディングボックス（四角枠）を計算
    # 半径から必要なグリッド数を割り出す
    range_grid = math.ceil(BRUSH_RADIUS / GRID_SIZE) + 1

    gx = int(mx / GRID_SIZE)
    gy = int(my / GRID_SIZE)

    min_x = max(0, gx - range_grid)
    max_x = min(cols, gx + range_grid + 1)
    min_y = max(0, gy - range_grid)
    max_y = min(rows, gy + range_grid + 1)

    if min_x >= max_x or min_y >= max_y:
        return

    # --- NumPyによる円形ブラシ計算 ---

    # 1. 切り出した範囲のグリッドインデックス配列を作成
    # ix は縦ベクトル(N,1), iy は横ベクトル(1,M) の形にする
    ix = np.arange(min_x, max_x)[:, np.newaxis]
    iy = np.arange(min_y, max_y)[np.newaxis, :]

    # 2. 各グリッドの中心座標(ピクセル)を計算
    # ブロードキャスト機能で (N, M) の形状の座標配列ができる
    grid_pos_x = ix * GRID_SIZE + GRID_SIZE / 2
    grid_pos_y = iy * GRID_SIZE + GRID_SIZE / 2

    # 3. マウス位置からの距離を計算
    dist = np.sqrt((grid_pos_x - mx) ** 2 + (grid_pos_y - my) ** 2)

    # 4. 距離に応じた重み（強さ）を作成
    # 中心で1.0、半径の位置で0.0になるように滑らかに変化させる
    # 半径外はマイナスになるので clip で 0 にする
    brush_weight = 1.0 - (dist / BRUSH_RADIUS)
    brush_weight = np.clip(brush_weight, 0.0, 1.0)

    # 5. 角度更新の適用
    # 対象エリアの現在の角度を取得
    target_area = grid_angles[min_x:max_x, min_y:max_y]

    # 角度差を計算
    diff = move_angle - target_area
    diff = (diff + np.pi) % (2 * np.pi) - np.pi  # -PI ~ PI に正規化

    # 更新量を計算： 角度差 * 基本強度 * 場所ごとの重み
    # これにより、中心ほど強く、外側ほど弱く角度が変わる
    update_amount = diff * BRUSH_STRENGTH * brush_weight

    # 更新適用
    grid_angles[min_x:max_x, min_y:max_y] += update_amount


def draw_hairs(surface):
    """計算と描画（前回と同じ）"""

    # 1. 座標計算
    grid_indices_x = (hair_pos[:, 0] / GRID_SIZE).astype(int)
    grid_indices_y = (hair_pos[:, 1] / GRID_SIZE).astype(int)
    np.clip(grid_indices_x, 0, cols - 1, out=grid_indices_x)
    np.clip(grid_indices_y, 0, rows - 1, out=grid_indices_y)

    angles = grid_angles[grid_indices_x, grid_indices_y]
    draw_angles = angles + (hair_props[:, 1] - 0.5) * 0.2

    cos_a = np.cos(draw_angles)
    sin_a = np.sin(draw_angles)

    end_pos[:, 0] = hair_pos[:, 0] + cos_a * hair_lengths
    end_pos[:, 1] = hair_pos[:, 1] + sin_a * hair_lengths

    # 2. 色計算
    factor = (-cos_a + 1.0) / 2.0
    factor = np.clip(factor, 0.0, 1.0)

    factor_exp = factor[:, np.newaxis]
    colors = COLOR_DARK + (COLOR_LIGHT - COLOR_DARK) * factor_exp
    colors += hair_color_vars[:, np.newaxis]

    colors_int = np.clip(colors, 0, 255).astype(np.uint8)

    # Pythonリストへ変換
    starts_list = hair_pos.tolist()
    ends_list = end_pos.tolist()
    colors_list = colors_int.tolist()

    # 3. 描画ループ
    surface.lock()
    for i in range(HAIR_COUNT):
        pygame.draw.line(surface, colors_list[i], starts_list[i], ends_list[i], 1)
    surface.unlock()


# --- メインループ ---
running = True
last_mouse_pos = pygame.mouse.get_pos()

while running:
    # 背景クリア
    screen.fill((15, 30, 45))

    # イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # マウス処理
    current_mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()[0]

    if mouse_pressed:
        # 新しい関数を呼び出す
        update_grid_soft(current_mouse_pos, last_mouse_pos)

    last_mouse_pos = current_mouse_pos

    # 描画
    draw_hairs(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
