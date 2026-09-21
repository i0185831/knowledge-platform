import json
import os
from datetime import datetime
import uuid

class ExampleManager:
    def __init__(self, data_dir="data/examples"):
        self.data_dir = data_dir
        self.examples_file = os.path.join(data_dir, "examples.json")
        self._ensure_data_dir()
        self.examples = self._load_examples()
    
    def _ensure_data_dir(self):
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.examples_file):
            with open(self.examples_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def _load_examples(self):
        try:
            with open(self.examples_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _save_examples(self):
        with open(self.examples_file, 'w', encoding='utf-8') as f:
            json.dump(self.examples, f, ensure_ascii=False, indent=2)
    
    def add_example(self, title, problem, solution, category="未分类", difficulty_level="中等"):
        example = {
            "id": str(uuid.uuid4()),
            "title": title,
            "problem": problem,
            "solution": solution,
            "category": category,
            "difficulty_level": difficulty_level,
            "is_reviewed": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self.examples.append(example)
        self._save_examples()
        return example
    
    def get_example(self, example_id):
        for example in self.examples:
            if example["id"] == example_id:
                return example
        return None
    
    def get_all_examples(self):
        return sorted(self.examples, key=lambda x: x["created_at"], reverse=True)
    
    def update_example(self, example_id, **kwargs):
        for example in self.examples:
            if example["id"] == example_id:
                example.update(kwargs)
                example["updated_at"] = datetime.now().isoformat()
                self._save_examples()
                return example
        return None
    
    def delete_example(self, example_id):
        self.examples = [e for e in self.examples if e["id"] != example_id]
        self._save_examples()
    
    def toggle_reviewed(self, example_id):
        for example in self.examples:
            if example["id"] == example_id:
                example["is_reviewed"] = not example.get("is_reviewed", False)
                example["updated_at"] = datetime.now().isoformat()
                self._save_examples()
                return example
        return None
    
    def search_examples(self, query):
        query = query.lower()
        return [e for e in self.examples 
                if query in e["title"].lower() 
                or query in e["problem"].lower() 
                or query in e["solution"].lower()]
    
    def get_by_category(self, category):
        return [e for e in self.examples if e.get("category") == category]
    
    def get_by_difficulty(self, difficulty_level):
        return [e for e in self.examples if e.get("difficulty_level") == difficulty_level]
    
    def get_categories(self):
        return list(set(e.get("category", "未分类") for e in self.examples))
    
    def get_statistics(self):
        total = len(self.examples)
        reviewed = sum(1 for e in self.examples if e.get("is_reviewed"))
        
        by_category = {}
        for example in self.examples:
            cat = example.get("category", "未分类")
            by_category[cat] = by_category.get(cat, 0) + 1
        
        by_difficulty = {}
        for example in self.examples:
            diff = example.get("difficulty_level", "未知")
            by_difficulty[diff] = by_difficulty.get(diff, 0) + 1
        
        return {
            "total": total,
            "reviewed": reviewed,
            "by_category": by_category,
            "by_difficulty": by_difficulty
        }