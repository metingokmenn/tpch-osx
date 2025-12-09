import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import os
import config
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from xgboost import XGBClassifier
from sklearn.multioutput import MultiOutputClassifier

def plot_feature_importance(model, feature_names):
    """XGBoost Feature Importance Grafiği Çizer"""
    # İlk estimator'ın önemlerini al (genelde benzerdir)
    importances = model.estimators_[0].feature_importances_
    df_imp = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
    df_imp = df_imp.sort_values(by='Importance', ascending=False)

    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=df_imp, palette='viridis')
    plt.title(f'Feature Importance (SF={config.SCALE_FACTOR})')
    plt.tight_layout()
    plt.savefig('assets/feature_importance.png')
    print("📊 Grafik kaydedildi: assets/feature_importance.png")

def plot_confusion_matrix_heatmap(y_test, y_pred, labels):
    """Her etiket için Confusion Matrix çizer (Basitleştirilmiş toplam)"""
    # Multi-label olduğu için karmaşık, en önemli etiketi (shipdate) örnek alalım
    # Veya tüm kararların doğruluğunu toplayalım
    
    # Örnek: İlk indeks (shipdate) için matrix
    idx_name = labels[0] # label_idx_lineitem_shipdate
    cm = confusion_matrix(y_test[idx_name], y_pred[:, 0])
    
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title(f'Confusion Matrix: {idx_name}')
    plt.ylabel('Gerçek')
    plt.xlabel('Tahmin')
    plt.tight_layout()
    plt.savefig('assets/confusion_matrix_sample.png')
    print("📊 Grafik kaydedildi: assets/confusion_matrix_sample.png")

def train_model():
    print(f"--- XGBOOST EĞİTİMİ (SF={config.SCALE_FACTOR}) ---")
    if not os.path.exists('assets'): os.makedirs('assets')

    try:
        df = pd.read_csv(config.DATA_FILE)
        print(f"Veri Seti: {len(df)} satır")
    except:
        print("HATA: Veri dosyası yok.")
        return

    # Veri Hazırlığı
    X = df.drop(columns=["query_id", "base_time"] + [c for c in df.columns if c.startswith("label_")])
    y = df[[c for c in df.columns if c.startswith("label_")]]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Eğitim
    xgb = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    model = MultiOutputClassifier(xgb)
    model.fit(X_train, y_train)

    # Test
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n✅ Doğruluk: {acc:.2%}")
    
    # --- GRAFİK ÜRETİMİ ---
    plot_feature_importance(model, X.columns)
    plot_confusion_matrix_heatmap(y_test, y_pred, y.columns)

    # Kayıt
    joblib.dump(model, config.MODEL_FILE)
    joblib.dump(list(X.columns), config.META_FEATURES)
    joblib.dump(list(y.columns), config.META_LABELS)
    print("💾 Model kaydedildi.")

if __name__ == "__main__":
    train_model()