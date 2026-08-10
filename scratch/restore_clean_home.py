import json

log_path = r'C:\Users\Mahanthesh\.gemini\antigravity\brain\525615c5-3732-40ce-9fbf-ba71d96ecc8d\.system_generated\logs\transcript.jsonl'
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get('step_index') == 638:
            for call in obj.get('tool_calls', []):
                args = call.get('args', {})
                if 'home.html' in args.get('TargetFile', ''):
                    content = args['CodeContent']
                    # content is the exact unescaped string
                    
                    marquee_html = """<!-- Top Continuous Marquee Announcement Bar (Full Width) -->
{% if announcement_competitions %}
<div class="marquee-container" aria-label="Live Competition Announcements">
  <div class="marquee-track">
    {% for i in range(4) %}
      {% for comp in announcement_competitions %}
      <a href="{{ url_for('competitions.detail', slug=comp.slug) }}" class="marquee-item">
        <span class="badge badge-error" style="animation:pulseGlow 2s infinite;">🏆 CONTEST</span>
        <span>{{ comp.title }} — Registration Open (Prize: {{ comp.prize_pool_text | replace('$', '₹') }})</span>
        <span style="color:var(--brand-cyan);">View Details →</span>
      </a>
      <span style="color:rgba(255,255,255,0.2);">•</span>
      {% endfor %}
    {% endfor %}
  </div>
</div>
{% endif %}

"""
                    full_content = content.replace('{% block content %}\n\n', '{% block content %}\n\n' + marquee_html)
                    with open('templates/home.html', 'w', encoding='utf-8') as out:
                        out.write(full_content)
                    print('Successfully restored clean home.html template!')
