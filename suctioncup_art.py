import pygame
import math
import random
import os

# --- 設定パラメータ ---
WIDTH, HEIGHT = 800, 600
BG_COLOR = (240, 245, 255)

# デザイン
COLOR_CUP = (0, 150, 200)
COLOR_HANDLE = (50, 50, 50)
COLOR_NECK = (0, 120, 180)

# 物理
MAX_STRETCH = 250.0
VACUUM_LIFE = 100.0
VACUUM_DECAY = 1.5
VACUUM_RECOVER = 2.0
SPRING_STIFFNESS = 0.25
DAMPING = 0.85


class Particle:
    """スポッ！エフェクト"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.alpha = 255
        self.growth = 8

    def update(self):
        self.radius += self.growth
        self.alpha -= 20
        if self.alpha < 0:
            self.alpha = 0

    def draw(self, screen):
        if self.alpha > 0:
            s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                s,
                (100, 200, 255, self.alpha),
                (self.radius, self.radius),
                self.radius,
                width=5,
            )
            screen.blit(s, (self.x - self.radius, self.y - self.radius))


class SuctionCup:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0

        self.is_stuck = False
        self.stuck_pos = (x, y)
        self.vacuum = VACUUM_LIFE
        self.stretch_dist = 0
        self.radius_base = 40

    def update(self, mouse_pos, mouse_pressed):
        target_x, target_y = mouse_pos
        state_changed = None  # "STICK", "POP", None

        # --- 接着ロジック ---
        if mouse_pressed:
            if not self.is_stuck:
                # 吸着開始
                self.is_stuck = True
                self.stuck_pos = (target_x, target_y)
                self.x, self.y = target_x, target_y
                self.vacuum = VACUUM_LIFE
                self.vx, self.vy = 0, 0
                state_changed = "STICK"
            else:
                # 引っ張り中
                dx = target_x - self.stuck_pos[0]
                dy = target_y - self.stuck_pos[1]
                self.stretch_dist = math.hypot(dx, dy)

                if self.stretch_dist > 20:
                    decay = (self.stretch_dist / MAX_STRETCH) * VACUUM_DECAY * 2
                    self.vacuum -= decay
                else:
                    self.vacuum += VACUUM_RECOVER

                self.vacuum = min(VACUUM_LIFE, self.vacuum)

                # 剥がれ判定
                if self.vacuum <= 0 or self.stretch_dist > MAX_STRETCH:
                    self.is_stuck = False
                    self.vx = dx * 0.45  # 跳ね返り速度
                    self.vy = dy * 0.45
                    state_changed = "POP"

        else:
            # マウス離した時（剥がれていればバネ運動）
            if self.is_stuck:
                # 吸着中に指を離した -> 即座に吸着解除されるわけではないが
                # 今回は「マウスについてくる」仕様なので、
                # ボタンを離す＝吸着解除とみなすか、あるいは「ボタン離しても張り付いたまま」にするか。
                # 「ペタペタ遊び」なら、ボタン離しても張り付いててほしいが、
                # 操作体系的に「ドラッグ中のみ有効」の方がわかりやすい。
                # ここでは「ボタンを離すと吸盤もその場に放置（張り付いたまま）」にしましょう。
                self.stretch_dist = 0
                pass
            else:
                # 完全にフリー
                self.stretch_dist = 0
                # マウスへの追従（バネ）
                ax = (target_x - self.x) * SPRING_STIFFNESS
                ay = (target_y - self.y) * SPRING_STIFFNESS
                self.vx += ax
                self.vy += ay
                self.vx *= DAMPING
                self.vy *= DAMPING
                self.x += self.vx
                self.y += self.vy

        return state_changed

    def draw(self, screen, mouse_pos):
        mx, my = mouse_pos
        bx, by = self.x, self.y

        if self.is_stuck:
            bx, by = self.stuck_pos

            # Neck
            width = max(5, 20 - self.stretch_dist * 0.05)
            pygame.draw.line(screen, COLOR_NECK, (bx, by), (mx, my), int(width))

            # Cup Body
            shake_x, shake_y = 0, 0
            if self.vacuum < 40:
                amp = (40 - self.vacuum) * 0.15
                shake_x = random.uniform(-amp, amp)
                shake_y = random.uniform(-amp, amp)

            radius = self.radius_base + 12
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*COLOR_CUP, 220), (radius, radius), radius)

            # Vacuum indicator
            alpha = int((self.vacuum / VACUUM_LIFE) * 200)
            pygame.draw.circle(
                s, (255, 255, 255, alpha), (radius, radius), radius * 0.6
            )

            screen.blit(s, (bx - radius + shake_x, by - radius + shake_y))

        else:
            pygame.draw.circle(screen, COLOR_CUP, (bx, by), self.radius_base)
            pygame.draw.circle(screen, (255, 255, 255), (bx - 12, by - 12), 10)

        # Handle
        hx, hy = (mx, my) if self.is_stuck else (bx, by)
        pygame.draw.circle(screen, COLOR_HANDLE, (hx, hy), 8)


def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)  # 遅延を減らす設定
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Suction Cup with Sound")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 20)

    # --- サウンド読み込み ---
    # ファイルがないとエラーになるのでチェック
    has_sound = False
    try:
        if os.path.exists("kyu.wav") and os.path.exists("pop.wav"):
            sound_kyu = pygame.mixer.Sound("kyu.wav")
            sound_pop = pygame.mixer.Sound("pop.wav")
            sound_kyu.set_volume(0.0)  # 最初は無音
            sound_kyu.play(-1)  # ループ再生開始（音量0で回しておく）
            has_sound = True
            print("Sound loaded successfully.")
        else:
            print("Sound files not found. Run make_sounds.py first.")
    except Exception as e:
        print(f"Sound Error: {e}")

    cup = SuctionCup(WIDTH // 2, HEIGHT // 2)
    particles = []

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # ロジック更新
        result = cup.update(mouse_pos, mouse_pressed)

        # --- 音響制御 (Sound Control) ---
        if has_sound:
            if result == "POP":
                sound_pop.play()  # スポッ！
                sound_kyu.set_volume(0.0)  # キュー音停止

            elif cup.is_stuck and mouse_pressed:
                # 引っ張っている間だけ「キュー」と鳴らす
                # 距離に応じて音量を変える（これが気持ちいい）
                if cup.stretch_dist > 30:
                    # 距離 30〜MAX_STRETCH を 音量 0.1〜1.0 にマッピング
                    vol = min(1.0, (cup.stretch_dist - 30) / (MAX_STRETCH - 30))
                    # 真空度が減るとさらに必死な音になる（ピッチは変えられないので音量で表現）
                    if cup.vacuum < 30:
                        vol = 1.0
                    sound_kyu.set_volume(vol)
                else:
                    sound_kyu.set_volume(0.0)
            else:
                sound_kyu.set_volume(0.0)

        # エフェクト
        if result == "POP":
            particles.append(Particle(cup.stuck_pos[0], cup.stuck_pos[1]))

        # 描画
        screen.fill(BG_COLOR)

        # ガイド線
        for i in range(0, WIDTH, 40):
            pygame.draw.line(screen, (235, 240, 250), (i, 0), (i, HEIGHT), 1)
        for i in range(0, HEIGHT, 40):
            pygame.draw.line(screen, (235, 240, 250), (0, i), (WIDTH, i), 1)

        for p in particles:
            p.update()
            p.draw(screen)
        particles = [p for p in particles if p.alpha > 0]

        cup.draw(screen, mouse_pos)

        # ゲージ
        if cup.is_stuck:
            bar_w, bar_h = 60, 6
            gx, gy = cup.stuck_pos[0] - bar_w / 2, cup.stuck_pos[1] + 55
            pygame.draw.rect(screen, (180, 180, 180), (gx, gy, bar_w, bar_h))

            pct = max(0, cup.vacuum / VACUUM_LIFE)
            col = (255, 50, 50) if pct < 0.3 else (50, 200, 100)
            pygame.draw.rect(screen, col, (gx, gy, bar_w * pct, bar_h))

        # UI
        msg = "Drag to Stretch!" if cup.is_stuck else "Click to Stick"
        if not has_sound:
            msg += " (Sound files missing)"
        screen.blit(font.render(msg, True, (150, 150, 170)), (20, HEIGHT - 30))

        pygame.display.flip()
        clock.tick(60)

    if has_sound:
        sound_kyu.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
