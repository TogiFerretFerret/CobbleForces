import os
import time
import shutil
import json
from flask import Flask, request, render_template, make_response, send_from_directory, abort, session, redirect, url_for, flash
from api.data.users import UserManager
from api.data.problem import ProblemManager
from api.data.contest import ContestManager
from api.data.validator import Validator

app = Flask(__name__)
app.secret_key = 'brainrot_secret_key_secure_admin_727' 

UPLOAD_FOLDER = 'submissions'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Managers
user_manager = UserManager()
problem_manager = ProblemManager()
contest_manager = ContestManager()
validator = Validator()

# --- ADMIN DECORATOR ---
def admin_required(f):
    def decorator(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if not user_manager.is_admin(session['username']):
            return abort(403)
        return f(*args, **kwargs)
    decorator.__name__ = f.__name__
    return decorator

# --- ROUTES ---

@app.route('/admin')
@admin_required
def admin_dashboard():
    # Reload managers to get fresh data
    global user_manager, contest_manager
    user_manager = UserManager() 
    
    users = user_manager.users
    probs = [p.id for p in problem_manager.get_all_problems()]
    
    return render_template('admin.html', 
                           users=users, 
                           contest_state={'start_time': contest_manager.start_time, 'end_time': contest_manager.end_time},
                           current_time=time.time(),
                           problems=probs,
                           current_user=session['username'],
                           msg=request.args.get('msg'),
                           msg_type=request.args.get('msg_type'))

@app.route('/admin/update_contest', methods=['POST'])
@admin_required
def update_contest():
    try:
        start = float(request.form.get('start_time'))
        end = float(request.form.get('end_time'))
        contest_manager.start_time = start
        contest_manager.end_time = end
        contest_manager._save_state()
        return redirect(url_for('admin_dashboard', msg="Contest times updated", msg_type="success"))
    except ValueError:
        return redirect(url_for('admin_dashboard', msg="Invalid timestamp format", msg_type="error"))

@app.route('/admin/reset_contest', methods=['POST'])
@admin_required
def reset_contest():
    # Clear submissions data
    with open(contest_manager.data_file, 'w') as f:
        json.dump({}, f)
    
    # Reload contest manager's internal cache if any
    # (ContestManager loads on each call in get_user_submissions so we are good, 
    # but let's be safe if we add caching later)
    
    # Delete submission files?
    # shutil.rmtree(UPLOAD_FOLDER)
    # os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    return redirect(url_for('admin_dashboard', msg="Contest submissions reset!", msg_type="success"))

@app.route('/admin/add_user', methods=['POST'])
@admin_required
def add_user():
    u = request.form.get('username')
    p = request.form.get('password')
    is_admin = request.form.get('is_admin') == 'on'
    
    if u in user_manager.users:
        return redirect(url_for('admin_dashboard', msg="User already exists", msg_type="error"))
    
    user_manager.users[u] = {'password': p, 'rating': 1500, 'is_admin': is_admin}
    # Save
    with open(user_manager.users_file, 'w') as f:
        json.dump(user_manager.users, f, indent=4)
        
    return redirect(url_for('admin_dashboard', msg="User added", msg_type="success"))

@app.route('/admin/delete_user', methods=['POST'])
@admin_required
def delete_user():
    u = request.form.get('username')
    if u == session['username']:
         return redirect(url_for('admin_dashboard', msg="Cannot delete yourself", msg_type="error"))
         
    if u in user_manager.users:
        del user_manager.users[u]
        with open(user_manager.users_file, 'w') as f:
            json.dump(user_manager.users, f, indent=4)
            
    return redirect(url_for('admin_dashboard', msg="User deleted", msg_type="success"))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if user_manager.validate_login(username, password):
        session['username'] = username
        return redirect(url_for('index'))
    else:
        return "Invalid Username or Password. <a href='/'>Try Again</a>"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/')
def index():
    if 'username' not in session:
        return render_template('index.html', logged_in=False)

    username = session['username']
    problems = problem_manager.get_all_problems()
    
    time_remaining = contest_manager.get_time_remaining()
    is_contest_over = contest_manager.is_over()

    user_subs = contest_manager.get_user_submissions(username)

    resp = make_response(render_template('index.html', 
                                         logged_in=True,
                                         username=username,
                                         problems=problems,
                                         time_remaining=time_remaining,
                                         is_contest_over=is_contest_over,
                                         submissions=user_subs))
    resp.headers['Content-Type'] = 'text/html'
    return resp

@app.route('/leaderboard')
def leaderboard():
    if 'username' not in session: return redirect(url_for('index'))
    
    all_users = list(user_manager.users.keys())
    board = contest_manager.get_leaderboard(all_users)
    problems = problem_manager.get_all_problems()
    
    return render_template('leaderboard.html', leaderboard=board, problems=problems)

@app.route('/problem/<problem_id>/pdf')
def view_pdf(problem_id):
    if 'username' not in session: return abort(403)
    
    problem = problem_manager.get_problem(problem_id)
    if not problem or not problem.has_pdf:
        abort(404)
        
    return send_from_directory(problem.problem_dir, "statement.pdf")

@app.route('/problem/<problem_id>/editorial')
def view_editorial(problem_id):
    if 'username' not in session: return abort(403)

    if not contest_manager.is_over():
        return "Contest is still active! Editorials are hidden.", 403

    problem = problem_manager.get_problem(problem_id)
    if not problem or not problem.has_editorial:
        abort(404)
        
    return send_from_directory(problem.problem_dir, "editorial.pdf")

@app.route('/submit', methods=['POST'])
def submit():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    if 'code_file' not in request.files: return "No file uploaded"
    
    file = request.files['code_file']
    problem_id = request.form.get('problem_id')
    
    if file.filename == '': return "No selected file"
    
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, f"submit_{session['username']}_{problem_id}.cpp")
        file.save(filepath)
        
        problem = problem_manager.get_problem(problem_id)
        if not problem:
             return "Invalid problem", 400
        
        result = validator.judge_submission(filepath, problem_id, max_points=problem.points)
        
        contest_manager.save_submission(session['username'], problem_id, result['verdict'], result['score'])
        
        resp = make_response(render_template('result.html', result=result, problem_id=problem_id))
        resp.headers['Content-Type'] = 'text/html'
        return resp

if __name__ == '__main__':
    print(f"Contest started! Ends at timestamp: {contest_manager.end_time}")
    app.run(debug=True, port=5000)
