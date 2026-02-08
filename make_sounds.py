import math
import struct
import wave
import random


def save_wav(filename, data, sample_rate=44100):
    # データをバイト列に変換 (16bit PCM)
    byte_data = b""
    for v in data:
        # -1.0 ~ 1.0 を -32767 ~ 32767 に変換
        i = int(max(-1.0, min(1.0, v)) * 32767)
        byte_data += struct.pack("<h", i)

    with wave.open(filename, "w") as f:
        f.setnchannels(1)  # モノラル
        f.setsampwidth(2)  # 2バイト(16bit)
        f.setframerate(sample_rate)
        f.writeframes(byte_data)
    print(f"Generated: {filename}")


def generate_kyu_sound():
    # 「きゅーっ」：ゴムが擦れるような、少しノイズ混じりの高い音
    sample_rate = 44100
    duration = 2.0  # 長めに作ってループさせる
    data = []

    freq_base = 600.0  # 基本周波数

    for t in range(int(sample_rate * duration)):
        time = t / sample_rate

        # 少し揺らぎ（摩擦感）を入れる
        freq = freq_base + math.sin(time * 50) * 20

        # 鋸波（Sawtooth）に近い波形で「ビリビリ感」を出す
        # math.sin ではなく、少し尖らせる
        val = 0.0
        # 倍音を重ねる
        val += 0.6 * math.sin(2 * math.pi * freq * time)
        val += 0.3 * math.sin(
            2 * math.pi * (freq * 2.05) * time
        )  # 少しずらすと不協和音でゴムっぽくなる
        val += 0.1 * (random.random() - 0.5)  # ホワイトノイズ（ザラザラ感）

        data.append(val * 0.5)  # 音量は控えめに

    return data


def generate_pop_sound():
    # 「すぽっ」：急激なピッチダウン（サイン波）
    sample_rate = 44100
    duration = 0.15
    data = []

    for t in range(int(sample_rate * duration)):
        time = t / sample_rate
        progress = time / duration

        # 周波数が急激に下がる (800Hz -> 100Hz)
        freq = 800 * (1 - progress) ** 2 + 100

        # サイン波
        val = math.sin(2 * math.pi * freq * time)

        # エンベロープ（出だし強く、すぐ消える）
        vol = 1.0 - progress
        data.append(val * vol)

    return data


if __name__ == "__main__":
    save_wav("kyu.wav", generate_kyu_sound())
    save_wav("pop.wav", generate_pop_sound())
