import threading
import queue
import time
import os
import json

class SubmissionQueue:
    def __init__(self, validator, contest_manager, num_workers=8):
        self.validator = validator
        self.contest_manager = contest_manager
        self.queue = queue.Queue()
        self.results = {} # sub_id -> result
        self.results_lock = threading.Lock()
        
        for i in range(num_workers):
            t = threading.Thread(target=self._worker, name=f"JudgeWorker-{i}", daemon=True)
            t.start()

    def add_submission(self, sub_id, username, source_path, contest_id, problem_id, time_limit=2.0):
        with self.results_lock:
            self.results[sub_id] = {'status': 'Queued', 'verdict': 'In Queue'}
        self.queue.put({
            'sub_id': sub_id,
            'username': username,
            'source_path': source_path,
            'contest_id': contest_id,
            'problem_id': problem_id,
            'time_limit': time_limit
        })

    def _worker(self):
        while True:
            task = self.queue.get()
            if task is None: break
            
            sub_id = task['sub_id']
            with self.results_lock:
                self.results[sub_id]['status'] = 'Judging'
                self.results[sub_id]['verdict'] = 'Starting'
                self.results[sub_id]['tests'] = []
            
            def update_progress(partial_result):
                with self.results_lock:
                    self.results[sub_id].update(partial_result)

            try:
                result = self.validator.judge_submission(
                    task['source_path'], 
                    task['contest_id'], 
                    task['problem_id'], 
                    max_points=100,
                    on_test_complete=update_progress,
                    time_limit=task.get('time_limit', 2.0)
                )
                
                # Save full result to a dedicated file atomatically
                res_path = os.path.join('submissions', f'result_{sub_id}.json')
                tmp_path = res_path + '.tmp'
                with open(tmp_path, 'w') as f:
                    json.dump(result, f, indent=4)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, res_path)

                # Update summary in contest_data.json
                # ContestManager now has its own internal RLock for file safety
                data = self.contest_manager._load_data()
                user_subs = data.get(task['username'], [])
                for s in user_subs:
                    if s.get('id') == sub_id:
                        s['verdict'] = result['verdict']
                        s['score'] = result['score']
                        break
                self.contest_manager._save_data(data)
                
                with self.results_lock:
                    self.results[sub_id] = result
                    self.results[sub_id]['status'] = 'Finished'
            except Exception as e:
                error_res = {'status': 'Error', 'verdict': 'IE', 'details': str(e), 'score': 0, 'tests': []}
                with self.results_lock:
                    self.results[sub_id] = error_res
                
                # Save error result to file
                try:
                    res_path = os.path.join('submissions', f'result_{sub_id}.json')
                    with open(res_path, 'w') as f:
                        json.dump(error_res, f, indent=4)
                except:
                    pass

                # Still try to update contest_data.json so it doesn't stay "Judging"
                try:
                    data = self.contest_manager._load_data()
                    user_subs = data.get(task['username'], [])
                    for s in user_subs:
                        if s.get('id') == sub_id:
                            s['verdict'] = 'IE'
                            break
                    self.contest_manager._save_data(data)
                except:
                    pass
            
            self.queue.task_done()

    def get_result(self, sub_id):
        with self.results_lock:
            return self.results.get(sub_id)
