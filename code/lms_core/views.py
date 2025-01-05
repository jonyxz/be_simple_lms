from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from lms_core.models import Course, Comment, CourseContent, CourseMember
from django.core import serializers
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.contrib import messages

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
    course = Course(
        name = "Belajar Django",
        description = "Belajar Django dengan Mudah",
        price = 1000000,
        teacher = User.objects.get(username="reza")
    )
    course.save()
    return JsonResponse({"message": "Data berhasil ditambahkan"})

# View untuk mengedit data course
def editData(request):
    course = Course.objects.filter(name="Belajar Django").first()
    course.name = "Belajar Django Setelah update"
    course.save()
    return JsonResponse({"message": "Data berhasil diubah"})

# View untuk menghapus data course
def deleteData(request):
    course = Course.objects.filter(name__icontains="Belajar Django").first()
    course.delete()
    return JsonResponse({"message": "Data berhasil dihapus"})

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
    # Filter komentar yang terkait dengan content_id dan sudah dimoderasi
    comments = Comment.objects.filter(content_id=content_id, is_approved=True)
    
    # Mengecek jika tidak ada komentar yang ditemukan
    if not comments.exists():
        return JsonResponse({"message": "No approved comments found for this content."}, status=404)
    
    # Serialisasi data komentar
    data = serializers.serialize("json", comments)
    return JsonResponse(data, safe=False)

# View untuk moderasi komentar
@csrf_exempt
def moderate_comment(request, content_id, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id, content_id=content_id)
    except Comment.DoesNotExist:
        return JsonResponse({"error": "Comment not found"}, status=404)

    if request.method == 'POST':
        data = json.loads(request.body)
        is_approved = data.get('is_approved', None)
        
        if is_approved is None:
            return JsonResponse({"error": "is_approved field is required"}, status=400)
        
        comment.is_approved = is_approved
        comment.save()
        return JsonResponse({"message": "Comment updated successfully"}, status=200)

    return JsonResponse({"error": "Invalid request method"}, status=405)

# View untuk menampilkan statistik aktivitas pengguna (User Activity Dashboard)
def user_activity_dashboard(request, user_id):
    user = User.objects.get(id=user_id)
    stats = user.get_course_stats()
    return JsonResponse(stats)

# View untuk menampilkan statistik course (Course Analytics)
def course_analytics(request, course_id):
    course = Course.objects.get(id=course_id)
    stats = course.get_course_stats()
    return JsonResponse(stats)

# View untuk menampilkan daftar konten course yang sudah dirilis
def list_course_contents(request, course_id):
    contents = CourseContent.objects.filter(course_id=course_id, release_date__lte=timezone.now())
    data = serializers.serialize("json", contents)
    return JsonResponse(data, safe=False)

# View untuk batch enroll students
@csrf_exempt
def batch_enroll(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_id = data.get('course_id')
            user_ids = data.get('user_ids')  # Expecting list of user IDs
            
            if not course_id or not user_ids:
                return JsonResponse({"error": "Course ID and user IDs are required"}, status=400)

            course = Course.objects.get(id=course_id)

            # Check if the course is already full
            if CourseMember.objects.filter(course_id=course).count() + len(user_ids) > course.max_students:
                return JsonResponse({"error": "Not enough slots available for all students"}, status=400)

            # Enroll students
            for user_id in user_ids:
                user = User.objects.get(id=user_id)
                if not CourseMember.objects.filter(course_id=course, user_id=user).exists():
                    CourseMember.objects.create(course_id=course, user_id=user)

            return JsonResponse({"message": "Students enrolled successfully"}, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Course.DoesNotExist:
            return JsonResponse({"error": "Course not found"}, status=404)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

    return JsonResponse({"error": "Invalid request method"}, status=405)
