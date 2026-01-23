import os

class Problem:
    def __init__(self, problem_id, problem_dir, contest_id):
        self.id = problem_id
        self.contest_id = contest_id
        self.problem_dir = problem_dir
        self.points = 100 # Default points, could be loaded from a meta file
        self.has_pdf = os.path.exists(os.path.join(problem_dir, 'statement.pdf'))
        self.has_editorial = os.path.exists(os.path.join(problem_dir, 'editorial.pdf'))

class ProblemManager:
    def __init__(self, problems_root='problems'):
        self.problems_root = problems_root

    def get_contest_problems(self, contest_id):
        problems = []
        contest_dir = os.path.join(self.problems_root, str(contest_id))
        
        if not os.path.exists(contest_dir):
            return []
        
        # List subdirectories (A, B, C...)
        for name in sorted(os.listdir(contest_dir)):
            path = os.path.join(contest_dir, name)
            if os.path.isdir(path):
                problems.append(Problem(name, path, contest_id))
        return problems

    def get_problem(self, contest_id, problem_id):
        path = os.path.join(self.problems_root, str(contest_id), problem_id)
        if os.path.isdir(path):
            return Problem(problem_id, path, contest_id)
        return None
    
    def get_all_problems_global(self):
        # Used for global admin view if needed
        all_probs = []
        if os.path.exists(self.problems_root):
            for cid in os.listdir(self.problems_root):
                cdir = os.path.join(self.problems_root, cid)
                if os.path.isdir(cdir):
                    for pid in os.listdir(cdir):
                        pdir = os.path.join(cdir, pid)
                        if os.path.isdir(pdir):
                            all_probs.append(Problem(pid, pdir, cid))
        return all_probs