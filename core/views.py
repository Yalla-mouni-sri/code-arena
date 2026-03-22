import os
import json
import google.generativeai as genai
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from dotenv import load_dotenv
from .models import Question, Solution
from accounts.models import Admin, Coder

load_dotenv()

# 🔐 Load Gemini API key from environment variable
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize model
model = genai.GenerativeModel("gemini-2.5-flash")

# AI Evaluation Mappings
EVAL_SCORES = {
    'Excellent': 4,
    'VeryGood': 3,
    'Good': 2,
    'Average': 1,
    'Bad': 0,
    'Error': 0,
    'Manual Review Required': 0
}

COIN_REWARDS = {
    'Excellent': 70,
    'VeryGood': 50,
    'Good': 25,
    'Average': 2,
    'Bad': 0,
    'Error': 0,
    'Manual Review Required': 0
}

def evaluate_code(question_text, user_code):
    """
    Evaluates the user's code based on the question description.
    Returns: Excellent, VeryGood, Good, Average, or Bad.
    """
    prompt = f"""
You are a strict programming evaluator.

Question:
{question_text}

User Code:
{user_code}

Evaluate the code based on:
1. Correctness
2. Efficiency
3. Readability

Return ONLY one word from:
Excellent
VeryGood
Good
Average
Bad
"""
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 20
            }
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "Error"


def admin_dashboard(request):
    if request.session.get('role') != 'admin':
        messages.error(request, 'You are not authorized to view the admin dashboard.')
        return redirect('home')
    
    admin_id = request.session.get('user_id')
    try:
        current_admin = Admin.objects.get(id=admin_id)
    except Admin.DoesNotExist:
        return redirect('home')
     # Post question logic
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        admin_id = request.session.get('user_id')
        admin = get_object_or_404(Admin, id=admin_id)
        
        Question.objects.create(title=title, description=description, created_by=admin)
        messages.success(request, 'Challenge published successfully!')
        return redirect('admin_dashboard')

    # Get all questions by this admin
    admin_id = request.session.get('user_id')
    questions = Question.objects.filter(created_by_id=admin_id).order_by('-created_at')
    
    # Get unapproved coders assigned to this admin
    unapproved_coders = Coder.objects.filter(is_approved=False, assigned_admin_id=admin_id)
    
    return render(request, 'core/admin_dashboard.html', {
        'questions': questions,
        'unapproved_coders': unapproved_coders
    })

def superadmin_dashboard(request):
    # Check if already authenticated as superadmin
    if request.session.get('role') == 'admin' and request.session.get('is_superadmin'):
        pending_admins = Admin.objects.filter(is_approved=False, is_superadmin=False)
        approved_admins = Admin.objects.filter(is_approved=True, is_superadmin=False)
        
        return render(request, 'core/superadmin_dashboard.html', {
            'pending_admins': pending_admins,
            'approved_admins': approved_admins
        })
    else:
        # Show login form for superadmin
        if request.method == 'POST':
            email = request.POST.get('email')
            name = request.POST.get('name')
            password = request.POST.get('password')
            
            try:
                admin_user = Admin.objects.get(email=email, name=name, password=password, is_superadmin=True)
                request.session['role'] = 'admin'
                request.session['user_id'] = admin_user.id
                request.session['user_name'] = admin_user.name
                request.session['is_superadmin'] = True
                
                messages.success(request, 'Super Admin login successful.')
                return redirect('superadmin_dashboard')
            except Admin.DoesNotExist:
                messages.error(request, 'Invalid Super Admin Credentials.')
                
        return render(request, 'accounts/superadmin_login.html')

def approve_admin(request, admin_id):
    if request.session.get('role') != 'admin' or not request.session.get('is_superadmin'):
        return redirect('home')
        
    admin_to_approve = get_object_or_404(Admin, id=admin_id)
    admin_to_approve.is_approved = True
    admin_to_approve.save()
    
    messages.success(request, f'Admin {admin_to_approve.name} approved successfully!')
    return redirect('superadmin_dashboard')

def coder_dashboard(request):
    if request.session.get('role') != 'coder':
        messages.error(request, 'You are not authorized to view the coder dashboard.')
        return redirect('home')
        
    coder_id = request.session.get('user_id')
    coder = get_object_or_404(Coder, id=coder_id)

    # Filter questions by the coder's assigned admin
    if coder.assigned_admin:
        questions = Question.objects.filter(created_by=coder.assigned_admin).order_by('-created_at')
    else:
        # Fallback for coders without an assigned admin (though they shouldn't exist now)
        questions = Question.objects.all().order_by('-created_at')
    
    question_data = []
    for q in questions:
        # Check if this coder has an existing solution to see their flag and points
        sol = Solution.objects.filter(question=q, coder_id=coder_id).first()
        flag = sol.flag if sol else True
        is_solved = sol and sol.code.strip() != ""
        # If question is closed, the status might change
        question_data.append({
            'question': q,
            'flag': flag and not q.is_closed,
            'is_closed': q.is_closed,
            'is_solved': is_solved
        })
        
    return render(request, 'core/coder_dashboard.html', {
        'question_data': question_data,
        'coder': coder
    })

def coding_environment(request, question_id):
    if request.session.get('role') != 'coder':
        messages.error(request, 'You are not authorized to access the coding environment.')
        return redirect('home')
        
    question = get_object_or_404(Question, id=question_id)
    coder_id = request.session.get('user_id')
    coder = get_object_or_404(Coder, id=coder_id)
    
    if question.is_closed:
        messages.error(request, 'This challenge is closed and cannot be accessed.')
        return redirect('coder_dashboard')
    
    if request.method == 'POST':
        code = request.POST.get('code')
        language = request.POST.get('language')
        
        try:
            coder = Coder.objects.get(id=coder_id)
            
            # Check flag before accepting POST
            solution_check = Solution.objects.filter(question=question, coder=coder).first()
            if solution_check and not solution_check.flag:
                messages.error(request, 'Submission rejected: 0 points remaining.')
                return redirect('coder_dashboard')
                
            if code and language:
                # Store or update the solution (only 1 per coder per question)
                solution, created = Solution.objects.update_or_create(
                    question=question,
                    coder=coder,
                    defaults={
                        'code': code.strip(),
                        'language': language
                    }
                )
                # Automatic AI Evaluation on submission
                try:
                    evaluation_result = evaluate_code(question.description, code)
                    solution.evaluation = evaluation_result
                except Exception as e:
                    print(f"AI Evaluation Error: {e}")
                    solution.evaluation = "Manual Review Required"
                
                solution.save()
                
                messages.success(request, 'Solution submitted successfully!')
                return JsonResponse({'status': 'success', 'redirect_url': '/core/coder-dashboard/'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Code and language are required.'}, status=400)
        except Coder.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid coder session.'}, status=401)
        
    # Get previous solution to auto-fill if it exists, or create a blank one to initialize points
    previous_solution = None
    if coder_id:
        try:
            coder = Coder.objects.get(id=coder_id)
            previous_solution, created = Solution.objects.get_or_create(
                question=question, 
                coder=coder,
                defaults={
                    'code': '',
                    'language': 'Python',
                    'points_left': 3,
                    'flag': True
                }
            )
            
            if not previous_solution.flag:
                messages.error(request, 'You cannot access this challenge because your points have reached zero.')
                return redirect('coder_dashboard')
                
        except Exception:
            pass

    return render(request, 'core/coding_environment.html', {
        'question': question,
        'previous_solution': previous_solution,
        'coder': coder
    })

def decrement_points(request, question_id):
    if request.method == 'POST' and request.session.get('role') == 'coder':
        coder_id = request.session.get('user_id')
        try:
            coder = Coder.objects.get(id=coder_id)
            question = get_object_or_404(Question, id=question_id)
            solution = Solution.objects.get(question=question, coder=coder)
            
            if solution.points_left > 0:
                solution.points_left -= 1
                if solution.points_left <= 0:
                    solution.flag = False
                solution.save()
            return JsonResponse({'status': 'success', 'points_left': solution.points_left, 'flag': solution.flag})
            
        except (Coder.DoesNotExist, Solution.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Invalid session or solution not found.'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)

def get_leaderboard(request, question_id):
    if request.session.get('role') != 'coder':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
        
    question = get_object_or_404(Question, id=question_id)
    coder_id = request.session.get('user_id')
    
    # Get all solutions for this question, excluding empty code submissions
    solutions = Solution.objects.filter(question=question).exclude(code='').select_related('coder')
    
    solutions_list = []
    user_rank = None
    
    for sol in solutions:
        score = EVAL_SCORES.get(sol.evaluation, 0)
        entry = {
            'name': sol.coder.rollno,
            'points': score,
            'evaluation': sol.evaluation or 'Pending',
            'submitted_at': sol.submitted_at.strftime("%Y-%m-%d %H:%M")
        }
        solutions_list.append(entry)
    
    # Sort by score (desc), then by time (asc)
    solutions_list.sort(key=lambda x: (-x['points'], x['submitted_at']))
    
    # Add rank and identify current user's rank
    for i, sol in enumerate(solutions_list):
        sol['rank'] = i + 1
        if sol['name'] == request.session.get('user_name'):
            user_rank = sol

    # Only return top 10 for the general board to keep it clean
    return JsonResponse({
        'status': 'success',
        'leaderboard': solutions_list[:10],
        'user_rank': user_rank
    })

def close_question(request, question_id):
    if request.session.get('role') != 'admin':
        return redirect('home')
        
    question = get_object_or_404(Question, id=question_id)
    if question.is_closed:
        return redirect('admin_dashboard')
        
    # Mark as closed
    question.is_closed = True
    question.save()
    
    # Calculate rewards based on evaluation
    solutions = Solution.objects.filter(question=question).exclude(code='').select_related('coder')
    
    for sol in solutions:
        reward = COIN_REWARDS.get(sol.evaluation, 0)
        
        if reward > 0:
            coder = sol.coder
            coder.coins += reward
            coder.save()
            
    question.is_closed = True
    question.save()
    
    return redirect('admin_dashboard')

def decrement_points(request, question_id):
    """
    AJAX view to decrement points when user exits fullscreen.
    """
    if request.method == "POST":
        coder_id = request.session.get('user_id')
        sol = get_object_or_404(Solution, question_id=question_id, coder_id=coder_id)
        if sol.points_left > 0:
            sol.points_left -= 1
            if sol.points_left == 0:
                sol.flag = False
            sol.save()
            return JsonResponse({'status': 'success', 'points_left': sol.points_left})
    return JsonResponse({'status': 'error'}, status=400)

def execute_code(request):
    """
    AJAX view to evaluate code via Gemini AI.
    """
    if request.method == "POST":
        question_id = request.POST.get("question_id")
        user_code = request.POST.get("code")
        
        question = get_object_or_404(Question, id=question_id)
        
        result = evaluate_code(question.description, user_code)
        
        return JsonResponse({
            "status": "success",
            "evaluation": result
        })
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)

def approve_coder(request, coder_id):
    """
    View for admin to approve a coder.
    """
    if request.session.get('role') != 'admin':
        return redirect('home')
        
    coder = get_object_or_404(Coder, id=coder_id)
    coder.is_approved = True
    coder.save()
    
    messages.success(request, f'Coder {coder.rollno} approved successfully!')
    return redirect('admin_dashboard')