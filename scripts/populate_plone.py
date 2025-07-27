#!/usr/bin/env python3
"""
Script to populate Plone with sample educational content.
This demonstrates the Plone integration for the project.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.eduhub.plone_integration import PloneClient, PloneConfig


async def populate_plone():
    """Populate Plone with sample educational content."""
    print("🚀 Starting Plone content population...")
    
    # Create Plone client
    config = PloneConfig()
    client = PloneClient(config)
    
    try:
        await client.connect()
        print(f"✅ Connected to Plone at {config.base_url}")
        
        # Check site info
        site_info = await client.get_site_info()
        print(f"📍 Site: {site_info.get('title', 'Unknown')}")
        
        # Create some sample courses
        courses = [
            {
                "id": "cs101",
                "title": "Introduction to Computer Science",
                "description": "Fundamental concepts of programming, algorithms, and data structures.",
                "department": "Computer Science",
                "instructor": "Dr. Smith",
                "enrolled_count": 156,
                "course_status": "active"
            },
            {
                "id": "phys101",
                "title": "Introduction to Physics",
                "description": "Fundamental concepts of mechanics, thermodynamics, and electromagnetism",
                "department": "Physics",
                "instructor": "Dr. Sarah Johnson",
                "enrolled_count": 132,
                "course_status": "active"
            },
            {
                "id": "math201",
                "title": "Calculus II",
                "description": "Integration techniques, applications, and series",
                "department": "Mathematics",
                "instructor": "Prof. Michael Chen",
                "enrolled_count": 98,
                "course_status": "active"
            }
        ]
        
        print("\n📚 Creating sample courses...")
        for course_data in courses:
            try:
                # Try to create a folder for courses if it doesn't exist
                result = await client.create_content(
                    parent_path="",
                    portal_type="Document",  # Using Document as Course type might not exist
                    title=course_data["title"],
                    description=course_data["description"],
                    text=f"""
                    <h2>Course Information</h2>
                    <p><strong>Department:</strong> {course_data['department']}</p>
                    <p><strong>Instructor:</strong> {course_data['instructor']}</p>
                    <p><strong>Enrolled Students:</strong> {course_data['enrolled_count']}</p>
                    <p><strong>Status:</strong> {course_data['course_status']}</p>
                    
                    <h3>Course Description</h3>
                    <p>{course_data['description']}</p>
                    """
                )
                print(f"  ✅ Created course: {course_data['title']}")
            except Exception as e:
                print(f"  ❌ Failed to create course {course_data['title']}: {e}")
        
        # Create some announcements
        announcements = [
            {
                "title": "Welcome to Spring 2025 Semester",
                "description": "Classes begin on January 20th. Make sure to check your schedule and course materials.",
                "text": "Welcome back students! The Spring 2025 semester is about to begin. Please ensure you have registered for all your courses and have access to the course materials."
            },
            {
                "title": "Library Extended Hours During Finals",
                "description": "The library will be open 24/7 during finals week to support your studies.",
                "text": "To support students during the finals period, the main library will remain open 24 hours a day from May 1-15."
            },
            {
                "title": "New Computer Lab Opening",
                "description": "A new state-of-the-art computer lab is now available in Building C.",
                "text": "We are excited to announce the opening of our new computer lab featuring 50 high-performance workstations."
            }
        ]
        
        print("\n📢 Creating sample announcements...")
        for announcement in announcements:
            try:
                result = await client.create_content(
                    parent_path="",
                    portal_type="News Item",
                    title=announcement["title"],
                    description=announcement["description"],
                    text=announcement["text"]
                )
                print(f"  ✅ Created announcement: {announcement['title']}")
            except Exception as e:
                print(f"  ❌ Failed to create announcement {announcement['title']}: {e}")
        
        print("\n✨ Plone content population completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure Plone is running and accessible at http://localhost:8080/Plone")
        print("   You can start Plone with: docker-compose up -d plone")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(populate_plone())