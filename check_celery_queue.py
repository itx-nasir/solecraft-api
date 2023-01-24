#!/usr/bin/env python3
"""
Check Celery queue status.
"""

import redis
from core.config import settings

def main():
    print("🔍 Checking Celery queue status...")
    
    try:
        # Connect to Redis broker
        r = redis.Redis.from_url(settings.celery_broker_url)
        
        # Check celery queue
        queue_length = r.llen('celery')
        print(f"📊 Tasks in 'celery' queue: {queue_length}")
        
        # Check for other queues
        all_keys = r.keys('*')
        list_keys = [key.decode() for key in all_keys if r.type(key) == b'list']
        print(f"📋 All list keys: {list_keys}")
        
        # Check specific email queue
        email_queue_length = r.llen('emails')
        print(f"📧 Tasks in 'emails' queue: {email_queue_length}")
        
        # Check celery result keys
        celery_keys = [key.decode() for key in all_keys if key.decode().startswith('celery-task-meta')]
        print(f"🎯 Celery result keys: {len(celery_keys)}")
        
        if queue_length > 0:
            print(f"⚠️  Warning: {queue_length} tasks are waiting to be processed!")
            print("💡 Make sure Celery worker is running to process these tasks.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 