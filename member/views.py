from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views, login, get_user_model
from django.urls import reverse_lazy
from .forms import StudentIDLoginForm
from librarian.models import Member as LibrarianMember, BorrowRecord, AdminProfile


class CustomLoginView(auth_views.LoginView):
	"""LoginView that supports a 'remember' checkbox to control session expiry.

	Uses template `member/login.html` and redirects to `member:profile` on success.
	"""
	template_name = 'member/login.html'
	redirect_authenticated_user = True
	success_url = reverse_lazy('member:profile')

	def form_valid(self, form):
		# If 'remember' not checked, expire session on browser close
		remember = self.request.POST.get('remember')
		if not remember:
			self.request.session.set_expiry(0)
		else:
			self.request.session.set_expiry(None)
		return super().form_valid(form)


def login_view(request):
	"""Two-step login: SSID → if admin show password step; if member go directly to profile."""
	User = get_user_model()

	if request.method == 'POST':
		step = request.POST.get('step', 'ssid')

		if step == 'ssid':
			form = StudentIDLoginForm(request, data=request.POST)
			if form.is_valid():
				ssid = form.cleaned_data['student_id']

				# Admin SSID → look up via AdminProfile.admin_id
				profile = AdminProfile.objects.filter(admin_id=ssid).select_related('user').first()
				if profile and profile.user.is_superuser and profile.user.is_active:
					request.session['pending_admin_ssid'] = ssid
					return redirect('member:login')

				# Member SSID → go straight to profile
				if LibrarianMember.objects.filter(ssid=ssid).exists():
					request.session['student_id'] = ssid
					return redirect('member:profile')

				form.add_error('student_id', 'No account found with that SSID.')
			return render(request, 'member/login.html', {'form': form, 'step': 'ssid'})

		elif step == 'password':
			pending_ssid = request.session.get('pending_admin_ssid')
			if not pending_ssid:
				return redirect('member:login')
			profile = AdminProfile.objects.filter(admin_id=pending_ssid).select_related('user').first()
			if not profile:
				return redirect('member:login')
			from django.contrib.auth import authenticate
			password = request.POST.get('password', '')
			user = authenticate(request, username=profile.user.username, password=password)
			if user and user.is_superuser:
				del request.session['pending_admin_ssid']
				login(request, user, backend='django.contrib.auth.backends.ModelBackend')
				return redirect('manage_books')
			return render(request, 'member/login.html', {
				'step': 'password',
				'pending_ssid': pending_ssid,
				'password_error': 'Incorrect password. Please try again.',
			})

	# GET: cancel clears the pending step
	if request.GET.get('cancel'):
		request.session.pop('pending_admin_ssid', None)
		return redirect('member:login')

	# GET: check if we are mid password-step
	pending_ssid = request.session.get('pending_admin_ssid')
	if pending_ssid:
		return render(request, 'member/login.html', {'step': 'password', 'pending_ssid': pending_ssid})

	form = StudentIDLoginForm()
	return render(request, 'member/login.html', {'form': form, 'step': 'ssid'})


def profile(request):
	student_id = request.session.get('student_id')
	member = None
	borrows = []
	history = []
	if student_id:
		member = LibrarianMember.objects.filter(ssid=student_id).first()
		if member:
			borrows = BorrowRecord.objects.filter(member=member, status='borrowing').select_related('book')
			# full history (including returned records)
			history = BorrowRecord.objects.filter(member=member).select_related('book').order_by('-start_date')
	else:
		history = []

	return render(request, 'member/profile.html', {
		'student_id': student_id,
		'member': member,
		'borrows': borrows,
		'history': history,
	})


def logout_view(request):
	# clear student_id and any session data we set
	try:
		del request.session['student_id']
	except KeyError:
		pass
	return redirect('member:login')


def history(request):
	"""Standalone history page showing all borrow records for the session student."""
	student_id = request.session.get('student_id')
	member = None
	history = []
	status_filter = request.GET.get('status', '')
	total_count = borrowed_count = returned_count = 0
	if student_id:
		member = LibrarianMember.objects.filter(ssid=student_id).first()
		if member:
			all_records = BorrowRecord.objects.filter(member=member).select_related('book')
			total_count    = all_records.count()
			borrowed_count = all_records.filter(status='borrowing').count()
			returned_count = all_records.filter(status='returned').count()
			history = all_records.order_by('-start_date')
			if status_filter == 'borrowed':
				history = history.filter(status='borrowing')
			elif status_filter == 'returned':
				history = history.filter(status='returned')

	return render(request, 'member/history.html', {
		'student_id': student_id,
		'member': member,
		'history': history,
		'status_filter': status_filter,
		'total_count': total_count,
		'borrowed_count': borrowed_count,
		'returned_count': returned_count,
	})
