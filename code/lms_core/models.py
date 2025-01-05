from django.db import models
from django.contrib.auth.models import User

class Course(models.Model):
    name = models.CharField("Nama", max_length=255)
    description = models.TextField("Deskripsi")
    price = models.IntegerField("Harga")
    image = models.ImageField("Gambar", upload_to="course", blank=True, null=True)
    teacher = models.ForeignKey(User, verbose_name="Pengajar", on_delete=models.RESTRICT)
    max_students = models.IntegerField("Jumlah Maksimal Siswa", default=30)  # Tambahkan field max_students
    created_at = models.DateTimeField("Dibuat pada", auto_now_add=True)
    updated_at = models.DateTimeField("Diperbarui pada", auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Mata Kuliah"
        verbose_name_plural = "Data Mata Kuliah"
        ordering = ["-created_at"]

    def is_member(self, user):
        return CourseMember.objects.filter(course_id=self, user_id=user).exists()

    def get_course_stats(self):
        return {
            'members_count': CourseMember.objects.filter(course_id=self).count(),
            'contents_count': CourseContent.objects.filter(course_id=self).count(),
            'comments_count': Comment.objects.filter(content_id__course_id=self).count(),
        }

ROLE_OPTIONS = [('std', "Siswa"), ('ast', "Asisten")]

class CourseMember(models.Model):
    course_id = models.ForeignKey(Course, verbose_name="matkul", on_delete=models.RESTRICT)
    user_id = models.ForeignKey(User, verbose_name="siswa", on_delete=models.RESTRICT)
    roles = models.CharField("peran", max_length=3, choices=ROLE_OPTIONS, default='std')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Subscriber Matkul"
        verbose_name_plural = "Subscriber Matkul"

    def __str__(self) -> str:
        return f"{self.course_id.name} : {self.user_id.username}"


class CourseContent(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file_attachment = models.FileField("File", null=True, blank=True)
    course_id = models.ForeignKey(Course, verbose_name="matkul", on_delete=models.RESTRICT)
    parent_id = models.ForeignKey("self", verbose_name="induk", on_delete=models.RESTRICT, null=True, blank=True)
    release_date = models.DateTimeField("Tanggal Rilis", null=True, blank=True)  # Tambahkan field release_date
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Konten Matkul"
        verbose_name_plural = "Konten Matkul"

    def __str__(self) -> str:
        return f'{self.course_id.name} - {self.name}'


class Comment(models.Model):
    content_id = models.ForeignKey(CourseContent, verbose_name="konten", on_delete=models.CASCADE)
    member_id = models.ForeignKey(CourseMember, verbose_name="pengguna", on_delete=models.CASCADE)
    comment = models.TextField('komentar')
    is_approved = models.BooleanField('Disetujui', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Komentar"
        verbose_name_plural = "Komentar"

    def __str__(self) -> str:
        return f"Komen oleh {self.member_id.user_id.username}: {self.comment}"


class ContentCompletion(models.Model):
    content = models.ForeignKey(CourseContent, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('content', 'user')

    def __str__(self):
        return f'{self.user.username} completed {self.content.name}'

User.add_to_class('get_course_stats', lambda self: {
    'courses_as_student': CourseMember.objects.filter(user_id=self, roles='std').count(),
    'courses_created': Course.objects.filter(teacher=self).count(),
    'comments_written': Comment.objects.filter(member_id__user_id=self).count(),
    'contents_completed': ContentCompletion.objects.filter(user=self).count(),
})