#######################################################
import uuid ## random id generator
from streamlit_option_menu import option_menu
import streamlit as st
import os
import shutil
import cv2
import numpy as np
import pandas as pd
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image, ImageDraw
from test import test
import torch
import datetime
#######################################################

# Pengaturan Tab Browser (Biar nggak polos tulisan Streamlit)
st.set_page_config(page_title="Presensi Fasilkom UNSIKA", page_icon="🎓", layout="centered")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VISITOR_DB = os.path.join(ROOT_DIR, "visitor_database")
VISITOR_HISTORY = os.path.join(ROOT_DIR, "visitor_history")
COLOR_DARK  = (0, 0, 153)
COLOR_WHITE = (255, 255, 255)
COLS_INFO   = ['Name']
COLS_ENCODE = [f'v{i}' for i in range(512)]
## Database
data_path       = VISITOR_DB
file_db         = 'visitors_db.csv'         ## To store user information
file_history    = 'visitors_history.csv'    ## To store visitor history information

## Image formats allowed
allowed_image_type = ['.png', 'jpg', '.jpeg']

def initialize_data():
    if os.path.exists(os.path.join(data_path, file_db)):
        df = pd.read_csv(os.path.join(data_path, file_db))
    else:
        df = pd.DataFrame(columns=COLS_INFO + COLS_ENCODE)
        df.to_csv(os.path.join(data_path, file_db), index=False)
    return df

def add_data_db(df_visitor_details):
    try:
        df_all = pd.read_csv(os.path.join(data_path, file_db))
        if not df_all.empty:
            df_all = pd.concat([df_all,df_visitor_details], ignore_index=False)
            df_all.drop_duplicates(keep='first', inplace=True)
            df_all.reset_index(inplace=True, drop=True)
            df_all.to_csv(os.path.join(data_path, file_db), index=False)
            st.success('Details Added Successfully!')
        else:
            df_visitor_details.to_csv(os.path.join(data_path, file_db), index=False)
            st.success('Initiated Data Successfully!')
    except Exception as e:
        st.error(e)

def BGR_to_RGB(image_in_array):
    return cv2.cvtColor(image_in_array, cv2.COLOR_BGR2RGB)

def attendance(id, name):
    f_p = os.path.join(VISITOR_HISTORY, file_history)
    now = datetime.datetime.now()
    dtString = now.strftime('%Y-%m-%d %H:%M:%S')
    df_attendace_temp = pd.DataFrame(data={ "id"            : [id],
                                            "visitor_name"  : [name],
                                            "Timing"        : [dtString]
                                            })

    if not os.path.isfile(f_p):
        df_attendace_temp.to_csv(f_p, index=False)
    else:
        df_attendace = pd.read_csv(f_p)
        df_attendace = pd.concat([df_attendace,df_attendace_temp])
        df_attendace.to_csv(f_p, index=False)

def view_attendace():
    f_p = os.path.join(VISITOR_HISTORY, file_history)
    df_attendace_temp = pd.DataFrame(columns=["id", "visitor_name", "Timing"])

    if not os.path.isfile(f_p):
        df_attendace_temp.to_csv(f_p, index=False)
    else:
        df_attendace_temp = pd.read_csv(f_p)

    df_attendace = df_attendace_temp.sort_values(by='Timing', ascending=False)
    df_attendace.reset_index(inplace=True, drop=True)

    st.write(df_attendace)

    if df_attendace.shape[0]>0:
        id_chk  = df_attendace.loc[0, 'id']
        id_name = df_attendace.loc[0, 'visitor_name']

        selected_img = st.selectbox('Search Image using ID', options=['None']+list(df_attendace['id']))

        avail_files = [file for file in list(os.listdir(VISITOR_HISTORY))
                       if ((file.endswith(tuple(allowed_image_type))) & 
                           (file.startswith(selected_img) == True))]

        if len(avail_files)>0:
            selected_img_path = os.path.join(VISITOR_HISTORY, avail_files[0])
            st.image(Image.open(selected_img_path))

def crop_image_with_ratio(img, height,width,middle):
    h, w = img.shape[:2]
    h=h-h%4
    new_w = int(h / height)*width
    startx = middle - new_w //2
    endx=middle+new_w //2
    if startx<=0:
        cropped_img = img[0:h, 0:new_w]
    elif endx>=w:
        cropped_img = img[0:h, w-new_w:w]
    else:
        cropped_img = img[0:h, startx:endx]
    return cropped_img

################################################### Defining Static Data ###############################################

# UI Fasilkom UNSIKA (Merah Marun)
user_color      = '#8B0000' 
title_webapp    = "Sistem Presensi Praktikum Fasilkom UNSIKA"
subtitle        = "Laboratorium AI & Data Science"

html_temp = f"""
            <div style="background-color:{user_color};padding:15px;border-radius:10px;margin-bottom:20px;box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
            <h1 style="color:white;text-align:center;font-size: 32px;font-family:sans-serif;margin-bottom:0px;">{title_webapp}</h1>
            <p style="color:#f0f0f0;text-align:center;font-size: 18px;margin-top:5px;font-weight:lighter;">{subtitle}</p>
            </div>
            """
st.markdown(html_temp, unsafe_allow_html=True)

###################### Defining Static Paths ###################
if st.sidebar.button('Click to Clear out all the data'):
    shutil.rmtree(VISITOR_DB, ignore_errors=True)
    os.mkdir(VISITOR_DB)
    shutil.rmtree(VISITOR_HISTORY, ignore_errors=True)
    os.mkdir(VISITOR_HISTORY)

if not os.path.exists(VISITOR_DB):
    os.mkdir(VISITOR_DB)

if not os.path.exists(VISITOR_HISTORY):
    os.mkdir(VISITOR_HISTORY)

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
mtcnn = MTCNN(
        image_size=160, margin=0, min_face_size=20,
        thresholds=[0.6, 0.7, 0.7], factor=0.709, post_process=True,
        device=device,keep_all=True
        )
########################################################################################################################

def main():
    st.sidebar.title("🎓 Info Laboratorium")
    st.sidebar.info("Sistem Presensi Cerdas menggunakan integrasi **Face Recognition** dan **Anti-Spoofing** (Liveness Detection).\n\n"
                    "Digunakan untuk keperluan verifikasi kehadiran mahasiswa secara *real-time* di lingkungan kampus.")
    st.sidebar.markdown("---")
    st.sidebar.subheader("👨‍💻 Pengelola Kelas:")
    st.sidebar.write("**Raihan Ahmad K.**")
    st.sidebar.caption("Asisten Laboratorium")
                    
    selected_menu = option_menu(None,
        ['Visitor Validation', 'View Visitor History', 'Add to Database'],
        icons=['camera', "clock-history", 'person-plus'],
        menu_icon="cast", default_index=0, orientation="horizontal")

    if selected_menu == 'Visitor Validation':
        visitor_id = uuid.uuid1()
        img_file_buffer = st.camera_input("Take a picture")

        if img_file_buffer is not None:
            bytes_data = img_file_buffer.getvalue()
            image_array         = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            image_array_copy    = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

            with open(os.path.join(VISITOR_HISTORY, f'{visitor_id}.jpg'), 'wb') as file:
                file.write(img_file_buffer.getbuffer())
                st.success('Image Saved Successfully!')

                max_faces   = 0
                rois        = []
                aligned=[]
                spoofs=[]
                can=[]
                
                # --- FIX BGR to RGB ---
                img_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
                face_locations ,prob = mtcnn(img_rgb, return_prob=True)
                boxes, _ = mtcnn.detect(img_rgb)
                # ----------------------
                
                if boxes is not None:
                    boxes_int = boxes.astype(int)
                else:
                    boxes_int = np.array([])
                    
                if face_locations is not None:
                    for idx, (left,top, right, bottom) in enumerate(boxes_int):
                        img=crop_image_with_ratio(image_array,4,3,(left+right)//2)
                        spoof=test(img,"./resources/anti_spoof_models",device)
                        if spoof<=1:
                            spoofs.append("REAL")
                            can.append(idx)
                        else:
                            spoofs.append("FAKE")
                    print(can)
                    
                if len(boxes_int) > 0:
                    for idx,  (left,top, right, bottom) in enumerate(boxes_int):
                        rois.append(image_array[top:bottom, left:right].copy())
                        cv2.rectangle(image_array, (left, top), (right, bottom), COLOR_DARK, 2)
                        cv2.rectangle(image_array, (left, bottom + 35), (right, bottom), COLOR_DARK, cv2.FILLED)
                        font = cv2.FONT_HERSHEY_DUPLEX
                        cv2.putText(image_array, f"#{idx} {spoofs[idx]}", (left + 5, bottom + 25), font, .55, COLOR_WHITE, 1)

                st.image(BGR_to_RGB(image_array), width=720)
                max_faces = len(boxes_int)

                if max_faces > 0:
                    col1, col2 = st.columns(2)
                    face_idxs = col1.multiselect("Select face#", can, default=can)
                    similarity_threshold = col2.slider('Select Threshold for Similarity', min_value=0.0, max_value=3.0, value=0.5)
                    flag_show = False
                
                    if ((col1.checkbox('Click to proceed!')) & (len(face_idxs)>0)):
                        dataframe_new = pd.DataFrame()
                        for idx,loc in enumerate(face_locations) :
                            torch_loc = torch.stack([loc]).to(device)
                            encodesCurFrame = resnet(torch_loc).detach().cpu()
                            aligned.append(encodesCurFrame)
                            
                        for face_idx in face_idxs:
                            database_data = initialize_data()
                            face_encodings  = database_data[COLS_ENCODE].values
                            dataframe       = database_data[COLS_INFO]

                            if len(aligned) < 1:
                                st.error(f'Please Try Again for face#{face_idx}!')
                            else:
                                face_to_compare = aligned[face_idx].numpy()
                                dataframe['similarity'] = [np.linalg.norm(e1 - face_to_compare) for e1 in face_encodings]
                                dataframe['similarity'] = dataframe['similarity'].astype(float)

                                dataframe_new = dataframe.drop_duplicates(keep='first')
                                dataframe_new.reset_index(drop=True, inplace=True)
                                dataframe_new.sort_values(by="similarity", ascending=True, inplace=True)
                                dataframe_new = dataframe_new[dataframe_new['similarity'] < similarity_threshold].head(1)
                                dataframe_new.reset_index(drop=True, inplace=True)

                                if dataframe_new.shape[0]>0:
                                    (left,top, right, bottom) = (boxes_int[face_idx])
                                    rois.append(image_array_copy[top:bottom, left:right].copy())
                                    cv2.rectangle(image_array_copy, (left, top), (right, bottom), COLOR_DARK, 2)
                                    cv2.rectangle(image_array_copy, (left, bottom + 35), (right, bottom), COLOR_DARK, cv2.FILLED)
                                    font = cv2.FONT_HERSHEY_DUPLEX
                                    cv2.putText(image_array_copy, f"#{dataframe_new.loc[0, 'Name']}", (left + 5, bottom + 25), font, .55, COLOR_WHITE, 1)

                                    name_visitor = dataframe_new.loc[0, 'Name']
                                    attendance(visitor_id, name_visitor)
                                    flag_show = True
                                else:
                                    st.error(f'No Match Found for the given Similarity Threshold! for face#{face_idx}')
                                    st.info('Please Update the database for a new person or click again!')
                                    attendance(visitor_id, 'Unknown')

                        if flag_show == True:
                            st.image(BGR_to_RGB(image_array_copy), width=720)

                else:
                    st.error('No human face detected.')

    if selected_menu == 'View Visitor History':
        view_attendace()

    if selected_menu == 'Add to Database':
        col1, col2, col3 = st.columns(3)
        face_name  = col1.text_input('Name:', '')
        pic_option = col2.radio('Upload Picture', options=["Upload a Picture", "Take a Picture with Cam"])

        if pic_option == 'Upload a Picture':
            img_file_buffer = col3.file_uploader('Upload a Picture', type=allowed_image_type)
            if img_file_buffer is not None:
                file_bytes = np.asarray(bytearray(img_file_buffer.read()), dtype=np.uint8)
        elif pic_option == 'Take a Picture with Cam':
            img_file_buffer = col3.camera_input("Take a Picture with Cam")
            if img_file_buffer is not None:
                file_bytes = np.frombuffer(img_file_buffer.getvalue(), np.uint8)

        if ((img_file_buffer is not None) & (len(face_name) > 1) & st.button('Click to Save!')):
            image_array = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            with open(os.path.join(VISITOR_DB, f'{face_name}.jpg'), 'wb') as file:
                file.write(img_file_buffer.getbuffer())

            # --- FIX BGR to RGB ---
            img_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            face_locations ,prob = mtcnn(img_rgb, return_prob=True)
            # ----------------------
            
            if face_locations is not None:
                torch_loc = torch.stack([face_locations[0]]).to(device)
                encodesCurFrame = resnet(torch_loc).detach().cpu()

                df_new = pd.DataFrame(data=encodesCurFrame, columns=COLS_ENCODE)
                df_new[COLS_INFO] = face_name
                df_new = df_new[COLS_INFO + COLS_ENCODE].copy()

                DB = initialize_data()
                add_data_db(df_new)
            else:
                st.error("No human face detected. Please try capturing again with a clear face.")

#######################################################
if __name__ == "__main__":
    main()
#######################################################