import streamlit as st
import pandas as pd
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# 1. DATABASE SETUP
DB_FILE = "uthsahaya_erp_v13.db"

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
            role TEXT
        )
    ''')
    try:
        c.execute("INSERT INTO users VALUES ('owner', 'admin123', 'Owner')")
        c.execute("INSERT INTO users VALUES ('staff1', 'staff123', 'Staff')")
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

init_db()

# 2. FIXED EMAIL SENDER (WITH ERROR HANDLING)
def send_monthly_report_email(receiver_email, business_name, report_csv_string, sender_email, sender_password):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"📊 Financial Statement - {business_name} ({datetime.now().strftime('%B %Y')})"
    
    body = f"Greetings Owner,\n\nPlease find attached the monthly financial analytics report for {business_name}.\n\nGenerated via Uthsahaya Premium ERP."
    msg.attach(MIMEText(body, 'plain'))
    
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(report_csv_string.encode('utf-8'))
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename={business_name}_Report.csv")
    msg.attach(part)
    
    try:
        server = smtplib.SMTP_SSL('://gmail.com', 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True, "Success"
    except Exception as e:
        return False, str(e)

# 3. PAGE INITIALIZATION
st.set_page_config(page_title="Uthsahaya Group ERP", layout="wide")

st.title("🔱 Uthsahaya Holdings Management System")
st.write("Automated Multi-Business Financial Intelligence & Registry System")
st.write("---")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

businesses_list = [
    "Uthsahaya Timber Mills", 
    "Uthsahaya Furniture", 
    "Uthsahaya Imported Timber", 
    "Uthsahaya Transport Service"
]

# 4. LOGIN PORTAL
if not st.session_state.logged_in:
    st.subheader("🔒 Secure Portal Gateway / ඇතුල් වීම")
    with st.form("login_form", clear_on_submit=False):
        username_input = st.text_input("📊 User ID / පරිශීලක නාමය")
        password_input = st.text_input("🔑 Security Key / මුරපදය", type="password")
        login_btn = st.form_submit_button("LOGIN")
        
        if login_btn:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT role FROM users WHERE username=? AND password=?", (username_input, password_input))
            user_data = c.fetchone()
            conn.close()
            
            if user_data:
                st.session_state.logged_in = True
                st.session_state.username = username_input
                st.session_state.role = user_data
                st.rerun()
            else:
                st.error("❌ Invalid Access Credentials.")

# 5. LOGGED IN DASHBOARD
else:
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.write(f"**Role:** {st.session_state.role}")
    if st.sidebar.button("🔒 LOGOUT"):
        st.session_state.logged_in = False
        st.rerun()

    def get_filtered_records():
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM records", conn)
        conn.close()
        return df

    # STAFF PORTAL (ANY USER CAN SELECT ANY BUSINESS TO ADD DATA)
    if st.session_state.role == "Staff":
        st.subheader("📝 Daily Data Entry Desk (දිනපතා ආදායම්/වියදම් ඇතුළත් කිරීම)")
        target_business = st.selectbox("🎯 ව්‍යාපාරය තෝරන්න (Select Business to Add Data)", businesses_list)
        
        with st.form("staff_entry_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                entry_date = st.date_input("Date (දිනය)", datetime.now())
                entry_type = st.selectbox("Transaction Flow (වර්ගය)", ["Income (ආදායම)", "Expense (වියදම)"])
            with col_b:
                category = st.text_input("Category Head (උදා: Sales, Bill, Salary)")
                amount = st.number_input("Amount (LKR)", min_value=0.0, format="%.2f")
            
            description = st.text_area("Notes / විස්තර")
            submit_btn = st.form_submit_button(f"SAVE RECORD TO {target_business.upper()}")
            
            if submit_btn and category and amount > 0:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO records (business_name, date, type, category, amount, description, entered_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (target_business, entry_date.strftime("%Y-%m-%d"), entry_type, category, amount, description, st.session_state.username))
                conn.commit()
                conn.close()
                st.success(f"✅ Data successfully saved under 【{target_business}】 ledger!")

    # OWNER PORTAL (EXECUTIVE HEADQUARTERS)
    elif st.session_state.role == "Owner":
        tabs = st.tabs(["📊 Financial Analytics HQ", "📝 Master Data Entry Gates", "⚙️ Staff User Settings"])
        
        # TAB 1: FINANCIAL REPORTS FOR OWNER
        with tabs:
            st.subheader("📈 Executive Command Headquarters & Analytics")
            selected_business = st.selectbox("🎯 View Audits For", businesses_list)
            st.write("---")
            
            data_df = get_filtered_records()
            biz_df = data_df[data_df['business_name'] == selected_business] if not data_df.empty else pd.DataFrame()
            
            if biz_df.empty:
                st.warning(f"⚠️ {selected_business} සඳහා තවමත් කිසිදු මූල්‍ය දත්තයක් ඇතුළත් කර නැත. කරුණාකර 'Master Data Entry Gates' ටැබ් එකෙන් හෝ Staff කෙනෙකු ලෙස ලොග් වී දත්ත ඇතුළත් කරන්න.")
            else:
                data_df['date'] = pd.to_datetime(data_df['date'])
                data_df['Month'] = data_df['date'].dt.to_period('M').astype(str)
                biz_df = data_df[data_df['business_name'] == selected_business]
                
                pnl = biz_df.pivot_table(index='Month', columns='type', values='amount', aggfunc='sum').fillna(0)
                if "Income (ආදායම)" not in pnl.columns: pnl["Income (ආදායම)"] = 0.0
                if "Expense (වියදම)" not in pnl.columns: pnl["Expense (වියදම)"] = 0.0
                pnl['Net Profit/Loss'] = pnl['Income (ආදායම)'] - pnl['Expense (වියදම)']
                
                latest_month = pnl.index[-1]
                m_col1, m_col2, m_col3 = st.columns(3)
                m_col1.metric(f"📈 Total Revenue ({latest_month})", f"LKR {pnl['Income (ආදායම)'].iloc[-1]:,.2f}")
                m_col2.metric("📉 Total Expense", f"LKR {pnl['Expense (වියදම)'].iloc[-1]:,.2f}")
                m_col3.metric("🔱 Net Profit / Loss", f"LKR {pnl['Net Profit/Loss'].iloc[-1]:,.2f}")
                
                st.write("---")
                st.write("#### 📊 Financial Trend Projections Graph")
                st.bar_chart(pnl[['Income (ආදායම)', 'Expense (වියදම)', 'Net Profit/Loss']])
                
                st.write("#### 📑 Ledger Overview Matrix Table")
                formatted_pnl = pnl.map(lambda x: f"LKR {x:,.2f}")
                st.dataframe(formatted_pnl, use_container_width=True)
                
                csv_string = pnl.to_csv()
                st.download_button("📥 DOWNLOAD AUDITED STATEMENT (.CSV)", data=csv_string.encode('utf-8'), file_name=f"{selected_business}_Report.csv")
                
                st.write("---")
                st.subheader("🚀 Central Automated Notification Gateway")
                
                st.info("💡 Email යැවීමට ප්‍රථමයෙන් ඔබගේ Sender Gmail ලිපිනය සහ App Password එක පහතින් ඇතුළත් කරන්න.")
                col_em1, col_em2 = st.columns(2)
                with col_em1:
                    sys_email = st.text_input("Your Gmail Address (Sender)", "example@gmail.com")
                with col_em2:
                    sys_password = st.text_input("Your Gmail App Password", type="password")
                
                col1, col2 = st.columns(2)
                with col1:
                    owner_email_input = st.text_input("Enter Destination Email Address", "owner@example.com")
                    if st.button("📧 BROADCAST STATEMENT VIA EMAIL"):
                        if sys_email == "example@gmail.com" or sys_password == "":
                            st.error("⚠️ කරුණාකර ඔබගේ නිවැරදි Sender Email සහ App Password එක ඇතුළත් කරන්න.")
                        else:
                            success, msg = send_monthly_report_email(owner_email_input, selected_business, csv_string, sys_email, sys_password)
                            if success:
                                st.success(f"📬 Report safely dispatched to {owner_email_input}!")
                            else:
                                st.error(f"❌ Email Connection Error: {msg}. Please verify your Gmail App Password.")
                with col2:
                    owner_phone_input = st.text_input("Enter Mobile Target Line", "077XXXXXXXX")

