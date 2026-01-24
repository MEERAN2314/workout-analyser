#!/usr/bin/env python3
"""
Check active Celery tasks
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def check_celery_status():
    """Check Celery worker and task status"""
    try:
        from app.services.celery_app import celery_app
        
        print("🔍 Checking Celery Status...")
        print("-" * 40)
        
        # Check if we can connect to broker
        try:
            inspect = celery_app.control.inspect()
            
            # Get active tasks
            active_tasks = inspect.active()
            if active_tasks:
                print("📋 Active Tasks:")
                for worker, tasks in active_tasks.items():
                    print(f"   Worker: {worker}")
                    for task in tasks:
                        print(f"     - Task: {task.get('name', 'unknown')}")
                        print(f"       ID: {task.get('id', 'no-id')}")
                        print(f"       Args: {task.get('args', [])}")
            else:
                print("📋 No active tasks found")
            
            # Get registered tasks
            registered = inspect.registered()
            if registered:
                print("\n📝 Registered Tasks:")
                for worker, tasks in registered.items():
                    print(f"   Worker: {worker}")
                    for task in tasks:
                        if 'video' in task or 'process' in task:
                            print(f"     - {task}")
            
            # Get worker stats
            stats = inspect.stats()
            if stats:
                print("\n📊 Worker Stats:")
                for worker, stat in stats.items():
                    print(f"   Worker: {worker}")
                    print(f"     Pool: {stat.get('pool', {}).get('max-concurrency', 'unknown')} workers")
                    print(f"     Total tasks: {stat.get('total', {})}")
            
        except Exception as e:
            print(f"❌ Cannot connect to Celery broker: {e}")
            print("   Make sure Redis is running and Celery worker is started")
            
    except ImportError as e:
        print(f"❌ Cannot import Celery app: {e}")

if __name__ == "__main__":
    check_celery_status()