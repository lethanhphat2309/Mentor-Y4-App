import streamlit as st
import google.generativeai as genai
import PyPDF2

# --- CÀI ĐẶT GIAO DIỆN ---
st.set_page_config(page_title="Trợ Lý Y4", page_icon="👨‍⚕️", layout="centered")
st.title("👨‍⚕️ Mentor Y Khoa Cá Nhân")

# --- THANH CÔNG CỤ BÊN TRÁI (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Cài đặt & Dữ liệu")
    api_key = st.text_input("Nhập Google Gemini API Key:", type="password")
    uploaded_file = st.file_uploader("Tải bài giảng (PDF/TXT)", type=["pdf", "txt"])
    st.markdown("---")
    st.caption("Ứng dụng độc quyền thiết kế riêng để trị bệnh lười!")

# --- XỬ LÝ LƯU TRỮ LỊCH SỬ CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Lời chào đầu tiên của Mentor
    st.session_state.messages.append({
        "role": "model", 
        "parts": ["Chào Phát! Mình là Mentor Y Khoa của bạn. Bạn muốn tóm tắt tài liệu, làm trắc nghiệm hay tâm sự chuyện đi lâm sàng mệt mỏi hôm nay?"]
    })

for msg in st.session_state.messages:
    with st.chat_message("ai" if msg["role"] == "model" else "user"):
        st.write(msg["parts"][0])

# --- XỬ LÝ KHUNG CHAT VÀ GỌI AI ---
user_input = st.chat_input("Nhắn cho Mentor (VD: Tạo 5 câu trắc nghiệm khó bài vừa tải lên...)")

if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "parts": [user_input]})
    
    # Đọc file PDF (nếu Phát có tải lên)
    context_prompt = ""
    if uploaded_file is not None:
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            context = ""
            for page in reader.pages:
                context += page.extract_text() + "\n"
            context_prompt = f"\n\n[DỮ LIỆU BÀI GIẢNG HIỆN TẠI]:\n{context[:15000]}"
        except Exception as e:
            st.error("Lỗi đọc file PDF. Hãy thử file khác nhé!")

    # Kết nối bộ não Gemini
    if api_key:
        genai.configure(api_key=api_key)
        try:
            model = genai.GenerativeModel('gemini-1.5-pro') 
            system_prompt = "Bạn là Mentor Y Khoa của Phát, sinh viên Y4. Hãy linh hoạt, tóm tắt dễ hiểu, chia nhỏ kiến thức, hỏi đáp giấu kết quả, và luôn động viên Phát. "
            full_prompt = system_prompt + context_prompt + "\n\nYêu cầu của Phát: " + user_input
            
            with st.spinner("Mentor đang suy nghĩ..."):
                response = model.generate_content(full_prompt)
                st.chat_message("ai").write(response.text)
                st.session_state.messages.append({"role": "model", "parts": [response.text]})
                
                # Gamification: Thưởng pháo hoa nếu Phát làm đúng
                if "chúc mừng" in response.text.lower() or "đúng" in response.text.lower():
                    st.balloons()
                    st.success("Tích lũy kinh nghiệm thành công! Cứ thế phát huy nhé!")
        except Exception as e:
            st.error(f"Lỗi API Key hoặc mạng. Vui lòng kiểm tra lại! Chi tiết: {e}")
    else:
        st.warning("Bạn quên nhập API Key ở góc trái kìa!")
