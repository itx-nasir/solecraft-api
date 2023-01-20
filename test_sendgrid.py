#!/usr/bin/env python3
"""
Quick test script to verify SendGrid configuration.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_sendgrid():
    """Test SendGrid configuration and send a test email."""
    
    # Check if SendGrid is installed
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, From, To, Subject, HtmlContent, PlainTextContent
        print("✅ SendGrid package is installed")
    except ImportError:
        print("❌ SendGrid package not found. Install with: pip install sendgrid")
        return False
    
    # Check environment variables
    api_key = os.getenv('SENDGRID_API_KEY', '')
    email_from = os.getenv('EMAIL_FROM', 'noreply@solecraft.com')
    email_from_name = os.getenv('EMAIL_FROM_NAME', 'SoleCraft')
    
    if not api_key or api_key == 'your-sendgrid-api-key-here':
        print("❌ SENDGRID_API_KEY not configured in .env file")
        print("💡 Get your API key from: https://app.sendgrid.com/settings/api_keys")
        return False
    
    print(f"✅ API Key configured: {api_key[:10]}...")
    print(f"✅ From Email: {email_from}")
    print(f"✅ From Name: {email_from_name}")
    
    # Test email sending
    test_email = input("\nEnter email address to send test email to: ").strip()
    if not test_email:
        print("❌ No email address provided")
        return False
    
    try:
        # Create SendGrid client
        sg = SendGridAPIClient(api_key)
        
        # Create email
        message = Mail(
            from_email=From(email_from, email_from_name),
            to_emails=To(test_email),
            subject=Subject("🧪 SendGrid Test Email from SoleCraft"),
            html_content=HtmlContent(f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; padding: 20px; }}
                        .container {{ max-width: 600px; margin: 0 auto; }}
                        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                        .content {{ background: white; padding: 20px; border: 1px solid #e0e0e0; border-radius: 0 0 10px 10px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🧪 SendGrid Test Success!</h1>
                        </div>
                        <div class="content">
                            <p>Congratulations! Your SendGrid integration is working perfectly.</p>
                            <p><strong>Configuration Details:</strong></p>
                            <ul>
                                <li>From: {email_from}</li>
                                <li>API Key: {api_key[:10]}...</li>
                                <li>Test Time: Now!</li>
                            </ul>
                            <p>You're ready to send beautiful emails from SoleCraft! 🎉</p>
                        </div>
                    </div>
                </body>
                </html>
            """),
            plain_text_content=PlainTextContent(f"""
                SendGrid Test Success!
                
                Congratulations! Your SendGrid integration is working perfectly.
                
                Configuration Details:
                - From: {email_from}
                - API Key: {api_key[:10]}...
                - Test Time: Now!
                
                You're ready to send beautiful emails from SoleCraft!
            """)
        )
        
        # Send email
        print(f"\n📧 Sending test email to {test_email}...")
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            print(f"✅ Email sent successfully! Status: {response.status_code}")
            print("📬 Check your inbox (and spam folder) for the test email")
            return True
        else:
            print(f"❌ Failed to send email. Status: {response.status_code}")
            print(f"Response: {response.body}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False


if __name__ == "__main__":
    print("🧪 SendGrid Configuration Test for SoleCraft")
    print("=" * 50)
    
    success = test_sendgrid()
    
    if success:
        print("\n🎉 SendGrid is configured and working!")
        print("💡 You can now test the full registration flow")
    else:
        print("\n❌ SendGrid configuration failed")
        print("📚 Check the setup guide: docs/EMAIL_SETUP.md")