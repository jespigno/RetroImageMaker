#make sure pillow is installed in order to run this
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageEnhance, ImageFilter

APP_TITLE = "RetroImageMaker"
PREVIEW_SIZE = (512, 512)
GRID_THUMB_SIZE = (256, 256)

PICO8_PALETTE = [
    (0, 0, 0), (29, 43, 83), (126, 37, 83), (0, 135, 81),
    (171, 82, 54), (95, 87, 79), (194, 195, 199), (255, 241, 232),
    (255, 0, 77), (255, 163, 0), (255, 236, 39), (0, 228, 54),
    (41, 173, 255), (131, 118, 156), (255, 119, 168), (255, 204, 170)
]

GAMEBOY_DMG_PALETTE = [
    (15, 56, 15), (48, 98, 48), (139, 172, 15), (155, 188, 15)
]

C64_PALETTE = [
    (0, 0, 0), (255, 255, 255), (136, 0, 0), (170, 255, 238),
    (204, 68, 204), (0, 170, 0), (0, 0, 170), (238, 238, 119),
    (221, 136, 85), (102, 68, 0), (255, 119, 119), (51, 51, 51),
    (119, 119, 119), (170, 255, 102), (102, 136, 255), (187, 187, 187)
]

ZX_SPECTRUM_8 = [
    (0, 0, 0), (0, 0, 192), (192, 0, 0), (192, 0, 192),
    (0, 192, 0), (0, 192, 192), (192, 192, 0), (192, 192, 192)
]

EGA16_PALETTE = [
    (0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
    (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
    (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
    (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)
]

APPLE2_LORES_16 = [
    (0, 0, 0), (147, 11, 124), (31, 53, 211), (187, 54, 255),
    (0, 118, 12), (126, 126, 126), (7, 168, 224), (157, 172, 255),
    (98, 76, 0), (249, 86, 29), (126, 126, 126), (255, 129, 236),
    (67, 200, 0), (220, 205, 22), (93, 247, 132), (255, 255, 255)
]

NES_NESTOPIA_54 = [
    (255,255,255),(173,173,173),(99,99,99),(0,0,0),(189,222,255),(99,173,255),(25,99,214),(0,41,140),
    (214,214,255),(148,148,255),(66,66,255),(16,16,165),(247,197,255),(197,115,255),(115,41,255),(58,0,165),
    (247,197,255),(239,107,255),(156,25,206),(90,0,123),(255,197,230),(255,107,206),(181,33,123),(107,0,66),
    (255,206,197),(255,132,115),(181,49,33),(107,8,0),(247,214,165),(230,156,33),(156,74,0),(82,33,0),
    (230,230,148),(189,189,0),(107,107,0),(49,49,0),(206,239,148),(140,214,0),(58,132,0),(8,74,0),
    (189,247,173),(90,230,49),(16,148,0),(0,82,0),(181,247,206),(66,222,132),(0,140,49),(0,82,8),
    (181,239,239),(74,206,222),(0,123,140),(0,66,74),(181,181,181),(82,82,82)
]

def fit_image_for_preview(img: Image.Image, max_size=PREVIEW_SIZE) -> Image.Image:
    img = img.copy()
    img.thumbnail(max_size, resample=Image.LANCZOS)
    return img

def build_palette_image(palette_colors):
    pal_img = Image.new('P', (1, 1))
    flat = []
    for (r, g, b) in palette_colors:
        flat += [int(r), int(g), int(b)]
    if len(palette_colors) < 256:
        flat += [0, 0, 0] * (256 - len(palette_colors))
    pal_img.putpalette(flat)
    return pal_img

def quantize_to_palette(img: Image.Image, palette_colors, dither: bool) -> Image.Image:
    pal_img = build_palette_image(palette_colors)
    dither_flag = 1 if dither else 0
    quant = img.convert('RGB').quantize(palette=pal_img, dither=dither_flag)
    return quant.convert('RGB')

def pixelate(img: Image.Image, pixel_size: int) -> Image.Image:
    w, h = img.size
    pixel_size = max(1, int(pixel_size))
    small_w = max(1, w // pixel_size)
    small_h = max(1, h // pixel_size)
    small = img.resize((small_w, small_h), resample=Image.BILINEAR)
    result = small.resize((w, h), resample=Image.NEAREST)
    return result

def enhance_arcade(img: Image.Image) -> Image.Image:
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img = ImageEnhance.Color(img).enhance(1.1)
    return img

def _snap_channel(channel: Image.Image, bits: int) -> Image.Image:
    levels = (1 << bits) - 1
    def _map(v):
        return int(round((v / 255.0) * levels)) * (255 // levels)
    return channel.point(_map)

def snap_rgb_bits(img: Image.Image, bits: int) -> Image.Image:
    r, g, b = img.convert('RGB').split()
    r = _snap_channel(r, bits)
    g = _snap_channel(g, bits)
    b = _snap_channel(b, bits)
    return Image.merge('RGB', (r, g, b))

def snap_rgb333(img: Image.Image) -> Image.Image:
    return snap_rgb_bits(img, 3)

def snap_rgb555(img: Image.Image) -> Image.Image:
    return snap_rgb_bits(img, 5)

def snap_rgb666(img: Image.Image) -> Image.Image:
    return snap_rgb_bits(img, 6)

def apply_nes_emphasis(palette, emphasize_r=False, emphasize_g=False, emphasize_b=False):
    # Approximate: dim non-emphasized channels by ~15%
    r_factor = 1.0 if emphasize_r else 0.85
    g_factor = 1.0 if emphasize_g else 0.85
    b_factor = 1.0 if emphasize_b else 0.85
    out = []
    for (r, g, b) in palette:
        rr = max(0, min(255, int(r * r_factor)))
        gg = max(0, min(255, int(g * g_factor)))
        bb = max(0, min(255, int(b * b_factor)))
        out.append((rr, gg, bb))
    return out

# ---- Genesis non-linear VDP curve ---- #
GENESIS_LEVELS = [0, 52, 87, 116, 144, 172, 206, 255]
def apply_genesis_vdp_curve(img: Image.Image) -> Image.Image:
    # Map each channel to nearest of GENESIS_LEVELS
    lut = []
    for v in range(256):
        nearest = min(GENESIS_LEVELS, key=lambda x: abs(x - v))
        lut.append(nearest)
    r, g, b = img.convert('RGB').split()
    r = r.point(lut)
    g = g.point(lut)
    b = b.point(lut)
    return Image.merge('RGB', (r, g, b))

STYLES = [
    "PICO-8 (16 colors)",
    "Game Boy (4 colors)",
    "Commodore 64 (16 colors)",
    "ZX Spectrum (8 colors)",
    "EGA 16",
    "Apple II (Lo-Res 16)",

    "Game Boy Color (RGB555, 32 colors)",
    "Game Boy Advance (RGB555, 64 colors)",
    "Nintendo DS (RGB666, 64 colors)",
    "PlayStation (PS1, RGB555, 32 colors)",
    "Sega Genesis / Mega Drive (RGB333, 64 colors)",
    "NES (Nestopia 54-color)",
    "Nintendo 64 (RGBA5551-like, 64 colors)",

    "Adaptive 32-color (Arcade-like)",
]

def apply_style(img: Image.Image, style: str, pixel_size: int, dither: bool,
                nes_r=False, nes_g=False, nes_b=False,
                genesis_vdp=False, ps1_movie=False,
                n64_mode="RGBA5551") -> Image.Image:
    work = pixelate(img, pixel_size)

    if style == "PICO-8 (16 colors)":
        work = quantize_to_palette(work, PICO8_PALETTE, dither)

    elif style == "Game Boy (4 colors)":
        work = ImageEnhance.Brightness(work).enhance(1.05)
        work = quantize_to_palette(work, GAMEBOY_DMG_PALETTE, dither)

    elif style == "Commodore 64 (16 colors)":
        work = quantize_to_palette(work, C64_PALETTE, dither)

    elif style == "ZX Spectrum (8 colors)":
        work = quantize_to_palette(work, ZX_SPECTRUM_8, dither)

    elif style == "EGA 16":
        work = quantize_to_palette(work, EGA16_PALETTE, dither)

    elif style == "Apple II (Lo-Res 16)":
        work = quantize_to_palette(work, APPLE2_LORES_16, dither)

    elif style == "Game Boy Color (RGB555, 32 colors)":
        work = snap_rgb555(work)
        dither_flag = 1 if dither else 0
        work = work.convert('RGB').quantize(colors=32, method=0, dither=dither_flag).convert('RGB')

    elif style == "Game Boy Advance (RGB555, 64 colors)":
        work = snap_rgb555(work)
        dither_flag = 1 if dither else 0
        work = work.convert('RGB').quantize(colors=64, method=0, dither=dither_flag).convert('RGB')

    elif style == "Nintendo DS (RGB666, 64 colors)":
        work = snap_rgb666(work)
        dither_flag = 1 if dither else 0
        work = work.convert('RGB').quantize(colors=64, method=0, dither=dither_flag).convert('RGB')

    elif style == "PlayStation (PS1, RGB555, 32 colors)":
        work = snap_rgb555(work)
        blur_radius = 1.2 if ps1_movie else 0.5
        work = work.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        if ps1_movie:
            # No palette limit in movie mode; keep snapped image
            pass
        else:
            dither_flag = 1 if dither else 0
            work = work.convert('RGB').quantize(colors=32, method=0, dither=dither_flag).convert('RGB')

    elif style == "Sega Genesis / Mega Drive (RGB333, 64 colors)":
        work = snap_rgb333(work)
        if genesis_vdp:
            work = apply_genesis_vdp_curve(work)
        dither_flag = 1 if dither else 0
        work = work.convert('RGB').quantize(colors=64, method=0, dither=dither_flag).convert('RGB')

    elif style == "NES (Nestopia 54-color)":
        pal = apply_nes_emphasis(NES_NESTOPIA_54, nes_r, nes_g, nes_b)
        work = quantize_to_palette(work, pal, dither)

    elif style == "Nintendo 64 (RGBA5551-like, 64 colors)":
        work = work.filter(ImageFilter.GaussianBlur(radius=0.6))
        work = snap_rgb555(work)
        dither_flag = 1 if dither else 0
        if n64_mode == "CI8":
            work = work.convert('RGB').quantize(colors=256, method=0, dither=dither_flag).convert('RGB')
        elif n64_mode == "CI4":
            work = work.convert('RGB').quantize(colors=16, method=0, dither=dither_flag).convert('RGB')
        else: 
            work = work.convert('RGB').quantize(colors=64, method=0, dither=dither_flag).convert('RGB')

    elif style == "Adaptive 32-color (Arcade-like)":
        work = enhance_arcade(work)
        dither_flag = 1 if dither else 0
        work = work.convert('RGB').quantize(colors=32, method=0, dither=dither_flag).convert('RGB')

    return work





#UI stuff
class PixelArtApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title(APP_TITLE)

        # State
        self.original_image = None
        self.processed_image = None
        self.preview_photo = None
        self.compare_photos = []  

        # Notebook
        self.nb = ttk.Notebook(root)
        self.nb.pack(fill=tk.BOTH, expand=True)

        self.single_tab = ttk.Frame(self.nb)
        self.nb.add(self.single_tab, text="Single Style")
        self.compare_tab = ttk.Frame(self.nb)
        self.nb.add(self.compare_tab, text="Compare All")
        controls = ttk.Frame(self.single_tab, padding=10)
        controls.pack(side=tk.TOP, fill=tk.X)

        self.load_btn = ttk.Button(controls, text="Load Image…", command=self.load_image)
        self.load_btn.grid(row=0, column=0, padx=(0, 8), pady=4, sticky="w")

        ttk.Label(controls, text="Style:").grid(row=0, column=1, padx=(0, 4), pady=4, sticky="e")
        self.style_var = tk.StringVar(value=STYLES[0])
        self.style_cb = ttk.Combobox(controls, textvariable=self.style_var, values=STYLES, state="readonly", width=42)
        self.style_cb.grid(row=0, column=2, padx=(0, 8), pady=4, sticky="w")
        self.style_cb.bind("<<ComboboxSelected>>", lambda e: self.update_processing())

        ttk.Label(controls, text="Pixel size:").grid(row=0, column=3, padx=(0, 4), pady=4, sticky="e")
        self.pixel_var = tk.IntVar(value=12)
        self.pixel_slider = ttk.Scale(controls, from_=4, to=48, orient=tk.HORIZONTAL, command=self.on_slider)
        self.pixel_slider.set(self.pixel_var.get())
        self.pixel_slider.grid(row=0, column=4, padx=(0, 8), pady=4, sticky="we")
        controls.columnconfigure(4, weight=1)
        self.pixel_label = ttk.Label(controls, text=f"{self.pixel_var.get()} px")
        self.pixel_label.grid(row=0, column=5, padx=(0, 8), pady=4, sticky="w")

        self.dither_var = tk.BooleanVar(value=False)
        self.dither_chk = ttk.Checkbutton(controls, text="Dithering", variable=self.dither_var, command=self.update_processing)
        self.dither_chk.grid(row=0, column=6, padx=(0, 8), pady=4, sticky="w")

        self.save_btn = ttk.Button(controls, text="Save Pixel Art…", command=self.save_image)
        self.save_btn.grid(row=0, column=7, padx=(0, 8), pady=4, sticky="e")

        adv = ttk.LabelFrame(self.single_tab, text="Advanced options", padding=10)
        adv.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 10))

        ttk.Label(adv, text="NES Emphasis:").grid(row=0, column=0, sticky="e")
        self.nes_r = tk.BooleanVar(value=False)
        self.nes_g = tk.BooleanVar(value=False)
        self.nes_b = tk.BooleanVar(value=False)
        ttk.Checkbutton(adv, text="Red", variable=self.nes_r, command=self.update_processing).grid(row=0, column=1, sticky="w")
        ttk.Checkbutton(adv, text="Green", variable=self.nes_g, command=self.update_processing).grid(row=0, column=2, sticky="w")
        ttk.Checkbutton(adv, text="Blue", variable=self.nes_b, command=self.update_processing).grid(row=0, column=3, sticky="w")

        self.genesis_vdp = tk.BooleanVar(value=False)
        ttk.Checkbutton(adv, text="Genesis non-linear VDP levels", variable=self.genesis_vdp, command=self.update_processing).grid(row=0, column=4, padx=10, sticky="w")

        self.ps1_movie = tk.BooleanVar(value=False)
        ttk.Checkbutton(adv, text="PS1 24-bit Movie mode", variable=self.ps1_movie, command=self.update_processing).grid(row=0, column=5, padx=10, sticky="w")

        ttk.Label(adv, text="N64 Texture Mode:").grid(row=0, column=6, sticky="e")
        self.n64_mode = tk.StringVar(value="RGBA5551")
        ttk.Combobox(adv, textvariable=self.n64_mode, values=["RGBA5551", "CI8", "CI4"], state="readonly", width=8).grid(row=0, column=7, padx=4, sticky="w")

        def _bind_n64(*_):
            self.update_processing()
        self.n64_mode.trace_add('write', lambda *args: _bind_n64())

        preview_frame = ttk.Frame(self.single_tab, padding=10)
        preview_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.preview_label = ttk.Label(preview_frame, text="Load an image to preview.", anchor="center")
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        compare_controls = ttk.Frame(self.compare_tab, padding=10)
        compare_controls.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(compare_controls, text="Refresh Grid", command=self.refresh_compare).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(compare_controls, text="Save All…", command=self.save_all).pack(side=tk.LEFT)

        self.grid_canvas = tk.Canvas(self.compare_tab)
        self.grid_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.grid_scroll = ttk.Scrollbar(self.compare_tab, orient=tk.VERTICAL, command=self.grid_canvas.yview)
        self.grid_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.grid_canvas.configure(yscrollcommand=self.grid_scroll.set)

        self.grid_inner = ttk.Frame(self.grid_canvas)
        self.grid_window = self.grid_canvas.create_window((0, 0), window=self.grid_inner, anchor='nw')
        self.grid_inner.bind("<Configure>", lambda e: self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox(self.grid_window)))
        self.grid_canvas.bind('<Configure>', self._on_canvas_resize)

    def _on_canvas_resize(self, event):
        self.grid_canvas.itemconfig(self.grid_window, width=event.width)

    def on_slider(self, value):
        val = int(float(value))
        self.pixel_var.set(val)
        self.pixel_label.configure(text=f"{val} px")
        self.update_processing()

    def load_image(self):
        filetypes = [
            ("Image files", ".png .jpg .jpeg .bmp .gif"),
            ("PNG", ".png"), ("JPEG", ".jpg .jpeg"), ("Bitmap", ".bmp"), ("GIF", ".gif"), ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(title="Select an image", filetypes=filetypes)
        if not path:
            return
        try:
            img = Image.open(path).convert('RGB')
            self.original_image = img
            self.update_processing()
            self.refresh_compare()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open image:\n{e}")

    def update_processing(self):
        if self.original_image is None:
            return
        try:
            style = self.style_var.get()
            pixel_size = int(self.pixel_var.get())
            dither = bool(self.dither_var.get())
            self.processed_image = apply_style(
                self.original_image, style, pixel_size, dither,
                nes_r=self.nes_r.get(), nes_g=self.nes_g.get(), nes_b=self.nes_b.get(),
                genesis_vdp=self.genesis_vdp.get(), ps1_movie=self.ps1_movie.get(),
                n64_mode=self.n64_mode.get()
            )
            preview_img = fit_image_for_preview(self.processed_image, PREVIEW_SIZE)
            self.preview_photo = ImageTk.PhotoImage(preview_img)
            self.preview_label.configure(image=self.preview_photo, text="")
        except Exception as e:
            messagebox.showerror("Error", f"Processing failed:\n{e}")

    def refresh_compare(self):
        # Clear existing
        for w in list(self.grid_inner.children.values()):
            w.destroy()
        self.compare_photos.clear()
        if self.original_image is None:
            ttk.Label(self.grid_inner, text="Load an image to compare styles.").grid(row=0, column=0, padx=10, pady=10, sticky='w')
            return
        pixel_size = int(self.pixel_var.get())
        dither = bool(self.dither_var.get())
        # Build grid of previews
        cols = 2
        r = c = 0
        for style in STYLES:
            try:
                out = apply_style(
                    self.original_image, style, pixel_size, dither,
                    nes_r=self.nes_r.get(), nes_g=self.nes_g.get(), nes_b=self.nes_b.get(),
                    genesis_vdp=self.genesis_vdp.get(), ps1_movie=self.ps1_movie.get(),
                    n64_mode=self.n64_mode.get()
                )
                thumb = fit_image_for_preview(out, GRID_THUMB_SIZE)
                photo = ImageTk.PhotoImage(thumb)
                self.compare_photos.append(photo)
                frame = ttk.Frame(self.grid_inner, padding=6)
                ttk.Label(frame, image=photo).pack()
                ttk.Label(frame, text=style).pack()
                frame.grid(row=r, column=c, sticky='nwe')
                c += 1
                if c >= cols:
                    c = 0
                    r += 1
            except Exception as e:
                frame = ttk.Frame(self.grid_inner, padding=6)
                ttk.Label(frame, text=f"{style}: error {e}").pack()
                frame.grid(row=r, column=c, sticky='nwe')
                c += 1
                if c >= cols:
                    c = 0
                    r += 1

    def save_image(self):
        if self.processed_image is None:
            messagebox.showinfo("Save", "Please load an image first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save pixel art",
            defaultextension=".png",
            filetypes=[("PNG", ".png"), ("JPEG", ".jpg .jpeg"), ("BMP", ".bmp"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            ext = os.path.splitext(path)[1].lower()
            img = self.processed_image
            if ext in (".jpg", ".jpeg") and img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(path)
            messagebox.showinfo("Saved", f"Pixel art saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save image:\n{e}")

    def save_all(self):
        if self.original_image is None:
            messagebox.showinfo("Save All", "Please load an image first.")
            return
        folder = filedialog.askdirectory(title="Select folder to save all styles")
        if not folder:
            return
        pixel_size = int(self.pixel_var.get())
        dither = bool(self.dither_var.get())
        count = 0
        errors = []
        for style in STYLES:
            try:
                out = apply_style(
                    self.original_image, style, pixel_size, dither,
                    nes_r=self.nes_r.get(), nes_g=self.nes_g.get(), nes_b=self.nes_b.get(),
                    genesis_vdp=self.genesis_vdp.get(), ps1_movie=self.ps1_movie.get(),
                    n64_mode=self.n64_mode.get()
                )
                safe = style.replace('/', '-').replace('(', '').replace(')', '').replace(',', '').replace(' ', '_')
                path = os.path.join(folder, f"pixel_{safe}.png")
                out.save(path)
                count += 1
            except Exception as e:
                errors.append(f"{style}: {e}")
        msg = f"Saved {count} images to\n{folder}"
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors)
        messagebox.showinfo("Save All", msg)

def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    app = PixelArtApp(root)
    root.geometry("1024x800")
    root.minsize(800, 600)
    root.mainloop()

if __name__ == "__main__":
    main()
