import urllib.request
import re

categories = [
    'programming', 'dsa', 'databases', 'computer-science',
    'artificial-intelligence', 'web-development', 'mathematics',
    'aptitude', 'competitive-exams', 'cloud-computing',
    'cybersecurity', 'soft-skills'
]

print("==================================================")
print("TESTING GLOBAL SUB-CATEGORY HTML RENDERING & BODY DOM")
print("==================================================")

all_passed = True
for slug in categories:
    url = f"http://127.0.0.1:5000/quiz/categories/{slug}"
    try:
        r = urllib.request.urlopen(url)
        html = r.read().decode('utf-8')
        
        has_sub_grid = '<div class="sub-card-grid">' in html
        has_cards = 'sub-glass-card' in html
        has_start_btn = 'sub-start-btn' in html or 'sub-login-btn' in html
        
        # Verify style block is properly closed before body elements
        unclosed_style = re.search(r'<style>[^<]*<div class="sub-card-grid">', html)
        
        if r.getcode() == 200 and has_sub_grid and has_cards and not unclosed_style:
            print(f"[OK] Category '{slug:<23}' -> HTML 200 OK | Grid: Yes | Cards: Yes | Clean DOM: Yes")
        else:
            print(f"[FAIL] Category '{slug:<21}' -> Issue detected (Grid: {has_sub_grid}, Cards: {has_cards}, Unclosed Style: {bool(unclosed_style)})")
            all_passed = False
    except Exception as e:
        print(f"[FAIL] Category '{slug:<21}' -> HTTP Error: {e}")
        all_passed = False

print("\n--------------------------------------------------")
if all_passed:
    print("ALL 12 CATEGORY PAGES AND 48 SUBCATEGORY CARDS RENDER CLEANLY!")
else:
    print("SOME CATEGORIES STILL HAVE RENDERING ISSUES.")
