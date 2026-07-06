from pathlib import Path

CSS_APPEND = """
.profile-section-hint {
  margin: -0.5rem 0 1rem;
  font-size: 0.9rem;
  color: var(--muted);
  line-height: 1.45;
}

.profile-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 0.8rem;
  color: var(--muted);
}

.profile-stat strong {
  font-size: 1.15rem;
  color: var(--text);
}

.profile-optional {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  border: 1px dashed var(--border);
  border-radius: 8px;
  background: var(--bg);
}

.profile-optional summary {
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--muted);
}

.profile-optional-hint {
  margin: 0.5rem 0 0.75rem;
  font-size: 0.85rem;
  color: var(--muted);
}

.skill-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.skill-chip {
  display: flex;
  align-items: flex-start;
  gap: 0.35rem;
  max-width: 100%;
  padding: 0.5rem 0.65rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
}

.skill-chip-technical {
  border-color: #dbeafe;
  background: var(--accent-soft);
}

.skill-chip-soft {
  border-color: #d1fae5;
  background: #ecfdf5;
}

.skill-chip-body {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.skill-chip-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.skill-chip-meta {
  font-size: 0.75rem;
  color: var(--muted);
}

.skill-chip-desc {
  margin: 0.25rem 0 0;
  font-size: 0.8rem;
  color: var(--text);
  line-height: 1.35;
}

.skill-chip-remove {
  flex-shrink: 0;
  border: none;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  padding: 0.1rem 0.25rem;
  font-size: 0.85rem;
  line-height: 1;
}

.skill-chip-remove:hover {
  color: var(--danger, #dc2626);
}

@media (max-width: 700px) {
  .profile-page .page-head {
    flex-direction: column;
  }

  .profile-stats {
    flex-wrap: wrap;
    width: 100%;
  }

  .profile-stat {
    flex: 1;
    min-width: 70px;
  }
}
"""

p = Path("frontend/src/index.css")
text = p.read_text(encoding="utf-8")
if ".skill-chips" not in text:
    p.write_text(text.rstrip() + "\n" + CSS_APPEND, encoding="utf-8", newline="\n")
    print("CSS appended")
else:
    print("CSS already present")
