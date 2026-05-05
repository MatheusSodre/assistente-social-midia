import { Plus, Save, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { ListEditor } from "@/components/marketing/ListEditor";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  brandMemoryApi,
  emptyPayload,
  useBrandMemoryList,
  type BrandMemory,
  type BrandMemoryPayload,
  type Persona,
} from "@/hooks/useBrandMemory";

export default function BrandMemoryPage() {
  const { items, loading, error, reload } = useBrandMemoryList();
  const [editing, setEditing] = useState<BrandMemory | null>(null);
  const [draft, setDraft] = useState<BrandMemoryPayload>(emptyPayload());
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    if (items.length && !editing) {
      setEditing(items[0]);
      setDraft(stripMeta(items[0]));
    }
  }, [items, editing]);

  function startNew() {
    setEditing(null);
    setDraft(emptyPayload());
  }

  function selectItem(item: BrandMemory) {
    setEditing(item);
    setDraft(stripMeta(item));
  }

  async function save() {
    setSaving(true);
    setSaveError(null);
    try {
      if (editing) {
        await brandMemoryApi.update(editing.id, draft);
      } else {
        await brandMemoryApi.create(draft);
      }
      await reload();
    } catch (e: unknown) {
      setSaveError(extractMsg(e));
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!editing) return;
    if (!confirm(`Apagar "${editing.name}"?`)) return;
    setSaving(true);
    try {
      await brandMemoryApi.remove(editing.id);
      setEditing(null);
      setDraft(emptyPayload());
      await reload();
    } catch (e: unknown) {
      setSaveError(extractMsg(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Brand Memory</h1>
          <p className="text-sm text-muted-foreground">
            Posicionamento, tom, visual e ICP que orientam todo conteúdo gerado.
          </p>
        </div>
        <Button onClick={startNew} variant="outline">
          <Plus className="mr-1 h-4 w-4" />
          Nova marca
        </Button>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="grid gap-6 lg:grid-cols-[260px,1fr]">
        <Card className="h-fit">
          <CardHeader>
            <CardTitle className="text-base">Marcas</CardTitle>
            <CardDescription>
              {loading ? "Carregando..." : `${items.length} cadastradas`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-1 px-3">
            {items.map((item) => (
              <button
                key={item.id}
                onClick={() => selectItem(item)}
                className={`w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
                  editing?.id === item.id
                    ? "bg-primary/10 text-primary"
                    : "hover:bg-accent/10"
                }`}
              >
                {item.name || "(sem nome)"}
              </button>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Identidade</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nome</Label>
                <Input
                  id="name"
                  value={draft.name}
                  onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="positioning">Posicionamento</Label>
                <Textarea
                  id="positioning"
                  rows={3}
                  value={draft.positioning ?? ""}
                  onChange={(e) =>
                    setDraft({ ...draft, positioning: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Pillars</Label>
                <ListEditor
                  values={draft.pillars}
                  onChange={(pillars) => setDraft({ ...draft, pillars })}
                  placeholder="Ex: Produtividade pra empreendedor"
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tom de Voz</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Estilo</Label>
                <Textarea
                  rows={2}
                  value={draft.tone_of_voice.style ?? ""}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      tone_of_voice: {
                        ...draft.tone_of_voice,
                        style: e.target.value,
                      },
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Do</Label>
                <ListEditor
                  values={draft.tone_of_voice.do}
                  onChange={(v) =>
                    setDraft({
                      ...draft,
                      tone_of_voice: { ...draft.tone_of_voice, do: v },
                    })
                  }
                  placeholder="O que SEMPRE fazer"
                />
              </div>
              <div className="space-y-2">
                <Label>Don't</Label>
                <ListEditor
                  values={draft.tone_of_voice.dont}
                  onChange={(v) =>
                    setDraft({
                      ...draft,
                      tone_of_voice: { ...draft.tone_of_voice, dont: v },
                    })
                  }
                  placeholder="O que NUNCA fazer"
                />
              </div>
              <div className="space-y-2">
                <Label>Exemplos</Label>
                <ListEditor
                  values={draft.tone_of_voice.examples}
                  onChange={(v) =>
                    setDraft({
                      ...draft,
                      tone_of_voice: { ...draft.tone_of_voice, examples: v },
                    })
                  }
                  placeholder="Frase exemplo do tom"
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Identidade Visual</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Cor primária</Label>
                  <Input
                    type="color"
                    value={draft.visual_identity.primary_color ?? "#FF6B2B"}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        visual_identity: {
                          ...draft.visual_identity,
                          primary_color: e.target.value,
                        },
                      })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>Cor secundária</Label>
                  <Input
                    type="color"
                    value={draft.visual_identity.secondary_color ?? "#080808"}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        visual_identity: {
                          ...draft.visual_identity,
                          secondary_color: e.target.value,
                        },
                      })
                    }
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Fontes</Label>
                <ListEditor
                  values={draft.visual_identity.fonts}
                  onChange={(fonts) =>
                    setDraft({
                      ...draft,
                      visual_identity: { ...draft.visual_identity, fonts },
                    })
                  }
                  placeholder="Ex: Inter"
                />
              </div>
              <div className="space-y-2">
                <Label>Logo URL</Label>
                <Input
                  value={draft.visual_identity.logo_url ?? ""}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      visual_identity: {
                        ...draft.visual_identity,
                        logo_url: e.target.value,
                      },
                    })
                  }
                  placeholder="https://..."
                />
              </div>
              <div className="space-y-2">
                <Label>Estilo visual (descrição em prosa)</Label>
                <Textarea
                  rows={3}
                  value={draft.visual_identity.style_description ?? ""}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      visual_identity: {
                        ...draft.visual_identity,
                        style_description: e.target.value,
                      },
                    })
                  }
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>ICP (Personas)</CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setDraft({
                    ...draft,
                    icp: [
                      ...draft.icp,
                      { name: "", role: "", pains: [], goals: [] },
                    ],
                  })
                }
              >
                <Plus className="mr-1 h-4 w-4" />
                Persona
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {draft.icp.map((p, idx) => (
                <PersonaCard
                  key={idx}
                  persona={p}
                  onChange={(next) => {
                    const icp = [...draft.icp];
                    icp[idx] = next;
                    setDraft({ ...draft, icp });
                  }}
                  onRemove={() =>
                    setDraft({
                      ...draft,
                      icp: draft.icp.filter((_, i) => i !== idx),
                    })
                  }
                />
              ))}
              {!draft.icp.length && (
                <p className="text-sm text-muted-foreground">
                  Sem personas. Clica em "Persona" pra adicionar.
                </p>
              )}
            </CardContent>
          </Card>

          {saveError && (
            <p className="text-sm text-destructive">{saveError}</p>
          )}
          <div className="flex items-center gap-2">
            <Button onClick={() => void save()} disabled={saving}>
              <Save className="mr-1 h-4 w-4" />
              {saving ? "Salvando..." : editing ? "Salvar" : "Criar"}
            </Button>
            {editing && (
              <Button
                onClick={() => void remove()}
                variant="destructive"
                disabled={saving}
              >
                <Trash2 className="mr-1 h-4 w-4" />
                Apagar
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function PersonaCard({
  persona,
  onChange,
  onRemove,
}: {
  persona: Persona;
  onChange: (p: Persona) => void;
  onRemove: () => void;
}) {
  return (
    <div className="rounded-md border border-border p-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Nome</Label>
          <Input
            value={persona.name}
            onChange={(e) => onChange({ ...persona, name: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label>Papel/Cargo</Label>
          <Input
            value={persona.role ?? ""}
            onChange={(e) => onChange({ ...persona, role: e.target.value })}
          />
        </div>
      </div>
      <div className="mt-3 space-y-2">
        <Label>Dores</Label>
        <ListEditor
          values={persona.pains}
          onChange={(pains) => onChange({ ...persona, pains })}
          placeholder="O que tira o sono"
        />
      </div>
      <div className="mt-3 space-y-2">
        <Label>Objetivos</Label>
        <ListEditor
          values={persona.goals}
          onChange={(goals) => onChange({ ...persona, goals })}
          placeholder="O que essa persona quer alcançar"
        />
      </div>
      <div className="mt-3 flex justify-end">
        <Button variant="ghost" size="sm" onClick={onRemove}>
          <Trash2 className="mr-1 h-4 w-4" />
          Remover persona
        </Button>
      </div>
    </div>
  );
}

function stripMeta(b: BrandMemory): BrandMemoryPayload {
  const { id: _id, tenant_id: _t, created_at: _c, updated_at: _u, ...rest } = b;
  return rest;
}

function extractMsg(e: unknown): string {
  if (e && typeof e === "object" && "detail" in e) {
    return String((e as { detail: unknown }).detail);
  }
  return e instanceof Error ? e.message : String(e);
}
