import threading
import queue
import time
import os

class SubmissionQueue:
    def __init__(self, validator, contest_manager):
        self.validator = validator
        self.contest_manager = contest_manager
        self.queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        self.results = {} # sub_id -> result

    def add_submission(self, sub_id, username, source_path, contest_id, problem_id):
        self.results[sub_id] = {'status': 'Queued', 'verdict': 'In Queue'}
        self.queue.put({
            'sub_id': sub_id,
            'username': username,
            'source_path': source_path,
            'contest_id': contest_id,
            'problem_id': problem_id
        })

    def _worker(self):
        while True:
            task = self.queue.get()
            if task is None: break
            
            sub_id = task['sub_id']
            self.results[sub_id]['status'] = 'Judging'
            self.results[sub_id]['verdict'] = 'Judging'
            self.results[sub_id]['tests'] = []
            
            def update_progress(partial_result):
                self.results[sub_id].update(partial_result)

            try:
                result = self.validator.judge_submission(
                    task['source_path'], 
                    task['contest_id'], 
                    task['problem_id'], 
                    max_points=100,
                    on_test_complete=update_progress
                )
                
                # Update in file
                data = self.contest_manager._load_data()
                user_subs = data.get(task['username'], [])
                for s in user_subs:
                    if s.get('id') == sub_id:
                        s['verdict'] = result['verdict']
                        s['score'] = result['score']
                        break
                self.contest_manager._save_data(data)
                
                self.results[sub_id] = result
                self.results[sub_id]['status'] = 'Finished'
            except Exception as e:
                self.results[sub_id] = {'status': 'Error', 'verdict': 'IE', 'details': str(e)}
            
            self.queue.task_done()

    def get_result(self, sub_id):
        return self.results.get(sub_id)
