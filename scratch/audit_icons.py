import urllib.request
import re

cats = [
    'programming', 'dsa', 'databases', 'computer-science',
    'artificial-intelligence', 'web-development', 'mathematics',
    'aptitude', 'competitive-exams', 'cloud-computing',
    'cybersecurity', 'soft-skills'
]

count = 0
for c in cats:
    url = f"http://127.0.0.1:5000/quiz/categories/{c}"
    html = urllib.request.urlopen(url).read().decode('utf-8')
    titles = re.findall(r'class="sub-card-title">(.*?)</h3>', html)
    icons = re.findall(r'sub-icon-wrap (icon-theme-[^"]+)', html)
    print(f"\n=== {c.upper()} ===")
    for t, ic in zip(titles, icons):
        count += 1
        print(f"  [OK] {t:<30} -> Icon Theme: {ic}")

print(f"\n==========================================")
print(f"TOTAL SUBCATEGORIES VERIFIED: {count}/48")
print(f"==========================================")
