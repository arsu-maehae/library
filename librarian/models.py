from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

# Create your models here.

class AdminProfile(models.Model):
    """Extends auth_user with a library-specific admin SSID."""
    user       = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='admin_profile')
    admin_id   = models.CharField(max_length=50, unique=True, help_text="Admin SSID used for login")
    admin_name = models.CharField(max_length=150, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.admin_id} ({self.admin_name})"

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
        return BorrowRecord.objects.filter(book=self, status=BorrowRecord.STATUS_BORROWING).exists()

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
    STATUS_BORROWING = 'borrowing'
    STATUS_RETURNED  = 'returned'
    STATUS_CHOICES   = [
        (STATUS_BORROWING, 'Borrowing'),
        (STATUS_RETURNED,  'Returned'),
    ]

    book             = models.ForeignKey(Book, on_delete=models.CASCADE)
    member           = models.ForeignKey(Member, on_delete=models.CASCADE)
    start_date       = models.DateField(default=timezone.now)
    due_date         = models.DateField()
    return_date      = models.DateField(null=True, blank=True)

    # ── New fields ──────────────────────────────────────────────────────
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_BORROWING)
    fine_amount      = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    created_by_admin = models.CharField(max_length=150, blank=True, default='')
    updated_at       = models.DateTimeField(auto_now=True)

    @property
    def fine(self):
        """Live fine for currently-borrowed overdue books (10 units/day)."""
        if self.status == self.STATUS_BORROWING and self.due_date < timezone.now().date():
            return (timezone.now().date() - self.due_date).days * 10
        return 0
