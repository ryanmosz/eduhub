"""
Course Management API Endpoints

Provides endpoints for fetching course data from Plone CMS,
replacing the mock data with real content.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..auth.dependencies import get_current_user
from ..auth.models import User
from ..plone_integration import get_plone_client, transform_plone_content

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/courses", tags=["Courses"])


class CourseResource(BaseModel):
    """Model for course resources (videos, PDFs, etc.)"""
    id: str
    title: str
    description: str
    type: str  # 'video', 'pdf', 'link', etc.
    url: str
    embedUrl: Optional[str] = None
    duration: Optional[str] = None
    instructor: Optional[str] = None


class Course(BaseModel):
    """Model for course data"""
    id: str
    title: str
    description: str
    department: str
    instructor: str
    students: int
    status: str  # 'active', 'completed', 'upcoming'
    resources: List[CourseResource] = []
    progress: Optional[int] = None  # For student view


class Announcement(BaseModel):
    """Model for announcements"""
    id: str
    title: str
    content: str
    type: str  # 'info', 'warning', 'success'
    created: str
    author: Optional[str] = None


@router.get("/", response_model=List[Course])
async def get_courses(
    current_user: User = Depends(get_current_user),
    department: Optional[str] = Query(None, description="Filter by department"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in title/description")
):
    """
    Get courses from Plone CMS.
    
    For students, returns enrolled courses with progress.
    For admin/dev, returns all courses with management info.
    """
    try:
        plone = await get_plone_client()
        
        # Build search parameters for Plone
        search_params = {
            "portal_type": "Course",  # Assuming Course content type in Plone
            "sort_on": "sortable_title",
            "sort_order": "ascending",
            "review_state": "published",  # Only published courses
        }
        
        # Add search query if provided
        if search:
            search_params["SearchableText"] = search
            
        # Add department filter if provided
        if department:
            search_params["Subject"] = department
            
        # Search for courses in Plone
        search_results = await plone.search_content(**search_params)
        
        courses = []
        for item in search_results.get("items", []):
            # Get full content for each course
            course_data = await plone.get_content(item["@id"].replace(plone.config.base_url, ""))
            
            # Transform to our Course model
            course = Course(
                id=course_data.get("UID", ""),
                title=course_data.get("title", ""),
                description=course_data.get("description", ""),
                department=course_data.get("department", "Unknown"),
                instructor=course_data.get("instructor", "Unknown"),
                students=course_data.get("enrolled_count", 0),
                status=course_data.get("course_status", "active"),
                resources=[]
            )
            
            # Get course resources (assuming they're stored as related items)
            if "items" in course_data:
                for resource_item in course_data.get("items", []):
                    resource = CourseResource(
                        id=resource_item.get("UID", ""),
                        title=resource_item.get("title", ""),
                        description=resource_item.get("description", ""),
                        type=resource_item.get("resource_type", "link"),
                        url=resource_item.get("url", ""),
                        embedUrl=resource_item.get("embed_url"),
                        duration=resource_item.get("duration"),
                        instructor=resource_item.get("instructor")
                    )
                    course.resources.append(resource)
            
            # Add student progress if user is a student
            if current_user.role == "student":
                # This would come from a separate tracking system
                course.progress = 0  # Default, would be fetched from user data
                
            courses.append(course)
            
        # Filter by status if provided (post-process since Plone might not have this field)
        if status:
            courses = [c for c in courses if c.status == status]
            
        return courses
        
    except Exception as e:
        logger.error(f"Error fetching courses from Plone: {e}")
        # Fallback to some default data to prevent complete failure
        return _get_fallback_courses(current_user)


@router.get("/announcements", response_model=List[Announcement])
async def get_announcements(
    current_user: User = Depends(get_current_user),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of announcements")
):
    """
    Get latest announcements from Plone CMS.
    """
    try:
        plone = await get_plone_client()
        
        # Search for announcements in Plone
        search_params = {
            "portal_type": ["News Item", "Event"],  # Common Plone types for announcements
            "sort_on": "created",
            "sort_order": "descending",
            "review_state": "published",
            "b_size": limit
        }
        
        search_results = await plone.search_content(**search_params)
        
        announcements = []
        for item in search_results.get("items", []):
            # Determine announcement type based on portal type
            announcement_type = "info"
            if item.get("@type") == "Event":
                announcement_type = "success"
            elif "urgent" in item.get("title", "").lower():
                announcement_type = "warning"
                
            announcement = Announcement(
                id=item.get("UID", ""),
                title=item.get("title", ""),
                content=item.get("description", ""),
                type=announcement_type,
                created=item.get("created", ""),
                author=item.get("Creator")
            )
            announcements.append(announcement)
            
        return announcements
        
    except Exception as e:
        logger.error(f"Error fetching announcements from Plone: {e}")
        # Fallback announcements
        return [
            Announcement(
                id="1",
                title="System Maintenance",
                content="Plone connection is being established. Content will be available shortly.",
                type="warning",
                created="2024-03-20T10:00:00Z",
                author="System"
            )
        ]


@router.get("/{course_id}", response_model=Course)
async def get_course_detail(
    course_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific course.
    """
    try:
        plone = await get_plone_client()
        
        # Search for course by UID
        search_results = await plone.search_content(
            UID=course_id,
            portal_type="Course"
        )
        
        if not search_results.get("items"):
            raise HTTPException(status_code=404, detail="Course not found")
            
        course_item = search_results["items"][0]
        course_data = await plone.get_content(
            course_item["@id"].replace(plone.config.base_url, "")
        )
        
        # Transform to Course model with full details
        course = Course(
            id=course_data.get("UID", ""),
            title=course_data.get("title", ""),
            description=course_data.get("description", ""),
            department=course_data.get("department", "Unknown"),
            instructor=course_data.get("instructor", "Unknown"),
            students=course_data.get("enrolled_count", 0),
            status=course_data.get("course_status", "active"),
            resources=[]
        )
        
        # Get detailed resources
        if "items" in course_data:
            for resource_item in course_data.get("items", []):
                resource = CourseResource(
                    id=resource_item.get("UID", ""),
                    title=resource_item.get("title", ""),
                    description=resource_item.get("description", ""),
                    type=resource_item.get("resource_type", "link"),
                    url=resource_item.get("url", ""),
                    embedUrl=resource_item.get("embed_url"),
                    duration=resource_item.get("duration"),
                    instructor=resource_item.get("instructor")
                )
                course.resources.append(resource)
                
        return course
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching course detail from Plone: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving course data")


def _get_fallback_courses(user: User) -> List[Course]:
    """
    Fallback course data when Plone is unavailable.
    This ensures the UI remains functional during development.
    """
    if user.role == "student":
        return [
            Course(
                id="phys101",
                title="Introduction to Physics",
                description="Fundamental concepts of mechanics, thermodynamics, and electromagnetism",
                department="Physics",
                instructor="Dr. Sarah Johnson",
                students=156,
                status="active",
                progress=65,
                resources=[
                    CourseResource(
                        id="1",
                        title="Quantum Mechanics Introduction",
                        description="Overview of quantum mechanics principles",
                        type="video",
                        url="https://www.youtube.com/watch?v=Iuv6hY6zsd0",
                        embedUrl="https://www.youtube.com/embed/Iuv6hY6zsd0",
                        duration="15:30"
                    )
                ]
            ),
            Course(
                id="math201",
                title="Calculus II",
                description="Integration techniques, applications, and series",
                department="Mathematics",
                instructor="Prof. Michael Chen",
                students=132,
                status="active",
                progress=80,
                resources=[]
            )
        ]
    else:
        # Admin/Dev view
        return [
            Course(
                id="phys101",
                title="Introduction to Physics",
                description="Fundamental concepts of mechanics, thermodynamics, and electromagnetism",
                department="Physics",
                instructor="Dr. Sarah Johnson",
                students=156,
                status="active",
                resources=[]
            ),
            Course(
                id="math201",
                title="Calculus II",
                description="Integration techniques, applications, and series",
                department="Mathematics",
                instructor="Prof. Michael Chen",
                students=132,
                status="active",
                resources=[]
            ),
            Course(
                id="cs301",
                title="Data Structures",
                description="Advanced data structures and algorithms",
                department="Computer Science",
                instructor="Dr. Emily Rodriguez",
                students=98,
                status="active",
                resources=[]
            )
        ]