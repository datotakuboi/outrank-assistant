import streamlit as st
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText

# Load Gemini API Key from Streamlit Secrets
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# Page Setup
st.set_page_config(page_title="Outrank Email Agent 🤖", layout="wide")
st.title("📨 Outrank Email Assistant")

# Styling for chat bubbles
st.markdown("""
<style>
.chat-bubble {
    padding: 12px;
    border-radius: 15px;
    margin-bottom: 8px;
    max-width: 70%;
    word-wrap: break-word;
    font-size: 16px;
}
.user-bubble {
    background-color: #0078FF;
    color: white;
    text-align: right;
    margin-left: auto;
}
.bot-bubble {
    background-color: #F0F0F0;
    color: black;
    text-align: left;
    margin-right: auto;
}
.chat-container {
    display: flex;
    flex-direction: column;
    margin: auto;
    max-width: 700px;
}
</style>
""", unsafe_allow_html=True)

# Session state
if "email_history" not in st.session_state:
    st.session_state.email_history = []

# Sidebar Settings
with st.sidebar:
    st.markdown("### ✉️ Email Settings")
    recipient_email = st.text_input("Recipient Email", "henry@example.com")
    sender_email = st.text_input("Your Email", "your_email@gmail.com")
    sender_password = st.text_input("App Password", type="password")
    send_flag = st.checkbox("Ready to send emails")

# Email function

def send_email(sender_email, sender_password, recipient_email, email_content):
    try:
        subject = ""
        lines = email_content.splitlines()
        if lines and lines[0].lower().startswith("subject:"):
            subject = lines[0][8:].strip()
            email_body = "\n".join(lines[1:]).strip()
        else:
            email_body = email_content.strip()

        msg = MIMEText(email_body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = recipient_email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return True, "✅ Email sent successfully!"
    except Exception as e:
        return False, f"❌ Failed to send email: {str(e)}"

# Display history
for msg in st.session_state.email_history:
    with st.container():
        st.markdown(f"""
        <div class="chat-container">
            <div class="chat-bubble {'user-bubble' if msg['role']=='user' else 'bot-bubble'}">
                {msg['content']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# Input
user_input = st.chat_input("Type a quick instruction like: email Henry I want to apply...")

if user_input:
    st.session_state.email_history.append({"role": "user", "content": user_input})

    sender_first_name = sender_email.split("@")[0].split(".")[0].capitalize()

    words = user_input.strip().lower().split()
    if words[0] == "email" and len(words) > 2:
        recipient_name = words[1].capitalize()
        message_body = " ".join(words[2:])
    else:
        recipient_name = "There"
        message_body = user_input

    prompt = f"""
You are an email assistant. Convert this message into a professional email with:
- A subject line
- A greeting (Dear {recipient_name},)
- A professional body using: \"{message_body}\"
- A polite closing:
Sincerely,
{sender_first_name}

Return only the email content, starting with 'Subject:' if applicable.
"""

    response = model.generate_content(prompt)
    email_text = response.text.strip()

    st.session_state.email_history.append({"role": "bot", "content": email_text})

    if send_flag:
        success, message = send_email(sender_email, sender_password, recipient_email, email_text)
        st.toast(message)
        st.session_state.email_history.append({"role": "bot", "content": message})
