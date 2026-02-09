import os
import json
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To

class CampaignManager:
    def __init__(self, api_key=None):
        """
        Manages email campaigns using SendGrid.
        api_key: SendGrid API Key (optional, can be set later)
        """
        self.api_key = api_key
        self.campaign_log_file = "campaign_history.json"
        
    def get_all_client_emails(self):
        """
        Extracts all unique client emails from memory files.
        Returns: List of email addresses
        """
        memory_dir = "client_memories"
        emails = []
        
        if not os.path.exists(memory_dir):
            return emails
            
        for filename in os.listdir(memory_dir):
            if filename.endswith('.json'):
                # Filename is the email (e.g., jessica@gmail.com.json)
                email = filename.replace('.json', '')
                if '@' in email:  # Basic validation
                    emails.append(email)
        
        return list(set(emails))  # Remove duplicates
    
    def send_campaign(self, subject, html_content, from_email="nes.shine@oracle.com", from_name="Nes Shine"):
        """
        Sends email campaign to all clients.
        Returns: (success_count, failed_count, error_message)
        """
        if not self.api_key:
            return (0, 0, "SendGrid API Key not configured")
        
        emails = self.get_all_client_emails()
        
        if not emails:
            return (0, 0, "No client emails found in memory")
        
        sg = SendGridAPIClient(self.api_key)
        success_count = 0
        failed_count = 0
        errors = []
        
        for email in emails:
            try:
                message = Mail(
                    from_email=(from_email, from_name),
                    to_emails=To(email),
                    subject=subject,
                    html_content=html_content
                )
                
                response = sg.send(message)
                
                if response.status_code in [200, 201, 202]:
                    success_count += 1
                else:
                    failed_count += 1
                    errors.append(f"{email}: Status {response.status_code}")
                    
            except Exception as e:
                failed_count += 1
                errors.append(f"{email}: {str(e)}")
        
        # Log the campaign
        self._log_campaign(subject, len(emails), success_count, failed_count)
        
        error_msg = "; ".join(errors[:5]) if errors else None  # Show first 5 errors
        return (success_count, failed_count, error_msg)
    
    def _log_campaign(self, subject, total_recipients, success, failed):
        """Logs campaign to history file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "subject": subject,
            "total_recipients": total_recipients,
            "success": success,
            "failed": failed
        }
        
        # Load existing log
        if os.path.exists(self.campaign_log_file):
            with open(self.campaign_log_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        history.append(log_entry)
        
        # Save updated log
        with open(self.campaign_log_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def get_campaign_history(self, limit=10):
        """Returns last N campaigns."""
        if not os.path.exists(self.campaign_log_file):
            return []
        
        with open(self.campaign_log_file, 'r') as f:
            history = json.load(f)
        
        return history[-limit:]  # Return last N entries


# EMAIL TEMPLATES
TEMPLATES = {
    "Moon Phase Insights": {
        "subject": "🌙 This Month's Cosmic Forecast",
        "body": """
        <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; background: #0a0000; color: #d4af37; padding: 40px;">
            <h1 style="text-align: center; color: #d4af37; font-size: 28px;">Moon Phase Insights</h1>
            <p style="font-size: 16px; line-height: 1.8;">
                The Full Moon in [SIGN] approaches, bringing a wave of transformation. 
                This is a time to release what no longer serves you and embrace the unknown.
            </p>
            <p style="font-size: 16px; line-height: 1.8;">
                [ADD YOUR INSIGHTS HERE]
            </p>
            <p style="text-align: center; margin-top: 40px;">
                <a href="[YOUR_BOOKING_LINK]" style="background: #7b0000; color: white; padding: 15px 30px; text-decoration: none; border-radius: 0px;">
                    Book Your Reading
                </a>
            </p>
            <p style="text-align: center; font-size: 12px; color: #888; margin-top: 30px;">
                Nes Shine // Oracle Engine
            </p>
        </div>
        """
    },
    "Exclusive Offer": {
        "subject": "⚡ Limited Grandmaster Slots Available",
        "body": """
        <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; background: #0a0000; color: #d4af37; padding: 40px;">
            <h1 style="text-align: center; color: #d4af37; font-size: 28px;">Exclusive Opportunity</h1>
            <p style="font-size: 16px; line-height: 1.8;">
                I'm opening <strong>5 Grandmaster Reading slots</strong> this week for select clients.
            </p>
            <p style="font-size: 16px; line-height: 1.8;">
                If you've been feeling stuck, confused, or at a crossroads, this is your moment.
            </p>
            <p style="text-align: center; margin-top: 40px;">
                <a href="[YOUR_BOOKING_LINK]" style="background: #7b0000; color: white; padding: 15px 30px; text-decoration: none; border-radius: 0px;">
                    Claim Your Slot
                </a>
            </p>
            <p style="text-align: center; font-size: 12px; color: #888; margin-top: 30px;">
                Nes Shine // Oracle Engine
            </p>
        </div>
        """
    },
    "Custom": {
        "subject": "",
        "body": ""
    }
}
