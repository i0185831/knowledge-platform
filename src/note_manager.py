"""
笔记管理核心模块
功能：增删改查、分类、标签、时间线
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class NoteManager:
    def __init__(self, data_dir: str = "data/notes"):
        self.data_dir = data_dir
        self.notes_file = os.path.join(data_dir, "notes.json")
        self.notes = self._load_notes()

    def _load_notes(self) -> List[Dict]:
        """加载笔记数据"""
        if os.path.exists(self.notes_file):
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_notes(self):
        """保存笔记数据"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.notes_file, 'w', encoding='utf-8') as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=2)

    def add_note(self, title: str, content: str, category: str, tags: List[str] = None) -> Dict:
        """添加新笔记"""
        note = {
            "id": len(self.notes) + 1,
            "title": title,
            "content": content,
            "category": category,
            "tags": tags or [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.notes.append(note)
        self._save_notes()
        return note

    def get_note(self, note_id: int) -> Optional[Dict]:
        """获取单条笔记"""
        for note in self.notes:
            if note["id"] == note_id:
                return note
        return None

    def update_note(self, note_id: int, title: str = None, content: str = None,
                   category: str = None, tags: List[str] = None) -> bool:
        """更新笔记"""
        note = self.get_note(note_id)
        if not note:
            return False

        if title:
            note["title"] = title
        if content:
            note["content"] = content
        if category:
            note["category"] = category
        if tags is not None:
            note["tags"] = tags

        note["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_notes()
        return True

    def delete_note(self, note_id: int) -> bool:
        """删除笔记"""
        for i, note in enumerate(self.notes):
            if note["id"] == note_id:
                self.notes.pop(i)
                self._save_notes()
                return True
        return False

    def get_all_notes(self) -> List[Dict]:
        """获取所有笔记"""
        return self.notes

    def get_notes_by_category(self, category: str) -> List[Dict]:
        """按分类获取笔记"""
        return [note for note in self.notes if note["category"] == category]

    def get_notes_by_tag(self, tag: str) -> List[Dict]:
        """按标签获取笔记"""
        return [note for note in self.notes if tag in note["tags"]]

    def search_notes(self, keyword: str) -> List[Dict]:
        """搜索笔记（标题和内容）"""
        keyword = keyword.lower()
        results = []
        for note in self.notes:
            if (keyword in note["title"].lower() or
                keyword in note["content"].lower()):
                results.append(note)
        return results

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set(note["category"] for note in self.notes)
        return sorted(list(categories))

    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        tags = set()
        for note in self.notes:
            tags.update(note["tags"])
        return sorted(list(tags))

    def get_timeline(self, limit: int = None) -> List[Dict]:
        """获取时间线（按创建时间倒序）"""
        sorted_notes = sorted(self.notes,
                            key=lambda x: x["created_at"],
                            reverse=True)
        if limit:
            return sorted_notes[:limit]
        return sorted_notes

    def get_stats(self) -> Dict:
        """获取统计数据"""
        stats = {
            "total_notes": len(self.notes),
            "categories": {},
            "tags": {},
            "recent_activity": []
        }

        for note in self.notes:
            cat = note["category"]
            stats["categories"][cat] = stats["categories"].get(cat, 0) + 1

        for note in self.notes:
            for tag in note["tags"]:
                stats["tags"][tag] = stats["tags"].get(tag, 0) + 1

        stats["recent_activity"] = self.get_timeline(limit=10)

        return stats