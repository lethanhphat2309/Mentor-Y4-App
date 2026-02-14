import streamlit as st
import google.generativeai as genai
import PyPDF2

# --- CÀI ĐẶT GIAO DIỆN ---
st.set_page_config(page_title="Mentor Y4 - Bản Cao Cấp", page_icon="👨‍⚕️", layout="centered")
st.title("👨‍⚕️ Mentor Y Khoa Cá Nhân (V3.0)")

# --- THANH CÔNG CỤ BÊN TRÁI ---
with st.sidebar:
    st.header("⚙️ Hệ Thống")
    api_key = st.text_input("Nhập Google Gemini API Key:", type="password")
    
    # Cập nhật các mô hình mới nhất 2026
    model_choice = st.selectbox(
        "Chọn Bộ Não AI:",
        ["gemini-3-pro-latest", "gemini-3-flash-latest", "gemini-1.5-pro-latest", "gemini-1.5-flash-latest"]
    )
    
    uploaded_file = st.file_uploader("Tải bài giảng PDF/TXT", type=["pdf", "txt"])
    st.markdown("---")
    st.info("Mẹo: Dùng Gemini 3 Pro để phân tích ca lâm sàng khó!")

# --- XỬ LÝ LỊCH SỬ CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "model", 
        "parts": ["Chào Phát! Mentor phiên bản Gemini 3 Pro đã sẵn sàng. Bạn muốn 'mổ xẻ' kiến thức nào hôm nay?"]
    })

# Hiển thị lịch sử chat (Sửa lỗi hiển thị HTML)
for msg in st.session_state.messages:
    with st.chat_message("ai" if msg["role"] == "model" else "user"):
        st.markdown(msg["parts"][0], unsafe_allow_html=True)

# --- XỬ LÝ CHAT VÀ GỌI AI ---
user_input = st.chat_input("Nhắn cho Mentor...")

if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "parts": [user_input]})
    
    context_prompt = ""
    if uploaded_file is not None:
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            context = "".join([page.extract_text() for page in reader.pages])
            context_prompt = f"\n\n[KIẾN THỨC TỪ PDF]:\n{context[:20000]}"
        except:
            st.error("Lỗi đọc PDF rồi Phát ơi!")

    if api_key:
        genai.configure(api_key=api_key)
        try:
            model = genai.GenerativeModel(model_choice) 
            # Dạy AI cách ẩn đáp án bằng HTML
            instruction = "Bạn là Mentor Y khoa. Khi tạo trắc nghiệm, LUÔN dùng thẻ <details><summary>Click xem đáp án</summary>...</details> để giấu đáp án. "
            full_prompt = instruction + context_prompt + "\n\nYêu cầu: " + user_input
            
            with st.spinner(f"Đang dùng não {model_choice} suy luận..."):
                response = model.generate_content(full_prompt)
                # Dùng .markdown với unsafe_allow_html=True để hiện nút bấm ẩn hiện
                st.chat_message("ai").markdown(response.text, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "model", "parts": [response.text]})
                
                if "chúc mừng" in response.text.lower() or "đúng" in response.text.lower():
                    st.balloons()
        except Exception as e:
            st.error(f"Lỗi rồi! Có thể mô hình này cần trả phí hoặc sai tên. Chi tiết: {e}")
    else:
        st.warning("Dán API Key vào đã nhé!")
