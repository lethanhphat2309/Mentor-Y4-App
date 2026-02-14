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
    
    # Cập nhật mã model chính xác từ hình ảnh Phát gửi
    model_choice = st.selectbox(
        "Chọn Bộ Não AI:",
        ["gemini-3-pro-preview", "gemini-3-flash-preview", "gemini-1.5-pro-latest", "gemini-1.5-flash-latest"]
    )
    
    uploaded_file = st.file_uploader("Tải bài giảng PDF/TXT", type=["pdf", "txt"])
    st.markdown("---")
    st.info("Mẹo: Dùng Gemini 3 Pro Preview để phân tích cơ chế bệnh sinh sâu nhất!")

# --- XỬ LÝ LỊCH SỬ CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "model", 
        "parts": ["Chào Phát! Mentor phiên bản Gemini 3 Pro đã sẵn sàng. Bạn muốn 'mổ xẻ' kiến thức nào hôm nay?"]
    })

# Hiển thị lịch sử chat (SỬA LỖI HIỂN THỊ HTML TẠI ĐÂY)
for msg in st.session_state.messages:
    with st.chat_message("ai" if msg["role"] == "model" else "user"):
        # Dùng st.markdown với unsafe_allow_html để hiện nút Click ẩn hiện
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
            # Giới hạn nội dung để tránh tràn bộ nhớ
            context_prompt = f"\n\n[KIẾN THỨC TỪ PDF]:\n{context[:20000]}"
        except:
            st.error("Lỗi đọc PDF rồi Phát ơi!")

    if api_key:
        genai.configure(api_key=api_key)
        try:
            model = genai.GenerativeModel(model_choice) 
            
            # Cấu hình lệnh hệ thống để AI dùng đúng thẻ HTML ẩn đáp án
            # Tìm và thay thế đoạn system_instruction cũ bằng đoạn này:
system_instruction = (
    "Bạn là Mentor Y khoa. Khi tạo câu hỏi trắc nghiệm, hãy tuân thủ TUYỆT ĐỐI định dạng sau:\n"
    "1. Mỗi đáp án A, B, C, D phải nằm trên MỘT DÒNG RIÊNG BIỆT.\n"
    "2. Sau mỗi câu hỏi, dùng thẻ HTML sau để ẩn đáp án:\n"
    "<details><summary><b>Click để xem đáp án và giải thích cặn kẽ</b></summary>\n"
    "<b>Đáp án đúng:</b> [A/B/C/D]<br>\n"
    "<b>Giải thích sâu:</b> [Phân tích cơ chế bệnh sinh, tại sao chọn câu này, tại sao các câu khác sai]...\n"
    "</details>\n"
    "Hãy trình bày thật sạch sẽ và dễ đọc cho sinh viên Y."
)
            
            full_prompt = system_instruction + context_prompt + "\n\nYêu cầu của Phát: " + user_input
            
            with st.spinner(f"Đang dùng não {model_choice} suy luận..."):
                response = model.generate_content(full_prompt)
                # Hiển thị kết quả dưới dạng Markdown có hỗ trợ HTML
                st.chat_message("ai").markdown(response.text, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "model", "parts": [response.text]})
                
                # Hiệu ứng pháo hoa khi hoàn thành bài
                if "đúng" in response.text.lower() or "chính xác" in response.text.lower():
                    st.balloons()
        except Exception as e:
            st.error(f"Lỗi rồi! Có thể tài khoản chưa được cấp quyền dùng bản Preview. Chi tiết: {e}")
    else:
        st.warning("Dán API Key vào thanh bên trái đã nhé!")
