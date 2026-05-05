import { X } from "lucide-react";
import { useState, type KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Props {
  values: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
}

export function ListEditor({ values, onChange, placeholder }: Props) {
  const [draft, setDraft] = useState("");

  function add() {
    const v = draft.trim();
    if (!v) return;
    onChange([...values, v]);
    setDraft("");
  }

  function remove(idx: number) {
    onChange(values.filter((_, i) => i !== idx));
  }

  function onKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      add();
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {values.map((v, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1 rounded-full bg-secondary px-2 py-1 text-xs"
          >
            {v}
            <button
              type="button"
              onClick={() => remove(i)}
              className="text-muted-foreground hover:text-foreground"
              aria-label="Remover"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        {values.length === 0 && (
          <span className="text-xs text-muted-foreground">Vazio.</span>
        )}
      </div>
      <div className="flex gap-2">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKey}
          placeholder={placeholder}
        />
        <Button type="button" variant="outline" onClick={add}>
          Adicionar
        </Button>
      </div>
    </div>
  );
}
