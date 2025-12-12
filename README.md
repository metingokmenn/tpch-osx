# ML-Based Database Index Recommender on TPC-H

Bu proje, PostgreSQL üzerinde TPC-H benchmark veri setini kullanarak, makine öğrenmesi (XGBoost) ile otomatik indeks önerisi yapan bir sistemdir. Sistem, "Batch Processing" yöntemiyle eğitim verisi toplar ve iş yüküne (Workload) en uygun indeksleri önerir.

## 📂 Proje Yapısı

- `config.py`: Tüm sistemin ayarlarının yapıldığı merkezi kontrol dosyası.
- `workload.py`: Rastgele SQL sorguları (Q1, Q3, Q6) üreten modül.
- `training_data_generator_batch.py`: Veritabanında indeksleri kurup/silerek performans verisi toplayan script.
- `model_trainer.py`: Toplanan verilerle XGBoost modelini eğiten ve analiz grafikleri üreten script.
- `index_recommender.py`: Canlı demo için kullanılan, anlık öneri ve hız testi yapan script.
- `result_visualizer.py`: SF=1 ve SF=10 karşılaştırma grafiğini çizen script.
- `assets/`: Üretilen grafiklerin ve modellerin kaydedildiği klasör.

---

## 🚀 Kurulum ve Hazırlık

### 1. Gereksinimlerin Yüklenmesi

Python sanal ortamınızı oluşturun ve gerekli kütüphaneleri yükleyin:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Veri Üretimi (DBGEN)

TPC-H verilerini üretmek için dbgen aracını kullanacağız.

dbgen klasörüne gidin:

```bash
cd dbgen
```

Aracı derleyin:

```bash
make -f makefile.suite
```

SF=1 (1 GB) Verisi Üret:

```bash
./dbgen -s 1
mkdir -p ../sf1_data
mv *.tbl ../sf1_data/
```

SF=10 (10 GB) Verisi Üret:

```bash
rm *.tbl  # Önceki dosyaları temizle
./dbgen -s 10
mkdir -p ../sf10_data
mv *.tbl ../sf10_data/
```

### 3. Veritabanı Kurulumu (PostgreSQL)

DataGrip veya psql kullanarak iki ayrı veritabanı oluşturun:

Veritabanlarını Oluşturun:

tpch_db (SF=1 verisi için)

tpch_db_10 (SF=10 verisi için)

Şemayı Yükleyin:

Her iki veritabanında da CREATE TABLE komutlarını çalıştırarak tabloları oluşturun.

Verileri İçeri Aktarın (Import):

sf1_data klasöründeki dosyaları tpch_db tablolarına yükleyin.

sf10_data klasöründeki dosyaları tpch_db_10 tablolarına yükleyin.

### ⚙️ Hiperparametreler ve Konfigürasyon (config.py)

Çalıştırmadan önce config.py dosyasındaki şu ayarları anlamak önemlidir:

SCALE_FACTOR (1 veya 10):

1: Küçük veri senaryosu. Hedef DB: tpch_db. Veriler RAM'e sığdığı için indeks etkisi azdır.

10: Büyük veri senaryosu. Hedef DB: tpch_db_10. Disk I/O darboğazı olduğu için indeks etkisi yüksektir.

Kullanım: Senaryoyu değiştirmek için bu değeri güncelleyin.

QUERY_COUNT (Örn: 50):

Model eğitimi için kaç farklı sorgu senaryosu üretileceğini belirler.

SF=10'da işlem uzun sürdüğü için 50, SF=1'de 100 yapılabilir.

IMPROVEMENT_THRESHOLD (0.90 - 1.0):

Modelin bir durumu "İndeks Gerekli (1)" olarak etiketlemesi için gereken hızlanma eşiği.

1.0: Süre eşit bile olsa indeksi başarılı say (SF=10 için önerilir).

0.90: En az %10 hızlanma şartı ara (SF=1 için önerilir).

### ▶️ Adım Adım Çalıştırma Rehberi

Projeyi uçtan uca çalıştırmak ve rapor çıktılarını almak için aşağıdaki sırayı takip edin.

AŞAMA 1: SF=1 (İndeksin Etkisiz Olduğunu Kanıtlama)
Amaç: Küçük veride PostgreSQL'in Sequential Scan tercih ettiğini göstermek.

Ayarla: config.py dosyasında SCALE_FACTOR = 1.

Veri Topla:

```bash
python training_data_generator_batch.py
```

Modeli Eğit:

````bash

python model_trainer.py
Yedekle: assets/ klasöründeki grafikleri _sf1 ekiyle yeniden adlandırın (örn: feature_importance_sf1.png).

AŞAMA 2: SF=10 (İndeksin Başarısını Kanıtlama - ASIL TEST)
Amaç: Büyük veride indeksin %60+ hızlanma sağladığını göstermek.

Ayarla: config.py dosyasında SCALE_FACTOR = 10, IMPROVEMENT_THRESHOLD = 1.0.

Veri Topla:

```bash
python training_data_generator_batch.py
````

(Not: Bu işlem 20-30 dakika sürebilir. Sabırla bekleyin).

Modeli Eğit:

```bash
python model_trainer.py
```

(Bu işlem sonucunda rapor için gereken ana grafikler assets klasöründe oluşacaktır).

### AŞAMA 3: Canlı Demo ve Raporlama

Canlı Demo (Video Kaydı İçin): Sistemin çalışmasını ve hızlanma oranını görmek için:

```bash
python index_recommender.py
```

Çıktı Örneği: 🚀 HIZLANMA: %67.6

Karşılaştırma Grafiği: result_visualizer.py dosyasını açın. base_times ve opt_times dizilerine, SF=1 ve SF=10 deneylerinden elde ettiğiniz gerçek süreleri (ms) yazın ve çalıştırın:

```bash
python result_visualizer.py
```

### 📊 Çıktılar (Assets)

Tüm süreç tamamlandığında assets/ klasöründe şu dosyalar yer alacaktır:

feature_importance.png: Modelin karar verirken en çok hangi özelliklere (Tarih aralığı, Tablo boyutu vb.) dikkat ettiğini gösterir.

confusion_matrix.png: Modelin tahmin başarısını ve hata oranlarını gösterir.

speedup_comparison.png: SF=1 ve SF=10 senaryoları arasındaki performans farkını gösteren karşılaştırma grafiği.

model_sf10_xgboost.pkl: Eğitilmiş ve kullanıma hazır model dosyası.
