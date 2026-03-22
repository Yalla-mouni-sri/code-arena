from django import forms
from .models import Admin, Coder

class AdminLoginForm(forms.Form):
    email = forms.EmailField(label="Registered Email ID")
    name = forms.CharField(max_length=150, label="Registered Name")
    password = forms.CharField(widget=forms.PasswordInput)

class AdminRegistrationForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    
    class Meta:
        model = Admin
        fields = ['name', 'email', 'location', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Password and Confirm Password do not match.")
        return cleaned_data

class CoderRegistrationForm(forms.ModelForm):
    class Meta:
        model = Coder
        fields = ['email', 'rollno', 'password', 'confirm_password', 'assigned_admin']
        labels = {
            'assigned_admin': 'Select Approving Admin'
        }
        widgets = {
            'password': forms.PasswordInput(),
            'confirm_password': forms.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_admin'].queryset = Admin.objects.filter(is_approved=True, is_superadmin=False)
        self.fields['assigned_admin'].empty_label = "Select an Admin"

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError(
                "Password and Confirm Password do not match."
            )
        return cleaned_data

class CoderLoginForm(forms.Form):
    rollno = forms.CharField(max_length=50, label="Roll No")
    password = forms.CharField(widget=forms.PasswordInput)
