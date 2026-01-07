import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_from = os.getenv("SMTP_FROM", "Digital Ninja <noreply@digitalninja.app>")
    
    def is_configured(self) -> bool:
        return bool(self.smtp_user and self.smtp_password)
    
    async def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        if not self.is_configured():
            logger.warning("SMTP not configured. Email not sent.")
            return False
        
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.smtp_from
            message["To"] = to_email
            
            if text_content:
                message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def send_verification_email(self, to_email: str, verification_link: str):
        subject = "Verify Your Digital Ninja Account"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #6366f1;">Welcome to Digital Ninja!</h2>
                <p>Thank you for registering. Please verify your email address by clicking the link below:</p>
                <p><a href="{verification_link}" style="background-color: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Verify Email</a></p>
                <p>If you didn't create an account, you can safely ignore this email.</p>
                <p style="color: #666; font-size: 12px; margin-top: 30px;">Digital Ninja App Builder</p>
            </body>
        </html>
        """
        return await self.send_email(to_email, subject, html_content)
    
    async def send_password_reset_email(self, to_email: str, reset_link: str):
        subject = "Reset Your Password"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #6366f1;">Password Reset Request</h2>
                <p>We received a request to reset your password. Click the link below to create a new password:</p>
                <p><a href="{reset_link}" style="background-color: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Reset Password</a></p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, you can safely ignore this email.</p>
                <p style="color: #666; font-size: 12px; margin-top: 30px;">Digital Ninja App Builder</p>
            </body>
        </html>
        """
        return await self.send_email(to_email, subject, html_content)
    
    async def send_invoice_email(self, to_email: str, invoice_pdf_path: str, amount: float):
        subject = f"Invoice - R{amount:.2f}"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #6366f1;">Your Invoice</h2>
                <p>Thank you for your payment of R{amount:.2f}.</p>
                <p>Your invoice is attached to this email.</p>
                <p style="color: #666; font-size: 12px; margin-top: 30px;">Digital Ninja App Builder</p>
            </body>
        </html>
        """
        return await self.send_email(to_email, subject, html_content)

email_service = EmailService()
