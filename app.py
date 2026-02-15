import streamlit as st
import google.generativeai as genai
import PyPDF2
import json
import re
import random

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Mentor Y4 - Tương Tác", page_icon="👨‍⚕️", layout="centered")

st.markdown("""
    <style>
    .stRadio > label { font-weight: bold; color: #4CAF50; font-size: 16px;}
    .stButton>button { border-radius: 8px; border: 1px solid #4CAF50; width: 100%; margin-bottom: 10px;}
    </style>
""", unsafe_allow_html=True)

st.title("👨‍⚕️ Mentor Y Khoa Cá Nhân")

# --- 2. BỘ NHỚ HỆ THỐNG ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "parts": ["Chào Phát! Muốn làm test, cứ nhắn có chữ 'trắc nghiệm' hoặc 'câu hỏi' nhé!"]}]
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = [] 
if "wrong_notebook" not in st.session_state:
    st.session_state.wrong_notebook = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "💬 Chat Mentor"

# --- 3. THANH ĐIỀU HƯỚNG BÊN TRÁI ---
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
    
    # ==========================================
    # MỚI: TÍNH NĂNG SAO LƯU VÀ KHÔI PHỤC
    # ==========================================
    st.markdown("---")
    st.header("💾 Đồng bộ & Sao lưu")
    
    # 1. Nút Tải xuống (Save Game)
    backup_data = {
        "messages": st.session_state.messages,
        "quiz_data": st.session_state.quiz_data,
        "wrong_notebook": st.session_state.wrong_notebook
    }
    json_backup = json.dumps(backup_data, ensure_ascii=False)
    
    st.download_button(
        label="⬇️ Lưu Hồ Sơ (Tải Backup)",
        data=json_backup,
        file_name="Ho_So_Y4_Phat.json",
        mime="application/json",
        help="Tải toàn bộ lịch sử chat và câu hỏi về máy để lần sau dùng tiếp."
    )
    
    # 2. Nút Tải lên (Load Game)
    restore_file = st.file_uploader("⬆️ Khôi phục Hồ sơ (File JSON)", type=["json"], help="Tải file 'Ho_So_Y4_Phat.json' lên đây để khôi phục.")
    if restore_file is not None:
        if st.button("🔄 Bấm để Khôi Phục Ngay"):
            try:
                loaded_data = json.load(restore_file)
                st.session_state.messages = loaded_data.get("messages", [{"role": "model", "parts": ["Đã khôi phục thành công!"]}])
                st.session_state.quiz_data = loaded_data.get("quiz_data", [])
                st.session_state.wrong_notebook = loaded_data.get("wrong_notebook", [])
                st.success("Khôi phục dữ liệu thành công! Hãy chọn lại Tab để xem.")
                st.rerun()
            except Exception as e:
                st.error("File không hợp lệ hoặc bị lỗi!")

# ==========================================
# CHẾ ĐỘ 1: CHAT MENTOR
# ==========================================
pdf_text = ""
if uploaded_file is not None:
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        pdf_text = f"\n\n[DỮ LIỆU PDF]:\n" + "".join([page.extract_text() for page in reader.pages])[:20000]
    except:
        pass

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
                with st.spinner("Đang soạn đề thi..."):
                    try:
                        response = model.generate_content(full_prompt)
                        clean_json = re.sub(r',\s*]', ']', response.text)
                        clean_json = re.sub(r',\s*}', '}', clean_json)
                        new_questions = json.loads(clean_json)
                        st.session_state.quiz_data.extend(new_questions)
                        st.session_state.messages.append({"role": "model", "parts": [f"Đã nạp thêm {len(new_questions)} câu hỏi vào Ngân Hàng Đề!"]})
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
    st.subheader(f"📝 Ngân Hàng Đề Thi ({len(st.session_state.quiz_data)} câu)")
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
                    if not any(item['question'] == q['question'] for item in st.session_state.wrong_notebook):
                        st.session_state.wrong_notebook.append(q)
            st.markdown("---")

# ==========================================
# CHẾ ĐỘ 3: SỔ TAY CÂU SAI
# ==========================================
elif st.session_state.current_page == "📓 Sổ Tay Câu Sai":
    st.subheader("📓 Góc Ôn Tập Của Phát")
    if len(st.session_state.wrong_notebook) == 0:
        st.success("Chưa có câu sai nào!")
    else:
        st.warning(f"Có {len(st.session_state.wrong_notebook)} câu cần ôn lại:")
        for idx, wq in enumerate(st.session_state.wrong_notebook):
            with st.expander(f"⚠️ {wq['question']}"):
                st.error(f"**Đáp án đúng:** {wq['answer']}")
                st.info(f"**Cơ chế bệnh sinh:** {wq['explanation']}")
