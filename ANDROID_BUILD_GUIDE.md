# 📱 Panduan Export & Build "Recoil Wing" ke Android

Game **Recoil Wing** telah dirancang dengan rasio layar Portrait (`400 x 700`), kontrol satu sentuhan (*one-touch tap*), tombol pause di layar sentuh, dan perulangan loop `asyncio` yang sepenuhnya kompatibel dengan ekosistem mobile/Android.

Ada **3 Cara** untuk menjalankan atau mem-build Recoil Wing ke Android:

---

## 🚀 Opsi 1: Uji Coba Instan di HP via Pygbag (PWA / Layar Penuh) — *Paling Mudah & Cepat*

Dengan metode ini, Anda **tidak perlu meng-install Android Studio atau compiler berat**. Game dikompilasi menjadi WebAssembly berkecepatan tinggi dan bisa langsung dimainkan di HP Android Anda melalui jaringan Wi-Fi lokal, serta dapat di-install ke layar utama HP seperti aplikasi asli.

### Langkah-langkah:
1. **Install pygbag di laptop:**
   ```bash
   pip install pygbag
   ```

2. **Jalankan web server lokal:**
   ```bash
   pygbag .
   ```
   *(Pygbag akan melakukan build WebAssembly dan membuka server di port `8000`)*.

3. **Buka di HP Android Anda:**
   - Pastikan laptop dan HP Android terhubung ke jaringan Wi-Fi yang sama.
   - Cari IP laptop Anda (ketik `ipconfig` di command prompt, misal `192.168.1.15`).
   - Buka browser **Google Chrome** di HP Android, lalu akses:
     ```
     http://192.168.1.15:8000
     ```
4. **Jadikan Aplikasi Penuh (PWA / Fullscreen App):**
   - Di Google Chrome HP, tekan menu titik tiga (⋮) di pojok kanan atas.
   - Pilih **"Tambahkan ke Layar Utama" (Add to Home screen)** atau **"Install Aplikasi"**.
   - Ikon game *Recoil Wing* akan muncul di daftar aplikasi HP Anda dan dapat dimainkan layar penuh tanpa bar browser!

---

## ☁️ Opsi 2: Build Native APK Otomatis di Cloud (GitHub Actions) — *Bebas Pusing*

Karena compiler Android (Buildozer / Android NDK) membutuhkan sistem operasi Linux, cara termudah dan terbersih tanpa harus meng-install Ubuntu/WSL di laptop Anda adalah memanfaatkan **GitHub Actions** yang sudah kami siapkan di file [`.github/workflows/android.yml`](file:///.github/workflows/android.yml).

### Langkah-langkah:
1. Buat repository baru di akun **GitHub** Anda dan push folder project ini:
   ```bash
   git remote add origin https://github.com/USERNAME/recoil-wing.git
   git push -u origin master
   ```
2. Buka halaman repository Anda di browser GitHub.
3. Klik tab **Actions** di bagian atas.
4. Di panel sebelah kiri, pilih workflow **"Build Android APK"**.
5. Klik tombol **"Run workflow"** ➔ **"Run workflow"**.
6. Server Ubuntu Cloud milik GitHub akan otomatis mengunduh Android NDK/SDK, Cython, dan meng-compile file APK asli untuk Anda (~10 - 15 menit).
7. Setelah selesai bertanda centang hijau, klik hasil build tersebut, gulir ke bagian **Artifacts**, dan unduh file:
   - **`RecoilWing-Android-APK.zip`**
8. Ekstrak zip tersebut, kirim file `.apk` ke HP Android Anda (lewat WA, Telegram, atau kabel data), lalu install!

---

## 💻 Opsi 3: Build Native APK Lokal (WSL2 / Linux)

Jika Anda memiliki **WSL 2 (Ubuntu)** di laptop Windows Anda:

1. Buka terminal WSL2 / Ubuntu:
   ```bash
   sudo apt update
   sudo apt install -y git zip unzip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev python3-pip openjdk-17-jdk
   ```
2. Install Buildozer & Cython:
   ```bash
   pip install Cython==0.29.36 buildozer virtualenv
   ```
3. Masuk ke direktori game di WSL (misal `/mnt/d/PRODUKTIF/Pygame/recoil_wing`) dan jalankan:
   ```bash
   buildozer android debug
   ```
4. File APK akan dihasilkan di dalam folder `bin/` (misal: `bin/recoilwing-1.0.0-arm64-v8a_armeabi-v7a-debug.apk`).
