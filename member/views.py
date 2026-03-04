from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from .forms import StudentIDLoginForm


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
	"""Accept a single student_id input, store it in session, and redirect to profile."""
	if request.method == 'POST':
		form = StudentIDLoginForm(request, data=request.POST)
		if form.is_valid():
			student_id = form.cleaned_data['student_id']
			request.session['student_id'] = student_id
			return redirect('member:profile')
	else:
		form = StudentIDLoginForm()

	return render(request, 'member/login.html', {'form': form})


def profile(request):
	student_id = request.session.get('student_id')
	return render(request, 'member/profile.html', {'student_id': student_id})


def logout_view(request):
	# clear student_id and any session data we set
	try:
		del request.session['student_id']
	except KeyError:
		pass
	return redirect('member:login')
