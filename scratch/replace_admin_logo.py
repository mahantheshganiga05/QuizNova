import os
import re

new_logo = '''<div class="sidebar-logo-mark" style="width:34px;height:34px;border-radius:10px;overflow:hidden;flex-shrink:0;display:flex;align-items:center;justify-content:center;">
        <img src="{{ url_for('static', filename='images/quiznova_logo.jpg') }}" alt="QuizNova Logo" style="width:34px;height:34px;object-fit:cover;border-radius:10px;">
      </div>
      <span class="sidebar-logo-text font-display" style="font-weight:800;color:white;">Quiz<span style="background:linear-gradient(135deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">Nova</span> <span style="font-size:10px;color:var(--brand-purple-light);background:rgba(124,58,237,0.2);padding:2px 6px;border-radius:4px;vertical-align:middle;margin-left:4px;">ADMIN</span></span>'''

logo_pattern = re.compile(r'<div class="sidebar-logo-mark".*?</div>\s*<span class="sidebar-logo-text.*?</span>', re.DOTALL)

for root, dirs, files in os.walk('templates/admin'):
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                content = fp.read()
            if '>Q</div>' in content or 'QuizNova Admin' in content or 'alt="Q"' in content:
                new_content = logo_pattern.sub(new_logo, content)
                with open(path, 'w', encoding='utf-8') as fp:
                    fp.write(new_content)
                print('Updated logo in:', path)
