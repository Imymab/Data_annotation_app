import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
    """, unsafe_allow_html=True)

# ---- Authentication ----
def authenticate_doctor():
    st.title("🔑 تسجيل الدخول")
    st.write("""
السلام عليكم! هذا المشروع هو جزء من أطروحة بحثية تهدف إلى بناء نظام ذكاء اصطناعي (روبوت دردشة) للإسعافات الأولية باللغة العربية.  
بالإشارة إلى تعريف الإسعافات الأولية المعروض في الهامش الأيمن من الصفحة، يرجى تصنيف كل سؤال من الأسئلة الطبية التي ستُعرض عليكم إلى:  
✔ **سؤال إسعافات أولية**  
✔ **ليس سؤال إسعافات أولية**  
✔ **لا أعلم**  
ستساهم مشاركتكم في تحسين دقة روبوت الدردشة الطبي. شكرًا لمساهمتكم!
""")

    doctor_code = st.text_input("الرجاء إدخال رمز الطبيب", type="password")
    if st.button("تسجيل الدخول"):
        if doctor_code in DOCTOR_CODES:
            st.session_state.doctor_sheet = DOCTOR_CODES[doctor_code]
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ رمز غير صحيح، يرجى المحاولة مرة أخرى")

# ---- Initialize Session State ----
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "index" not in st.session_state:
    st.session_state.index = 0
if "annotations" not in st.session_state:
    st.session_state.annotations = []

# ---- Authenticate Doctor ----
if not st.session_state.authenticated:
    display_definitions()
    authenticate_doctor()
else:
    sheet_name = st.session_state.doctor_sheet
    sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
    df = pd.read_excel("Altibbi_msa_20.xlsx")

    # Define urgency options with numerical mapping
    urgency_mapping = {
        "سؤال إسعافات أولية": 1,
        "ليس سؤال إسعافات أولية": 0,
        "لا أعلم": -1
    }
    urgency_options = list(urgency_mapping.keys())

    # Load existing annotations
   
    existing_data = sheet.get_all_values()
    header_offset = 0 
    annotations_data = existing_data[header_offset:]
    if not st.session_state.annotations:
       st.session_state.annotations = existing_data[header_offset:]
    # Load index from D1 if available
       saved_index = int(sheet.acell("D1").value)
       st.session_state.index = saved_index


    # Custom right-to-left progress bar (thinner)
    progress = st.session_state.index / len(df)
    percentage = int(progress * 100)
    st.markdown(f"""
    <div style="direction: rtl; text-align: right">
        <p>تم تصنيف {st.session_state.index} من أصل {len(df)} سؤال</p>
        <div style="width: 100%; background-color: #f0f0f0; border-radius: 10px; height: 10px;">
            <div style="width: {percentage}%; background-color: #4CAF50; height: 100%; border-radius: 10px 0 0 10px; float: right;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Layout
    col1, col2, col3 = st.columns([1.5, 2, 1.5])
    with col1:
        display_definitions()
    with col2:
        st.title("تصنيف الأسئلة الطبية")

        if st.session_state.index < len(df):
            question = df.iloc[st.session_state.index]["Msa_questions"]
            st.markdown(f"**📝 السؤال {st.session_state.index + 1}:** {question}")

            previous_choice = None
            if st.session_state.index < len(st.session_state.annotations):
                try:
                    val = st.session_state.annotations[st.session_state.index][1]
                    for label, num in urgency_mapping.items():
                        if str(val) == str(num):
                            previous_choice = label
                            break
                except IndexError:
                    previous_choice = None

            urgency = st.radio("هل هذا السؤال؟", urgency_options,
                               index=(urgency_options.index(previous_choice) if previous_choice in urgency_options else 0))
            urgency_value = urgency_mapping[urgency]
            row = [question, urgency_value]

            # Save/Update Google Sheet
            
            # Update local session
            if st.session_state.index < len(st.session_state.annotations):
                st.session_state.annotations[st.session_state.index] = row
            else:
                st.session_state.annotations.append(row)

            row_number = st.session_state.index + 2
            if st.session_state.index < len(existing_data) - header_offset:
                sheet.update(f"A{row_number}:B{row_number}", [row])
            else:
                sheet.append_row(row)
            # Navigation
            col_prev, col_next = st.columns([1, 1])
            with col_prev:
                if st.button("➡️ السؤال السابق", disabled=(st.session_state.index == 0)):
                    st.session_state.index -= 1
                    st.rerun()
            with col_next:
                if st.button("⬅️ إرسال والانتقال للسؤال التالي"):
                    row_number = st.session_state.index + 1
                    if st.session_state.index < len(st.session_state.annotations):
                       st.session_state.annotations[st.session_state.index] = row
                    else:
                       st.session_state.annotations.append(row)
                    
                    if st.session_state.index < len(annotations_data):
                        sheet.update(f"A{row_number}:B{row_number}", [row])
                    else:
                        sheet.append_row(row)
                        
                    st.session_state.index += 1

                    # Save current index to D1 (resume functionality)
                    sheet.update_acell("D1", str(st.session_state.index))

                    st.rerun()

        else:
            st.success("✅ جميع الأسئلة قد تم تصنيفها! جزاكم الله خيرا")
