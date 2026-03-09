from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q, Exists, OuterRef
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
    status_filter = request.GET.get('status', '')

    # Annotate each book with a boolean `_is_borrowed` usable in ORM filters
    active_borrow = BorrowRecord.objects.filter(book=OuterRef('pk'), return_date__isnull=True)
    books = Book.objects.select_related('category').annotate(
        _is_borrowed=Exists(active_borrow)
    )

    total_count     = Book.objects.count()
    available_count = books.filter(_is_borrowed=False).count()
    borrowed_count  = books.filter(_is_borrowed=True).count()

    if query:
        books = books.filter(
            Q(name__icontains=query) |
            Q(author__icontains=query) |
            Q(category__name__icontains=query) |
            Q(isbn__icontains=query)
        )
    if status_filter == 'available':
        books = books.filter(_is_borrowed=False)
    elif status_filter == 'borrowed':
        books = books.filter(_is_borrowed=True)

    categories = Category.objects.all()
    return render(request, 'librarian/manage_books.html', {
        'books': books,
        'categories': categories,
        'total_count': total_count,
        'available_count': available_count,
        'borrowed_count': borrowed_count,
        'status_filter': status_filter,
        'query': query,
    })

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
    records = BorrowRecord.objects.filter(return_date__isnull=True).order_by('book__id')
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
            # Check if member has any overdue (fine > 0) unreturned books
            overdue_records = BorrowRecord.objects.filter(
                member=member,
                return_date__isnull=True,
                due_date__lt=timezone.now().date()
            ).select_related('book')
            if overdue_records.exists():
                overdue_titles = ', '.join(f"'{r.book.name}'" for r in overdue_records)
                context['error'] = (
                    f"Member '{member.ssid}' has overdue book(s): {overdue_titles}. "
                    f"Please return them before borrowing again."
                )
                context['overdue_records'] = overdue_records
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
    status_filter = request.GET.get('status', '')
    records = []
    member = None
    active_count = returned_count = total_count = 0
    if ssid:
        member = Member.objects.filter(ssid=ssid).first()
        if member:
            all_records = BorrowRecord.objects.filter(member=member)
            total_count   = all_records.count()
            active_count  = all_records.filter(return_date__isnull=True).count()
            returned_count = all_records.filter(return_date__isnull=False).count()
            records = all_records.order_by('-start_date')
            if status_filter == 'active':
                records = records.filter(return_date__isnull=True)
            elif status_filter == 'returned':
                records = records.filter(return_date__isnull=False)

    return render(request, 'librarian/return_book.html', {
        'records': records, 'ssid': ssid, 'member': member,
        'status_filter': status_filter,
        'total_count': total_count,
        'active_count': active_count,
        'returned_count': returned_count,
    })

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
        elif action == 'edit':
            member = get_object_or_404(Member, id=request.POST.get('member_id'))
            member.name = request.POST.get('name')
            member.email = request.POST.get('email')
            member.phone = request.POST.get('phone')
            member.save()
        elif action == 'remove':
            Member.objects.filter(ssid=request.POST.get('ssid')).delete()
        return redirect('manage_users')

    query = request.GET.get('ssid', '')
    members = Member.objects.all()
    if query:
        members = members.filter(ssid__icontains=query)
        
    return render(request, 'librarian/manage_users.html', {'members': members})

from django.contrib.auth import logout as auth_logout

def admin_logout(request):
    auth_logout(request)
    return redirect('member:login')

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
