from pathlib import Path

p = Path("frontend/src/index.css")
raw = p.read_bytes()
if b"\x00" in raw:
    t = raw.decode("utf-16-le")
else:
    t = raw.decode("utf-8")

old = """/* Forms */
.scrape-form label {
  display: block;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--muted);
}

.scrape-form input,
.scrape-form textarea,
.search-input,
.toolbar select {
  display: block;
  width: 100%;
  margin-top: 0.35rem;
  padding: 0.6rem 0.85rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 0.95rem;
  font-family: inherit;
  background: var(--surface);
  color: var(--text);
  transition: border-color 0.15s;
}

.scrape-form input:focus,
.scrape-form textarea:focus,
.search-input:focus,
.toolbar select:focus {
  outline: none;
  border-color: var(--accent);
}"""

new = """/* Forms */
.scrape-form label,
.profile-section > label,
.profile-section .form-row > label,
.profile-add-form > label {
  display: block;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--muted);
}

.scrape-form input,
.scrape-form textarea,
.profile-section input:not([type="checkbox"]),
.profile-section textarea,
.profile-add-form textarea,
.search-input,
.toolbar select {
  display: block;
  width: 100%;
  margin-top: 0.35rem;
  padding: 0.6rem 0.85rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 0.95rem;
  font-family: inherit;
  background: var(--surface);
  color: var(--text);
  transition: border-color 0.15s;
  box-sizing: border-box;
}

.scrape-form input:focus,
.scrape-form textarea:focus,
.profile-section input:not([type="checkbox"]):focus,
.profile-section textarea:focus,
.search-input:focus,
.toolbar select:focus {
  outline: none;
  border-color: var(--accent);
}"""

if old in t:
    t = t.replace(old, new)
    p.write_text(t, encoding="utf-8", newline="\n")
    print("fixed")
else:
    print("pattern not found", ".profile-section > label" in t)
