import os
import subprocess
import glob
import resource

class Validator:
    def __init__(self):
        pass
    
    def _set_limits(self):
        # 2 seconds CPU time
        resource.setrlimit(resource.RLIMIT_CPU, (2, 3))
        # 512MB Memory
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))

    def judge_submission(self, source_path, contest_id, problem_id, max_points=100):
        # 1. Compile
        exe_path = source_path + ".exe"
        compile_cmd = ["g++", "-O2", "-o", exe_path, source_path]
        
        try:
            subprocess.run(compile_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            return {
                "verdict": "CE",
                "score": 0,
                "max_points": max_points,
                "details": e.stderr
            }

        # 2. Find Test Cases
        # Look in problems/<contest_id>/<problem_id>/
        problem_dir = os.path.join("problems", str(contest_id), problem_id)
        if not os.path.exists(problem_dir):
             return {
                "verdict": "IE", # Internal Error (Problem not found)
                "score": 0,
                "max_points": max_points,
                "details": "Problem directory not found."
            }

        inputs = sorted(glob.glob(os.path.join(problem_dir, "input_*.txt")))
        
        tests = []
        passed_count = 0
        total_tests = len(inputs)
        
        overall_verdict = "AC"
        
        # Sandbox command base
        sandbox_cmd = [
            "bwrap",
            "--ro-bind", "/", "/", 
            "--dev", "/dev",
            "--proc", "/proc",
            "--unshare-all",
            "--die-with-parent",
            exe_path
        ]

        for input_file in inputs:
            filename = os.path.basename(input_file)
            test_case_num = filename.replace("input_", "").replace(".txt", "")
            output_file = os.path.join(problem_dir, f"output_{test_case_num}.txt")
            
            if not os.path.exists(output_file):
                continue
                
            with open(output_file, 'r') as f:
                expected_output = f.read().strip()
            
            with open(input_file, 'r') as f:
                input_data = f.read()

            status = "AC"
            
            try:
                proc = subprocess.run(
                    sandbox_cmd, 
                    input=input_data, 
                    capture_output=True, 
                    text=True, 
                    timeout=2.0,
                    preexec_fn=self._set_limits
                )
                actual_output = proc.stdout.strip()
                
                if proc.returncode != 0:
                    if proc.returncode < 0:
                        if proc.returncode == -24: # SIGXCPU
                            status = "TLE"
                        else:
                            status = "RE"
                    elif proc.returncode == 152: # bwrap exit code for SIGXCPU
                        status = "TLE"
                    else:
                        status = "RE" 
                elif actual_output != expected_output:
                    actual_lines = [l.strip() for l in actual_output.splitlines() if l.strip()]
                    expected_lines = [l.strip() for l in expected_output.splitlines() if l.strip()]
                    
                    if actual_lines != expected_lines:
                        status = "WA"
                
            except subprocess.TimeoutExpired:
                status = "TLE"
            except Exception as e:
                status = "RE"
                
            tests.append({
                "case": test_case_num,
                "status": status,
                "time": "N/A"
            })
            
            if status == "AC":
                passed_count += 1
            elif overall_verdict == "AC":
                overall_verdict = status
        
        if os.path.exists(exe_path):
            os.remove(exe_path)

        if total_tests > 0:
            score = int((passed_count / total_tests) * max_points)
        else:
            score = 0
            
        return {
            "verdict": overall_verdict if total_tests > 0 else "IE", 
            "score": score,
            "max_points": max_points,
            "tests": tests
        }
