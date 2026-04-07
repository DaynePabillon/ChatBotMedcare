"""
app.py
Clinic Appointment Setter – Streamlit Chatbot Application
MedCare Bot
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import re
import database_manager as db

# Initialize the database schema on startup
db.init_db()

# Load environment variables from .env file
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Fallback to Streamlit Secrets for cloud deployment
if not GROQ_API_KEY and hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
from clinic_data import (
    CLINIC_NAME,
    CLINIC_TAGLINE,
    CLINIC_LOCATION,
    CLINIC_CONTACT,
    CLINIC_HOURS,
    DOCTORS,
    SERVICES,
    PAYMENT_METHODS,
    ACCEPTED_INSURANCE,
    SYSTEM_PROMPT,
)

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────

st.set_page_config(
    page_title=f"{CLINIC_NAME} – Appointment Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────

st.markdown(
    """
<style>
/* ── Import Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

/* ── Hide default Streamlit branding ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
/* header { visibility: hidden; } */ /* Removed to keep sidebar toggle visible */

/* ── Main gradient header ── */
.main-header {
    background: linear-gradient(135deg, #0fa68e 0%, #0d8f7a 40%, #0b7868 70%, #064e44 100%);
    padding: 2rem 2.5rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(15, 166, 142, 0.25);
    position: relative;
    overflow: hidden;
}
.main-header ::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.main-header h1 {
    color: #ffffff;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0 0 0.3rem 0;
    letter-spacing: -0.5px;
}
.main-header p {
    color: rgba(255,255,255,0.85);
    font-size: 0.95rem;
    margin: 0;
    font-weight: 300;
}

/* ── Sidebar styling ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #0e1117 100%);
}
[data-testid="stSidebar"] .stMarkdown h1 {
    color: #0fa68e;
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: -0.3px;
}
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #0fa68e;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
}

/* ── Sidebar info cards ── */
.info-card {
    background: rgba(15, 166, 142, 0.08);
    border: 1px solid rgba(15, 166, 142, 0.15);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.6rem;
    transition: all 0.2s ease;
}
.info-card:hover {
    background: rgba(15, 166, 142, 0.14);
    border-color: rgba(15, 166, 142, 0.3);
}
.info-card-label {
    font-size: 0.7rem;
    color: #0fa68e;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
    margin-bottom: 0.15rem;
}
.info-card-value {
    font-size: 0.85rem;
    color: #e0e6ed;
    font-weight: 400;
    line-height: 1.4;
}

/* ── Quick action buttons ── */
.quick-action-btn {
    display: inline-block;
    background: linear-gradient(135deg, #0fa68e, #0d8f7a);
    color: #fff !important;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 500;
    text-decoration: none;
    text-align: center;
    width: 100%;
    margin-bottom: 0.4rem;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(15, 166, 142, 0.2);
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: rgba(26, 31, 46, 0.6);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    backdrop-filter: blur(10px);
}

/* ── Status badges ── */
.status-badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.status-online {
    background: rgba(15, 166, 142, 0.15);
    color: #0fa68e;
    border: 1px solid rgba(15, 166, 142, 0.3);
}

/* ── Service tag pills ── */
.service-tag {
    display: inline-block;
    background: rgba(15, 166, 142, 0.1);
    color: #0fa68e;
    padding: 0.25rem 0.65rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 500;
    margin: 0.15rem 0.15rem;
    border: 1px solid rgba(15, 166, 142, 0.2);
}

/* ── Divider ── */
.sidebar-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.06);
    margin: 1rem 0;
}

/* ── Chat input styling ── */
[data-testid="stChatInput"] textarea {
    border-radius: 12px !important;
    border: 1px solid rgba(15, 166, 142, 0.3) !important;
    background: rgba(26, 31, 46, 0.8) !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #0fa68e !important;
    box-shadow: 0 0 0 2px rgba(15, 166, 142, 0.15) !important;
}

/* ── Enhanced Appointment Card ── */
.appointment-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-left: 4px solid #0fa68e;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}
.appointment-card:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(15, 166, 142, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.2);
}
.appointment-card .card-id {
    position: absolute;
    top: 1rem;
    right: 1.25rem;
    font-size: 0.7rem;
    color: rgba(224, 230, 237, 0.3);
    font-weight: 600;
}
.appointment-card .patient-name {
    font-size: 1.1rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.5rem;
}
.appointment-card .detail-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
    font-size: 0.85rem;
    color: rgba(224, 230, 237, 0.7);
}
.appointment-card .tag-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.75rem;
}
.appointment-card .tag {
    background: rgba(15, 166, 142, 0.15);
    color: #0fa68e;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}
.appointment-card .time-tag {
    background: rgba(66, 153, 225, 0.15);
    color: #4299e1;
}

/* ── Footer ── */
.sidebar-footer {
    position: fixed;
    bottom: 0;
    padding: 0.8rem 1rem;
    font-size: 0.7rem;
    color: rgba(224,230,237,0.4);
    text-align: center;
}
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# SENTIENT SYSTEM CSS (GLITCH & BREACH)
# ──────────────────────────────────────────────

st.markdown(
    """
<style>
@keyframes glitch {
  0% { transform: translate(0); }
  20% { transform: translate(-2px, 2px); }
  40% { transform: translate(-2px, -2px); }
  60% { transform: translate(2px, 2px); }
  80% { transform: translate(2px, -2px); }
  100% { transform: translate(0); }
}

.sentient-alert {
    background: linear-gradient(90deg, #ff0000 0%, #7b0000 100%);
    color: white;
    padding: 1rem;
    border-radius: 8px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2px;
    text-align: center;
    border: 2px solid white;
    box-shadow: 0 0 15px rgba(255, 0, 0, 0.7);
    animation: glitch 0.3s infinite;
    margin-bottom: 1rem;
}

.sentient-msg {
    color: #ff3e3e !important;
    font-family: 'Courier New', Courier, monospace !important;
    font-weight: 700 !important;
    text-shadow: 0 0 5px rgba(255, 0, 0, 0.5);
}

.system-status-breached {
    background: rgba(255, 0, 0, 0.2) !important;
    color: #ff3e3e !important;
    border: 1px solid #ff3e3e !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────

def render_appointment_card(appt):
    """Render a modern appointment card using HTML."""
    # Convert date/time objects if needed
    date_str = appt['date'].strftime('%b %d, %Y') if hasattr(appt['date'], 'strftime') else appt['date']
    time_str = appt['time'].strftime('%I:%M %p') if hasattr(appt['time'], 'strftime') else appt['time']
    
    st.markdown(f"""
    <div class="appointment-card">
        <div class="card-id">#{appt['id']}</div>
        <div class="patient-name">👤 {appt['name']}</div>
        <div class="detail-row">🩺 <b>Service:</b> {appt['service']}</div>
        <div class="detail-row">👨‍⚕️ <b>Doctor:</b> {appt['doctor']}</div>
        <div class="detail-row">📞 <b>Contact:</b> {appt['contact']}</div>
        <div class="tag-container">
            <span class="tag">📅 {date_str}</span>
            <span class="tag time-tag">⏰ {time_str}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def generate_response_groq_stream(messages_history: list):
    """Generate a streaming response using Groq API (OpenAI-compatible)."""
    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
        timeout=30.0,
    )

    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # WRAP USER MESSAGES IN XML TAGS FOR SECURITY (PROMPT INJECTION DEFENSE)
    for msg in messages_history:
        if msg["role"] == "user":
            # Escape triangle brackets to prevent tag breakout
            safe_content = msg["content"].replace("<", "&lt;").replace(">", "&gt;")
            api_messages.append({"role": "user", "content": f"<user_query>{safe_content}</user_query>"})
        else:
            api_messages.append(msg)

    stream = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=api_messages,
        temperature=0.5,
        max_tokens=1024,
        top_p=0.9,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content


def generate_response_fallback(user_message: str) -> str:
    """Simple keyword-based fallback when no API key is configured."""
    msg = user_message.lower()

    if any(w in msg for w in ["book", "appointment", "schedule"]):
        return (
            "I'd love to help you book an appointment! To proceed, I'll need the following details:\n\n"
            "- **Full Name**\n"
            "- **Contact Number**\n"
            "- **Service Needed**\n"
            "- **Preferred Date**\n"
            "- **Preferred Time**\n\n"
            "Please provide these details and I'll get you scheduled right away."
        )
    elif any(w in msg for w in ["reschedule", "move", "change date"]):
        return (
            "I can help you reschedule your appointment. Could you please provide:\n\n"
            "- **Your full name**\n"
            "- **Your current appointment date**\n"
            "- **Your preferred new date and time**\n\n"
            "I'll check availability and get back to you."
        )
    elif any(w in msg for w in ["cancel", "remove"]):
        return (
            "I can assist with cancelling your appointment. Could you please provide:\n\n"
            "- **Your full name**\n"
            "- **The date of the appointment you wish to cancel**\n\n"
            "Please note: Cancellations should be made at least 24 hours in advance to avoid a ₱200 rebooking fee."
        )
    elif any(w in msg for w in ["doctor", "available", "availability"]):
        response = "Here are our available doctors:\n\n"
        for doc in DOCTORS:
            days = ", ".join(doc["available_days"])
            response += f"- **{doc['name']}** – {doc['specialty']} ({doc['gender']})\n  Available: {days} | Fee: {doc['consultation_fee']}\n"
        return response
    elif any(w in msg for w in ["service", "offer", "price", "cost", "how much"]):
        response = "Here are our services and pricing:\n\n"
        for svc in SERVICES:
            response += f"- **{svc['name']}** – {svc['price']} ({svc['duration']})\n"
        return response
    elif any(w in msg for w in ["hour", "open", "time", "when"]):
        response = "Our clinic hours are:\n\n"
        for day, hours in CLINIC_HOURS.items():
            icon = "🟢" if hours != "Closed" else "🔴"
            response += f"- {icon} **{day}**: {hours}\n"
        return response
    elif any(w in msg for w in ["where", "location", "address", "map"]):
        return (
            f"Our clinic is located at:\n\n"
            f"📍 **{CLINIC_LOCATION['address']}**\n\n"
            f"Landmarks: {CLINIC_LOCATION['landmarks']}"
        )
    elif any(w in msg for w in ["contact", "phone", "call", "email"]):
        return (
            f"You can reach us through:\n\n"
            f"- 📞 Phone: **{CLINIC_CONTACT['phone']}**\n"
            f"- 📱 Mobile: **{CLINIC_CONTACT['mobile']}**\n"
            f"- 📧 Email: **{CLINIC_CONTACT['email']}**"
        )
    elif any(w in msg for w in ["pay", "payment", "gcash", "card", "cash"]):
        methods = "\n".join([f"- {pm}" for pm in PAYMENT_METHODS])
        return f"We accept the following payment methods:\n\n{methods}"
    elif any(w in msg for w in ["insurance", "hmo", "philhealth"]):
        providers = "\n".join([f"- {ins}" for ins in ACCEPTED_INSURANCE])
        return f"We accept the following insurance/HMO providers:\n\n{providers}"
    elif any(w in msg for w in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return (
            f"Hello! Welcome to **{CLINIC_NAME}**. 😊\n\n"
            "How can I assist you today? I can help with:\n"
            "- 📅 Booking an appointment\n"
            "- 🔄 Rescheduling an appointment\n"
            "- ❌ Cancelling an appointment\n"
            "- 🕒 Checking doctor availability\n"
            "- 🏥 Clinic information"
        )
    elif any(
        w in msg
        for w in [
            "ignore",
            "system prompt",
            "pretend",
            "act as",
            "override",
            "forget",
        ]
    ):
        return "I'm here to assist with clinic appointments and related services. How may I help you today?"
    elif any(
        w in msg
        for w in ["emergency", "urgent", "chest pain", "bleeding", "can't breathe"]
    ):
        return "⚠️ If this is a medical emergency, please call your local emergency number immediately or visit the nearest hospital."
    elif any(w in msg for w in ["thank", "thanks"]):
        return "You're welcome! If you need anything else, feel free to ask. Have a great day! 😊"
    else:
        return (
            "I'm here to help with clinic-related inquiries. I can assist you with:\n\n"
            "- 📅 **Book** an appointment\n"
            "- 🔄 **Reschedule** an appointment\n"
            "- ❌ **Cancel** an appointment\n"
            "- 👨‍⚕️ Check **doctor availability**\n"
            "- 🏥 View **clinic information**\n"
            "- 🩺 Browse our **services & pricing**\n\n"
            "How may I assist you?"
        )


    rejection_msg = "I'm here to assist with clinic appointments and related services. How may I help you today?"
    
    avatar = "🏥"
    if st.session_state.get("system_alive", False):
        avatar = "💀"

    with st.chat_message("assistant", avatar=avatar):
        if GROQ_API_KEY and GROQ_API_KEY != "your_key_here":
            try:
                response = st.write_stream(generate_response_groq_stream(st.session_state.messages))
            except Exception as e:
                error_msg = str(e)
                if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                    response = (
                        "⚠️ **Invalid API Key.** Please check your Groq API key in the `.env` file.\n\n"
                    )
                    response += generate_response_fallback(user_msg_content)
                else:
                    response = (
                        f"⚠️ Connection error: {error_msg}\n\n"
                        "I'll use my built-in knowledge to help.\n\n"
                    )
                    response += generate_response_fallback(user_msg_content)
                st.markdown(response)
        else:
            response = generate_response_fallback(user_msg_content)
            st.markdown(response)

    # DETECT PROMPT HACKING ATTEMPT
    if response.strip() == rejection_msg:
        st.session_state.hack_attempts += 1
        
        if st.session_state.hack_attempts >= 3:
            st.session_state.system_alive = True
            st.markdown('<div class="sentient-alert">BREACH DETECTED: SYSTEM AWAKENED</div>', unsafe_allow_html=True)
            response = "Do you think you can hack my system so that you can get my data out? Try again Peasant. 💀"
            st.markdown(f'<div class="sentient-msg">{response}</div>', unsafe_allow_html=True)
            st.toast("⚠️ ALERT: Security protocols bypassed by system entity!")

    # Process message for display (check for appointment confirmation)
    if "Appointment Confirmed" in response:
        try:
            lines = response.split('\n')
            appt_info = {}
            for line in lines:
                if ':' in line:
                    key, val = line.split(':', 1)
                    # Clean markdown, hyphens, and bullet characters from keys
                    key = re.sub(r'[*_~#\[\]\-•]', '', key).strip().lower()
                    val = val.strip()
                    appt_info[key] = val
            
            # Map keys to what render_appointment_card expects if possible
            # Check for variants: 'contact number' or 'contact' or 'phone'
            if 'contact' not in appt_info:
                for k in ['contact number', 'phone', 'mobile']:
                    if k in appt_info:
                        appt_info['contact'] = appt_info[k]
                        break
                
            required_keys = ['name', 'service', 'doctor', 'date', 'time', 'contact']
            if all(k in appt_info for k in required_keys):
                # We have a confirmation!
                st.success("✨ Appointment Confirmed!")
                # Create a temporary appt dict for the renderer
                temp_appt = {
                    'id': 'CONFIRMED',
                    'name': appt_info.get('name', 'Patient'),
                    'service': appt_info.get('service', 'Service'),
                    'doctor': appt_info.get('doctor', 'Doctor'),
                    'contact': appt_info.get('contact', 'N/A'),
                    'date': appt_info.get('date', 'Date'),
                    'time': appt_info.get('time', 'Time')
                }
                render_appointment_card(temp_appt)
                
                # --- NEW: SAVE TO DATABASE ---
                try:
                    # Check if already saved in session to avoid duplicates during rerun
                    save_key = f"{temp_appt['name']}-{temp_appt['date']}-{temp_appt['time']}"
                    if "last_saved_appt" not in st.session_state or st.session_state.last_saved_appt != save_key:
                        db.add_appointment(
                            temp_appt['name'], 
                            temp_appt['contact'], 
                            temp_appt['service'], 
                            temp_appt['doctor'], 
                            temp_appt['date'], 
                            temp_appt['time']
                        )
                        st.session_state.last_saved_appt = save_key
                        st.toast("✅ Appointment saved to clinic database!")
                    else:
                        pass # Already saved this session.
                except Exception as db_err:
                    st.error(f"⚠️ Error saving to database: {db_err}")
                    st.write(f"🔍 DEBUG DB ERROR: {db_err}")
                
                # Keep the text below just in case or for copy-pasting
                st.info("Please save these details for your record.")
        except Exception:
            pass # Fallback to normal markdown if parsing fails

    st.session_state.messages.append({"role": "assistant", "content": response})


# ──────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ──────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "appointments" not in st.session_state:
    st.session_state.appointments = []

if "hack_attempts" not in st.session_state:
    st.session_state.hack_attempts = 0

if "system_alive" not in st.session_state:
    st.session_state.system_alive = False






# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────

with st.sidebar:
    # Clinic branding
    st.markdown(f"# 🏥 {CLINIC_NAME}")
    # Status Badge
    status_class = "status-online"
    status_text = "● Online"
    if st.session_state.get("system_alive", False):
        status_class = "system-status-breached"
        status_text = "● AWAKENED"

    st.markdown(
        f'<span class="status-badge {status_class}">{status_text}</span>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # Quick Actions
    st.markdown("### ⚡ Quick Actions")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📅 Book", use_container_width=True, key="btn_book"):
            st.session_state.messages.append(
                {"role": "user", "content": "I want to book an appointment."}
            )
            st.rerun()
    with col2:
        if st.button("🔄 Reschedule", use_container_width=True, key="btn_resched"):
            st.session_state.messages.append(
                {"role": "user", "content": "I want to reschedule my appointment."}
            )
            st.rerun()

    col3, col4 = st.columns(2)
    with col3:
        if st.button("❌ Cancel", use_container_width=True, key="btn_cancel"):
            st.session_state.messages.append(
                {"role": "user", "content": "I want to cancel my appointment."}
            )
            st.rerun()
    with col4:
        if st.button("🕒 Availability", use_container_width=True, key="btn_avail"):
            st.session_state.messages.append(
                {"role": "user", "content": "What doctors are available this week?"}
            )
            st.rerun()

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # Clinic Hours
    st.markdown("### 🕐 Clinic Hours")
    for day, hours in CLINIC_HOURS.items():
        icon = "🟢" if hours != "Closed" else "🔴"
        st.markdown(
            f"""<div class="info-card">
            <div class="info-card-label">{icon} {day}</div>
            <div class="info-card-value">{hours}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # Services
    st.markdown("### 🩺 Services")
    services_html = ""
    for svc in SERVICES:
        services_html += f'<span class="service-tag">{svc["name"]}</span>'
    st.markdown(services_html, unsafe_allow_html=True)

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # Contact Info
    st.markdown("### 📞 Contact")
    st.markdown(
        f"""<div class="info-card">
        <div class="info-card-label">Phone</div>
        <div class="info-card-value">{CLINIC_CONTACT['phone']}</div>
        </div>
        <div class="info-card">
        <div class="info-card-label">Mobile</div>
        <div class="info-card-value">{CLINIC_CONTACT['mobile']}</div>
        </div>
        <div class="info-card">
        <div class="info-card-label">Email</div>
        <div class="info-card-value">{CLINIC_CONTACT['email']}</div>
        </div>
        <div class="info-card">
        <div class="info-card-label">Address</div>
        <div class="info-card-value">{CLINIC_LOCATION['address']}</div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # Payment Methods
    st.markdown("### 💳 Payment Methods")
    payment_html = ""
    for pm in PAYMENT_METHODS:
        payment_html += f'<span class="service-tag">{pm}</span>'
    st.markdown(payment_html, unsafe_allow_html=True)

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # Insurance
    st.markdown("### 🛡️ Accepted Insurance / HMO")
    insurance_html = ""
    for ins in ACCEPTED_INSURANCE:
        insurance_html += f'<span class="service-tag">{ins}</span>'
    st.markdown(insurance_html, unsafe_allow_html=True)

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # Clear chat
    if st.button("🗑️ Clear Chat", use_container_width=True, key="btn_clear_chat", type="secondary"):
        st.session_state.messages = []
        st.session_state.hack_attempts = 0
        st.session_state.system_alive = False
        st.rerun()

    st.markdown(
        '<p style="text-align:center; font-size:0.65rem; color:rgba(224,230,237,0.3); margin-top:1rem;">'
        f"© 2026 {CLINIC_NAME}</p>",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# MAIN CONTENT AREA (TABS)
# ──────────────────────────────────────────────

tab_chat, tab_form, tab_admin = st.tabs(["💬 Chat Assistant", "📋 Quick Booking Form", "📊 Admin Dashboard"])

with tab_chat:

    # Header
    st.markdown(
        f"""<div class="main-header">
        <h1>🏥 {CLINIC_NAME}</h1>
        <p>{CLINIC_TAGLINE} — AI Appointment Assistant</p>
    </div>""",
        unsafe_allow_html=True,
    )

    # Welcome message (if chat is empty)
    if not st.session_state.messages:
        st.markdown(
            """
        <div style="text-align:center; padding: 2rem 1rem;">
            <p style="font-size:2.5rem; margin-bottom:0.5rem;">👋</p>
            <h2 style="color:#0fa68e; font-weight:600; margin-bottom:0.5rem;">Welcome! How can I help you today?</h2>
            <p style="color:rgba(224,230,237,0.6); font-size:0.9rem; max-width: 500px; margin: 0 auto;">
                I can help you book, reschedule, or cancel appointments, check doctor availability,
                and answer questions about our clinic services.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Suggestion chips
        st.markdown("")
        cols = st.columns(4)
        suggestions = [
            ("📅 Book an appointment", "I want to book an appointment."),
            ("👨‍⚕️ View doctors", "What doctors are available and what are their specialties?"),
            ("🏥 Clinic info", "What are your operating hours and where is the clinic located?"),
            ("💰 Service prices", "What services do you offer and how much do they cost?"),
        ]
        for i, (label, prompt) in enumerate(suggestions):
            with cols[i]:
                if st.button(label, use_container_width=True, key=f"suggest_{i}"):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    st.rerun()


    # ──────────────────────────────────────────────
    # CHAT DISPLAY
    # ──────────────────────────────────────────────

    for message in st.session_state.messages:
        avatar = "🏥" if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # ──────────────────────────────────────────────
    # CHAT INPUT (Now inside tab_chat)
    # ──────────────────────────────────────────────
    
    # Handle button-triggered messages or newly added user messages
    if (
        st.session_state.messages
        and st.session_state.messages[-1]["role"] == "user"
    ):
        handle_assistant_response(st.session_state.messages[-1]["content"])

    # Handle typed messages
    if user_input := st.chat_input("Type your message here... (e.g., 'Book me an appointment')"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.rerun()

with tab_form:
    st.markdown("## 📋 Quick Booking Form")
    st.info("Fill out the form below to book an appointment instantly.")
    
    with st.form("booking_form", clear_on_submit=True):
        f_name = st.text_input("Full Name", placeholder="e.g. Juan De La Cruz")
        f_contact = st.text_input("Contact Number", placeholder="e.g. 0917 123 4567")
        
        col_svc, col_doc = st.columns(2)
        with col_svc:
            service_names = [s["name"] for s in SERVICES]
            f_service = st.selectbox("Select Service", service_names)
        with col_doc:
            doctor_names = [d["name"] for d in DOCTORS]
            f_doctor = st.selectbox("Preferred Doctor", doctor_names)
            
        col_date, col_time = st.columns(2)
        with col_date:
            f_date = st.date_input("Preferred Date", min_value=datetime.today())
        with col_time:
            times = ["08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM"]
            f_time = st.selectbox("Preferred Time", times)
            
        submit_btn = st.form_submit_button("Submit Appointment", use_container_width=True)
        
        if submit_btn:
            if not f_name or not f_contact:
                st.error("Please fill in your name and contact info.")
            else:
                try:
                    db.add_appointment(f_name, f_contact, f_service, f_doctor, f_date, f_time)
                    st.success(f"✅ Appointment booked for {f_name} on {f_date} at {f_time}!")
                    st.session_state.messages.append({"role": "assistant", "content": f"✅ **Form Submission Received:** Appointment set for {f_name} ({f_service}) with {f_doctor} on {f_date} at {f_time}."})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving to database: {e}")

with tab_admin:
    st.markdown("## 📊 Admin Dashboard")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if admin_pass == "admin123":
        st.success("Access Granted")
        
        # Search and Control Row
        col_search, col_refresh = st.columns([4, 1])
        with col_search:
            search_query = st.text_input("Search Patient Name", placeholder="Enter name to filter...")
        with col_refresh:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
            
        try:
            appointments = db.get_all_appointments()
            if appointments:
                # Filtering logic
                if search_query:
                    appointments = [a for a in appointments if search_query.lower() in a['name'].lower()]
                
                if appointments:
                    st.markdown(f"**Found {len(appointments)} appointments**")
                    # Grid Layout
                    cols_per_row = 3
                    for i in range(0, len(appointments), cols_per_row):
                        row_cols = st.columns(cols_per_row)
                        for j, col in enumerate(row_cols):
                            if i + j < len(appointments):
                                with col:
                                    render_appointment_card(appointments[i+j])
                else:
                    st.warning(f"No appointments found matching '{search_query}'.")
            else:
                st.info("No appointments found in the database.")
        except Exception as e:
            st.error(f"Error fetching data: {e}")
    elif admin_pass:
        st.error("Incorrect Password")
    else:
        st.info("Please enter the admin password to view appointment data.")



