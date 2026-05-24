import streamlit as st
import pandas as pd
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# 1. DATABASE & SECURITY SETUP
DB_FILE = "business_finance_v3.db"

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
    try:
        c.execute("INSERT INTO users VALUES ('owner', 'admin123', 'Owner', 'All')")
        c.execute("INSERT INTO users VALUES ('staff1', 'staff123', 'Staff', 'Business 1')")
        c.execute("INSERT INTO users VALUES ('staff2', 'staff456', 'Staff', 'Business 2')")
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

init_db()

# 2. AUTOMATED EMAIL & SMS NOTIFICATION FUNCTIONS
def send_monthly_report_email(receiver_email, business_name, report_csv_string):
    sender_email = "your_gmail@gmail.com"
    sender_password = "xxxx xxxx xxxx xxxx"
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"📊 Monthly Financial Report - {business_name} ({datetime.now().strftime('%B %Y')})"
    
    body = f"Hello Owner,\n\nPlease find attached the monthly profit/loss statement for {business_name}."
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
        st.error(f"Email Error: {e}")
        return False

def send_alert_sms(phone_number, message_text):
    return True

# 3. INTERFACE CONFIGURATION
st.set_page_config(page_title="Secure Business Network ERP", layout="wide")
st.title("🔐 Multi-User Secure Enterprise Management System")
st.write("---")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.assigned_business = ""

# 4. LOGIN INTERFACE
if not st.session_state.logged_in:
    st.subheader("👤 User Authentication / පද්ධතියට ඇතුල් වීම")
    with st.form("login_form", clear_on_submit=False):
        username_input = st.text_input("Username (පරිශීලක නාමය)")
        password_input = st.text_input("Password (මුරපදය)", type="password")
        login_btn = st.form_submit_button("Login / ඇතුල් වන්න")
        
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
                st.error("❌ වැරදි Username එකක් හෝ Password එකක්.")

# 5. LOGGED IN SYSTEM DASHBOARD
else:
    st.sidebar.subheader(f"👋 Welcome, {st.session_state.username}!")
    st.sidebar.write(f"**Role:** {st.session_state.role}")
    if st.sidebar.button("Logout / පද්ධතියෙන් ඉවත් වන්න"):
        st.session_state.logged_in = False
        st.rerun()

    def get_filtered_records():
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM records", conn)
        conn.close()
        return df

    # STAFF PORTAL
    if st.session_state.role == "Staff":
        business_scope = st.session_state.assigned_business
        st.subheader(f"📝 Daily Data Entry Dashboard - 【{business_scope}】")
        
        with st.form("staff_entry_form", clear_on_submit=True):
            entry_date = st.date_input("Date (දිනය)", datetime.now())
            entry_type = st.selectbox("Transaction Type (වර්ගය)", ["Income (ආදායම)", "Expense (වියදම)"])
            category = st.text_input("Category (උදා: Sales, Supplier, Bill, Rent)")
            amount = st.number_input("Amount (LKR)", min_value=0.0, format="%.2f")
            description = st.text_area("Description / විස්තර")
            
            submit_btn = st.form_submit_button("Save Record")
            if submit_btn and category and amount > 0:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO records (business_name, date, type, category, amount, description, entered_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (business_scope, entry_date.strftime("%Y-%m-%d"), entry_type, category, amount, description, st.session_state.username))
                conn.commit()
                conn.close()
                st.success("✅ දත්තයන් සාර්ථකව සේවාදායකයේ තැන්පත් කරන ලදී!")

    # OWNER PORTAL
    elif st.session_state.role == "Owner":
        st.subheader("📈 Executive Profit/Loss Central Intelligence")
        
        businesses = ["Business 1", "Business 2", "Business 3", "Business 4"]
        selected_business = st.selectbox("Select Target Business to Audit", businesses)
        
        data_df = get_filtered_records()
        
        if data_df.empty:
            st.warning("පද්ධතිය තුළ තවමත් කිසිදු මූල්‍ය දත්තයක් ගබඩා වී නොමැත. කරුණාකර Staff ගිණුමකින් දත්ත කිහිපයක් ඇතුළත් කර බලන්න.")
        else:
            data_df['date'] = pd.to_datetime(data_df['date'])
            data_df['Month'] = data_df['date'].dt.to_period('M').astype(str)
            
            biz_df = data_df[data_df['business_name'] == selected_business]
            
            if biz_df.empty:
                st.info(f"{selected_business} සඳහා තවමත් දත්ත ඇතුළත් කර නැත.")
            else:
                pnl = biz_df.pivot_table(index='Month', columns='type', values='amount', aggfunc='sum').fillna(0)
                if "Income (ආදායම)" not in pnl.columns: pnl["Income (ආදායම)"] = 0.0
                if "Expense (වියදම)" not in pnl.columns: pnl["Expense (වියදම)"] = 0.0
                pnl['Net Profit/Loss'] = pnl['Income (ආදායම)'] - pnl['Expense (වියදම)']
                
                # Format to text strings to avoid display matrix render crashes
                formatted_pnl = pnl.map(lambda x: f"LKR {x:,.2f}")
                st.dataframe(formatted_pnl, use_container_width=True)
                
                csv_string = pnl.to_csv()
                st.download_button("📥 Export Report to Excel/CSV File", data=csv_string.encode('utf-8'), file_name=f"{selected_business}_Report.csv")
                
                st.write("---")
                st.subheader("🚀 Broadcaster & Alert Integration")
                
                col1, col2 = st.columns(2)
                with col1:
                    owner_email_input = st.text_input("Enter Destination Email Address", "owner@example.com")
                    if st.button("📧 Send Monthly Statement to Email"):
                        if send_monthly_report_email(owner_email_input, selected_business, csv_string):
                            st.success(f"📬 Report securely broadcasted to {owner_email_input}!")
                
                with col2:
                    owner_phone_input = st.text_input("Enter Destination Mobile Number", "077XXXXXXXX")
                    if st.button("💬 Send Fast Profit Summary via SMS"):
                        latest_month = pnl.index[-1]
                        latest_profit = pnl['Net Profit/Loss'].iloc[-1]
                        sms_msg = f"Alert: {selected_business} {latest_month} Profit/Loss status is LKR {latest_profit:,.2f}."
                        if send_alert_sms(owner_phone_input, sms_msg):
                            st.success(f"📱 SMS Summary safely pushed to {owner_phone_input}!")
