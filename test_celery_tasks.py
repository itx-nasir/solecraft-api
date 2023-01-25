#!/usr/bin/env python3
"""
Test script to debug Celery task execution and email sending.
"""

import asyncio
import sys
from core.config import settings
from workers.email_tasks import send_welcome_email, get_email_service

def test_sendgrid_direct():
    """Test SendGrid directly without Celery."""
    print("🧪 Testing SendGrid directly...")
    
    try:
        email_service = get_email_service()
        
        success = email_service.send_email(
            to_email="test@example.com",
            subject_text="Test Email",
            html_content="<h1>Test Email</h1><p>This is a test email.</p>",
            text_content="Test Email\n\nThis is a test email."
        )
        
        if success:
            print("✅ SendGrid direct test passed")
            return True
        else:
            print("❌ SendGrid direct test failed")
            return False
            
    except Exception as e:
        print(f"❌ SendGrid direct test error: {e}")
        return False

def test_celery_task_queue():
    """Test Celery task queueing."""
    print("\n🧪 Testing Celery task queueing...")
    
    try:
        # Queue the task
        result = send_welcome_email.delay("test-user-123", "test@example.com", "Test User")
        print(f"✅ Task queued successfully with ID: {result.id}")
        
        # Check task status
        print(f"📊 Task state: {result.state}")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery task queueing error: {e}")
        return False

def test_redis_connection():
    """Test Redis connection."""
    print("\n🧪 Testing Redis connection...")
    
    try:
        import redis
        r = redis.Redis.from_url(settings.redis_url)
        
        # Test basic operations
        r.ping()
        print("✅ Redis ping successful")
        
        # Test queue operations
        r.lpush("test_queue", "test_message")
        message = r.rpop("test_queue")
        print(f"✅ Redis queue test successful: {message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False

def check_environment():
    """Check environment configuration."""
    print("\n🧪 Checking environment configuration...")
    
    config_issues = []
    
    if not settings.sendgrid_api_key:
        config_issues.append("SENDGRID_API_KEY not set")
    
    if not settings.email_from:
        config_issues.append("EMAIL_FROM not set")
    
    if not settings.redis_url:
        config_issues.append("REDIS_URL not set")
    
    if not settings.celery_broker_url:
        config_issues.append("CELERY_BROKER_URL not set")
    
    if config_issues:
        print("❌ Configuration issues found:")
        for issue in config_issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ Configuration looks good")
        return True

def main():
    """Run all tests."""
    print("🚀 SoleCraft Celery & Email Debug Test")
    print("=" * 50)
    
    all_passed = True
    
    # Test environment
    if not check_environment():
        all_passed = False
    
    # Test Redis
    if not test_redis_connection():
        all_passed = False
    
    # Test SendGrid directly
    if not test_sendgrid_direct():
        all_passed = False
    
    # Test Celery task queueing
    if not test_celery_task_queue():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Email system should be working.")
        print("\n💡 If emails still aren't being sent during registration:")
        print("   1. Make sure Celery worker is running")
        print("   2. Check Celery worker logs for errors")
        print("   3. Verify SendGrid API key has send permissions")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 