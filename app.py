import streamlit as st
import google.generativeai as genai
import PyPDF2
import json
import re
import random
import gspread # MỚI: Ống hút dữ liệu
from google.oauth2.service_account import Credentials # MỚI: Chìa khóa vào kho

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Mentor Y4 - Cloud Sync", page_icon="👨‍⚕️", layout="centered")

st.markdown("""
    <style>
    .stRadio > label { font-weight: bold; color: #4CAF50; font-size: 16px;}
    .stButton>button { border-radius: 8px; border: 1px solid #4CAF50; width: 100%; margin-bottom: 10px;}
    </style>
""", unsafe_allow_html=True)

st.title("👨‍⚕️ Mentor Y Khoa Cá Nhân")
st.caption("☁️ Đã kích hoạt công nghệ Đồng Bộ Đám Mây (Google Sheets)")

# --- 2. KẾT NỐI GOOGLE SHEETS BÍ MẬT ---
@st.cache_resource
def init_gsheets():
    try:
        # Mở két sắt Streamlit lấy chìa khóa
        creds_json = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open("Mentor_Y4_Database") # Mở file Excel của Phát
    except Exception as e:
        st.error("Chưa kết nối được Cloud. Phát kiểm tra lại Bước 1 (Secrets) nhé!")
        return None

sheet_db = init_gsheets()

# --- 3. BỘ NHỚ HỆ THỐNG & TỰ ĐỘNG TẢI DỮ LIỆU ---
if "data_loaded" not in st.session_state:
    st.session_state.messages = [{"role": "model", "parts": ["Chào Phát! Dữ liệu của bạn đã được bảo vệ trên Cloud!"]}]
    st.session_state.quiz_data = []
    st.session_state.wrong_notebook = []
    st.session_state.current_page = "💬 Chat Mentor"
    st.session_state.data_loaded = True # Đánh dấu đã tải
    
    # Hút dữ liệu từ ô A1 của Google Sheets về App
    if sheet_db:
        try:
            quiz_val = sheet_db.worksheet("QuizBank").acell('A1').value
            if quiz_val: st.session_state.quiz_data = json.loads(quiz_val)
            
            wrong_val = sheet_db.worksheet("WrongNotebook").acell('A1').value
            if wrong_val: st.session_state.wrong_notebook = json.loads(wrong_val)
        except:
            pass # Lần đầu tiên file Excel rỗng thì bỏ qua

# Hàm Tự Động Bơm Dữ Liệu Lên Cloud
def sync_to_cloud():
    if sheet_db:
        try:
            # Gói toàn bộ câu hỏi thành 1 cục JSON và nhét thẳng vào ô A1
            q_str = json.dumps(st.session_state.quiz_data, ensure_ascii=False)
            w_str = json.dumps(st.session_state.wrong_notebook, ensure_ascii=False)
            sheet_db.worksheet("QuizBank").update_acell('A1', q_str)
            sheet_db.worksheet("WrongNotebook").update_acell('A1', w_str)
        except Exception as e:
            pass

# --- 4. THANH ĐIỀU HƯỚNG BÊN TRÁI ---
with st.sidebar:
    st.header("⚙️ Hệ Thống")
    api_key = st.text_input("Nhập Google Gemini API Key:", type="password")
    model_choice = st.selectbox("Chọn Bộ Não AI:", ["gemini-3-pro-preview", "gemini-3-flash-preview", "gemini-1.5-pro-latest"])
    
    st.markdown("---")
    menu_options = ["💬 Chat Mentor", "📝 Phòng Thi Ảo", "📓 Sổ Tay Câu Sai"]
    selected_page = st.radio("📌 Điều Hướng Ứng Dụng", menu_options, index=menu_options.index(st.session_state.current_page))
    
    if selected_page != st.session_state.current_page:
        st.session_state.current_page = selected_page
        st.rerun()
    
    uploaded_file = st.file_uploader("Tải tài liệu PDF", type=["pdf", "txt"])
    
    st.markdown("---")
    st.caption("Quản lý Cloud:")
    if st.button("🔄 Ép Đồng Bộ Lên Cloud Ngay"):
        sync_to_cloud()
        st.success("Đã lưu an toàn lên Google Sheets!")
        
    if st.button("🗑️ Xóa sạch Sổ Tay (Cả trên Cloud)"):
        st.session_state.wrong_notebook = []
        sync_to_cloud()
        st.rerun()

pdf_text = ""
if uploaded_file is not None:
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        pdf_text = f"\n\n[DỮ LIỆU PDF]:\n" + "".join([page.extract_text() for page in reader.pages])[:20000]
    except:
        pass

# ==========================================
# CHẾ ĐỘ 1: CHAT MENTOR
# ==========================================
if st.session_state.current_page == "💬 Chat Mentor":
    for msg in st.session_state.messages:
        with st.chat_message("ai" if msg["role"] == "model" else "user"):
            st.markdown(msg["parts"][0], unsafe_allow_html=True)

    user_input = st.chat_input("Nhắn Mentor (VD: Tạo 5 câu trắc nghiệm)")

    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state.messages.append({"role": "user", "parts": [user_input]})
        
        if api_key:
            genai.configure(api_key=api_key)
            if any(kw in user_input.lower() for kw in ["trắc nghiệm", "câu hỏi", "test", "đề thi"]):
                model = genai.GenerativeModel(model_name=model_choice, generation_config={"response_mime_type": "application/json"})
                schema_instruction = (
                    "Bạn là Mentor Y Khoa. Trả về MẢNG JSON chứa trắc nghiệm:\n"
                    "[\n"
                    "  {\n"
                    "    \"question\": \"Câu hỏi...\",\n"
                    "    \"options\": [\"A. ...\", \"B. ...\", \"C. ...\", \"D. ...\"],\n"
                    "    \"answer\": \"A. ...\",\n"
                    "    \"explanation\": \"Giải thích...\"\n"
                    "  }\n"
                    "]\n"
                    "TUYỆT ĐỐI KHÔNG để dấu phẩy (,) ở cuối phần tử cuối cùng."
                )
                full_prompt = schema_instruction + pdf_text + "\n\nYêu cầu tạo test: " + user_input
                with st.spinner("Đang soạn đề thi và lưu lên Cloud..."):
                    try:
                        response = model.generate_content(full_prompt)
                        clean_json = re.sub(r',\s*]', ']', response.text)
                        clean_json = re.sub(r',\s*}', '}', clean_json)
                        new_questions = json.loads(clean_json)
                        
                        st.session_state.quiz_data.extend(new_questions)
                        sync_to_cloud() # <--- TỰ ĐỘNG ĐỒNG BỘ LÊN CLOUD NGAY LẬP TỨC
                        
                        st.session_state.messages.append({"role": "model", "parts": [f"Đã nạp thêm {len(new_questions)} câu hỏi vào Ngân Hàng Đề và lưu lên Cloud!"]})
                        st.session_state.current_page = "📝 Phòng Thi Ảo"
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Lỗi tạo đề thi JSON: {e}")
            else:
                model = genai.GenerativeModel(model_choice)
                full_prompt = "Bạn là Mentor Y Khoa." + pdf_text + "\n\n" + user_input
                with st.spinner("Mentor đang nghĩ..."):
                    response = model.generate_content(full_prompt)
                    st.chat_message("ai").markdown(response.text)
                    st.session_state.messages.append({"role": "model", "parts": [response.text]})
        else:
            st.warning("Nhớ nhập API Key nhé Phát!")

# ==========================================
# CHẾ ĐỘ 2: PHÒNG THI ẢO 
# ==========================================
elif st.session_state.current_page == "📝 Phòng Thi Ảo":
    st.subheader(f"📝 Ngân Hàng Đề Thi Cloud ({len(st.session_state.quiz_data)} câu)")
    if len(st.session_state.quiz_data) == 0:
        st.info("Chưa có câu hỏi. Hãy về tab Chat Mentor yêu cầu tạo trắc nghiệm.")
    else:
        if st.button("🎲 Xáo Trộn Đề (Ôn Tập Ngẫu Nhiên)"):
            random.shuffle(st.session_state.quiz_data)
            st.rerun()
        st.markdown("---")
        for idx, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**Câu {idx+1}: {q['question']}**")
            choice = st.radio("Chọn đáp án:", q['options'], key=f"radio_{idx}", index=None)
            if st.button(f"Nộp đáp án Câu {idx+1}", key=f"btn_{idx}"):
                if choice is None:
                    st.warning("Chưa chọn đáp án kìa!")
                elif choice == q['answer']:
                    st.success(f"🎉 ĐÚNG RỒI! \n\n**Giải thích sâu:** {q['explanation']}")
                    st.balloons()
                else:
                    st.error(f"❌ SAI RỒI! \n\n**Đáp án đúng:** {q['answer']} \n\n**Giải thích sâu:** {q['explanation']}")
                    # Tự động gắp vào sổ tay và lưu ngay lên Cloud
                    if not any(item['question'] == q['question'] for item in st.session_state.wrong_notebook):
                        st.session_state.wrong_notebook.append(q)
                        sync_to_cloud() # <--- TỰ ĐỘNG LƯU CÂU SAI LÊN CLOUD
            st.markdown("---")

# ==========================================
# CHẾ ĐỘ 3: SỔ TAY CÂU SAI
# ==========================================
elif st.session_state.current_page == "📓 Sổ Tay Câu Sai":
    st.subheader("📓 Góc Ôn Tập Của Phát")
    if len(st.session_state.wrong_notebook) == 0:
        st.success("Tuyệt vời! Bạn chưa làm sai câu nào.")
    else:
        st.warning(f"Có {len(st.session_state.wrong_notebook)} câu cần ôn lại:")
        for idx, wq in enumerate(st.session_state.wrong_notebook):
            with st.expander(f"⚠️ {wq['question']}"):
                st.error(f"**Đáp án đúng:** {wq['answer']}")
                st.info(f"**Cơ chế bệnh sinh:** {wq['explanation']}")
