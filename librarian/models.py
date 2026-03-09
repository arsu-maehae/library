from django.db import models
from django.utils import timezone

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Book(models.Model):
    isbn = models.CharField(max_length=20, null=True, blank=True)
    name = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.name

    @property
    def is_borrowed(self):
        return BorrowRecord.objects.filter(book=self, return_date__isnull=True).exists()

class Member(models.Model):
    ssid = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.ssid

class BorrowRecord(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)

    @property
    def fine(self):
        if not self.return_date and self.due_date < timezone.now().date():
            overdue_days = (timezone.now().date() - self.due_date).days
            return overdue_days * 10  # Assuming 10 units fine per day
        return 0
