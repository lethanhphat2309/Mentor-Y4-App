import streamlit as st
import google.generativeai as genai
import PyPDF2
import json

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Mentor Y4 - Bản Tương Tác", page_icon="👨‍⚕️", layout="centered")

st.markdown("""
    <style>
    .stRadio > label { font-weight: bold; color: #4CAF50; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #1e1e1e; border: 1px solid #4CAF50;}
    </style>
""", unsafe_allow_html=True)

st.title("👨‍⚕️ Mentor Y Khoa Cá Nhân")

# --- LƯU TRỮ DỮ LIỆU TẠM THỜI ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "parts": ["Chào Phát! Hệ thống Trắc nghiệm tương tác đã sẵn sàng."]}]
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = [] # Lưu câu hỏi hiện tại
if "wrong_notebook" not in st.session_state:
    st.session_state.wrong_notebook = [] # Lưu các câu làm sai

# --- THANH CÔNG CỤ SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Hệ Thống")
    api_key = st.text_input("Nhập Google Gemini API Key:", type="password")
    model_choice = st.selectbox("Chọn Bộ Não AI:", ["gemini-3-pro-preview", "gemini-3-flash-preview", "gemini-1.5-pro-latest"])
    uploaded_file = st.file_uploader("Tải tài liệu PDF", type=["pdf", "txt"])
    
    # Nút xóa sổ tay
    if st.button("🗑️ Xóa Sổ Tay Câu Sai"):
        st.session_state.wrong_notebook = []
        st.success("Đã xóa sổ tay!")

# --- CHIA APP THÀNH 3 TAB ---
tab_chat, tab_quiz, tab_notebook = st.tabs(["💬 Chat Mentor", "📝 Phòng Thi Ảo", "📓 Sổ Tay Câu Sai"])

pdf_text = ""
if uploaded_file is not None:
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        pdf_text = f"\n\n[DỮ LIỆU PDF]:\n" + "".join([page.extract_text() for page in reader.pages])[:20000]
    except:
        st.error("Lỗi đọc PDF!")

# ==========================================
# TAB 1: KHUNG CHAT BÌNH THƯỜNG
# ==========================================
with tab_chat:
    for msg in st.session_state.messages:
        with st.chat_message("ai" if msg["role"] == "model" else "user"):
            st.markdown(msg["parts"][0], unsafe_allow_html=True)

    user_input = st.chat_input("Nhắn Mentor (Bắt đầu bằng chữ 'Tạo trắc nghiệm' để vào Phòng Thi)")

    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state.messages.append({"role": "user", "parts": [user_input]})
        
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_choice)
            
            # Nếu Phát muốn tạo trắc nghiệm, ép AI trả về dữ liệu máy tính (JSON)
            if "tạo trắc nghiệm" in user_input.lower():
                system_instruction = (
                    "Bạn là Mentor Y Khoa. Người dùng yêu cầu tạo trắc nghiệm. BẮT BUỘC trả về kết quả bằng định dạng JSON chuẩn xác 100%, không kèm chữ nào khác ngoài JSON. Cấu trúc JSON:\n"
                    "[\n"
                    "  {\n"
                    "    \"question\": \"Câu 1: Nội dung...\",\n"
                    "    \"options\": [\"A. ...\", \"B. ...\", \"C. ...\", \"D. ...\"],\n"
                    "    \"answer\": \"A. ...\",\n"
                    "    \"explanation\": \"Giải thích vì sao...\"\n"
                    "  }\n"
                    "]"
                )
                full_prompt = system_instruction + pdf_text + "\n\nYêu cầu: " + user_input
                
                with st.spinner("Đang biên soạn đề thi..."):
                    response = model.generate_content(full_prompt)
                    try:
                        # Gỡ bỏ các ký tự thừa để lấy chuẩn JSON
                        clean_json = response.text.replace("```json", "").replace("```", "").strip()
                        st.session_state.quiz_data = json.loads(clean_json)
                        
                        msg_success = "✅ Đã tạo đề thi xong! Phát hãy chuyển sang Tab **'📝 Phòng Thi Ảo'** ở trên cùng để làm bài nhé!"
                        st.chat_message("ai").markdown(msg_success)
                        st.session_state.messages.append({"role": "model", "parts": [msg_success]})
                    except Exception as e:
                        st.error("Lỗi trích xuất đề thi. Hãy thử yêu cầu lại!")
            else:
                # Chat bình thường không phải trắc nghiệm
                full_prompt = "Bạn là Mentor Y Khoa. Trả lời chi tiết, động viên sinh viên Y4." + pdf_text + "\n\n" + user_input
                with st.spinner("Mentor đang nghĩ..."):
                    response = model.generate_content(full_prompt)
                    st.chat_message("ai").markdown(response.text)
                    st.session_state.messages.append({"role": "model", "parts": [response.text]})

# ==========================================
# TAB 2: PHÒNG THI ẢO (BẤM CHỌN ĐÁP ÁN)
# ==========================================
with tab_quiz:
    st.subheader("📝 Bài Kiểm Tra")
    if len(st.session_state.quiz_data) == 0:
        st.info("Chưa có câu hỏi nào. Hãy sang Tab Chat và yêu cầu: 'Tạo trắc nghiệm bài này'.")
    else:
        # Hiển thị từng câu hỏi thành các khối có thể tương tác
        for idx, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**{q['question']}**")
            # Tạo nút tick tròn (Radio)
            choice = st.radio("Chọn đáp án của bạn:", q['options'], key=f"radio_{idx}", index=None)
            
            # Nút nộp bài cho từng câu
            if st.button("Kiểm tra câu này", key=f"btn_{idx}"):
                if choice is None:
                    st.warning("Bạn chưa chọn đáp án kìa!")
                elif choice == q['answer']:
                    st.success(f"🎉 CHÍNH XÁC! \n\n**Giải thích:** {q['explanation']}")
                    st.balloons()
                else:
                    st.error(f"❌ SAI RỒI! \n\n**Đáp án đúng là:** {q['answer']} \n\n**Giải thích:** {q['explanation']}")
                    
                    # Tự động gắp bỏ vào Sổ Tay nếu làm sai
                    if q not in st.session_state.wrong_notebook:
                        st.session_state.wrong_notebook.append(q)
            st.markdown("---")

# ==========================================
# TAB 3: SỔ TAY CÂU SAI
# ==========================================
with tab_notebook:
    st.subheader("📓 Góc Ôn Tập Của Phát")
    if len(st.session_state.wrong_notebook) == 0:
        st.success("Tuyệt vời! Bạn chưa làm sai câu nào (hoặc chưa làm bài test).")
    else:
        st.warning(f"Bạn có {len(st.session_state.wrong_notebook)} câu cần ôn lại:")
        for idx, wq in enumerate(st.session_state.wrong_notebook):
            with st.expander(f"⚠️ {wq['question']}"):
                st.error(f"**Đáp án đúng:** {wq['answer']}")
                st.info(f"**Cơ chế / Giải thích:** {wq['explanation']}")
