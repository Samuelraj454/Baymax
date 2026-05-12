import smtplib
import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from loguru import logger

class GmailClient:
    def __init__(self):
        self.user = os.getenv("GMAIL_ADDRESS")
        self.password = os.getenv("GMAIL_APP_PASSWORD")

    def is_configured(self):
        return bool(self.user and self.password)

    def send_email(self, to, subject, body, cc=None):
        if not self.is_configured():
            return "Gmail not configured. Add GMAIL_ADDRESS and GMAIL_APP_PASSWORD to .env."

        try:
            msg = MIMEMultipart()
            msg['From'] = self.user
            msg['To'] = to
            msg['Subject'] = subject
            if cc:
                msg['Cc'] = cc
            
            msg.attach(MIMEText(body, 'plain'))
            
            recipients = [to]
            if cc:
                recipients.append(cc)

            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.user, self.password)
            server.sendmail(self.user, recipients, msg.as_string())
            server.quit()
            
            return f"Email sent successfully to {to}."
        except Exception as e:
            logger.error(f"Gmail Send Error: {e}")
            return f"Failed to send email: {str(e)}"

    def read_emails(self, count=5, folder="INBOX"):
        if not self.is_configured():
            return "Gmail not configured."

        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.user, self.password)
            mail.select(folder)
            
            status, messages = mail.search(None, 'ALL')
            email_ids = messages[0].split()
            
            results = []
            for i in range(1, min(count, len(email_ids)) + 1):
                res, msg_data = mail.fetch(email_ids[-i], '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = msg['subject']
                        sender = msg['from']
                        
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode()
                            
                        results.append({
                            "subject": subject,
                            "from": sender,
                            "snippet": body[:200] + "..." if len(body) > 200 else body
                        })
            mail.logout()
            return results
        except Exception as e:
            logger.error(f"Gmail Read Error: {e}")
            return f"Error reading emails: {str(e)}"
