import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER_EMAIL = "iamsubhansh1@gmail.com"
SENDER_PASSWORD = "zcxa vldh gmdq aebd" 

def send_verification_email(to_email: str, username: str, token: str):
    subject = "Verify your email"
    verification_link = f"http://localhost:5173/verify/{token}"  # backend endpoint
    body = f"""
    Hi {username},

    Please verify your email by clicking the link below:
    {verification_link}

    Thank you!
    """

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
 