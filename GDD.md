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

### 3.3. Obstacles, Hazards & In-Flight Gates
1. **Solid Pipes (Unbreakable):** Dinding pipa logam padat berarsitektur industrial yang wajib dihindari.
2. **Destructible Crates / Blocks:** Peti bahaya rapuh di antara celah pipa yang bisa dihancurkan dengan tembakan ke bawah untuk membuka jalur bebas.
3. **In-Flight Choice Gates (Real-Time Evolution):**
   - Di titik skor milestone (5, 12, 20, 32), muncul sepasang gerbang portal energi holografik atas & bawah.
   - **Tanpa Pause!** Pemain bebas mengarahkan recoil untuk terbang menembus salah satu gerbang yang diinginkan secara *seamless* tanpa memutus momentum terbang.
   - Gerbang tidak mematikan; pemain yang melewatkan gerbang tetap aman melanjutkan permainan.


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
| **Toggle Mute Audio** | `M` | - |
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

- [x] **Milestone 3: Rintangan Interaktif & Destructible Blocks**
  - [x] Generator pipa bergulir dari kanan ke kiri dengan visual industrial shading.
  - [x] Variasi rintangan: Pipa padat dan peti bahaya (*hazard crate*) yang bisa ditembak hancur.
  - [x] Collision detection lengkap (Pemain vs Pipa/Balok, Peluru vs Balok/Pipa).
  - [x] Sistem partikel puing ledakan (*crate debris burst*) dan percikan api logam (*sparks*).
  - [x] Sistem skor rintangan (+1) dan bonus skor penghancuran peti (+2).

- [x] **Milestone 4: Game Loop, Scoring, & Polish (Juicing)**
  - [x] Layar Title / Ready dengan rekor terbaik, In-Game HUD, dan Game Over modal.
  - [x] Sistem penyimpanan High Score persisten lokal (`highscore.dat`) & pita "NEW BEST RECORD".
  - [x] Kamera Screen Shake berbasis trauma quadratic (recoil kick, crate blast, crash).
  - [x] Selongsong peluru kuningan (*brass shell casings*) yang terlempar & memantul di tanah.
  - [x] Partikel kepulan asap laras senjata (*muzzle smoke puffs*).
  - [x] Efek popup teks skor melayang (`+1`, `+2 CRATE!`).
  - [x] Parallax background silhouette skyline kota cyberpunk yang bergulir halus.

- [x] **Milestone 5: Ekstensi Fitur (Perks & Modifiers)**
  - [x] Sistem Roguelite In-Flight Choice Gates tanpa pause di skor threshold.
  - [x] Perk **Scatter Cannon (Shotgun)**: 3 peluru menyebar dengan daya tolak recoil ekstra.
  - [x] Perk **Energy Shield**: Barrier kinetik berputar yang menyerap 1x tabrakan maut.
  - [x] Perk **Ricochet Rounds**: Peluru memantul 2x di pipa & lantai untuk melibas peti dari berbagai sudut.
  - [x] Perk **Overclocked Cell**: Kapasitas peluru naik menjadi 6 slot + reload 35% lebih cepat.
  - [x] Perk **Hyper Piercer**: Laser ungu tembus rintangan dalam 1 garis lurus.
  - [x] HUD indikator active perk badge di pojok kiri atas.

- [x] **Phase 2 - Milestone 6: Audio, SFX & Background Music (BGM)**
  - [x] Generator sintesis audio prosedural tanpa ketergantungan download (`src/utils/audio_generator.py`).
  - [x] 8 file WAV efek suara sintetis: `shoot.wav`, `shotgun.wav`, `laser.wav`, `explosion.wav`, `portal.wav`, `shield_deflect.wav`, `score.wav`, `crash.wav`.
  - [x] 1 file WAV musik synthwave 132 BPM seamless loop bawaan (`bgm_gameplay.wav`).
  - [x] Sistem pemutar BGM streaming dengan prioritas otomatis untuk file custom pengguna (`bgm_gameplay.mp3` atau `.ogg`).
  - [x] Audio ducking cerdas (volume musik melembut saat Game Over).
  - [x] SoundManager modular (`src/utils/sound_manager.py`) dengan multi-channel audio dan safe fallback.
  - [x] Fitur mute cepat via tombol keyboard `M` (mute SFX & BGM sekaligus).

- [x] **Phase 3 - Milestone 7: Airborne Security Drones & Dual-Lane Split Paths**
  - [x] Entitas musuh Drone (`src/entities/enemy.py`) dengan animasi jet thruster ganda, chassis heksagonal gelap, antena sinyal, dan mata sensor merah dengan radar scan pulse meluas.
  - [x] **Dual-Lane Split-Corridor System**: Khusus saat rintangan Drone muncul, pipa otomatis bercabang menjadi 2 jalur terbang (Jalur Atas vs Jalur Bawah) yang dipisahkan oleh central divider hub:
    - **1 Jalur Aman (Safe Corridor)**: Celah bersih dan lega (150px) tanpa musuh untuk pemain yang ingin menghindar atau amunisi sedang menipis.
    - **1 Jalur Tempur (Combat Drone Corridor)**: Celah yang dijaga oleh patroli Drone bagi pemain yang ingin menembak drone untuk meraih reward.
    - **LED Waypoint Indicator**: Indikator lampu status di tengah divider (Merah = Jalur Berbahaya/Drone, Hijau/Teal = Jalur Aman Terbuka).
  - [x] Pipa standar tanpa musuh (Peti / Bersih) tetap menggunakan 1 jalur tunggal dengan celah yang diperlebar (`PIPE_GAP = 185px`) agar tidak terasa sempit dan lebih adil bagi manuver player.
  - [x] Mekanik Aerial Combo ala Downwell: Menembak jatuh Drone menghadiahkan **+2 Skor** dan **Instant +1 Ammo Refund** untuk melanjutkan kombo terbang tanpa mendarat!
  - [x] Sistem debris sibernetik (`create_drone_debris`) dengan serpihan logam gelap, percikan api merah dan percikan listrik neon.
  - [x] Interaksi Energy Shield: Shield kinetik dapat menghancurkan drone seketika saat bertabrakan tanpa mematikan player.

- [x] **Phase 4 - Milestone 8: Dynamic Combo Multiplier & Streak System**
  - [x] Sistem Streak Combo bertingkat (`x2 COMBO`, `x3 SUPER`, `x4 ULTRA`, `x5+ HYPER STREAK`) saat menghancurkan drone & peti berturut-turut.
  - [x] Skor multiplier dinamis (`base_score * combo_multiplier`) dengan popup teks animasi berwarna sesuai tingkatan tier.
  - [x] Timer jendela combo (~2.6 detik) dengan perpanjangan waktu saat berhasil melintasi celah pipa atau portal choice gate.
  - [x] Visual **Luminous Afterimage Motion Trail**: Karakter burung mengeluarkan siluet bayangan berkecepatan tinggi yang berubah warna sesuai tier combo (Teal ➔ Gold ➔ Rose ➔ Cosmic Violet).
  - [x] HUD Arcade Combo Badge: Indikator pill box menyala di bawah skor dengan depleting timer bar horizontal.
  - [x] Rekap statistik **MAX STREAK** di layar Game Over modal.

- [x] **Phase 5 - Milestone 9: Dynamic Biome & Atmospheric Weather Shifting**
  - [x] Modul cuaca & bioma prosedural (`src/entities/weather.py`) dengan optimasi partikel strictly-capped (60 FPS stabil).
  - [x] **Sektor 1 (Skor 0 - 14): Neon Downtown**: Langit malam indigo tenang, jendela kota neon cyan, dan partikel udara bersih.
  - [x] **Sektor 2 (Skor 15 - 29): Acid Rain District**: Gradien langit petrol/dark teal, hujan asam cyber miring (`RainDrop`), percikan air di lantai (`SplashParticle`), kilatan petir latar ambient, dan jendela gedung hijau asam.
  - [x] **Sektor 3 (Skor 30+): Solar Overdrive**: Gradien merah crimson senja cyberpunk, partikel bara api melayang naik dengan sinusoidal drift (`EmberParticle`), dan jendela gedung rose red.
  - [x] **Holographic Sector Transition Banner**: Notifikasi banner futuristik bersudut tekno yang meluncur dari atas layar saat memasuki sektor baru dengan audio cue halus.







