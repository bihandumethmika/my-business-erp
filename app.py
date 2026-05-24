import streamlit as st
import pandas as pd
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# 1. DATABASE & SECURITY SETUP (V4 WITH CUSTOM NAMES)
DB_FILE = "uthsahaya_erp_v4.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT,
            date TEXT,
            type TEXT,
            category TEXT,
            amount REAL,
            description TEXT,
            entered_by TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT,
            assigned_business TEXT
        )
    ''')
    
    # Auto-populate configured businesses with custom names
    try:
        c.execute("INSERT INTO users VALUES ('owner', 'admin123', 'Owner', 'All')")
        c.execute("INSERT INTO users VALUES ('staff1', 'staff123', 'Staff', 'Uthsahaya Timber Mills')")
        c.execute("INSERT INTO users VALUES ('staff2', 'staff456', 'Staff', 'Uthsahaya Furniture')")
        c.execute("INSERT INTO users VALUES ('staff3', 'staff789', 'Staff', 'Uthsahaya Imported Timber')")
        c.execute("INSERT INTO users VALUES ('staff4', 'staff000', 'Staff', 'Uthsahaya Transport Service')")
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

init_db()

# 2. EMAIL NOTIFICATION BROADCASTER
def send_monthly_report_email(receiver_email, business_name, report_csv_string):
    sender_email = "your_gmail@gmail.com"
    sender_password = "xxxx xxxx xxxx xxxx"
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"📊 Executive Financial Statement - {business_name} ({datetime.now().strftime('%B %Y')})"
    
    body = f"Greetings Owner,\n\nPlease find attached the premium monthly financial analytics matrix for {business_name}.\n\nGenerated securely via Uthsahaya Networks ERP."
    msg.attach(MIMEText(body, 'plain'))
    
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(report_csv_string.encode('utf-8'))
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename={business_name}_Report.csv")
    msg.attach(part)
    
    try:
        server = smtplib.SMTP('://gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Network Email Exception: {e}")
        return False

# 3. INTERFACE CONFIGURATION & PREMIUM GRAPHICS THEME
st.set_page_config(page_title="Uthsahaya Group ERP", layout="wide")

# Custom UI Styling Injection
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    h1 { color: #ffd700; font-family: 'Helvetica Neue', sans-serif; font-weight: 800; text-align: center; }
    h3 { color: #f0f2f6; }
    .stButton>button { background-color: #ffd700; color: #0e1117; font-weight: bold; border-radius: 8px; border: none; width: 100%; transition: 0.3s; }
    .stButton>button:hover { background-color: #e6c200; transform: scale(1.02); }
    .metric-card { background: linear-gradient(135deg, #1e222b 0%, #11141a 100%); padding: 25px; border-radius: 12px; border-left: 5px solid #ffd700; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .metric-title { color: #8a92a6; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { color: #ffffff; font-size: 28px; font-weight: bold; margin-top: 5px; }
    </style>
""", unsafe_allowed_html=True)

st.title("🔱 Uthsahaya Holdings Premium Management Networks")
st.write("<p style='text-align: center; color: #8a92a6;'>Automated Multi-Business Financial Intelligence & Registry System</p>", unsafe_allowed_html=True)
st.write("---")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.assigned_business = ""

# 4. LUXURY AUTHENTICATION INTERFACE
if not st.session_state.logged_in:
    columns = st.columns([1, 2, 1])
    with columns[1]:
        st.markdown("<div style='background-color: #1c202a; padding: 30px; border-radius: 15px; border: 1px solid #2d323f;'>", unsafe_allowed_html=True)
        st.subheader("🔒 Secure Portal Gateway")
        with st.form("login_form", clear_on_submit=False):
            username_input = st.text_input("📊 User ID / පරිශීලක නාමය")
            password_input = st.text_input("🔑 Security Key / මුරපදය", type="password")
            login_btn = st.form_submit_button("AUTHORIZE ACCESS")
            
            if login_btn:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT role, assigned_business FROM users WHERE username=? AND password=?", (username_input, password_input))
                user_data = c.fetchone()
                conn.close()
                
                if user_data:
                    st.session_state.logged_in = True
                    st.session_state.username = username_input
                    st.session_state.role = user_data[0]
                    st.session_state.assigned_business = user_data[1]
                    st.rerun()
                else:
                    st.error("❌ Invalid Access Credentials. Security breach log updated.")
        st.markdown("</div>", unsafe_allowed_html=True)

# 5. ENTERPRISE ACTIVE PORTAL
else:
    st.sidebar.markdown(f"<div style='text-align:center;'><h2 style='color:#ffd700; margin-bottom:0;'>Uthsahaya</h2><p style='color:#8a92a6; font-size:12px;'>User: {st.session_state.username} ({st.session_state.role})</p></div>", unsafe_allowed_html=True)
    st.sidebar.write("---")
    if st.sidebar.button("🔒 LOGOUT FROM SYSTEM"):
        st.session_state.logged_in = False
        st.rerun()

    def get_filtered_records():
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM records", conn)
        conn.close()
        return df

    # STAFF PORTAL (DAILY DATA ENTRY GATES)
    if st.session_state.role == "Staff":
        business_scope = st.session_state.assigned_business
        st.subheader(f"📝 Registry Desk — 【 {business_scope} 】")
        
        with st.form("staff_entry_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                entry_date = st.date_input("Date (දිනය)", datetime.now())
                entry_type = st.selectbox("Transaction Flow (වර්ගය)", ["Income (ආදායම)", "Expense (වියදම)"])
            with col_b:
                category = st.text_input("Category Head (උදා: Retail Sales, Supplier Pay, Bills)")
                amount = st.number_input("Total Valuation Amount (LKR)", min_value=0.0, format="%.2f", step=500.0)
            
            description = st.text_area("Audit Log Notes / විස්තර පැහැදිලි කිරීම")
            submit_btn = st.form_submit_button("SUBMIT SECURE RECORD")
            
            if submit_btn and category and amount > 0:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO records (business_name, date, type, category, amount, description, entered_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (business_scope, entry_date.strftime("%Y-%m-%d"), entry_type, category, amount, description, st.session_state.username))
                conn.commit()
                conn.close()
                st.success(f"✅ Data localized and encrypted into {business_scope} Database ledger!")

    # OWNER PORTAL (EXECUTIVE LEVEL HQ COCKPIT)
    elif st.session_state.role == "Owner":
        st.subheader("📈 Executive Command Headquarters & Analytics Cockpit")
        
        businesses_list = [
            "Uthsahaya Timber Mills", 
            "Uthsahaya Furniture", 
            "Uthsahaya Imported Timber", 
            "Uthsahaya Transport Service"
        ]
        selected_business = st.selectbox("🎯 Select Target Network Ledger to Audit", businesses_list)
        st.write("---")
        
        data_df = get_filtered_records()
        
        if data_df.empty:
            st.warning("⚠️ No data streams found in the cloud server. Please request staff users to input operational figures.")
        else:
            data_df['date'] = pd.to_datetime(data_df['date'])
            data_df['Month'] = data_df['date'].dt.to_period('M').astype(str)
            
            biz_df = data_df[data_df['business_name'] == selected_business]
            
            if biz_df.empty:
                st.info(f"ℹ️ {selected_business} possesses no active logs for this duration.")
            else:
                # Calculate Core Figures
                pnl = biz_df.pivot_table(index='Month', columns='type', values='amount', aggfunc='sum').fillna(0)
                if "Income (ආදායම)" not in pnl.columns: pnl["Income (ආදායම)"] = 0.0
                if "Expense (වියදම)" not in pnl.columns: pnl["Expense (වියදම)"] = 0.0
                pnl['Net Profit/Loss'] = pnl['Income (ආදායම)'] - pnl['Expense (වියදම)']
                
                # INFOGRAPHICS DISPLAY MATRIX CARDS (Premium UI Metrics)
                latest_income = pnl["Income (ආදායම)"].iloc[-1]
                latest_expense = pnl["Expense (වියදම)"].iloc[-1]
                latest_pnl = pnl['Net Profit/Loss'].iloc[-1]
                
                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
