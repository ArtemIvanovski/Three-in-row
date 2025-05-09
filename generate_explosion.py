import os
import math
import random
from PIL import Image, ImageDraw
import imageio

# Параметры
src_path   = "assets/elements/yellow.png"
tile_size  = 8         # базовый размер «плитки» (будет масштабироваться)
nframes    = 120
output_dir = "assets/output"
frames_dir = os.path.join(output_dir, "frames")
os.makedirs(frames_dir, exist_ok=True)

# Загружаем и дополняем холст до целых плиток
src = Image.open(src_path).convert("RGBA")
cols = math.ceil(src.width  / tile_size)
rows = math.ceil(src.height / tile_size)
pad_w = cols * tile_size
pad_h = rows * tile_size
padded = Image.new("RGBA", (pad_w, pad_h), (0, 0, 0, 0))
offset_x = (pad_w - src.width ) // 2
offset_y = (pad_h - src.height) // 2
padded.paste(src, (offset_x, offset_y))

center     = (pad_w / 2, pad_h / 2)
max_radius = max(pad_w, pad_h) * 1.2  # насколько далеко разлетятся фрагменты

# Генерация «частиц»
pieces = []
for r in range(rows):
    for c in range(cols):
        # исходная ячейка
        x0, y0 = c*tile_size, r*tile_size
        box = (x0, y0, x0 + tile_size, y0 + tile_size)
        tile = padded.crop(box)
        if not tile.getbbox():
            continue  # пропускаем пустые

        # направление движения от центра
        cx = x0 + tile_size/2
        cy = y0 + tile_size/2
        dx, dy = cx - center[0], cy - center[1]
        length = math.hypot(dx, dy) or 1
        dir_vec = (dx/length, dy/length)

        if abs(dx) < 1e-6 and abs(dy) < 1e-6:
            continue

        # случайная форма и масштаб
        scale = random.uniform(0.5, 1.5)
        new_w = int(tile_size * scale)
        new_h = new_w
        tile_scaled = tile.resize((new_w, new_h), Image.LANCZOS)

        # маска фигуры
        mask = Image.new("L", (new_w, new_h), 0)
        draw = ImageDraw.Draw(mask)
        shape_type = random.choice(["ellipse", "triangle", "rect", "polygon"])
        if shape_type == "ellipse":
            draw.ellipse([(0,0), (new_w-1, new_h-1)], fill=255)
        elif shape_type == "rect":
            draw.rectangle([(0,0), (new_w-1, new_h-1)], fill=255)
        elif shape_type == "triangle":
            pts = [(new_w/2, 0), (0, new_h-1), (new_w-1, new_h-1)]
            draw.polygon(pts, fill=255)
        else:  # случайный многоугольник 5–7 углов
            n = random.randint(5, 7)
            pts = []
            for i in range(n):
                angle = 2*math.pi * i / n + random.uniform(-0.2,0.2)
                radius = new_w/2 * random.uniform(0.7,1.0)
                pts.append((new_w/2 + math.cos(angle)*radius,
                            new_h/2 + math.sin(angle)*radius))
            draw.polygon(pts, fill=255)

        # итоговый «кусочек»
        piece_img = Image.new("RGBA", (new_w, new_h), (0,0,0,0))
        piece_img.paste(tile_scaled, (0,0), mask=mask)

        # скорректированная стартовая точка (чтобы центр совпадал)
        start_x = x0 + (tile_size-new_w)/2
        start_y = y0 + (tile_size-new_h)/2

        pieces.append({
            "img":   piece_img,
            "start": (start_x, start_y),
            "dir":   dir_vec
        })

# Генерация кадров и сохранение
frames = []
for i in range(nframes):
    t = i / (nframes - 1)
    canvas = Image.new("RGBA", (pad_w, pad_h), (0,0,0,0))
    for p in pieces:
        dist = max_radius * t
        x = int(p["start"][0] + p["dir"][0] * dist)
        y = int(p["start"][1] + p["dir"][1] * dist)
        # можно добавить случайную лёгкую ротацию:
        rot = p["img"].rotate(random.uniform(-15,15), expand=True)
        canvas.alpha_composite(rot, (x, y))
    frames.append(canvas)
    # сохранить отдельный PNG
    frame_path = os.path.join(frames_dir, f"frame_{i:02d}.png")
    canvas.save(frame_path)
    print(f"Saved frame {i} → {frame_path}")
