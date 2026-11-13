"""Moonlit Manor player sprites from the Gemini sheets.
Outputs walk (4 frames), idle (8 frames with breathing + blink), fishing poses
(64x48, right + left) and the catch pose, all sharing one palette and alignment."""
import os
import numpy as np
from PIL import Image
from collections import Counter
from scipy import ndimage

U = "/mnt/user-data/uploads/"
SRC = {
    "stride": U + "Pixel_art_character_turnaround_s__12cd4883_2K.jpg",
    "stand": U + "Pixel_art_character_turnaround_s__8bc3fb71_2K.jpg",
    "blink": U + "Pixel_art_character_turnaround_s__6fa65f16_2K.jpg",
    "fish": U + "Pixel_art_character_turnaround_s__e84c64d5_2K.jpg",
    "catch": U + "Pixel_art_character_turnaround_s__bca92f61_2K.jpg",
}
OUT = "/home/claude/kit/fish/out/player_sprites"
INK = (18, 14, 31, 255)
VIEWS = ["down", "right", "left", "up"]          # figure order in the turnaround sheets
TARGET_H = 30


def load(path):
    s = np.array(Image.open(path).convert("RGB")).astype(int)
    r, g, b = s[..., 0], s[..., 1], s[..., 2]
    bg = ((r > 150) & (b > 150) & (g < 120)) | ((r > 110) & (b > 80) & (g < 70) & (r - g > 70) & (b - g > 50))
    glow = (b > 170) & (r > 90) & (g < 150) & (b - g > 60)      # purple halo around the caught fish
    return s, bg | glow


def components(bg):
    fg = ndimage.binary_opening(~bg, iterations=2)
    lab, n = ndimage.label(fg)
    objs = ndimage.find_objects(lab)
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    comps = [(i + 1, objs[i]) for i, sz in enumerate(sizes) if sz > 20000]
    comps.sort(key=lambda c: c[1][1].start)
    return lab, comps


def outline(fr):
    lab, n = ndimage.label(fr[..., 3] > 0)
    if n > 1:                                   # drop stray specks of 1-3 px
        sizes = ndimage.sum(np.ones(lab.shape), lab, range(1, n + 1))
        fr = fr.copy()
        for k, sz in enumerate(sizes):
            if sz <= 3:
                fr[lab == k + 1] = 0
    a = fr[..., 3] > 0
    o = fr.copy()
    H, W = a.shape
    for y in range(H):
        for x in range(W):
            if not a[y, x] and any(0 <= x + dx < W and 0 <= y + dy < H and a[y + dy, x + dx]
                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                o[y, x] = INK
    return o


def main():
    os.makedirs(f"{OUT}/fishing", exist_ok=True)
    data = {k: load(p) for k, p in SRC.items()}
    sample = np.concatenate([s[~m][::9] for s, m in data.values()])
    N = 32
    pal = np.array(Image.fromarray(sample.reshape(-1, 1, 3).astype(np.uint8)).quantize(
        N, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE, kmeans=3).getpalette()[:N * 3]).reshape(-1, 3)
    idx = {}
    for k, (s, m) in data.items():
        flat = s.reshape(-1, 3).astype(np.float32)
        p32 = pal.astype(np.float32)
        i = np.empty(flat.shape[0], np.int32)
        for c0 in range(0, flat.shape[0], 200000):
            ch = flat[c0:c0 + 200000]
            i[c0:c0 + 200000] = ((ch[:, None, :] - p32[None]) ** 2).sum(-1).argmin(1)
        i = i.reshape(s.shape[:2])
        i[m] = -1
        idx[k] = i

    # shared scale from the standing front view height
    lab, comps = components(data["stand"][1])
    sl = comps[0][1]
    scale = TARGET_H / (sl[0].stop - sl[0].start)

    ROD = (196, 140, 72)

    def rod_mask(key):
        sv, _ = data[key]
        r, g, b = sv[..., 0], sv[..., 1], sv[..., 2]
        tan = (r > 120) & (g > 70) & (b < 110) & (r > g) & (g > b) & (r - b > 60)
        big = ndimage.binary_opening(tan, structure=np.ones((3, 3)), iterations=14)
        thin = tan & ~ndimage.binary_dilation(big, iterations=6)
        return ndimage.binary_closing(thin, iterations=2)

    rods = {"fish": rod_mask("fish")}

    def render(key, member, cx_src, base_src, W, H, cx_t):
        """Mode-sample the member pixels into a WxH frame. cx_src (source x) lands on
        target x cx_t; the source baseline lands on the frame's second-to-last row."""
        i = idx[key]
        out = np.zeros((H, W, 4), np.uint8)
        for Y in range(H - 1):
            y0 = base_src - (H - 1 - Y) / scale
            y1 = base_src - (H - 2 - Y) / scale
            ya, yb = int(round(y0)), int(round(y1))
            if yb <= 0 or ya >= i.shape[0]:
                continue
            ya, yb = max(ya, 0), min(yb, i.shape[0])
            for X in range(W):
                x0 = cx_src + (X - cx_t - 0.5) / scale
                x1 = cx_src + (X - cx_t + 0.5) / scale
                xa, xb = int(round(x0)), int(round(x1))
                if xb <= 0 or xa >= i.shape[1]:
                    continue
                xa, xb = max(xa, 0), min(xb, i.shape[1])
                blk = np.where(member[ya:yb, xa:xb], i[ya:yb, xa:xb], -1).ravel()
                if blk.size == 0:
                    continue
                if key in rods and (rods[key][ya:yb, xa:xb] & member[ya:yb, xa:xb]).sum() >= blk.size * 0.12:
                    out[Y, X, :3] = ROD
                    out[Y, X, 3] = 255
                    continue
                c = Counter(blk.tolist())
                if c.get(-1, 0) > blk.size * 0.5:
                    continue
                c.pop(-1, None)
                items = c.most_common()
                k = items[0][0]
                dark = [(z, v) for z, v in items if pal[z].sum() < 110]
                if dark and dark[0][1] >= blk.size * 0.3:
                    k = dark[0][0]
                out[Y, X, :3] = pal[k]
                out[Y, X, 3] = 255
        return out

    def head_cx(member, sl):
        ys = np.where(member.any(1))[0]
        top = member[ys.min(): ys.min() + int((ys.max() - ys.min()) * 0.3)]
        xs = np.where(top.any(0))[0]
        return (xs.min() + xs.max()) / 2

    def turnaround(key):
        s, m = data[key]
        lab, comps = components(m)
        res = {}
        for v, (n, sl) in zip(VIEWS, comps[:4]):
            member = lab == n
            base = np.where(member.any(1))[0].max() + 1
            res[v] = render(key, member, head_cx(member, sl), base, 32, 32, 15.5)
        return res

    stand, stride, blink = turnaround("stand"), turnaround("stride"), turnaround("blink")

    def mirror_legs(fr, cut=24):
        a = fr[..., 3] > 0
        xs = np.where(a.any(0))[0]
        cx = (xs.min() + xs.max()) / 2
        fl = np.zeros_like(fr)
        for x in range(fr.shape[1]):
            sx = int(round(2 * cx - x))
            if 0 <= sx < fr.shape[1]:
                fl[:, x] = fr[:, sx]
        r = fr.copy()
        r[cut:] = fl[cut:]
        return r

    def breathe(fr, cut=24):
        b = fr.copy()
        b[1:cut + 1] = fr[0:cut]
        b[0] = 0
        return b

    def with_blink(st, bl):
        """Copy only the face band (rows 6-15) from the eyes-closed frame."""
        r = st.copy()
        r[6:16] = bl[6:16]
        return r

    order = ["down", "up", "right", "left"]
    walk, idle = {}, {}
    for v in order:
        s1 = stride[v]
        s3 = mirror_legs(s1) if v in ("down", "up") else s1
        walk[v] = [outline(f) for f in (s1, stand[v], s3, stand[v])]
        st, br = stand[v], breathe(stand[v])
        bk = with_blink(st, blink[v]) if v != "up" else st
        idle[v] = [outline(f) for f in (st, st, br, br, st, bk, br, br)]

    def save_strip(frames, path):
        h, w = frames[0].shape[:2]
        strip = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
        for c, f in enumerate(frames):
            strip.paste(Image.fromarray(f), (c * w, 0))
        strip.save(path)

    for v in order:
        save_strip(walk[v], f"{OUT}/walk_{v}.png")
        save_strip(idle[v], f"{OUT}/idle_{v}.png")

    # ---- fishing poses (one sheet, four poses facing right; poses 3 and 4 touch)
    s, m = data["fish"]
    lab, comps = components(m)
    H_img, W_img = m.shape
    yy, xx = np.mgrid[0:H_img, 0:W_img]
    merged = lab == comps[2][0]
    rodm = rods["fish"]
    p3 = merged & ((xx < 1890) | (rodm & (xx < 2060)))
    p4 = merged & (xx >= 1890) & ~(rodm & (xx < 2060))
    members = [lab == comps[0][0], lab == comps[1][0], p3, p4]
    heads = [385, 985, 1630, 2185]                   # hair centre of each pose (source px)
    names = ["windup", "cast", "wait", "reel"]
    fishing = {}
    for name, mem, hx in zip(names, members, heads):
        base = np.where(mem.any(1))[0].max() + 1
        fishing[name] = render("fish", mem, hx, base, 64, 48, 31.5)
    seqs = {
        "windup": [fishing["windup"]],
        "cast": [fishing["cast"]],
        "wait": [fishing["wait"], breathe(fishing["wait"], cut=40)],
        "reel": [fishing["reel"], breathe(fishing["reel"], cut=40)],
    }
    for name, frs in seqs.items():
        frs = [outline(f) for f in frs]
        save_strip(frs, f"{OUT}/fishing/fish_{name}_right.png")
        save_strip([f[:, ::-1] for f in frs], f"{OUT}/fishing/fish_{name}_left.png")

    # ---- catch pose (middle figure of the catch sheet)
    s, m = data["catch"]
    lab, comps = components(m)
    mem = lab == comps[1][0]
    base = np.where(mem.any(1))[0].max() + 1
    ys = np.where(mem.any(1))[0]
    bottom = mem[ys.max() - int((ys.max() - ys.min()) * 0.15): ys.max() + 1]
    xs = np.where(bottom.any(0))[0]
    catch = outline(render("catch", mem, (xs.min() + xs.max()) / 2, base, 64, 48, 31.5))
    save_strip([catch], f"{OUT}/fishing/fish_catch.png")

    # ---- previews
    def gif(rows, path, dur, scale_=6):
        n = max(len(r) for r in rows)
        h = max(r[0].shape[0] for r in rows)
        w = sum(r[0].shape[1] for r in rows)
        frames = []
        for c in range(n):
            canvas = Image.new("RGBA", ((w + 2 * len(rows)) * scale_, (h + 4) * scale_), (43, 37, 71, 255))
            x = scale_
            for r in rows:
                f = Image.fromarray(r[c % len(r)])
                f = f.resize((f.width * scale_, f.height * scale_), Image.NEAREST)
                canvas.alpha_composite(f, (x, (h - r[0].shape[0] + 2) * scale_))
                x += f.width + 2 * scale_
            frames.append(canvas.convert("P", palette=Image.ADAPTIVE))
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=dur, loop=0)

    gif([walk[v] for v in order], f"{OUT}/preview_walk.gif", 125)
    gif([idle[v] for v in order], f"{OUT}/preview_idle.gif", 250)
    fish_seq = [outline(fishing[n]) for n in names] + [catch]
    gif([[f] for f in fish_seq], f"{OUT}/preview_fishing.png.gif", 1000, 4)
    # static fishing contact sheet
    sc = 5
    sheet = Image.new("RGBA", ((64 + 4) * 5 * sc, (48 * 2 + 12) * sc), (43, 37, 71, 255))
    for c, f in enumerate(fish_seq):
        im = Image.fromarray(f).resize((64 * sc, 48 * sc), Image.NEAREST)
        sheet.alpha_composite(im, (c * (68 * sc) + 2 * sc, 2 * sc))
        sheet.alpha_composite(Image.fromarray(f[:, ::-1].copy()).resize((64 * sc, 48 * sc), Image.NEAREST),
                              (c * (68 * sc) + 2 * sc, (50 + 4) * sc))
    sheet.save(f"{OUT}/preview_fishing.png")
    os.remove(f"{OUT}/preview_fishing.png.gif")


if __name__ == "__main__":
    main()
