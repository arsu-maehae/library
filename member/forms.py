from django import forms


class StudentIDLoginForm(forms.Form):
    student_id = forms.CharField(
        max_length=150,
        label='Student ID',
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_student_id'})
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        student_id = cleaned_data.get('student_id')
        if not student_id:
            raise forms.ValidationError('Enter your student ID.')
        return cleaned_data
