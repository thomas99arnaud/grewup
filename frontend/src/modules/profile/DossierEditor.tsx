import { KeyboardEvent, useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { api } from "../../shared/api";

type EditorRow = { key: string; cells: string[] };

function newKey() {
  return crypto.randomUUID();
}

function columnCount(rows: string[][]) {
  const widest = Math.max(0, ...rows.map((row) => row.length));
  return widest > 0 ? widest : 2;
}

function toEditorRows(rows: string[][]): EditorRow[] {
  const cols = columnCount(rows);
  const mapped = rows.map((cells) => ({
    key: newKey(),
    cells: [...cells, ...Array(Math.max(0, cols - cells.length)).fill("")],
  }));
  return mapped.length > 0 ? mapped : [{ key: newKey(), cells: Array(cols).fill("") }];
}

function WordCell({
  value,
  onChange,
  onTab,
}: {
  value: string;
  onChange: (value: string) => void;
  onTab?: () => void;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = `${el.scrollHeight}px`;
  }, [value]);

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Tab" && !event.shiftKey && onTab) {
      event.preventDefault();
      onTab();
    }
  };

  return (
    <textarea
      ref={ref}
      rows={1}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      onKeyDown={onKeyDown}
    />
  );
}

export function DossierEditor({
  onError,
}: {
  onError?: (message: string | null) => void;
}) {
  const [rows, setRows] = useState<EditorRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const dirtyRef = useRef(false);
  const rowsRef = useRef<EditorRow[]>([]);
  const updatedAtRef = useRef<string | null>(null);
  const saveTimer = useRef<number | null>(null);

  const applyRemote = useCallback((data: { rows: string[][]; updated_at: string | null }) => {
    const next = toEditorRows(data.rows);
    setRows(next);
    rowsRef.current = next;
    updatedAtRef.current = data.updated_at;
    dirtyRef.current = false;
  }, []);

  const load = useCallback(
    async (quiet = false) => {
      if (!quiet) setLoading(true);
      try {
        const data = await api.getDossier();
        applyRemote(data);
        onError?.(null);
      } catch (err) {
        if (!quiet) onError?.(err instanceof Error ? err.message : "Erreur");
      } finally {
        if (!quiet) setLoading(false);
      }
    },
    [applyRemote, onError],
  );

  useEffect(() => {
    load();
  }, [load]);

  const save = useCallback(async () => {
    if (!dirtyRef.current) return;
    setSaving(true);
    try {
      const payload = rowsRef.current.map((row) => row.cells.map((cell) => cell.trimEnd()));
      const data = await api.updateDossier(payload);
      updatedAtRef.current = data.updated_at;
      dirtyRef.current = false;
      onError?.(null);
    } catch (err) {
      onError?.(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSaving(false);
    }
  }, [onError]);

  const scheduleSave = useCallback(() => {
    if (saveTimer.current) window.clearTimeout(saveTimer.current);
    saveTimer.current = window.setTimeout(() => {
      void save();
    }, 800);
  }, [save]);

  useEffect(() => {
    const timer = window.setInterval(async () => {
      if (dirtyRef.current) return;
      try {
        const data = await api.getDossier();
        if (data.updated_at && data.updated_at !== updatedAtRef.current) {
          applyRemote(data);
        }
      } catch {
        /* ignore polling errors */
      }
    }, 4000);
    return () => window.clearInterval(timer);
  }, [applyRemote]);

  useEffect(() => {
    const onKey = (event: globalThis.KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        if (saveTimer.current) window.clearTimeout(saveTimer.current);
        void save();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [save]);

  useEffect(() => {
    return () => {
      if (saveTimer.current) window.clearTimeout(saveTimer.current);
    };
  }, []);

  const markDirty = (next: EditorRow[]) => {
    setRows(next);
    rowsRef.current = next;
    dirtyRef.current = true;
    scheduleSave();
  };

  if (loading) return <p className="empty word-loading">Ouverture du document…</p>;

  const cols = rows[0]?.cells.length || 2;

  const setCell = (rowIndex: number, colIndex: number, value: string) => {
    markDirty(
      rows.map((item, i) =>
        i === rowIndex
          ? { ...item, cells: item.cells.map((cell, j) => (j === colIndex ? value : cell)) }
          : item,
      ),
    );
  };

  const addRow = () => {
    markDirty([...rows, { key: newKey(), cells: Array(cols).fill("") }]);
  };

  const addColumn = () => {
    markDirty(rows.map((row) => ({ ...row, cells: [...row.cells, ""] })));
  };

  const removeColumn = (colIndex: number) => {
    if (cols <= 1) return;
    markDirty(rows.map((row) => ({ ...row, cells: row.cells.filter((_, j) => j !== colIndex) })));
  };

  return (
    <div className="word-sheet">
      <div className="word-table-shell">
        <div className="word-col-tools" aria-hidden={cols <= 1}>
          {Array.from({ length: cols }, (_, index) => (
            <button
              key={index}
              type="button"
              className="word-ghost"
              title="Supprimer la colonne"
              disabled={cols <= 1}
              onClick={() => removeColumn(index)}
            >
              ✕
            </button>
          ))}
        </div>
        <table className="dossier-grid">
          <colgroup>
            {Array.from({ length: cols }, (_, index) => (
              <col key={index} className={index === 0 && cols === 2 ? "dossier-col-first" : undefined} />
            ))}
          </colgroup>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={row.key}>
                {row.cells.map((cell, colIndex) => (
                  <td key={colIndex}>
                    <WordCell
                      value={cell}
                      onChange={(value) => setCell(rowIndex, colIndex, value)}
                      onTab={
                        rowIndex === rows.length - 1 && colIndex === cols - 1 ? addRow : undefined
                      }
                    />
                  </td>
                ))}
                <td className="word-row-tool">
                  <button
                    type="button"
                    className="word-ghost"
                    title="Supprimer la ligne"
                    onClick={() => markDirty(rows.filter((_, i) => i !== rowIndex))}
                  >
                    ✕
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <button type="button" className="word-add-col" title="Ajouter une colonne" onClick={addColumn}>
          +
        </button>
        <button type="button" className="word-add-row" title="Ajouter une ligne" onClick={addRow}>
          +
        </button>
      </div>
      {saving && <span className="word-status">Enregistrement…</span>}
    </div>
  );
}
