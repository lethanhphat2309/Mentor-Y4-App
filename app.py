import streamlit as st
import google.generativeai as genai
import PyPDF2

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Mentor Y4 của Phát", page_icon="👨‍⚕️", layout="centered")

# CSS để làm giao diện đẹp hơn và hiển thị trắc nghiệm rõ ràng
st.markdown("""
    <style>
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; }
    details { border: 1px solid #4CAF50; border-radius: 5px; padding: 10px; background-color: #1e1e1e; }
    summary { font-weight: bold; cursor: pointer; color: #4CAF50; }
    </style>
""", unsafe_allow_html=True)

st.title("👨‍⚕️ Mentor Y Khoa Cá Nhân")
st.caption("Phiên bản hỗ trợ Gemini 3 Pro & Flash - Thiết kế riêng cho Phát")

# --- 2. THANH CÔNG CỤ (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Hệ Thống")
    api_key = st.text_input("Nhập Google Gemini API Key:", type="password")
    
    # Cập nhật danh sách các mô hình mạnh nhất 2026
    model_choice = st.selectbox(
        "Chọn Bộ Não AI:",
        ["gemini-3-pro-preview", "gemini-3-flash-preview", "gemini-1.5-pro-latest", "gemini-1.5-flash-latest"]
    )
    
    uploaded_file = st.file_uploader("Tải bài giảng PDF/TXT", type=["pdf", "txt"])
    
    st.markdown("---")
    st.info("💡 **Mẹo cho Phát:** Nếu đi trực mệt, hãy bảo Mentor 'tóm tắt cực ngắn'. Nếu muốn học kỹ, hãy bảo 'giải thích cơ chế sâu'.")

# --- 3. KHỞI TẠO LỊCH SỬ CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "model", 
        "parts": ["Chào Phát! Mentor đã sẵn sàng. Hôm nay bạn muốn học bài nào hay cần mình tạo thử thách trắc nghiệm?"]
    })

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message("ai" if msg["role"] == "model" else "user"):
        st.markdown(msg["parts"][0], unsafe_allow_html=True)

# --- 4. XỬ LÝ CHAT VÀ GỌI API ---
user_input = st.chat_input("Nhắn cho Mentor ở đây...")

if user_input:
    # Hiển thị tin nhắn người dùng
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "parts": [user_input]})
    
    # Đọc nội dung file PDF
    pdf_text = ""
    if uploaded_file is not None:
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            pdf_text = "".join([page.extract_text() for page in reader.pages])
            # Giới hạn để không bị quá tải bộ nhớ
            pdf_text = f"\n\n[NỘI DUNG TÀI LIỆU]:\n{pdf_text[:25000]}"
        except:
            st.error("Lỗi đọc file PDF rồi Phát ơi!")

    if api_key:
        genai.configure(api_key=api_key)
        try:
            # Thiết lập mô hình
            model = genai.GenerativeModel(model_choice) 
            
            # CÂU LỆNH HỆ THỐNG (Quyết định cách AI trả lời)
            system_instruction = (
                "Bạn là Mentor Y khoa của Phát, một sinh viên Y4 có lối học chậm nhưng chắc, thích hiểu sâu cơ chế. "
                "Khi tạo câu hỏi trắc nghiệm, bạn phải tuân thủ nghiêm ngặt các quy tắc sau:\n"
                "1. Mỗi đáp án A, B, C, D phải bắt đầu trên một dòng mới.\n"
                "2. Luôn giấu đáp án và lời giải trong thẻ HTML sau:\n"
                "<details><summary>Click để xem đáp án và giải thích chi tiết</summary>\n"
                "<b>Đáp án đúng:</b> [Điền đáp án]<br>\n"
                "<b>Giải thích cơ chế:</b> [Giải thích thật sâu và cặn kẽ vì sao đúng/sai]</details>\n"
                "3. Hãy động viên Phát thường xuyên. Nếu Phát làm đúng, hãy khen ngợi nhiệt tình."
            )
            
            full_prompt = system_instruction + pdf_text + "\n\nYêu cầu của Phát: " + user_input
            
            with st.spinner(f"Mentor ({model_choice}) đang suy luận..."):
                response = model.generate_content(full_prompt)
                
                # Hiển thị câu trả lời của AI
                st.chat_message("ai").markdown(response.text, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "model", "parts": [response.text]})
                
                # Hiệu ứng pháo hoa khi hoàn thành bài tốt
                if any(word in response.text.lower() for word in ["đúng", "chính xác", "giỏi", "chúc mừng"]):
                    st.balloons()
                    
        except Exception as e:
            st.error(f"Lỗi rồi! Có thể API Key sai hoặc mô hình chưa sẵn sàng. Chi tiết: {e}")
    else:
        st.warning("Phát ơi, dán API Key vào thanh bên trái mới dùng được nhé!")
