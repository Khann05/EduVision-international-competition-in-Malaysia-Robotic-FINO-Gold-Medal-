# ============================================================
# RoboFlow_camera_test.py — JoyStudio FINAL (THREAD + SMOOTH)
# ============================================================
# - Kamera jalan halus (Roboflow dipanggil di thread terpisah)
# - FPS ditampilkan di layar
# - Tiap ~0.7 detik kirim 1 frame ke Roboflow
# - Tekan 'q' untuk keluar
# ============================================================

import cv2
import time
import threading
from roboflow_uniform import detect_tie_belt

CAM_WIDTH = 1280
CAM_HEIGHT = 720

# shared state untuk hasil Roboflow
last_rf_result = None   # hasil terakhir (dict)
rf_busy = False         # True kalau thread Roboflow lagi jalan
rf_last_time = 0.0      # kapan terakhir dapat respon


def open_logitech_or_fallback():
    print("⏳ [INIT] Opening camera for Roboflow test...")
    for idx in [0, 1, 2, 3]:
        print(f"🔎 Testing camera index {idx} ...")
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, 30)

        if not cap.isOpened():
            cap.release()
            continue

        ret, frame = cap.read()
        if not ret or frame is None:
            cap.release()
            continue

        h, w = frame.shape[:2]
        print(f"✅ Using camera index {idx} (resolution {w}x{h})")
        return cap

    print("❌ Tidak ada kamera yang bisa dipakai (0,1,2,3 semua gagal).")
    raise SystemExit


def rf_worker(frame_bgr):
    """
    Worker terpisah untuk panggil Roboflow
    supaya loop kamera tidak nge-freeze.
    """
    global last_rf_result, rf_busy, rf_last_time
    try:
        result = detect_tie_belt(frame_bgr)
        last_rf_result = result
        rf_last_time = time.time()
    finally:
        rf_busy = False


def main():
    global rf_busy, last_rf_result

    cap = open_logitech_or_fallback()

    print("📡 Roboflow camera test berjalan...")
    print("   - Tiap ~0.7 detik kirim 1 frame ke Roboflow (di thread terpisah)")
    print("   - Tekan 'q' untuk keluar\n")

    send_interval = 0.7  # detik antar request ke Roboflow
    last_send = 0.0

    prev_time = time.time()
    fps = 0.0

    WIN_NAME = "Roboflow Tie/Belt Camera Test"
    cv2.namedWindow(WIN_NAME)

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("⚠️ Frame tidak terbaca, stop.")
            break

        # Hitung FPS kasar (pakai smoothing biar stabil)
        now = time.time()
        dt = now - prev_time
        prev_time = now
        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt)

        # Kirim ke Roboflow tiap interval, tapi di thread terpisah
        if (now - last_send) >= send_interval and not rf_busy:
            last_send = now
            rf_busy = True
            frame_for_rf = frame.copy()
            threading.Thread(
                target=rf_worker,
                args=(frame_for_rf,),
                daemon=True
            ).start()

        # Teks judul
        cv2.putText(
            frame,
            "Roboflow Camera Test - press 'q' to quit",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

        # Info FPS + status Roboflow
        status_text = f"FPS: {fps:4.1f}"
        if rf_busy:
            status_text += " | Roboflow: processing..."
        else:
            if rf_last_time > 0:
                dt_since = now - rf_last_time
                status_text += f" | last RF: {dt_since:4.1f}s ago"
            else:
                status_text += " | last RF: (none)"

        cv2.putText(
            frame,
            status_text,
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        # Gambarkan hasil terakhir Roboflow
        if last_rf_result is not None:
            tie_box = last_rf_result.get("tie")
            belt_box = last_rf_result.get("belt")

            if tie_box is not None:
                x1, y1, x2, y2, conf = tie_box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"Tie {conf*100:.1f}%",
                    (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )

            if belt_box is not None:
                x1, y1, x2, y2, conf = belt_box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(
                    frame,
                    f"Belt {conf*100:.1f}%",
                    (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 0, 0),
                    2,
                    cv2.LINE_AA,
                )

        cv2.imshow(WIN_NAME, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
