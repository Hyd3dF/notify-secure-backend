from app import create_app
from app.worker import BackgroundWorker
import os

app = create_app()

# Worker'ın sadece tek bir instance olarak çalışmasını garanti edelim
# Gunicorn master process değil, worker process içinde olduğumuzu varsayıyoruz.
# Global bir flag veya lock mekanizması kullanabiliriz ama en basiti:
# Gunicorn config içinde 'preload_app' kullanmak veya aşağıdaki gibi basit bir kontrol.

if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    # Production veya Debug reloader içindeyiz
    try:
        # Basit bir singleton kontrolü
        if not hasattr(app, 'worker_started'):
            worker = BackgroundWorker(app)
            worker.start()
            app.worker_started = True
            print(">>> Background Worker Başlatıldı (Singleton)")
    except Exception as e:
        print(f"Worker başlatma hatası: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
