# Game Design Document (GDD) - Recoil Wing

**Status:** Living Document / In Progress  
**Platform:** PC (Desktop - Pygame)  
**Genre:** Arcade / Physics-Action / Flappy-Shooter  
**Target Resolution:** 450 x 750 (Vertical Arcade Ratio) @ 60 FPS  

---

## 1. Executive Summary & Pitch
**Recoil Wing** adalah reinterpretasi modern dan dinamis dari mekanik klasik Flappy Bird. Bukannya sekadar mengepakkan sayap untuk naik, pemain mengendalikan robot/burung bersenjata yang melayang menggunakan **daya tolak (*recoil physics*) dari tembakan senjata ke arah bawah**.

Pemain tidak hanya dituntut untuk menghindari rintangan pipa, tetapi juga dapat **menembak dan menghancurkan blok rintangan**, mengelola amunisi/cooldown agar tidak jatuh bebas, serta memanfaatkan ledakan untuk momentum navigasi celah sempit.

---

## 2. Core Gameplay Loop
```
[Gravitasi Menarik Pemain Turun] 
          │
          ▼
[Pemain Menembak Senjata ke Bawah] 
          │
          ├──► Daya Tolak (Recoil) Mendorong Pemain ke Atas
          └──► Proyektil Melesat Menghancurkan Balok / Musuh di Bawah
          │
          ▼
[Navigasi Celah Pipa & Kumpulkan Skor]
          │
          ├── Tabrak Rintangan / Jatuh ke Tanah ──► [GAME OVER] ──► [Instant Restart]
          └── Selamat Melewati Rintangan ──► [Skor Bertambah & Kecepatan Naik]
```

---

## 3. Gameplay Mechanics

### 3.1. Physics & Movement
- **Gravity:** Menarik karakter ke bawah secara eksponensial hingga batas *terminal velocity*.
- **Recoil Impulse:** Setiap tembakan memicu gaya impuls negatif secara vertikal (`velocity_y -= RECOIL_FORCE`), sekaligus membatasi kecepatan naik maksimal (*max climb velocity*).
- **Subtle Forward Tilt:** Saat menembak, badan karakter terhentak sedikit dan miring sesuai momentum.

### 3.2. Shooting & Ammo / Heat Management
- **One-Button Action:** Tombol `SPACE` atau `Mouse Left Click` memicu tembakan.
- **Ammo / Burst Capacity:**
  - Karakter memiliki slot peluru (contoh: 3-4 peluru cepat).
  - Menginjak tanah atau cooldown singkat otomatis mengisi ulang peluru, sehingga pemain tidak bisa sekadar *mash button* tanpa perhitungan ritme.

### 3.3. Obstacles & Environment
1. **Solid Pipes (Unbreakable):** Dinding pipa logam padat yang wajib dihindari.
2. **Destructible Crates / Blocks:** Balok rapuh di antara celah pipa yang bisa dihancurkan dengan 1-2 tembakan untuk membuka jalan pintas.
3. **Hazard Spikes / Lasers:** Area bahaya tambahan di level lebih lanjut.

---

## 4. Visual & Game Juice Direction

Game arcade sederhana menjadi luar biasa berkat **"Game Feel" (Juicing)**:
- **Screen Shake:** Hentakan layar halus (2-4px) setiap kali menembak dan ledakan balok.
- **Muzzle Flash & Ejected Shells:** Kilatan cahaya moncong senjata dan selongsong peluru yang terlempar ke atas.
- **Smoke & Sparks Particles:** Jejak asap kecil saat karakter meluncur dan percikan puing saat balok hancur.
- **Color Palette (Arcade Cyberpunk / Modern Retro):**
  - Background: Deep Indigo / Slate Navy (`#181926`)
  - Karakter: Vibrant Cyan & Lemon Gold
  - Dinding Pipa: Metallic Steel Charcoal
  - Balok Hancur: Amber Orange / Hot Red
  - Peluru & Efek: Neon Yellow Glow

---

## 5. Controls
| Aksi | Keyboard | Mouse |
| :--- | :--- | :--- |
| **Shoot / Recoil Jump** | `SPACE` / `UP ARROW` / `W` | `Left Click` |
| **Restart Game** | `R` / `SPACE` (saat Game Over) | `Left Click` |
| **Pause / Resume** | `ESC` / `P` | - |

---

## 6. Project Architecture & Directory Structure
```
recoil_wing/
├── .gitignore
├── GDD.md
├── README.md
├── main.py                     # Entry point program
├── assets/                     # Sprites, SFX, Fonts
│   ├── images/
│   ├── sounds/
│   └── fonts/
└── src/
    ├── __init__.py
    ├── config.py               # Konstanta fisika, warna, resolusi, kontrol
    ├── game.py                 # State manager & game loop utama
    ├── utils/                  # Helper math, drawing, screen shake
    │   ├── __init__.py
    │   └── camera.py
    └── entities/               # Objek-objek dalam game
        ├── __init__.py
        ├── player.py           # Karakter & fisika recoil
        ├── bullet.py           # Proyektil & pooling
        ├── obstacle.py         # Pipa & balok yang bisa hancur
        └── particle.py         # Partikel asap, kilatan, & puing
```

---

## 7. Roadmap & Milestone Checklist

- [x] **Milestone 1: Fondasi & Gerakan Karakter**
  - [x] Setup game window, 60 FPS clock, loop bersih.
  - [x] Karakter burung/drone dengan gravitasi dan animasi tilt/idle.
  - [x] Pembatas layar atas dan bawah (*floor & ceiling clamp*).
- [x] **Milestone 2: Mekanik Recoil & Sistem Tembak**
  - [x] Mekanik tembak ke bawah dengan tombol Spasi / Klik Mouse.
  - [x] Gaya dorong impuls (*velocity impulse*) pada pemain.
  - [x] Entity proyektil (peluru) yang bergerak ke bawah dengan trail neon.
  - [x] Sistem batasan amunisi & indikator recharge pips di HUD.
  - [x] Visual muzzle flash & kickback animation pada moncong senjata.

- [ ] **Milestone 3: Rintangan Interaktif & Destructible Blocks**
  - [ ] Generator pipa bergulir dari kanan ke kiri.
  - [ ] Variasi rintangan: Pipa padat dan balok yang bisa ditembak hancur.
  - [ ] Collision detection (Pemain vs Pipa/Balok, Peluru vs Balok).
- [ ] **Milestone 4: Game Loop, Scoring, & Polish (Juicing)**
  - [ ] Layar Title / Ready, In-Game, dan Game Over screen.
  - [ ] Sistem penghitungan skor & High Score.
  - [ ] Screen shake pada kamera saat menembak dan balok meledak.
  - [ ] Efek partikel (asap tembakan, selongsong peluru, serpihan hancur).
- [ ] **Milestone 5: Ekstensi Fitur (Perks & Modifiers)**
  - [ ] Eksperimen power-up / upgrade berkala (Shotgun recoil, bouncing bullet, dll.).
