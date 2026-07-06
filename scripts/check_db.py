import sqlite3

c = sqlite3.connect("data/grew.db")
total = c.execute("select count(*) from offers where status != 'archived'").fetchone()[0]
vie = c.execute("select count(*) from offers where source='vie' and status != 'archived'").fetchone()[0]
by_source = c.execute("select source, count(*) from offers group by source").fetchall()
runs = c.execute(
    "select offers_found, offers_new, offers_duplicates, status from scrape_runs order by created_at desc limit 5"
).fetchall()
print("total", total, "vie", vie)
print("by_source", by_source)
for r in runs:
    print("run", r)
sample = c.execute("select url, source from offers limit 5").fetchall()
print("sample", sample)
