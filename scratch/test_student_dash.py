import re
from app import create_app

app = create_app('development')
client = app.test_client()

r1 = client.get('/auth/login')
csrf_token = re.search(r'name="csrf_token"\s+value="([^"]+)"', r1.data.decode('utf-8')).group(1)
client.post('/auth/login', data={'csrf_token': csrf_token, 'email': 'demo@quiznova.com', 'password': 'Demo@Student1'}, follow_redirects=True)

r = client.get('/dashboard/')
html = r.get_data(as_text=True)
print('Dashboard Status Code:', r.status_code)
print('Chart.js included in HTML?:', 'chart.umd.min.js' in html)
print('Achievements page status:', client.get('/dashboard/achievements').status_code)
