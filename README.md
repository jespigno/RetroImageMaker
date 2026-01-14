# RetroImageMaker
Python app that converts input images into the pixelated style seen in different old school consoles. Currently, there is support for the following systems: **PICO-8**, **Game Boy (DMG)**, **Commodore 64**, **ZX Spectrum**, **EGA 16**, **Apple II (Lo-Res 16)**,
  **Game Boy Color (RGB555, 32)**, **Game Boy Advance (RGB555, 64)**, **Nintendo DS (RGB666, 64)**,
  **PlayStation (PS1, RGB555, 32)**, **Sega Genesis/Mega Drive (RGB333, 64)**, **NES (Nestopia 54)**,
  **Nintendo 64 (RGBA5551-like, 64)**, **Adaptive 32-color**.

## Screenshots

| <img src="https://github.com/user-attachments/assets/1f82ea24-08cd-4554-9fdf-7308ca40c1a9" /> |<img src="https://github.com/user-attachments/assets/fde9d327-b4dc-4806-b944-4d0964c108ef" /> | <img src="https://github.com/user-attachments/assets/debb9079-9dc4-4f09-a6ed-f5c119568d4b" /> |
|---|---|---|

## Run
```bash
pip install pillow
python RetroImageMaker.py
```

## Notes (hardware-informed approximations)
- **NES Emphasis bits** are simulated by dimming non-selected color channels (~15%), approximating PPU color emphasis behavior
- **Genesis VDP levels** uses a non-linear mapping observed on hardware where channels are mapped to nearest measured steps (e.g., 0, 52, 87, 116, 144, 172, 206, 255)
- **PS1 24-bit Movie mode**: real hardware can display 24-bit images via VRAM transfers; we avoid palette limiting and add stronger blur for a filmic look
- **N64 texture modes**: common formats include RGBA5551 and CI8/CI4; palette sizes are emulated with quantization
