# Startkey Astra — Instagram Otomatik Yayın

Her gün **10:00 Türkiye saatinde** o günün içeriğini yayınlar: **1 feed gönderisi (4:5) + 1 hikaye (9:16).**
30 gün var, 25 Ağustos'tan başlar, 23 Eylül'de biter.

GitHub'ın sunucularında çalışır — bilgisayarın kapalı olabilir.

---

## Ne nerede

| Dosya | İşi |
|---|---|
| `media/feed/DAY_NN.jpg` | Feed görseli (1080×1350) |
| `media/story/DAY_NN.jpg` | Hikâye görseli (1080×1920) |
| `icerik.json` | Her günün görseli, caption'ı ve tarihi |
| `state/durum.json` | Yayın kaydı (feed_id + story_id her gün için ayrı tutulur) |
| `publish.py` | Yayınlama betiği |
| `.github/workflows/yayinla.yml` | Zamanlama |

**Sıra takvimle belirlenir, sayaçla değil.** Her günün `icerik.json` içinde kendi tarihi var (`tarih: "2026-08-25"` gibi). Betik her çalıştığında "tarihi gelmiş, henüz tamamlanmamış en eski gün"ü bulup onu yayınlar. Bir gün iş çalışmazsa (GitHub kesintisi, token süresi vb.) içerik kaybolmaz — bir sonraki çalıştırmada o gün yayınlanır, plan kaymaz.

**Feed ve hikâye ayrı ayrı işaretlenir.** Feed yayınlanıp hikâye başarısız olursa, bir sonraki çalıştırmada yalnızca hikâye denenir — feed tekrar yayınlanmaz.

---

## Kurulum — bir kereye mahsus

### 1. Depoyu GitHub'a yükle

`1-GITHUB-YUKLE.bat` dosyasını çalıştır. Önce github.com'da **herkese açık (public)** boş bir depo oluşturman gerekir — Meta görselleri açık bir adresten indirmek zorunda, kapalı depoda görseller görünmez ve yayın başarısız olur.

### 2. Meta erişim anahtarını üret

Facebook sayfasına gerek yok — "Instagram Login" yöntemi doğrudan Instagram profesyonel hesabıyla çalışır.

1. `developers.facebook.com` → sağ üstten **My Apps** → **Create App**
2. Uygulama türü sorulduğunda **Other** → **Business** seç, bir isim ver.
3. Uygulama panelinde **Add products** → **Instagram** → **Set up**
4. Sol menüden **Instagram** → **API setup with Instagram login**
5. **1. adım: Generate access token** → `@startkey.astra` hesabını ekle, giriş yap, izinleri onayla.
   - İstenen izin: `instagram_business_content_publish` ve `instagram_business_basic`
6. Ekranda çıkan **erişim anahtarını** ve **Instagram user ID** değerini kopyala.

Anahtar **60 gün** geçerli. 30 günlük kampanya bunun içine sığmaz — **~29 Eylül civarı bir kez yenilemen gerekecek** (Meta panel → aynı ekrandan → Generate token, sonra adım 3'teki secret'ı güncelle).

### 3. Anahtarları GitHub'a gizli olarak gir

Depoda **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| İsim | Değer |
|---|---|
| `IG_ACCESS_TOKEN` | 5. adımdaki erişim anahtarı |
| `IG_USER_ID` | Instagram user ID |

### 4. Deneme çalıştır

**Actions** sekmesi → **Startkey Astra Instagram yayin** → **Run workflow** → `Deneme modu` **açık** bırak → çalıştır.

Kayıtta o günün görsel adreslerini ve caption'ın ilk satırını görürsün ama hiçbir şey yayınlanmaz. Adresler doğru görünüyorsa aynı adımı `Deneme modu` **kapalı** olarak tekrarla — ilk gerçek gönderi yayınlanır.

Bu andan sonra sistem kendi kendine her gün 10:00'da çalışır.

---

## İçeriği güncellemek (fiyat değişti, ilan kalktı, metin düzeltilecek)

Kaynak, bu klasör **değil** — `Startkey-Astra-Social-Media/_motor/icerik-*.json`. Orada düzenle, sonra sırasıyla:

```bash
node ../../_motor/astra-motor.mjs      # görselleri yeniden üret
node ../../_motor/dosya-uret.mjs        # 03_READY_TO_PUBLISH'i tazele
node ../../_motor/bot-uret.mjs          # bu klasörü tazele (state/durum.json KORUNUR)
```

Sonra `git add -A && git commit && git push` ile bu depoyu güncelle. Henüz yayınlanmamış günler yeni içerikle yayınlanır; yayınlanmış günlere dokunulmaz.

---

## Bilinmesi gerekenler

- **Hikâye çıkartmaları eklenemez.** Bağlantı, anket, soru kutusu çıkartmalarını Meta'nın API'si desteklemiyor. Her günün önerisi `icerik.json` içindeki `cikartma` alanında ve iş çıktısında yazılı duruyor; yayından sonra elle eklenmeli.
- **Saatler tam dakikasında olmayabilir.** GitHub zamanlayıcısı yoğunluğa göre 5–20 dakika gecikebilir.
- **Meta günde 100 yayın izni veriyor**, biz günde 2 (1 feed + 1 hikâye) kullanıyoruz.
- **Token 60 günlük, kampanya 30 gün** — süre içinde biter ama marjin dar; ~29 Eylül'e kadar bir kez daha yenilemen iyi olur.
- **Seri bitince** iş kendiliğinden durur; 30 günün tamamı yayınlandığında betik hiçbir şey yapmadan çıkar.
