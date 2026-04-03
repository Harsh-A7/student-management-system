"""
Student Management System
Technologies: Python, File Handling, OOP
Features: Add, View, Search, Delete student records with JSON-based persistent storage
"""

import json
import os
from datetime import datetime


# ─────────────────────────────────────────────
#  Data Model
# ─────────────────────────────────────────────

class Student:
    """Represents a single student record."""

    def __init__(self, student_id: str, name: str, age: int,
                 grade: str, email: str, enrolled_date: str = None):
        self.student_id   = student_id
        self.name         = name
        self.age          = age
        self.grade        = grade
        self.email        = email
        self.enrolled_date = enrolled_date or datetime.today().strftime("%Y-%m-%d")

    # ── Serialisation ──────────────────────────
    def to_dict(self) -> dict:
        return {
            "student_id":    self.student_id,
            "name":          self.name,
            "age":           self.age,
            "grade":         self.grade,
            "email":         self.email,
            "enrolled_date": self.enrolled_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        return cls(
            student_id    = data["student_id"],
            name          = data["name"],
            age           = data["age"],
            grade         = data["grade"],
            email         = data["email"],
            enrolled_date = data.get("enrolled_date"),
        )

    # ── Display ────────────────────────────────
    def display(self) -> str:
        return (
            f"\n{'─'*45}\n"
            f"  ID       : {self.student_id}\n"
            f"  Name     : {self.name}\n"
            f"  Age      : {self.age}\n"
            f"  Grade    : {self.grade}\n"
            f"  Email    : {self.email}\n"
            f"  Enrolled : {self.enrolled_date}\n"
            f"{'─'*45}"
        )


# ─────────────────────────────────────────────
#  File / Storage Layer
# ─────────────────────────────────────────────

class StudentRepository:
    """Handles all file I/O using JSON for persistent storage."""

    def __init__(self, filepath: str = "students.json"):
        self.filepath = filepath
        self._ensure_file()

    # ── Internal helpers ───────────────────────
    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w") as f:
                json.dump([], f)

    def _load(self) -> list[dict]:
        with open(self.filepath, "r") as f:
            return json.load(f)

    def _save(self, records: list[dict]):
        with open(self.filepath, "w") as f:
            json.dump(records, f, indent=4)

    # ── CRUD operations ────────────────────────
    def get_all(self) -> list[Student]:
        return [Student.from_dict(r) for r in self._load()]

    def get_by_id(self, student_id: str) -> Student | None:
        for r in self._load():
            if r["student_id"] == student_id:
                return Student.from_dict(r)
        return None

    def id_exists(self, student_id: str) -> bool:
        return any(r["student_id"] == student_id for r in self._load())

    def add(self, student: Student) -> bool:
        if self.id_exists(student.student_id):
            return False
        records = self._load()
        records.append(student.to_dict())
        self._save(records)
        return True

    def delete(self, student_id: str) -> bool:
        records = self._load()
        new_records = [r for r in records if r["student_id"] != student_id]
        if len(new_records) == len(records):
            return False
        self._save(new_records)
        return True

    def search_by_name(self, keyword: str) -> list[Student]:
        kw = keyword.lower()
        return [Student.from_dict(r) for r in self._load()
                if kw in r["name"].lower()]

    def update(self, student: Student) -> bool:
        records = self._load()
        for i, r in enumerate(records):
            if r["student_id"] == student.student_id:
                records[i] = student.to_dict()
                self._save(records)
                return True
        return False


# ─────────────────────────────────────────────
#  Business / Service Layer
# ─────────────────────────────────────────────

class StudentService:
    """Encapsulates business logic and validation."""

    VALID_GRADES = {"A", "B", "C", "D", "F"}

    def __init__(self, repo: StudentRepository):
        self.repo = repo

    def add_student(self, student_id, name, age, grade, email) -> tuple[bool, str]:
        if not student_id or not name or not email:
            return False, "ID, name, and email are required."
        if not isinstance(age, int) or age <= 0 or age > 120:
            return False, "Age must be a positive integer (1–120)."
        if grade.upper() not in self.VALID_GRADES:
            return False, f"Grade must be one of: {', '.join(sorted(self.VALID_GRADES))}."
        if "@" not in email:
            return False, "Email address appears invalid."
        if self.repo.id_exists(student_id):
            return False, f"Student ID '{student_id}' already exists."

        student = Student(student_id, name, age, grade.upper(), email)
        self.repo.add(student)
        return True, "Student added successfully."

    def view_all(self) -> list[Student]:
        return self.repo.get_all()

    def search(self, keyword: str) -> list[Student]:
        return self.repo.search_by_name(keyword)

    def delete_student(self, student_id: str) -> tuple[bool, str]:
        if self.repo.delete(student_id):
            return True, f"Student '{student_id}' deleted successfully."
        return False, f"No student found with ID '{student_id}'."

    def update_student(self, student_id, name, age, grade, email) -> tuple[bool, str]:
        existing = self.repo.get_by_id(student_id)
        if not existing:
            return False, f"No student found with ID '{student_id}'."
        if not isinstance(age, int) or age <= 0:
            return False, "Age must be a positive integer."
        if grade.upper() not in self.VALID_GRADES:
            return False, f"Grade must be one of: {', '.join(sorted(self.VALID_GRADES))}."
        updated = Student(student_id, name, age, grade.upper(), email,
                          existing.enrolled_date)
        self.repo.update(updated)
        return True, "Student record updated successfully."


# ─────────────────────────────────────────────
#  UI / Console Layer
# ─────────────────────────────────────────────

class ConsoleUI:
    """Menu-driven console interface."""

    BANNER = r"""
  ╔══════════════════════════════════════════════╗
  ║       STUDENT  MANAGEMENT  SYSTEM           ║
  ║          Python · OOP · JSON Storage        ║
  ╚══════════════════════════════════════════════╝"""

    MENU = """
  ┌─────────────────────────────┐
  │  1. Add Student             │
  │  2. View All Students       │
  │  3. Search Student by Name  │
  │  4. Delete Student          │
  │  5. Update Student          │
  │  6. Exit                    │
  └─────────────────────────────┘"""

    def __init__(self, service: StudentService):
        self.service = service

    # ── Utilities ──────────────────────────────
    @staticmethod
    def _input(prompt: str) -> str:
        return input(f"  {prompt}").strip()

    @staticmethod
    def _print(msg: str):
        print(f"\n  {msg}")

    @staticmethod
    def _int_input(prompt: str) -> int | None:
        try:
            return int(input(f"  {prompt}").strip())
        except ValueError:
            return None

    # ── Handlers ───────────────────────────────
    def _handle_add(self):
        print("\n  ── Add New Student ──")
        sid   = self._input("Student ID   : ")
        name  = self._input("Full Name    : ")
        age   = self._int_input("Age          : ")
        grade = self._input("Grade (A-F)  : ")
        email = self._input("Email        : ")

        ok, msg = self.service.add_student(sid, name, age, grade, email)
        self._print(f"{'✔' if ok else '✘'}  {msg}")

    def _handle_view(self):
        students = self.service.view_all()
        if not students:
            self._print("No student records found.")
            return
        print(f"\n  Total records: {len(students)}")
        for s in students:
            print(s.display())

    def _handle_search(self):
        keyword = self._input("Enter name to search: ")
        results = self.service.search(keyword)
        if not results:
            self._print(f"No students found matching '{keyword}'.")
            return
        print(f"\n  {len(results)} result(s) found:")
        for s in results:
            print(s.display())

    def _handle_delete(self):
        sid = self._input("Enter Student ID to delete: ")
        ok, msg = self.service.delete_student(sid)
        self._print(f"{'✔' if ok else '✘'}  {msg}")

    def _handle_update(self):
        sid = self._input("Enter Student ID to update: ")
        existing = self.service.repo.get_by_id(sid)
        if not existing:
            self._print(f"✘  No student found with ID '{sid}'.")
            return
        print(existing.display())
        print("\n  Enter new details (press Enter to keep current):")

        name  = self._input(f"Full Name    [{existing.name}]: ") or existing.name
        age_s = self._input(f"Age          [{existing.age}]: ")
        age   = int(age_s) if age_s.isdigit() else existing.age
        grade = self._input(f"Grade (A-F)  [{existing.grade}]: ") or existing.grade
        email = self._input(f"Email        [{existing.email}]: ") or existing.email

        ok, msg = self.service.update_student(sid, name, age, grade, email)
        self._print(f"{'✔' if ok else '✘'}  {msg}")

    # ── Main loop ──────────────────────────────
    def run(self):
        print(self.BANNER)
        handlers = {
            "1": self._handle_add,
            "2": self._handle_view,
            "3": self._handle_search,
            "4": self._handle_delete,
            "5": self._handle_update,
        }
        while True:
            print(self.MENU)
            choice = self._input("Select an option (1-6): ")
            if choice == "6":
                self._print("Goodbye! 👋")
                break
            elif choice in handlers:
                handlers[choice]()
            else:
                self._print("✘  Invalid option. Please choose 1–6.")


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────

def main():
    repo    = StudentRepository("students.json")
    service = StudentService(repo)
    ui      = ConsoleUI(service)
    ui.run()


if __name__ == "__main__":
    main()
