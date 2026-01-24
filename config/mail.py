from fastapi_mail import FastMail, ConnectionConfig
import os
from dotenv import load_dotenv

load_dotenv()

# Email configuration for Mailtrap
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "your-mailtrap-username"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "your-mailtrap-password"),
    MAIL_FROM=os.getenv("MAIL_FROM", "noreply@yourapp.com"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.mailtrap.io",
    # Security settings for port 2525
    MAIL_STARTTLS=True,  # connection upgrade to be encrypted
    MAIL_SSL_TLS=False,  # if true means connection is encrypted from the beginning no neesd to upgrade
    # Authentication
    USE_CREDENTIALS=True,  # Login with username/password
    # Certificate validation
    VALIDATE_CERTS=True,  # Check server certificate is valid
)

# Create FastMail instance
fast_mail = FastMail(conf)
