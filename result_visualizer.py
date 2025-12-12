import matplotlib.pyplot as plt
import numpy as np
import os

def create_comparison_chart():
    if not os.path.exists('assets'): os.makedirs('assets')

    # BU VERİLERİ TEST SONUÇLARINDAN ALIP BURAYA GİREBİLİRSİN
    # Örnek Senaryo:
    # SF=1: İndekssiz 500ms, İndeksli 490ms (Fark yok)
    # SF=10: İndekssiz 2200ms, İndeksli 700ms (Büyük fark)
    
    scenarios = ['SF=1 (1GB)', 'SF=10 (10GB)']
    base_times = [140, 2227]      # İndekssiz Süreler (ms)
    opt_times = [125, 236]        # İndeksli Süreler (ms)

    x = np.arange(len(scenarios))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 6))
    rects1 = ax.bar(x - width/2, base_times, width, label='İndekssiz (Base)', color='#e74c3c')
    rects2 = ax.bar(x + width/2, opt_times, width, label='İndeksli (Optimized)', color='#2ecc71')

    ax.set_ylabel('Sorgu Süresi (ms)')
    ax.set_title('Ölçek Faktörüne Göre İndeks Performans Etkisi')
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.legend()

    # Değerleri çubukların üzerine yaz
    ax.bar_label(rects1, padding=3)
    ax.bar_label(rects2, padding=3)

    plt.tight_layout()
    plt.savefig('assets/speedup_comparison.png')
    print("📊 Grafik kaydedildi: assets/speedup_comparison.png")

if __name__ == "__main__":
    create_comparison_chart()