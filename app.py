import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from streamlit_option_menu import option_menu
import smtplib
from email.mime.text import MIMEText

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]


# Configure Gemini with error handling
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
except Exception as e:
    st.error(f"Failed to initialize Gemini API: {str(e)}")
    model = None

# Gemini wrapper
def ask_gemini(prompt):
    if not model:
        return "❌ Gemini API not available."
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Error with Gemini API: {str(e)}"

# Email sender with subject extraction
def send_email(sender_email, sender_password, recipient_email, email_content):
    try:
        subject = ""
        lines = email_content.splitlines()

        # Extract Subject from first line if present
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

        return True, "Email sent successfully!"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

# Streamlit UI
st.set_page_config(page_title="Outrank Email Agent", layout="wide")
st.title("💼 Outrank Strategy")

# Sidebar navigation & settings
with st.sidebar:
    selected = option_menu(
        menu_title="Navigation",
        options=["Email Agent"],
        icons=["envelope"],
        menu_icon="cast",
        default_index=0,
    )

    st.markdown("### ✉️ Email Settings")
    recipient_email = st.text_input("Recipient Email", "henry@example.com")
    sender_email = st.text_input("Your Email", "your_email@gmail.com")
    sender_password = st.text_input("Your App Password", type="password", help="Use an App Password for Gmail if 2FA is enabled")

    # Credential verification
    st.markdown("### 🔐 Confirm App Password")

    if "credentials_verified" not in st.session_state:
        st.session_state.credentials_verified = False

    if st.button("Confirm App Password", key="confirm_btn"):
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
            st.success("✅ App password is valid and verified.")
            st.session_state.credentials_verified = True
        except smtplib.SMTPAuthenticationError:
            st.session_state.credentials_verified = False
            st.error("❌ Invalid credentials or App Password not enabled. Please check your Gmail settings.")
        except Exception as e:
            st.session_state.credentials_verified = False
            st.error(f"⚠️ Error: {str(e)}")

# App Logic
if selected == "Email Agent":
    st.header("📧 Email Agent")
    st.write("Enter a simple phrase, and I’ll turn it into a professional email!")

    user_prompt = st.chat_input("What do you want to say?", "e.g., email Henry I’m going on vacation")

    if "generated_email" not in st.session_state:
        st.session_state.generated_email = ""

    if st.button("Preview Email", key="preview_btn"):
        if not st.session_state.credentials_verified:
            st.warning("Please confirm your App Password in the sidebar before generating emails.")
            st.stop()

        if user_prompt and recipient_email and sender_email and sender_password:
            with st.spinner("Generating email..."):
                # Extract sender first name
                sender_username = sender_email.split("@")[0]
                sender_first_name = sender_username.split(".")[0].split("0")[0].capitalize()

                # Extract recipient and message
                words = user_prompt.strip().lower().split()
                if words[0] == "email" and len(words) > 2:
                    recipient_name = words[1].capitalize()
                    message_body = " ".join(words[2:])
                else:
                    recipient_name = "There"
                    message_body = user_prompt

                # Gemini prompt
                prompt = f"""
You are a professional email assistant. Based on the user's input, write a complete and polished email including:

- A subject line (only if it's relevant, like job applications, absences, follow-ups, etc.)
- A greeting that starts with: Dear {recipient_name},
- A professional, well-structured body using the following message as context:
"{message_body}"
- A polite closing with:
Sincerely,
{sender_first_name}

The subject line should be short, clear, and relevant. Keep the tone formal and respectful.
Do NOT include email headers like To, From, or Date.
Output only the email's subject (if applicable), greeting, body, and sign-off.
"""
                st.session_state.generated_email = ask_gemini(prompt)

    if st.session_state.generated_email:
        st.subheader("Generated Email (Editable)")
        edited_email = st.text_area("Edit your email below before sending:", value=st.session_state.generated_email, height=250)

        if st.button("Send Email", key="send_btn"):
            if not st.session_state.credentials_verified:
                st.warning("App Password not verified. Please confirm in the sidebar.")
                st.stop()

            if edited_email:
                success, message = send_email(sender_email, sender_password, recipient_email, edited_email)
                if success:
                    st.success(message)
                    st.session_state.generated_email = ""
                else:
                    st.error(message)
            else:
                st.warning("Email content is empty.")
