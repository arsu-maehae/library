from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Book, Category, Member, BorrowRecord

# Create your views here.

def is_admin(user):
    return user.is_authenticated and user.is_superuser

class AdminLoginView(auth_views.LoginView):
    template_name = 'librarian/login.html'
    redirect_authenticated_user = True

@login_required
@user_passes_test(is_admin)
def manage_books(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            # Get or Create Category from text input
            category_name = request.POST.get('category')
            category = None
            if category_name:
                category, _ = Category.objects.get_or_create(name=category_name)

            isbn = request.POST.get('isbn')
            name = request.POST.get('name')
            author = request.POST.get('author')
            book_id = request.POST.get('book_id')

            # If a book_id was provided and a Book with that id exists, update it.
            # Otherwise create a new Book. Do NOT pass an explicit primary key
            # into create() as that can violate UNIQUE constraints.
            if book_id and book_id.isdigit():
                existing = Book.objects.filter(id=book_id).first()
                if existing:
                    existing.isbn = isbn
                    existing.name = name
                    existing.author = author
                    existing.category = category
                    existing.save()
                else:
                    Book.objects.create(isbn=isbn, name=name, author=author, category=category)
            else:
                Book.objects.create(isbn=isbn, name=name, author=author, category=category)
        elif action == 'edit':
            book = get_object_or_404(Book, id=request.POST.get('book_id'))
            
            category_name = request.POST.get('category')
            category = None
            if category_name:
                category, _ = Category.objects.get_or_create(name=category_name)

            book.isbn = request.POST.get('isbn')
            book.name = request.POST.get('name')
            book.author = request.POST.get('author')
            book.category = category
            book.save()
        elif action == 'delete':
            book = get_object_or_404(Book, id=request.POST.get('book_id'))
            book.delete()
        return redirect('manage_books')

    query = request.GET.get('q', '')
    books = Book.objects.all()
    if query:
        books = books.filter(
            Q(name__icontains=query) | 
            Q(author__icontains=query) | 
            Q(category__name__icontains=query) |
            Q(isbn__icontains=query)
        )
    
    categories = Category.objects.all()
    return render(request, 'librarian/manage_books.html', {'books': books, 'categories': categories})

@login_required
@user_passes_test(is_admin)
def active_borrows(request):
    if request.method == 'POST':
        # Return book action
        record_id = request.POST.get('record_id')
        record = get_object_or_404(BorrowRecord, id=record_id)
        record.return_date = timezone.now().date()
        record.save()
        return redirect('active_borrows')

    query = request.GET.get('ssid', '')
    records = BorrowRecord.objects.filter(return_date__isnull=True)
    if query:
        records = records.filter(member__ssid__icontains=query)
        
    return render(request, 'librarian/active_borrows.html', {'records': records})

@login_required
@user_passes_test(is_admin)
def borrow_process(request):
    context = {}
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        ssid = request.POST.get('ssid')
        duration = int(request.POST.get('duration', 7))
        unit = request.POST.get('unit', 'days')
        start_date_str = request.POST.get('start_date')
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        else:
            start_date = timezone.now().date()
        
        # Validate Book and Member without raising 404
        book = None
        if book_id and book_id.isdigit():
            book = Book.objects.filter(id=book_id).first()
        
        member = Member.objects.filter(ssid=ssid).first()
        
        if not book:
            context['error'] = f"Book ID '{book_id}' not found."
        elif not member:
            context['error'] = f"Member SSID '{ssid}' not found."
        elif book.is_borrowed:
            context['error'] = f"Book '{book.name}' is already borrowed."
        else:
            days_to_add = duration
            if unit == 'months':
                days_to_add = duration * 30
            elif unit == 'years':
                days_to_add = duration * 365
            
            BorrowRecord.objects.create(
                book=book,
                member=member,
                start_date=start_date,
                due_date=start_date + timedelta(days=days_to_add)
            )
            context['success'] = f"Successfully borrowed '{book.name}' to {member.name} ({member.ssid})."

    return render(request, 'librarian/borrow_process.html', context)

@login_required
@user_passes_test(is_admin)
def return_book(request):
    if request.method == 'POST':
        record_id = request.POST.get('record_id')
        record = get_object_or_404(BorrowRecord, id=record_id)
        record.return_date = timezone.now().date()
        record.save()
        return redirect(f"{request.path}?ssid={record.member.ssid}")

    ssid = request.GET.get('ssid', '')
    records = []
    member = None
    if ssid:
        member = Member.objects.filter(ssid=ssid).first()
        if member:
            records = BorrowRecord.objects.filter(member=member).order_by('-start_date')
    
    return render(request, 'librarian/return_book.html', {'records': records, 'ssid': ssid, 'member': member})

@login_required
@user_passes_test(is_admin)
def manage_users(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            Member.objects.create(
                ssid=request.POST.get('ssid'),
                name=request.POST.get('name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone')
            )
        elif action == 'remove':
            Member.objects.filter(ssid=request.POST.get('ssid')).delete()
        return redirect('manage_users')

    query = request.GET.get('ssid', '')
    members = Member.objects.all()
    if query:
        members = members.filter(ssid__icontains=query)
        
    return render(request, 'librarian/manage_users.html', {'members': members})

@login_required
@user_passes_test(is_admin)
def settings_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('settings_view')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'librarian/settings.html', {'form': form})
