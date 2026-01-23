import os
import time
import shutil
import json
from flask import Flask, request, render_template, make_response, send_from_directory, abort, session, redirect, url_for, flash
from markupsafe import Markup
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

# --- CONTEXT PROCESSOR ---
@app.context_processor
def inject_user():
    username = session.get('username')
    is_admin_user = False
    rating = 0
    gender = 'Male'
    if username:
        is_admin_user = user_manager.is_admin(username)
        rating = user_manager.get_rating(username)
        gender = user_manager.get_gender(username)
    return dict(current_user=username, is_admin=is_admin_user, current_user_rating=rating, current_user_gender=gender)

# --- TEMPLATE FILTERS ---
@app.template_filter('handle')
def format_handle(username, rating=None):
    if not username: return ""
    try:
        r = int(rating) if rating is not None else 0
    except:
        r = 0
        
    cls = "user-lurker"
    if r < 400: cls = "user-lurker"
    elif r < 800: cls = "user-newbie"
    elif r < 1200: cls = "user-beginner"
    elif r < 1400: cls = "user-pupil"
    elif r < 1600: cls = "user-specialist"
    elif r < 1900: cls = "user-expert"
    elif r < 2100: cls = "user-candidate-master"
    elif r < 2300: cls = "user-master"
    elif r < 2400: cls = "user-international-master"
    elif r < 2500: cls = "user-grandmaster"
    elif r < 3000: cls = "user-legendary"
    elif r < 3200: cls = "user-protagonist"
    elif r < 3500: cls = "user-otaku"
    elif r < 3800: cls = "user-hime"
    elif r < 4000: cls = "user-yaoi"
    else: cls = "user-yuri"

    # Yuri Case (Bocchi Themed) >= 4000
    if r >= 4000:
        colors = ['#E7569D', '#E60416', '#F3C047', '#0067C0', '#F3C047', '#9B59B6', '#808080', '#8B4513']
        formatted_name = ""
        for i, char in enumerate(username):
            color = colors[i % len(colors)]
            formatted_name += f'<span style="color: {color}; font-weight: bold;">{char}</span>'
        return Markup(f'<span class="user-yuri" style="font-weight: bold;">{formatted_name}</span>')

    # Yaoi Case (Black + Purple + Glow) 3800 <= r < 4000
    if r >= 3800 and r < 4000:
        first = username[0]
        rest = username[1:]
        return Markup(f'<span class="user-yaoi"><span class="legendary-first">{first}</span><span style="color:#800080">{rest}</span></span>')

    # Hime Case (Pink Glow) 3500 <= r < 3800
    if r >= 3500 and r < 3800:
        return Markup(f'<span class="user-hime">{username}</span>')

    # Nutella-style (LGM)
    if (r >= 2500 and r < 3000):
        first = username[0]
        rest = username[1:]
        return Markup(f'<span class="{cls}"><span class="legendary-first">{first}</span>{rest}</span>')
    
    return Markup(f'<span class="{cls}">{username}</span>')

@app.template_filter('handle_icon')
def handle_icon(rating):
    try: r = int(rating)
    except: return ""
    if r >= 4000: return Markup('<span class="perk-icon crown-gold" title="Yuri Overlord">👑</span>')
    if r >= 3800: return Markup('<span class="perk-icon" title="Yaoi Master">🎖️</span>')
    if r >= 3500: return Markup('<span class="perk-icon" title="Hime Status">🌸</span>')
    if r >= 3000: return Markup('<span class="perk-icon" title="Protagonist">🗡️</span>')
    return ""

@app.template_filter('rank_name')
def get_rank_name(rating, gender='Male'):
    try: r = int(rating)
    except: r = 0
    
    if gender not in ['Male', 'Female']: gender = 'Male'
    
    if r < 400: return "Lurker"
    elif r < 800: return "Newbie"
    elif r < 1200: return "Beginner"
    elif r < 1400: return "Pupil"
    elif r < 1600: return "Specialist"
    elif r < 1900: return "Expert"
    elif r < 2100: return "Candidate Master"
    elif r < 2300: return "Master"
    elif r < 2400: return "International Master"
    elif r < 2500: return "Grandmaster"
    elif r < 3000: return "Legendary Grandmaster"
    elif r < 3200: return "Protagonist"
    elif r < 3500: return "Otaku"
    elif r < 3800:
        return "Himejoshi" if gender == "Female" else "Himedanshi"
    elif r < 4000:
        return "Fujoshi" if gender == "Female" else "Fudanshi"
    return "Yurijoshi" if gender == "Female" else "Yuridanshi"

@app.template_filter('datetime')
def format_datetime(value):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))

@app.template_filter('datetime_local')
def format_datetime_local(value):
    return time.strftime('%Y-%m-%dT%H:%M', time.localtime(value))

# --- ADMIN DECORATOR ---
def admin_required(f):
    def decorator(*args, **kwargs):
        if 'username' not in session: return redirect(url_for('login'))
        if not user_manager.is_admin(session['username']): return abort(403)
        return f(*args, **kwargs)
    decorator.__name__ = f.__name__
    return decorator

# --- ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    u = request.form.get('username')
    p = request.form.get('password')
    g = request.form.get('gender')
    
    if u in user_manager.users:
        return "Username taken. <a href='/register'>Try Again</a>"
    
    # Register user
    user_manager.users[u] = {
        'password': p, 
        'rating': 1500, # Default
        'is_admin': False,
        'gender': g
    }
    with open(user_manager.users_file, 'w') as f:
        json.dump(user_manager.users, f, indent=4)
        
    session['username'] = u
    return redirect(url_for('index'))

@app.route('/')
def index():
    # List of Contests
    contests = contest_manager.get_all_contests()
    now = time.time()
    return render_template('contests.html', contests=contests, now=now)

@app.route('/contest/<contest_id>')
def contest_dashboard(contest_id):
    contest = contest_manager.get_contest(contest_id)
    if not contest: abort(404)
    
    if 'username' not in session:
        return render_template('contest_dashboard.html', contest=contest, logged_in=False)

    username = session['username']
    problems = problem_manager.get_contest_problems(contest_id)
    time_remaining = contest_manager.get_time_remaining(contest_id)
    is_contest_over = contest_manager.is_over(contest_id)
    user_subs = contest_manager.get_user_submissions(username, contest_id)

    return render_template('contest_dashboard.html', 
                           logged_in=True,
                           username=username,
                           contest=contest,
                           problems=problems,
                           time_remaining=time_remaining,
                           is_contest_over=is_contest_over,
                           submissions=user_subs)

@app.route('/standings')
def standings_redirect():
    contests = contest_manager.get_all_contests()
    if not contests:
        return redirect(url_for('index'))
    # get_all_contests already sorts by start_time descending
    latest_id = contests[0]['id']
    return redirect(url_for('contest_standings', contest_id=latest_id))

@app.route('/contest/<contest_id>/standings')
def contest_standings(contest_id):
    contest = contest_manager.get_contest(contest_id)
    if not contest: abort(404)
    
    all_users = list(user_manager.users.keys())
    board = contest_manager.get_leaderboard(contest_id, all_users, user_manager)
    problems = problem_manager.get_contest_problems(contest_id)
    
    return render_template('standings.html', contest=contest, leaderboard=board, problems=problems)

@app.route('/problem/<contest_id>/<problem_id>/pdf')
def view_pdf(contest_id, problem_id):
    if 'username' not in session: return abort(403)
    
    problem = problem_manager.get_problem(contest_id, problem_id)
    if not problem or not problem.has_pdf:
        abort(404)
        
    return send_from_directory(problem.problem_dir, "statement.pdf")

@app.route('/problem/<contest_id>/<problem_id>/editorial')
def view_editorial(contest_id, problem_id):
    if 'username' not in session: return abort(403)

    if not contest_manager.is_over(contest_id):
        return "Contest is still active! Editorials are hidden.", 403

    problem = problem_manager.get_problem(contest_id, problem_id)
    if not problem or not problem.has_editorial:
        abort(404)
        
    return send_from_directory(problem.problem_dir, "editorial.pdf")

@app.route('/submit', methods=['POST'])
def submit():
    if 'username' not in session: return redirect(url_for('index'))
    
    contest_id = request.form.get('contest_id')
    problem_id = request.form.get('problem_id')
    file = request.files.get('code_file')
    
    if not file or file.filename == '': return "No selected file"
    
    contest = contest_manager.get_contest(contest_id)
    if not contest: return "Invalid contest", 400
    
    # Check if contest is running or if we allow practice
    # For now, allow always, but maybe mark differently?
    
    filepath = os.path.join(UPLOAD_FOLDER, f"submit_{session['username']}_{contest_id}_{problem_id}.cpp")
    file.save(filepath)
    
    problem = problem_manager.get_problem(contest_id, problem_id)
    if not problem: return "Invalid problem", 400
    
    result = validator.judge_submission(filepath, contest_id, problem_id, max_points=problem.points)
    
    contest_manager.save_submission(session['username'], contest_id, problem_id, result['verdict'], result['score'])
    
    return render_template('result.html', result=result, problem_id=problem_id, contest_id=contest_id)

@app.route('/rankings')
def rankings():
    users_data = []
    for u, data in user_manager.users.items():
        users_data.append({
            'username': u, 
            'rating': data.get('rating', 0),
            'gender': data.get('gender', 'Male')
        })
    users_data.sort(key=lambda x: x['rating'], reverse=True)
    return render_template('rankings.html', rankings=users_data)

@app.route('/rating-system')
def rating_system():
    return render_template('rating_system.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if user_manager.validate_login(username, password):
        session['username'] = username
        return redirect(url_for('index'))
    return "Invalid Username or Password. <a href='/'>Try Again</a>"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# --- ADMIN ROUTES ---

@app.route('/admin')
@admin_required
def admin_dashboard():
    user_manager = UserManager() # Reload
    contest_manager = ContestManager() # Reload
    users = user_manager.users
    contests = contest_manager.get_all_contests()
    
    return render_template('admin.html', 
                           users=users, 
                           contests=contests,
                           current_time=time.time(),
                           current_user=session['username'],
                           msg=request.args.get('msg'),
                           msg_type=request.args.get('msg_type'))

@app.route('/admin/create_contest', methods=['POST'])
@admin_required
def create_contest():
    name = request.form.get('name')
    start_str = request.form.get('start_time')
    end_str = request.form.get('end_time')
    
    try:
        start_time = time.mktime(time.strptime(start_str, "%Y-%m-%dT%H:%M"))
        end_time = time.mktime(time.strptime(end_str, "%Y-%m-%dT%H:%M"))
        
        cid = contest_manager.create_contest(name, start_time, end_time)
        os.makedirs(os.path.join('problems', cid), exist_ok=True)
        return redirect(url_for('admin_dashboard', msg=f"Contest {cid} created!", msg_type="success"))
    except Exception as e:
        return redirect(url_for('admin_dashboard', msg=f"Error parsing date: {e}", msg_type="error"))

@app.route('/admin/edit_contest/<contest_id>', methods=['GET', 'POST'])
@admin_required
def edit_contest(contest_id):
    contest = contest_manager.get_contest(contest_id)
    if not contest: abort(404)
    
    if request.method == 'POST':
        name = request.form.get('name')
        start_str = request.form.get('start_time')
        end_str = request.form.get('end_time')
        
        try:
            start_time = time.mktime(time.strptime(start_str, "%Y-%m-%dT%H:%M"))
            end_time = time.mktime(time.strptime(end_str, "%Y-%m-%dT%H:%M"))
            
            contest_manager.contests[contest_id]['name'] = name
            contest_manager.contests[contest_id]['start_time'] = float(start_time)
            contest_manager.contests[contest_id]['end_time'] = float(end_time)
            contest_manager.save_contests()
            return redirect(url_for('admin_dashboard', msg="Contest updated", msg_type="success"))
        except Exception as e:
            return redirect(url_for('admin_dashboard', msg=f"Error parsing date: {e}", msg_type="error"))
            
    return render_template('edit_contest.html', contest=contest)

@app.route('/admin/calculate_ratings', methods=['POST'])
@admin_required
def calculate_ratings():
    contest_id = request.form.get('contest_id')
    contest_manager.update_ratings(user_manager, contest_id)
    return redirect(url_for('admin_dashboard', msg=f"Ratings updated for Contest {contest_id}", msg_type="success"))

# Keep other admin routes (update_rating, add_user, delete_user) similar to before...
@app.route('/admin/update_rating', methods=['POST'])
@admin_required
def update_rating():
    username = request.form.get('username')
    try: new_rating = int(request.form.get('rating'))
    except: return redirect(url_for('admin_dashboard', msg="Invalid rating", msg_type="error"))
    
    if username in user_manager.users:
        user_manager.users[username]['rating'] = new_rating
        with open(user_manager.users_file, 'w') as f: json.dump(user_manager.users, f, indent=4)
        return redirect(url_for('admin_dashboard', msg="Rating updated", msg_type="success"))
    return redirect(url_for('admin_dashboard', msg="User not found", msg_type="error"))

@app.route('/admin/add_user', methods=['POST'])
@admin_required
def add_user():
    u = request.form.get('username')
    p = request.form.get('password')
    g = request.form.get('gender')
    is_admin = request.form.get('is_admin') == 'on'
    if u in user_manager.users: return redirect(url_for('admin_dashboard', msg="User exists", msg_type="error"))
    user_manager.users[u] = {'password': p, 'rating': 1500, 'is_admin': is_admin, 'gender': g}
    with open(user_manager.users_file, 'w') as f: json.dump(user_manager.users, f, indent=4)
    return redirect(url_for('admin_dashboard', msg="User added", msg_type="success"))

@app.route('/admin/delete_user', methods=['POST'])
@admin_required
def delete_user():
    u = request.form.get('username')
    if u == session['username']: return redirect(url_for('admin_dashboard', msg="Cannot delete self", msg_type="error"))
    if u in user_manager.users:
        del user_manager.users[u]
        with open(user_manager.users_file, 'w') as f: json.dump(user_manager.users, f, indent=4)
    return redirect(url_for('admin_dashboard', msg="User deleted", msg_type="success"))

if __name__ == '__main__':
    print("Contest Platform Started")
    app.run(debug=True, port=5000)