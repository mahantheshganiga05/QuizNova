import sys

with open('scratch/full_home_638.html', 'r', encoding='utf-8') as f:
    orig = f.read()

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

full_content = orig.replace('{% block content %}\n\n', '{% block content %}\n\n' + marquee_html)

with open('templates/home.html', 'w', encoding='utf-8') as out:
    out.write(full_content)

print('Successfully restored home.html with full-width dynamic marquee!')
