import re
import requests
from bs4 import BeautifulSoup

class CourseValidator:
    def __init__(self, roadmap, completed):
        self.roadmap = [[str(c).strip().lstrip('0') for c in sem] for sem in roadmap]
        self.taken = {str(c).strip().lstrip('0') for c in completed}
        self.errors = []
        self.course_name_cache = {}

    def get_course_data(self, course_id):
        # Cache to avoid hitting the same course page multiple times (saving time)
        if course_id in self.course_name_cache:
            return self.course_name_cache[course_id]

        api_url = f"https://students.technion.ac.il/local/technionsearch/course/{course_id}?lang=en"
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code != 200:
                return f"ID {course_id}", []

            soup = BeautifulSoup(response.text, 'html.parser')
            breadcrumb_ol = soup.find('ol', class_='breadcrumb')
            course_name = breadcrumb_ol.find_all('li')[-1].get_text(strip=True) if breadcrumb_ol else f"ID {course_id}"

            general_info = soup.find('div', id='general_information')
            if not general_info:
                self.course_name_cache[course_id] = (course_name, [])
                return course_name, []

            dependencies = []
            header = general_info.find('h5', string=re.compile(r'Pre-required|Pre-requisite', re.I))
            
            if header:
                found_ids = []
                content_text = ""
                curr = header.next_sibling
                while curr and curr.name not in ['h5', 'hr']:
                    if hasattr(curr, 'find_all'):
                        links = curr.find_all('a', attrs={'data-course': True})
                        found_ids.extend([l['data-course'].strip().lstrip('0') for l in links])
                        content_text += curr.get_text().lower()
                    curr = curr.next_sibling
                
                if found_ids:
                    # Logic for OR (e.g. Logic A or Logic B)
                    if " or " in content_text or " או " in content_text:
                        dependencies.append(("OR", list(set(found_ids))))
                    else:
                        for fid in set(found_ids):
                            dependencies.append(("AND", [fid]))

            self.course_name_cache[course_id] = (course_name, dependencies)
            return course_name, dependencies
        except:
            return f"ID {course_id}", []

    def run(self):
        for i, semester in enumerate(self.roadmap, 1):
            print(f"--- Checking Semester {i} ---")
            for course_id in semester:
                name, deps = self.get_course_data(course_id)
                print(f"🔍 {name}")
                
                passed_reqs = []
                missing_reqs = []

                for logic, ids in deps:
                    if logic == "AND":
                        req_id = ids[0]
                        req_name, _ = self.get_course_data(req_id)
                        full_info = f"{req_name} ({req_id})"
                        if req_id in self.taken:
                            passed_reqs.append(full_info)
                        else:
                            missing_reqs.append(full_info)
                    
                    elif logic == "OR":
                        choice_names = [f"{self.get_course_data(rid)[0]} ({rid})" for rid in ids]
                        if any(rid in self.taken for rid in ids):
                            passed_reqs.append(f"OR choice met: {choice_names}")
                        else:
                            missing_reqs.append(f"Missing one of: {choice_names}")

                # Output formatting
                if passed_reqs:
                    print(f"   ✅ Passed: {passed_reqs}")
                if missing_reqs:
                    print(f"   ❌ Missing: {missing_reqs}")
                    for m in missing_reqs:
                        self.errors.append(f"Sem {i} | {name} requires {m}")
                if not passed_reqs and not missing_reqs:
                    print(f"   ✅ No prerequisites found.")

            self.taken.update(semester)
            print(f"Semester {i} done.\n")
        self.summary()

    def summary(self):
        print("\n" + "="*50 + "\nFINAL REPORT\n" + "="*50)
        if not self.errors:
            print("🎉 PLAN IS VALID.")
        else:
            for e in self.errors: print(f" - {e}")

# --- UPDATED DATA ---
# Added Intro to CS (234114) and Data Structures 1 (234218)
# Also assuming you did Discrete Math (234129) as it blocks Logic/Theory
past_completed = [
    "234114", # Intro to CS
    "234218", # Data Structures 1
    "234129", # Discrete Mathematics
    "104031", # Infi 1
    "104032", # Infi 2
    "104016",  # Algebra 1
    "234247", # Algorithms 1 
    "234118", # Computer Organization and Programming 
    "234124", # Introduction to Systems Programming 
    "234125"  # numerical algos
] 
my_roadmap = [
    ["234123", "236267", "236343", "234292"],           # Sem 1: Theory Foundations
    ["236501", "236334", "236363", "134058", "236013"], # Sem 2: Systems & AI Base
    ["236756", "236342", "236360", "236322", "236350"], # Sem 3: ML Theory & Security
    ["236370", "236009", "236422", "236341", "236491"], # Sem 4: Kernel & Distributed ML
    ["236351", "236278", "236345", "236371", "104033"], # Sem 5: Accelerators & Verification
    ["236781", "236509", "236755", "236366", "236005"]  # Sem 6: The Capstone
]

if __name__ == "__main__":
    v = CourseValidator(my_roadmap, past_completed)
    v.run()
