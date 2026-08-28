<div align="center">

# ⚡ LoL AutoPilot PRO

**League of Legends için Yeni Nesil, %100 Güvenli ve Tam Otomatik İstemci Asistanı**

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Discord](https://img.shields.io/badge/Discord-Join%20Community-5865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/MXXEttvfs)
[![Vanguard Safe](https://img.shields.io/badge/Vanguard-100%25%20Safe-brightgreen.svg?style=for-the-badge&logo=riotgames&logoColor=white)](#-g%C3%BCvenlik--ban-riski)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![UI Engine](https://img.shields.io/badge/UI-PyWebView%20%26%20CSS3-ff69b4.svg?style=for-the-badge)](https://pywebview.flowrl.com/)
[![License](https://img.shields.io/badge/License-MIT-orange.svg?style=for-the-badge)](LICENSE)

<br/>

> **LoL AutoPilot PRO**, resmi **Riot League Client Update (LCU) REST API** protokolünü kullanarak maç kabulünden şampiyon seçimine, özel profil arka planından lig istatistiklerine kadar tüm istemci deneyiminizi tek bir modern arayüzden yönetmenizi sağlar.

</div>

---

## 🌟 Öne Çıkan Özellikler

### ⚡ 1. Hızlı Otomasyonlar
* **⚡ Anında Maç Kabul:** Maç sırası geldiğinde saliseler içinde maçı otomatik kabul eder.
* **🎖️ Otomatik Takdir (Auto Honor):** Oyun bittiğinde en iyi takım arkadaşınızı (veya rastgele) otomatik takdir ederek zamandan kazandırır.
* **🚪 Oyun Başlayınca LoL'ü Kapat (Game Killer):** Şampiyon seçimi tamamlanıp yükleme ekranına (Loading Screen) geçildiğinde istemciyi otomatik kapatır; diğer oyuncuları yükleme ekranında bekletir *(Sigara ve kahve molaları için ideal 😄)*.

### 🏆 2. Canlı İstatistik & Şampiyon Ustalık Vitrini
* **📊 Canlı Dereceli Kartları:** Tek/Çift (Solo/Duo) ve Esnek (Flex) lig dereceniz, LP'niz, Galibiyet/Mağlubiyet ve Kazanma Oranınız (% Winrate) anlık istemciden çekilerek gösterilir.
* **⚔️ En Çok Oynanan 6 Şampiyon:** Ustalık seviyeleri ve binlik formatlı tam ustalık puanları (Mastery Points) şık kartlar halinde sergilenir.

### 👑 3. Özel Profil Arka Planı (Splash) Ayarlayıcı
* Sahip olmasanız bile oyundaki **herhangi bir şampiyonun ve kostümünün** HD Splash Art görselini League of Legends profilinizin arka planına tek tıkla uygular.

### 🚫 4. Akıllı Ban Sistemi
* **Koridora Özel Ban Listeleri:** Üst Koridor, Orman, Orta Koridor, Alt Koridor ve Destek rolleri için öncelikli ban listeleri.
* **🛡️ Takım Arkadaşı Koruma:** Takım arkadaşınızın seçmek istediği (Pick Intent) şampiyonları asla banlamaz, sıradaki yedek şampiyona geçer.

### 🎯 5. Akıllı Şampiyon Seçimi & Kilitleme (Auto Pick)
* Her koridor için 1., 2. ve 3. öncelikli şampiyon tercihleri.
* Yasaklanan veya karşı takım tarafından alınan şampiyonlarda otomatik yedek şampiyonu kilitler.

### 👻 6. Deceive (Hayalet / Çevrimdışı Modu)
* Arkadaş listenize **Çevrimdışı (Görünmez)** görünerek gizlice tek başınıza maç oynayın.
* Özel durum mesajları ve sahte mobil/uzakta durumları ayarlayın.

### 📋 7. Canlı Olay & LCU Log Konsolu
* İstemcide gerçekleşen tüm durumları (Sıra, Şampiyon Seçimi, Banlama, API Yanıtları) milisaniyelik zaman damgalarıyla anlık takip edin.

---

## 🛡️ Güvenlik & Ban Riski (%100 Vanguard Safe)

> **LoL AutoPilot PRO tamamen ban riski taşımayan resmi API altyapısı üzerine inşa edilmiştir.**

* ❌ **Bellek (RAM) Modifikasyonu Yapmaz:** Oyun içi bellek bloklarını okumaz, yazmaz veya taramaz.
* ❌ **DirectX / Render Hook İçermez:** Oyun motoruna herhangi bir `.dll` enjekte etmez.
* ❌ **Pixel Search / Macro İçermez:** Tıklama simülasyonu değil, doğrudan soket veri transferi yapar.
* ✅ **Resmi LCU REST API:** Riot Games'in kendi istemcisinin kullandığı resmi yerel port ve şifreli HTTPS/WSS protokolüyle güvenle iletişim kurar.

---

## 🚀 Kurulum & Çalıştırma

### Yöntem 1: Hazır `.exe` Olarak Çalıştırma (Tavsiye Edilen)
1. `dist/LoL_AutoPilot/LoL_AutoPilot.exe` dosyasını çalıştırın veya masaüstünüzdeki kısayola tıklayın.
2. League of Legends istemcinizi açın; program otomatik olarak bağlanacak ve hazır hale gelecektir.

### Yöntem 2: Kaynak Koddan Çalıştırma (Geliştirici Modu)
```bash
# 1. Proje dizinine gidin
cd "c:\kod\yeni program"

# 2. Gerekli kütüphaneleri yükleyin
pip install pywebview requests urllib3 pillow

# 3. Uygulamayı başlatın
python app_webview.py
```

### Projeyi Tekrar Derleme (PyInstaller Build)
```bash
python -m PyInstaller --noconfirm --onedir --windowed \
  --name "LoL_AutoPilot" \
  --icon "icon.ico" \
  --add-data "champions.json;." \
  --add-data "icon.ico;." \
  --collect-all webview \
  --collect-all pythonnet \
  --collect-all clr_loader \
  app_webview.py
```

---

## 🛠️ Kullanılan Teknolojiler

* **Çekirdek:** Python 3.10+
* **Arayüz:** PyWebView (Edge Chromium / WebView2 Engine)
* **Tasarım:** Modern Glassmorphism, Dark Neon Cyberpunk CSS3
* **İletişim:** Riot LCU REST API (Local HTTPS Protocol) & CommunityDragon / DDragon CDN

---

## 📫 İletişim & Destek (Contact & Support)

Herhangi bir hata bildirimi, özellik önerisi veya destek için aşağıdaki kanallardan bize ulaşabilirsiniz:

* 💬 **Discord Topluluğu:** [discord.gg/MXXEttvfs](https://discord.gg/MXXEttvfs)
* 🐛 **Hata Bildirimi & İstekler:** [GitHub Issues](https://github.com/) sekmesinden yeni bir başlık açabilirsiniz.
* ⭐ **Destek Olmak İçin:** Projeyi beğendiyseniz sağ üstteki **Star (Yıldız) ⭐** butonuna tıklayarak destek olabilirsiniz!

---

## ⚖️ Yasal Uyarı (Disclaimer)

*LoL AutoPilot PRO, Riot Games tarafından onaylanmamıştır ve Riot Games veya League of Legends'ın yapımında veya yönetiminde resmi olarak yer alan herhangi bir kişinin görüş veya düşüncelerini yansıtmaz. League of Legends ve Riot Games, Riot Games, Inc.'in ticari markaları veya tescilli ticari markalarıdır.*

---

<div align="center">
  Geliştirici: <b>LoL AutoPilot Team</b> • Keyifli Oyunlar! 🎮🏆
</div>
