import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_extras.colored_header import colored_header

# ---- Google Sheets Authentication ----
SERVICE_ACCOUNT_FILE = st.secrets["service_account"]
SHEET_ID = st.secrets["SHEET_ID"]
DOCTOR_CODES = st.secrets["DOCTOR_CODES"]

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(SERVICE_ACCOUNT_FILE, scope)
client = gspread.authorize(creds)

# ---- UI Styling ----
st.set_page_config(page_title="تصنيف الأسئلة الطبية", layout="wide")
st.markdown("<style> body { direction: rtl; text-align: right; font-family: 'Arial'; } </style>", unsafe_allow_html=True)

# ---- Display First Aid Definitions ----
def display_definitions():
    st.sidebar.markdown("""
    ## 🩹 تعريف الإسعافات الأولية
    الإسعافات الأولية هي الرعاية الطبية الفورية التي تُقدَّم لشخص مصاب أو مريض بشكل مفاجئ قبل وصول المساعدة الطبية المتخصصة 🚑. تهدف إلى:
    - ✔️ إنقاذ الحياة 🏥
    - ✔️ منع تفاقم الحالة الصحية ⚠️
    - ✔️ تشجيع التعافي 🌱
    
    **❗ سؤال الإسعافات الأولية العاجل**
    🔴 يتعلق بحالة مهددة للحياة أو تتطلب تدخلاً فورياً ⏳ لإنقاذ شخص ما.
    
    **⚠️ سؤال الإسعافات الأولية غير العاجل**
    🟢 يتعلق بحالة غير مهددة للحياة ويمكن التعامل معها بالرعاية الأساسية حتى تتوفر المساعدة الطبية.
    """, unsafe_allow_html=True)

def authenticate_doctor():
    st.title("🔑 تسجيل الدخول")
    st.write(""" السلام عليكم! هذا المشروع هو جزء من أطروحة بحثية لبناء نظام ذكاء اصطناعي (روبوت دردشة) للإسعافات الأولية باللغة العربية. 
    بالإشارة إلى تعريف الإسعافات الأولية  المعروض في الهامش  الأيمن من الصفحة، يرجى تصنيف كل سؤال من الأسئلة الطبية التي ستعرض عليكم إلى سؤال "عاجل" أو سؤال "غير عاجل". 
    ستساهم مشاركتكم في تحسين دقة روبوت الدردشة الطبي. شكرًا لمساهمتكم!
   """)
    
    doctor_code = st.text_input("الرجاء إدخال رمز الطبيب", type="password")
    if st.button("تسجيل الدخول"):
        if doctor_code in DOCTOR_CODES:
            st.session_state.doctor_sheet = DOCTOR_CODES[doctor_code]
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("رمز غير صحيح، يرجى المحاولة مرة أخرى")

# ---- Initialize Session State ----
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "index" not in st.session_state:
    st.session_state.index = 0
    st.session_state.annotations = []

# ---- Authenticate Doctor ----
if not st.session_state.authenticated:
    display_definitions()
    authenticate_doctor()
else:
    sheet_name = st.session_state.doctor_sheet
    sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
    df = pd.read_excel("Altibbi_20_questions2.xlsx")
    
    # Layout
    col1, col2, col3 = st.columns([1.5, 2, 1.5])
    with col1:
        display_definitions()
    with col2:
        st.title("تصنيف الأسئلة الطبية")
        
        if st.session_state.index < len(df):
            question = df.iloc[st.session_state.index]["Question"]
            
            
            st.markdown(f"**📝 السؤال {st.session_state.index + 1}:** {question}")
           
            
            previous_choice = None
            if st.session_state.index < len(st.session_state.annotations):
                previous_choice = st.session_state.annotations[st.session_state.index][2]
            
            urgency = st.radio(هل هذا السؤال ؟", ["عاجل", "غير عاجل", "لا أعلم" ]",
                              index=([ "عاجل", "غير عاجل", "لا أعلم"].index(previous_choice) if previous_choice else 0))
            
            col_prev, col_next = st.columns([1, 1])
            with col_prev:
                if st.button("➡️السؤال السابق", disabled=(st.session_state.index == 0)):
                    st.session_state.index -= 1
                    st.rerun()
            with col_next:
                if st.button("⬅️إرسال والانتقال للسؤال التالي"):
                    if st.session_state.index < len(st.session_state.annotations):
                        st.session_state.annotations[st.session_state.index] = [question, answer, urgency]
                    else:
                        st.session_state.annotations.append([question, answer, urgency])
                    
                    st.session_state.index += 1
                    st.rerun()
        else:
            st.write("✅ جميع الأسئلة قد تم تصنيفها!")
            annotated_df = pd.DataFrame(st.session_state.annotations, columns=["question", "Urgency"])
            
            try:
                sheet.append_rows(annotated_df.values.tolist())
                st.success("✅جزاكم الله خيرا على مساهمتكم!")
            except Exception as e:
                st.error(f"❌ خطأ أثناء حفظ البيانات: {e}")
            
            if st.button("البدء من جديد"):
                st.session_state.index = 0
                st.session_state.annotations = []
                st.rerun()
