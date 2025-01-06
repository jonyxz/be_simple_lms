from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.http import JsonResponse
from lms_core.models import Course, Comment, CourseContent, CourseMember
from django.core import serializers
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required

# View untuk halaman utama
def index(request):
    return HttpResponse("<h1>Hello World</h1>")

# View untuk testing, mengembalikan semua course dalam format JSON
def testing(request):
    dataCourse = Course.objects.all()
    dataCourse = serializers.serialize("python", dataCourse)
    return JsonResponse(dataCourse, safe=False)

# View untuk menambahkan data course
def addData(request):
    try:
        teacher = User.objects.get(username="reza")
        course = Course.objects.create(
            name="Belajar Django",
            description="Belajar Django dengan Mudah",
            price=1000000,
            teacher=teacher
        )
        return JsonResponse({"message": "Data berhasil ditambahkan"})
    except User.DoesNotExist:
        return JsonResponse({"error": "Teacher not found"}, status=404)

# View untuk mengedit data course
def editData(request):
    course = Course.objects.filter(name="Belajar Django").first()
    if course:
        course.name = "Belajar Django Setelah update"
        course.save()
        return JsonResponse({"message": "Data berhasil diubah"})
    return JsonResponse({"error": "Course not found"}, status=404)

# View untuk menghapus data course
def deleteData(request):
    course = Course.objects.filter(name__icontains="Belajar Django").first()
    if course:
        course.delete()
        return JsonResponse({"message": "Data berhasil dihapus"})
    return JsonResponse({"error": "Course not found"}, status=404)

# View untuk register user baru
@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")
            email = data.get("email")

            if not username or not password or not email:
                return JsonResponse({"error": "All fields are required"}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({"error": "Username already exists"}, status=400)

            User.objects.create_user(username=username, password=password, email=email)
            return JsonResponse({"message": "User registered successfully"}, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

# View untuk menampilkan komentar yang sudah dimoderasi
def list_comments(request, content_id):
    comments = Comment.objects.filter(content_id=content_id, is_approved=True)
    
    if not comments.exists():
        return JsonResponse({"message": "No approved comments found for this content."}, status=404)
    
    data = serializers.serialize("json", comments)
    return JsonResponse(data, safe=False)

# View untuk moderasi komentar
@csrf_exempt
def moderate_comment(request, content_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, content_id=content_id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            is_approved = data.get('is_approved')

            if is_approved is None:
                return JsonResponse({"error": "is_approved field is required"}, status=400)

            comment.is_approved = is_approved
            comment.save()
            return JsonResponse({"message": "Comment updated successfully"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

# View untuk menampilkan statistik aktivitas pengguna
def user_activity_dashboard(request, user_id):
    user = get_object_or_404(User, id=user_id)
    stats = user.get_course_stats()
    return JsonResponse(stats)

# View untuk menampilkan statistik course
def course_analytics(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    stats = course.get_course_stats()
    return JsonResponse(stats)

# Batch enroll students
@csrf_exempt
def batch_enroll(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_id = data.get('course_id')
            user_ids = data.get('user_ids')  
            
            if not course_id or not user_ids:
                return JsonResponse({"error": "Course ID and user IDs are required"}, status=400)

            course = get_object_or_404(Course, id=course_id)

            # Check if the course is already full
            if CourseMember.objects.filter(course_id=course).count() + len(user_ids) > course.max_students:
                return JsonResponse({"error": "Not enough slots available for all students"}, status=400)

            # Enroll students
            for user_id in user_ids:
                try:
                    user = User.objects.get(id=user_id)
                    if not CourseMember.objects.filter(course_id=course, user_id=user).exists():
                        CourseMember.objects.create(course_id=course, user_id=user)
                except User.DoesNotExist:
                    return JsonResponse({"error": f"User {user_id} not found"}, status=404)

            return JsonResponse({"message": "Students enrolled successfully"}, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

def list_course_contents(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    contents = CourseContent.objects.filter(
        course=course, scheduled_start_time__lte=timezone.now()
    ).order_by('scheduled_start_time')

    return JsonResponse({
        "contents": [
            {
                "name": content.name,
                "description": content.description,
                "file_attachment": content.file_attachment.url if content.file_attachment else None,
                "start_time": content.scheduled_start_time,
                "end_time": content.scheduled_end_time,
            }
            for content in contents if content.is_available()
        ]
    })
    
@csrf_exempt
def enroll_student(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        course_id = data.get('course_id')
        user_id = data.get('user_id')

        course = Course.objects.get(id=course_id)
        user = User.objects.get(id=user_id)

        if CourseMember.objects.filter(course_id=course, user_id=user).exists():
            return JsonResponse({"error": "Student is already enrolled in this course"}, status=400)

        if CourseMember.objects.filter(course_id=course).count() >= course.max_students:
            return JsonResponse({"error": "Course is full"}, status=400)

        CourseMember.objects.create(course_id=course, user_id=user)
        return JsonResponse({"message": "Student enrolled successfully"}, status=201)

    return JsonResponse({"error": "Invalid request method"}, status=405)