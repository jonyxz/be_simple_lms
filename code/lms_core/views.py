from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from lms_core.models import Course, Comment, CourseContent, CourseMember
from django.core import serializers
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django import forms
from django.contrib import messages

def index(request):
    return HttpResponse("<h1>Hello World</h1>")
    
def testing(request):
    dataCourse = Course.objects.all()
    dataCourse = serializers.serialize("python", dataCourse)
    return JsonResponse(dataCourse, safe=False)

def addData(request): 
    course = Course(
        name = "Belajar Django",
        description = "Belajar Django dengan Mudah",
        price = 1000000,
        teacher = User.objects.get(username="reza")
    )
    course.save()
    return JsonResponse({"message": "Data berhasil ditambahkan"})

def editData(request):
    course = Course.objects.filter(name="Belajar Django").first()
    course.name = "Belajar Django Setelah update"
    course.save()
    return JsonResponse({"message": "Data berhasil diubah"})

def deleteData(request):
    course = Course.objects.filter(name__icontains="Belajar Django").first()
    course.delete()
    return JsonResponse({"message": "Data berhasil dihapus"})

@csrf_exempt
def register(request):
    if request.method == 'POST':
        username = ""
        password = ""
        email = ""

        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username already exists"}, status=400)

        User.objects.create_user(username=username, password=password, email=email)
        return JsonResponse({"message": "User registered successfully"}, status=201)

    return JsonResponse({"error": "Invalid request method"}, status=405)

def list_comments(request, content_id):
    comments = Comment.objects.filter(content_id=content_id, is_approved=True)
    data = serializers.serialize("json", comments)
    return JsonResponse(data, safe=False)

def user_activity_dashboard(request, user_id):
    user = User.objects.get(id=user_id)
    stats = user.get_course_stats()
    return JsonResponse(stats)

def course_analytics(request, course_id):
    course = Course.objects.get(id=course_id)
    stats = course.get_course_stats()
    return JsonResponse(stats)

def list_course_contents(request, course_id):
    contents = CourseContent.objects.filter(course_id=course_id, release_date__lte=timezone.now())
    data = serializers.serialize("json", contents)
    return JsonResponse(data, safe=False)

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

class BatchEnrollForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), label="Course")
    students = forms.ModelMultipleChoiceField(queryset=User.objects.filter(is_staff=False), label="Students")

def batch_enroll(request):
    if request.method == 'POST':
        form = BatchEnrollForm(request.POST)
        if form.is_valid():
            course = form.cleaned_data['course']
            students = form.cleaned_data['students']
            if CourseMember.objects.filter(course_id=course).count() + len(students) > course.max_students:
                messages.error(request, "Not enough slots available for all students")
                return redirect('batch_enroll')
            for student in students:
                if not CourseMember.objects.filter(course_id=course, user_id=student).exists():
                    CourseMember.objects.create(course_id=course, user_id=student)
            messages.success(request, "Students enrolled successfully")
            return redirect('admin:index')
    else:
        form = BatchEnrollForm()
    return render(request, 'admin/batch_enroll.html', {'form': form})