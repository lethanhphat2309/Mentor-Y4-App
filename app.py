import streamlit as st
import google.generativeai as genai
import PyPDF2

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Mentor Y4 - Bản Fix Lỗi", page_icon="👨‍⚕️", layout="centered")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 10px; margin-bottom: 15px; }
    details { border: 2px solid #4CAF50; border-radius: 8px; padding: 12px; background-color: #1e1e1e; margin-top: 10px; }
    summary { font-weight: bold; cursor: pointer; color: #4CAF50; }
    </style>
""", unsafe_allow_html=True)

st.title("👨‍⚕️ Mentor Y Khoa Cá Nhân")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Hệ Thống")
    api_key = st.text_input("Nhập Google Gemini API Key:", type="password")
    
    # Cập nhật danh sách mô hình (Ưu tiên bản 3 Pro Phát tìm thấy)
    model_choice = st.selectbox(
        "Chọn Bộ Não AI:",
        ["gemini-3-pro-preview", "gemini-3-flash-preview", "gemini-1.5-pro-latest"]
    )
    
    uploaded_file = st.file_uploader("Tải tài liệu PDF học tập", type=["pdf", "txt"])
    st.markdown("---")
    st.info("💡 **Gợi ý:** Nếu AI vẫn chưa xuống dòng, Phát chỉ cần nhắn: 'Hãy liệt kê đáp án theo hàng dọc'.")

# --- LỊCH SỬ CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "model", "parts": ["Chào Phát! Mentor đã fix xong lỗi xuống dòng. Hãy thử tải tài liệu lên nhé!"]})

for msg in st.session_state.messages:
    with st.chat_message("ai" if msg["role"] == "model" else "user"):
        st.markdown(msg["parts"][0], unsafe_allow_html=True)

# --- XỬ LÝ CHAT ---
user_input = st.chat_input("Nhắn cho Mentor...")

if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "parts": [user_input]})
    
    pdf_text = ""
    if uploaded_file is not None:
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            pdf_text = f"\n\n[DỮ LIỆU PDF]:\n" + "".join([page.extract_text() for page in reader.pages])[:25000]
        except:
            st.error("Lỗi đọc PDF rồi!")

    if api_key:
        genai.configure(api_key=api_key)
        try:
            model = genai.GenerativeModel(model_choice) 
            
            # LỆNH HỆ THỐNG CẢI TIẾN: ÉP AI DÙNG DANH SÁCH HÀNG DỌC
            system_instruction = (
                "Bạn là Mentor Y khoa của Phát. Khi tạo câu hỏi trắc nghiệm, bạn PHẢI tuân thủ định dạng này:\n"
                "Câu hỏi: [Nội dung]\n"
                "- A. [Đáp án A]\n"
                "- B. [Đáp án B]\n"
                "- C. [Đáp án C]\n"
                "- D. [Đáp án D]\n\n"
                "(Dấu gạch đầu dòng '-' sẽ giúp mỗi đáp án tự động xuống hàng).\n\n"
                "<details><summary>Click để xem đáp án</summary>...</details>"
            )
            
            full_prompt = system_instruction + pdf_text + "\n\nYêu cầu của Phát: " + user_input
            
            with st.spinner(f"Mentor {model_choice} đang soạn bài..."):
                response = model.generate_content(full_prompt)
                st.chat_message("ai").markdown(response.text, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "model", "parts": [response.text]})
                
                if any(word in response.text.lower() for word in ["đúng", "chính xác", "giỏi"]):
                    st.balloons()
        except Exception as e:
            st.error(f"Lỗi: {e}")
