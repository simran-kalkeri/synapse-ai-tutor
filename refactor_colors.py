import os
import re

replacements = [
    # Backgrounds
    (r"background:\s*['\"]rgba\(26,\s*26,\s*46,\s*0\.7\)['\"]", "background: 'var(--glass-bg)'"),
    (r"background:\s*['\"]#1a1a2e['\"]", "background: 'var(--bg-card)'"),
    (r"background:\s*['\"]#0f0f23['\"]", "background: 'var(--bg-surface)'"),
    (r"background:\s*['\"]#0a0a1a['\"]", "background: 'var(--bg-base)'"),
    (r"background:\s*['\"]rgba\(255,\s*255,\s*255,\s*0\.0[234]5?\)['\"]", "background: 'var(--bg-hover)'"),
    (r"background:\s*['\"]rgba\(255,\s*255,\s*255,\s*0\.0[568]5?\)['\"]", "background: 'var(--border-subtle)'"),
    (r"background:\s*['\"]rgba\(124,\s*58,\s*237,\s*0\.[12]\d?\)['\"]", "background: 'var(--primary-subtle)'"),
    (r"backgroundColor:\s*['\"]rgba\(124,\s*58,\s*237,\s*0\.[12]\d?\)['\"]", "backgroundColor: 'var(--primary-subtle)'"),
    (r"background:\s*['\"]rgba\(16,\s*185,\s*129,\s*0\.[0-9]+?\)['\"]", "background: 'var(--success)'"),
    (r"background:\s*['\"]rgba\(239,\s*68,\s*68,\s*0\.[0-9]+?\)['\"]", "background: 'var(--danger)'"),
    (r"background:\s*['\"]linear-gradient\(135deg,\s*rgba\(124,58,237,0\.15\)\s*0%,\s*rgba\(6,182,212,0\.1\)\s*100%\)['\"]", "background: 'var(--glass-bg)'"),
    (r"background:\s*['\"]linear-gradient\(135deg,\s*#7c3aed,\s*#06b6d4\)['\"]", "background: 'linear-gradient(135deg, var(--primary), var(--primary-light))'"),
    (r"background:\s*['\"]linear-gradient\(135deg,#7c3aed,#06b6d4\)['\"]", "background: 'linear-gradient(135deg, var(--primary), var(--primary-light))'"),
    (r"background:\s*['\"]#7c3aed['\"]", "background: 'var(--primary)'"),
    
    # Borders
    (r"border:\s*['\"]1px solid rgba\(124,\s*58,\s*237,\s*0\.[1234]\d?\)['\"]", "border: '1px solid var(--border)'"),
    (r"border:\s*['\"]1px solid rgba\(255,\s*255,\s*255,\s*0\.0[56]5?\)['\"]", "border: '1px solid var(--border-subtle)'"),
    (r"borderTop:\s*['\"]1px solid rgba\(255,\s*255,\s*255,\s*0\.0[56]5?\)['\"]", "borderTop: '1px solid var(--border-subtle)'"),
    (r"borderBottom:\s*['\"]1px solid rgba\(255,\s*255,\s*255,\s*0\.0[56]5?\)['\"]", "borderBottom: '1px solid var(--border-subtle)'"),
    (r"borderColor:\s*['\"]rgba\(124,\s*58,\s*237,\s*0\.[1234]\d?\)['\"]", "borderColor: 'var(--border)'"),
    
    # Text Colors
    (r"color:\s*['\"]#f1f5f9['\"]", "color: 'var(--text-primary)'"),
    (r"color:\s*['\"]#e2e8f0['\"]", "color: 'var(--text-primary)'"),
    (r"color:\s*['\"]#94a3b8['\"]", "color: 'var(--text-secondary)'"),
    (r"color:\s*['\"]#64748b['\"]", "color: 'var(--text-muted)'"),
    (r"color:\s*['\"]#475569['\"]", "color: 'var(--text-muted)'"),
    (r"color:\s*['\"]#a78bfa['\"]", "color: 'var(--primary)'"),
    (r"color:\s*['\"]#7c3aed['\"]", "color: 'var(--primary)'"),
    (r"color:\s*['\"]#06b6d4['\"]", "color: 'var(--accent)'"),
    (r"color:\s*['\"]#10b981['\"]", "color: 'var(--success)'"),
    (r"color:\s*['\"]#f59e0b['\"]", "color: 'var(--warning)'"),
    (r"color:\s*['\"]#ef4444['\"]", "color: 'var(--danger)'"),
    
    # Shadows
    (r"boxShadow:\s*['\"]0 0 20px rgba\(124,\s*58,\s*237,\s*0\.4\)['\"]", "boxShadow: 'var(--shadow-sm)'"),
    (r"boxShadow:\s*['\"]0 4px 20px rgba\(0,\s*0,\s*0,\s*0\.5\)['\"]", "boxShadow: 'var(--shadow-md)'"),

    # Generic
    (r"rgba\(26,\s*26,\s*46,\s*0\.7\)", "var(--glass-bg)"),
    (r"rgba\(124,\s*58,\s*237,\s*0\.15\)", "var(--border)"),
]

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    for pattern, replacement in replacements:
        new_content = re.sub(pattern, replacement, new_content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

def process_dir(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.tsx', '.ts')):
                process_file(os.path.join(root, file))

if __name__ == '__main__':
    src_dir = os.path.join('d:\\college\\6th sem\\GEN AI\\synapse-ai-tutor\\frontend\\src')
    process_dir(src_dir)
