import streamlit as st
import google.generativeai as genai
import PyPDF2
import json
import re
import random # MỚI: Thư viện để xáo trộn câu hỏi ôn tập

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
    st.session_state.quiz_data = [] # Lưu trữ NGÂN HÀNG ĐỀ CỘNG DỒN
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
    
    st.markdown("---")
    st.caption("Quản lý dữ liệu:")
    # Nút dọn dẹp phòng thi nếu đề quá nhiều
    if st.button("🗑️ Xóa sạch Phòng Thi"):
        st.session_state.quiz_data = []
        st.rerun()
    if st.button("🗑️ Xóa Sổ Tay Câu Sai"):
        st.session_state.wrong_notebook = []
        st.rerun()

pdf_text = ""
if uploaded_file is not None:
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        pdf_text = f"\n\n[DỮ LIỆU PDF MỚI NHẤT]:\n" + "".join([page.extract_text() for page in reader.pages])[:20000]
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
                model = genai.GenerativeModel(
                    model_name=model_choice,
                    generation_config={"response_mime_type": "application/json"}
                )
                
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
                    "CẢNH BÁO: TUYỆT ĐỐI KHÔNG để dấu phẩy (,) ở cuối phần tử cuối cùng của mảng."
                )
                full_prompt = schema_instruction + pdf_text + "\n\nYêu cầu tạo test: " + user_input
                
                with st.spinner("Đang soạn thêm đề thi và gộp vào Phòng Thi Ảo..."):
                    try:
                        response = model.generate_content(full_prompt)
                        
                        raw_json = response.text
                        clean_json = re.sub(r',\s*]', ']', raw_json)
                        clean_json = re.sub(r',\s*}', '}', clean_json)
                        
                        new_questions = json.loads(clean_json)
                        
                        # CÔNG NGHỆ MỚI: CỘNG DỒN CÂU HỎI VÀO NGÂN HÀNG ĐỀ (Không ghi đè nữa)
                        st.session_state.quiz_data.extend(new_questions)
                        
                        st.session_state.messages.append({"role": "model", "parts": [f"Đã nạp thêm {len(new_questions)} câu hỏi mới vào Ngân Hàng Đề Thi!"]})
                        st.session_state.current_page = "📝 Phòng Thi Ảo"
                        st.rerun() 
                        
                    except Exception as e:
                        st.error(f"Lỗi tạo đề thi. Phát thử nhắn lại nhé! Lỗi chi tiết: {e}")
            
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
# CHẾ ĐỘ 2: PHÒNG THI ẢO (NGÂN HÀNG ĐỀ)
# ==========================================
elif st.session_state.current_page == "📝 Phòng Thi Ảo":
    st.subheader(f"📝 Ngân Hàng Đề Thi Tổng Hợp ({len(st.session_state.quiz_data)} câu)")
    
    if len(st.session_state.quiz_data) == 0:
        st.info("Chưa có câu hỏi. Phát hãy tải bài giảng lên và yêu cầu tạo trắc nghiệm nhé.")
    else:
        # Nút xáo trộn câu hỏi để chống học vẹt
        if st.button("🎲 Xáo Trộn Đề (Ôn Tập Ngẫu Nhiên)"):
            random.shuffle(st.session_state.quiz_data)
            st.rerun()
            
        st.markdown("---")
            
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
elif st.session_state.current_page == "📓 Sổ Tay Câu Sai":
    st.subheader("📓 Góc Ôn Tập Của Phát")
    if len(st.session_state.wrong_notebook) == 0:
        st.success("Tuyệt vời! Bạn chưa làm sai câu nào (hoặc chưa làm bài test).")
    else:
        st.warning(f"Phát đang có {len(st.session_state.wrong_notebook)} câu cần ôn lại:")
        for idx, wq in enumerate(st.session_state.wrong_notebook):
            with st.expander(f"⚠️ {wq['question']}"):
                st.error(f"**Đáp án đúng:** {wq['answer']}")
                st.info(f"**Cơ chế bệnh sinh:** {wq['explanation']}")
