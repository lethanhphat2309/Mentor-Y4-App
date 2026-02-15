import streamlit as st
import google.generativeai as genai
import PyPDF2
import json
import re # <-- MỚI: Thêm thư viện dọn dẹp chuỗi siêu mạnh

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Mentor Y4 - Tương Tác", page_icon="👨‍⚕️", layout="centered")

st.markdown("""
    <style>
    .stRadio > label { font-weight: bold; color: #4CAF50; font-size: 16px;}
    .stButton>button { border-radius: 8px; border: 1px solid #4CAF50; width: 100%;}
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
if "nav_menu" not in st.session_state:
    st.session_state.nav_menu = "💬 Chat Mentor" 

# --- 3. THANH ĐIỀU HƯỚNG BÊN TRÁI ---
with st.sidebar:
    st.header("⚙️ Hệ Thống")
    api_key = st.text_input("Nhập Google Gemini API Key:", type="password")
    model_choice = st.selectbox("Chọn Bộ Não AI:", ["gemini-3-pro-preview", "gemini-3-flash-preview", "gemini-1.5-pro-latest"])
    
    st.markdown("---")
    st.radio("📌 Điều Hướng Ứng Dụng", 
             ["💬 Chat Mentor", "📝 Phòng Thi Ảo", "📓 Sổ Tay Câu Sai"], 
             key="nav_menu")
    
    uploaded_file = st.file_uploader("Tải tài liệu PDF", type=["pdf", "txt"])
    if st.button("🗑️ Xóa Sổ Tay Câu Sai"):
        st.session_state.wrong_notebook = []
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
if st.session_state.nav_menu == "💬 Chat Mentor":
    for msg in st.session_state.messages:
        with st.chat_message("ai" if msg["role"] == "model" else "user"):
            st.markdown(msg["parts"][0], unsafe_allow_html=True)

    user_input = st.chat_input("Nhắn Mentor (VD: Tạo 5 câu trắc nghiệm bài này)")

    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state.messages.append({"role": "user", "parts": [user_input]})
        
        if api_key:
            genai.configure(api_key=api_key)
            
            if any(kw in user_input.lower() for kw in ["trắc nghiệm", "câu hỏi", "test", "đề thi"]):
                model = genai.GenerativeModel(
                    model_name=model_choice,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                # Lệnh hệ thống nghiêm ngặt hơn
                schema_instruction = (
                    "Bạn là Mentor Y Khoa. Trả về một MẢNG JSON chứa các câu hỏi trắc nghiệm. Định dạng BẮT BUỘC:\n"
                    "[\n"
                    "  {\n"
                    "    \"question\": \"Nội dung câu hỏi...\",\n"
                    "    \"options\": [\"A. ...\", \"B. ...\", \"C. ...\", \"D. ...\"],\n"
                    "    \"answer\": \"A. ...\",\n"
                    "    \"explanation\": \"Giải thích cơ chế y khoa thật chi tiết...\"\n"
                    "  }\n"
                    "]\n"
                    "CẢNH BÁO: TUYỆT ĐỐI KHÔNG để dấu phẩy (,) ở cuối phần tử cuối cùng của mảng. Trả về chuẩn JSON 100%."
                )
                full_prompt = schema_instruction + pdf_text + "\n\nYêu cầu tạo test: " + user_input
                
                with st.spinner("Đang lên đề thi và chuẩn bị chuyển bạn vào Phòng Thi Ảo..."):
                    try:
                        response = model.generate_content(full_prompt)
                        
                        # CÔNG NGHỆ CHỐNG LỖI TẠI ĐÂY
                        raw_json = response.text
                        clean_json = re.sub(r',\s*]', ']', raw_json) # Xóa dấu phẩy thừa trước ngoặc vuông
                        clean_json = re.sub(r',\s*}', '}', clean_json) # Xóa dấu phẩy thừa trước ngoặc nhọn
                        
                        st.session_state.quiz_data = json.loads(clean_json)
                        st.session_state.messages.append({"role": "model", "parts": ["Đã chuẩn bị xong đề thi!"]})
                        st.session_state.nav_menu = "📝 Phòng Thi Ảo"
                        st.rerun() 
                        
                    except Exception as e:
                        st.error(f"Lỗi hệ thống. Phát thử gửi lại yêu cầu nhé! Lỗi chi tiết: {e}")
            
            else:
                model = genai.GenerativeModel(model_choice)
                full_prompt = "Bạn là Mentor Y Khoa. Trình bày rõ ràng." + pdf_text + "\n\n" + user_input
                with st.spinner("Mentor đang suy nghĩ..."):
                    response = model.generate_content(full_prompt)
                    st.chat_message("ai").markdown(response.text)
                    st.session_state.messages.append({"role": "model", "parts": [response.text]})
        else:
            st.warning("Nhớ nhập API Key nhé Phát!")

# ==========================================
# CHẾ ĐỘ 2: PHÒNG THI ẢO 
# ==========================================
elif st.session_state.nav_menu == "📝 Phòng Thi Ảo":
    st.subheader("📝 Bài Kiểm Tra Tương Tác")
    if len(st.session_state.quiz_data) == 0:
        st.info("Chưa có câu hỏi. Phát hãy quay lại 'Chat Mentor' và gõ 'Tạo trắc nghiệm' nhé.")
    else:
        for idx, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**Câu {idx+1}: {q['question']}**")
            choice = st.radio("Chọn đáp án:", q['options'], key=f"radio_{idx}", index=None)
            
            if st.button(f"Nộp đáp án Câu {idx+1}", key=f"btn_{idx}"):
                if choice is None:
                    st.warning("Phát chưa chọn đáp án kìa!")
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
elif st.session_state.nav_menu == "📓 Sổ Tay Câu Sai":
    st.subheader("📓 Góc Ôn Tập Của Phát")
    if len(st.session_state.wrong_notebook) == 0:
        st.success("Tuyệt vời! Bạn chưa làm sai câu nào (hoặc chưa làm bài test).")
    else:
        st.warning(f"Phát đang có {len(st.session_state.wrong_notebook)} câu cần ôn lại:")
        for idx, wq in enumerate(st.session_state.wrong_notebook):
            with st.expander(f"⚠️ {wq['question']}"):
                st.error(f"**Đáp án đúng:** {wq['answer']}")
                st.info(f"**Cơ chế bệnh sinh:** {wq['explanation']}")
