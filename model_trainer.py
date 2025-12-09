import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier
from sklearn.multioutput import MultiOutputClassifier
import config # YENİ

def train_model():
    print(f"--- MODEL EĞİTİMİ (SF={config.SCALE_FACTOR}) ---")
    print(f"Veri Kaynağı: {config.DATA_FILE}")

    try:
        df = pd.read_csv(config.DATA_FILE)
        print(f"Yüklenen Veri: {len(df)} satır")
    except:
        print("HATA: Dosya bulunamadı. Önce veri toplayıcıyı çalıştırın!")
        return

    # Veriyi Hazırla
    X = df.drop(columns=["query_id", "base_time"] + [c for c in df.columns if c.startswith("label_")])
    y = df[[c for c in df.columns if c.startswith("label_")]]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # XGBoost Eğitimi
    print("XGBoost eğitiliyor...")
    xgb = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    model = MultiOutputClassifier(xgb)
    model.fit(X_train, y_train)

    # Test
    acc = accuracy_score(y_test, model.predict(X_test))
    print(f"\n✅ Doğruluk: {acc:.2%}")

    # Kaydet (Dinamik İsimlendirme)
    joblib.dump(model, config.MODEL_FILE)
    joblib.dump(list(X.columns), config.META_FEATURES)
    joblib.dump(list(y.columns), config.META_LABELS)
    
    print(f"💾 Model Kaydedildi: {config.MODEL_FILE}")

if __name__ == "__main__":
    train_model()