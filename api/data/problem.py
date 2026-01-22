import os

class Problem:
    def __init__(self, problem_id, problem_dir):
        self.id = problem_id
        self.problem_dir = problem_dir
        self.points = 100 # Default points
        self.has_pdf = os.path.exists(os.path.join(problem_dir, 'statement.pdf'))
        self.has_editorial = os.path.exists(os.path.join(problem_dir, 'editorial.pdf'))

class ProblemManager:
    def __init__(self, problems_dir='problems'):
        self.problems_dir = problems_dir

    def get_all_problems(self):
        problems = []
        if not os.path.exists(self.problems_dir):
            return []
        
        # List subdirectories
        for name in sorted(os.listdir(self.problems_dir)):
            path = os.path.join(self.problems_dir, name)
            if os.path.isdir(path):
                problems.append(Problem(name, path))
        return problems

    def get_problem(self, problem_id):
        path = os.path.join(self.problems_dir, problem_id)
        if os.path.isdir(path):
            return Problem(problem_id, path)
        return None
