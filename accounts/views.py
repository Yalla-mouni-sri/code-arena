from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import AdminLoginForm, CoderLoginForm, CoderRegistrationForm, AdminRegistrationForm
from .models import Admin, Coder

def home(request):
    return render(request, 'home.html')

def admin_login(request):
    if request.session.get('role') == 'admin':
        if request.session.get('is_superadmin'):
            return redirect('superadmin_dashboard')
        return redirect('admin_dashboard')
        
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']
            
            try:
                # Normal admins only
                admin_user = Admin.objects.get(email=email, name=name, password=password, is_superadmin=False)
                
                if not admin_user.is_approved:
                    messages.warning(request, 'Your account is pending approval from the Super Admin.')
                    return redirect('admin_login')
                
                request.session['role'] = 'admin'
                request.session['user_id'] = admin_user.id
                request.session['user_name'] = admin_user.name
                request.session['is_superadmin'] = False
                
                return redirect('admin_dashboard')
            except Admin.DoesNotExist:
                messages.error(request, 'Invalid Admin Credentials (or you are the Super Admin).')
    else:
        form = AdminLoginForm()
    return render(request, 'accounts/admin_login.html', {'form': form})

def admin_register(request):
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            admin_user = form.save(commit=False)
            admin_user.is_approved = False  # Ensure it defaults to False
            admin_user.save()
            messages.success(request, 'Registration successful! Please wait for Super Admin approval.')
            return redirect('admin_login')
    else:
        form = AdminRegistrationForm()
    return render(request, 'accounts/admin_register.html', {'form': form})

def coder_login(request):
    if request.session.get('role') == 'coder':
        return redirect('coder_dashboard')
        
    if request.method == 'POST':
        form = CoderLoginForm(request.POST)
        if form.is_valid():
            rollno = form.cleaned_data['rollno']
            password = form.cleaned_data['password']
            
            try:
                coder_user = Coder.objects.get(rollno=rollno, password=password)
                if not coder_user.is_approved:
                    messages.warning(request, 'admin have to permit to login')
                    return redirect('coder_login')
                
                request.session['role'] = 'coder'
                request.session['user_id'] = coder_user.id
                request.session['user_name'] = coder_user.rollno
                return redirect('coder_dashboard')
            except Coder.DoesNotExist:
                messages.error(request, 'Invalid Coder Credentials.')
    else:
        form = CoderLoginForm()
    return render(request, 'accounts/coder_login.html', {'form': form})

def coder_register(request):
    if request.method == 'POST':
        form = CoderRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful! Please wait for admin approval before logging in.')
            return redirect('home')
    else:
        form = CoderRegistrationForm()
    return render(request, 'accounts/coder_register.html', {'form': form})

def custom_logout(request):
    request.session.flush()
    return redirect('home')
