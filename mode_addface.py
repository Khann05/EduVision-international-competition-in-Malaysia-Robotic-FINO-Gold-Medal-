import cv2
import os
import numpy as np
import pickle
import requests

# ================================
# SHEETY CONFIG
# ================================
SHEETY_BASE_URL = "https://api.sheety.co/3ab53c0248a4ec9ed835849c5f401488/dataSiswa"
SHEETY_STUDENT_URL = f"{SHEETY_BASE_URL}/studentData"

SHEETY_TOKEN = ""  # isi kalau pakai token Bearer
SHEETY_HEADERS = {}
if SHEETY_TOKEN:
    SHEETY_HEADERS["Authorization"] = SHEETY_TOKEN

# ================================
# DIRECTORIES
# ================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
os.makedirs(DATASET_DIR, exist_ok=True)

TRAINER_PATH = os.path.join(BASE_DIR, "trainer.yml")
LABEL_MAP_PATH = os.path.join(BASE_DIR, "label_map.pkl")

# ================================
# CAMERA SETUP (SAMA DENGAN TRAINER)
# ================================
CAM_WIDTH = 1280
CAM_HEIGHT = 720


def open_logitech_or_fallback():
    """
    Sama seperti di trainer:
    - Prioritas Logitech USB index 0 (DirectShow, 1280x720 @30fps)
    - Kalau gagal, coba 1, 2, 3
    """
    print("⏳ [INIT] Opening camera (Logitech on index 0)...")

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 30)

    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            h, w = frame.shape[:2]
            print(f"✅ Using Logitech USB (index 0), resolution {w}x{h}")
            return cap
        cap.release()

    print("⚠️ Logitech USB (index 0) gagal, mencoba kamera lain...")

    for idx in [1, 2, 3]:
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


# ================================
# INPUT DATA
# ================================
name = input("Enter Student Name: ").strip()
kelas = input("Enter Class (ex: 7A, 9B, X IPA 2): ").strip().upper()
gender = input("Enter Gender (L/P): ").strip().upper()

if not name:
    print("❌ Nama tidak boleh kosong.")
    raise SystemExit

name_lower = name.lower()

# Folder siswa
person_dir = os.path.join(DATASET_DIR, name)
if os.path.exists(person_dir):
    # hapus foto lama biar bersih
    for f in os.listdir(person_dir):
        try:
            os.remove(os.path.join(person_dir, f))
        except:
            pass
else:
    os.makedirs(person_dir, exist_ok=True)

# ================================
# CAMERA + FACE DETECTOR
# ================================
video = open_logitech_or_fallback()
detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

captured_count = 0
last_face_crop = None
WINDOW_NAME = "Add Face Data"

clicked = False


# ===========================================================
# MOUSE CALLBACK → jika klik kiri, tandai untuk capture
# ===========================================================
def mouse_click(event, x, y, flags, param):
    global clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked = True


cv2.namedWindow(WINDOW_NAME)
cv2.setMouseCallback(WINDOW_NAME, mouse_click)

print("\n📸 Mode: MANUAL CAPTURE (WEBCAM)")
print("➡ Arahkan wajah ke kamera, klik kiri mouse untuk mengambil foto.")
print("➡ Ambil total 50 foto untuk hasil terbaik.")
print("➡ Tekan Q untuk berhenti lebih awal.\n")

# ================================
# MAIN CAPTURE LOOP
# ================================
while True:
    ret, frame = video.read()
    if not ret:
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, 1.3, 5)

    # ambil wajah terbesar
    if len(faces) > 0:
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        (x, y, w, h) = faces[0]
        face_crop = gray[y:y + h, x:x + w]
        face_crop = cv2.resize(face_crop, (200, 200))
        last_face_crop = face_crop

        # gambar box
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    else:
        last_face_crop = None

    # Teks info di layar
    cv2.putText(frame, f"Captured: {captured_count}/50",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                1, (255, 255, 0), 2)

    cv2.putText(frame, "Left Click = Capture Face | Q = Quit",
                (20, 70), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 255, 255), 2)

    cv2.imshow(WINDOW_NAME, frame)

    # jika klik kiri & ada wajah
    if clicked and last_face_crop is not None:
        captured_count += 1
        save_path = os.path.join(person_dir, f"{captured_count}.jpg")
        cv2.imwrite(save_path, last_face_crop)
        print(f"📸 Saved Image {captured_count} -> {save_path}")
        clicked = False

    # selesai
    if captured_count >= 50:
        print("✅ Completed 50 images.")
        break

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("⏹ Dihentikan oleh user (Q).")
        break

video.release()
cv2.destroyAllWindows()


# ===========================================================
# UPDATE STUDENTDATA DI SHEETY (AUTO CREATE / UPDATE)
# ===========================================================
def ensure_student_in_sheet():
    try:
        print("📄 Checking StudentData on Sheety...")
        res = requests.get(SHEETY_STUDENT_URL, headers=SHEETY_HEADERS)
        data = res.json()
        rows = data.get("studentData") or data.get("studentdata") or []

        existing_row = None
        for row in rows:
            if row.get("name", "").lower().strip() == name_lower:
                existing_row = row
                break

        if existing_row is None:
            # ====== BELUM ADA → BUAT BARU ======
            payload = {
                "studentdatum": {
                    "name": name,
                    "class": kelas,
                    "gender": gender,
                    "pointsLeft": 100
                }
            }

            print("➕ Adding student to Sheety...")
            post_res = requests.post(SHEETY_STUDENT_URL, json=payload, headers=SHEETY_HEADERS)

            if post_res.status_code not in (200, 201):
                print("⚠️ Sheety error (POST):", post_res.status_code, post_res.text)
            else:
                print("✅ Added to Sheety!")
        else:
            # ====== SUDAH ADA → UPDATE CLASS & GENDER, POINTS TETAP ======
            row_id = existing_row.get("id")
            if row_id is None:
                print("⚠️ Sheety row has no ID, cannot update.")
                return

            current_points = existing_row.get("pointsLeft", 100)

            payload = {
                "studentdatum": {
                    "name": name,
                    "class": kelas,
                    "gender": gender,
                    "pointsLeft": current_points
                }
            }

            url = f"{SHEETY_STUDENT_URL}/{row_id}"
            print(f"✏️ Updating existing student in Sheety (row id {row_id})...")
            put_res = requests.put(url, json=payload, headers=SHEETY_HEADERS)

            if put_res.status_code not in (200, 201):
                print("⚠️ Sheety error (PUT):", put_res.status_code, put_res.text)
            else:
                print("✅ Student updated in Sheety!")

    except Exception as e:
        print("⚠️ Error Sheety:", e)


ensure_student_in_sheet()

# ===========================================================
# TRAIN LBPH MODEL
# ===========================================================
print("📚 Training LBPH model...")

faces = []
labels = []
label_map = {}
label_id = 0

old_map = {}
if os.path.exists(LABEL_MAP_PATH):
    try:
        with open(LABEL_MAP_PATH, "rb") as f:
            old_map = pickle.load(f)
    except:
        old_map = {}

for person in os.listdir(DATASET_DIR):
    folder = os.path.join(DATASET_DIR, person)
    if not os.path.isdir(folder):
        continue

    # ambil class dan gender lama
    found_class = "Unknown"
    found_gender = ""
    for key, val in old_map.items():
        if isinstance(val, dict) and val.get("name") == person:
            found_class = val.get("class", "Unknown")
            found_gender = val.get("gender", "")
            break

    # override untuk siswa yang baru diinput
    if person == name:
        found_class = kelas
        found_gender = gender

    label_map[label_id] = {
        "name": person,
        "class": found_class,
        "gender": found_gender
    }

    for img in os.listdir(folder):
        path = os.path.join(folder, img)

        # ⛔ skip kalau ini folder (menghindari YOLO dataset di dalamnya)
        if os.path.isdir(path):
            continue

        # ⛔ hanya ambil file gambar
        if not (img.lower().endswith(".jpg") or
                img.lower().endswith(".jpeg") or
                img.lower().endswith(".png")):
            continue

        img_gray = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img_gray is None:
            continue

        faces.append(cv2.resize(img_gray, (200, 200)))
        labels.append(label_id)

    label_id += 1

if len(faces) == 0:
    print("❌ Tidak ada data wajah yang valid untuk training. LBPH tidak diupdate.")
    raise SystemExit

faces = np.asarray(faces)
labels = np.asarray(labels)

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(faces, labels)
recognizer.save(TRAINER_PATH)

with open(LABEL_MAP_PATH, "wb") as f:
    pickle.dump(label_map, f)

print("✅ Training complete!")
print("👤 Student:", name)
print("🏫 Class:", kelas)
print("🚻 Gender:", gender)
print(f"💾 Saved LBPH model to: {TRAINER_PATH}")
print(f"💾 Saved label map to: {LABEL_MAP_PATH}")
