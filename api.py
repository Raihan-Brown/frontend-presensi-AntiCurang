from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import pandas as pd
import torch
import os
import uuid
import datetime
import uvicorn
from facenet_pytorch import MTCNN, InceptionResnetV1
from test import test # Import fungsi anti-spoof bawaan repositori

app = FastAPI(title="API Presensi AI Fasilkom")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VISITOR_DB = os.path.join(ROOT_DIR, "visitor_database")
VISITOR_HISTORY = os.path.join(ROOT_DIR, "visitor_history")
file_db = 'visitors_db.csv'
file_history = 'visitors_history.csv'
COLS_INFO = ['Name']
COLS_ENCODE = [f'v{i}' for i in range(512)]

# Pastikan folder history ada
if not os.path.exists(VISITOR_HISTORY):
    os.mkdir(VISITOR_HISTORY)

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
mtcnn = MTCNN(
    image_size=160, margin=0, min_face_size=20,
    thresholds=[0.6, 0.7, 0.7], factor=0.709, post_process=True,
    device=device, keep_all=True
)

def crop_image_with_ratio(img, height, width, middle):
    h, w = img.shape[:2]
    h = h - h % 4
    new_w = int(h / height) * width
    startx = middle - new_w // 2
    endx = middle + new_w // 2
    if startx <= 0: return img[0:h, 0:new_w]
    elif endx >= w: return img[0:h, w-new_w:w]
    else: return img[0:h, startx:endx]

# Fungsi Nyatet Absen ke CSV
def record_attendance(name, session_name):
    f_p = os.path.join(VISITOR_HISTORY, file_history)
    dtString = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_data = pd.DataFrame({
        "id": [str(uuid.uuid4())[:8]], # Ambil 8 karakter aja biar rapi
        "visitor_name": [name],
        "session": [session_name],
        "Timing": [dtString]
    })
    
    if not os.path.isfile(f_p):
        new_data.to_csv(f_p, index=False)
    else:
        df = pd.read_csv(f_p)
        df = pd.concat([df, new_data])
        df.to_csv(f_p, index=False)

@app.post("/verify")
async def verify_visitor(file: UploadFile = File(...), session_class: str = Form(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
    
    face_locations, prob = mtcnn(img_rgb, return_prob=True)
    boxes, _ = mtcnn.detect(img_rgb)
    
    if boxes is None or len(boxes) == 0:
        return {"status": "error", "message": "Tidak ada wajah!"}
    
    boxes_int = boxes.astype(int)
    (left, top, right, bottom) = boxes_int[0]
    
    img_crop = crop_image_with_ratio(image_array, 4, 3, (left + right) // 2)
    spoof_score = test(img_crop, "./resources/anti_spoof_models", device)
    
    is_real = spoof_score <= 1
    spoof_status = "REAL" if is_real else "FAKE (Spoofing)"
    
    torch_loc = torch.stack([face_locations[0]]).to(device)
    encodesCurFrame = resnet(torch_loc).detach().cpu().numpy()
    
    db_path = os.path.join(VISITOR_DB, file_db)
    if not os.path.exists(db_path): return {"status": "error", "message": "Database kosong."}
        
    df_db = pd.read_csv(db_path)
    face_encodings = df_db[COLS_ENCODE].values
    
    distances = [np.linalg.norm(e - encodesCurFrame) for e in face_encodings]
    min_distance_idx = np.argmin(distances)
    best_match_distance = distances[min_distance_idx]
    
    similarity_threshold = 0.8
    
    if best_match_distance < similarity_threshold:
        matched_name = df_db.loc[min_distance_idx, 'Name']
        
        # Cuma catet absen kalau mukanya ASLI dan COCOK
        if is_real:
            record_attendance(matched_name, session_class)
            
        return {
            "status": "success",
            "data": {
                "nama": matched_name,
                "spoof_status": spoof_status,
                "similarity": round(float(best_match_distance), 3)
            }
        }
    else:
        return {"status": "failed", "message": "Wajah tidak cocok dengan database.", "data": {"nama": "Unknown", "spoof_status": spoof_status, "similarity": round(float(best_match_distance), 3)}}

# Endpoint untuk ngambil riwayat data ke Frontend
@app.get("/history")
def get_history():
    f_p = os.path.join(VISITOR_HISTORY, file_history)
    if not os.path.isfile(f_p):
        return {"status": "success", "data": []}
    
    df = pd.read_csv(f_p)

    df = df.fillna("")

    # Urutkan dari yang terbaru
    df = df.sort_values(by='Timing', ascending=False)
    return {"status": "success", "data": df.to_dict(orient="records")}

@app.delete("/reset-history")
def reset_history():
    f_p = os.path.join(VISITOR_HISTORY, file_history)
    if os.path.exists(f_p):
        os.remove(f_p) # Hapus file CSV-nya
    return {"status": "success", "message": "Semua data presensi berhasil dihapus!"}

# Endpoint buat daftarin wajah baru ke Database
@app.post("/add-visitor")
async def add_visitor(file: UploadFile = File(...), name: str = Form(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
    
    # Deteksi letak wajah
    face_locations, prob = mtcnn(img_rgb, return_prob=True)
    if face_locations is None or len(face_locations) == 0:
        return {"status": "error", "message": "Wajah tidak terdeteksi. Maju dikit ke kamera!"}
        
    # Ekstrak fitur wajah jadi angka (Encoding)
    torch_loc = torch.stack([face_locations[0]]).to(device)
    encodesCurFrame = resnet(torch_loc).detach().cpu().numpy()[0]
    
    db_path = os.path.join(VISITOR_DB, file_db)
    
    # Susun data 512 kolom
    row_data = {"Name": name}
    for i in range(512):
        row_data[f"v{i}"] = encodesCurFrame[i]
        
    new_df = pd.DataFrame([row_data])
    
    if not os.path.exists(db_path):
        new_df.to_csv(db_path, index=False)
    else:
        df_db = pd.read_csv(db_path)
        df_db = pd.concat([df_db, new_df], ignore_index=True)
        # Kalau namanya udah ada, kita timpa data wajahnya pake yang baru
        df_db.drop_duplicates(subset=['Name'], keep='last', inplace=True) 
        df_db.to_csv(db_path, index=False)
        
    return {"status": "success", "message": f"Mantap! Wajah {name} berhasil didaftarkan ke sistem."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)