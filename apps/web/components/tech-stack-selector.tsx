"use client";
import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { api } from "@/lib/api";

interface Props {
  selectedField: string;
  selectedStacks: string[];
  onFieldChange: (field: string) => void;
  onStacksChange: (stacks: string[]) => void;
}

export function TechStackSelector({ selectedField, selectedStacks, onFieldChange, onStacksChange }: Props) {
  const [fields, setFields] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [custom, setCustom] = useState("");

  useEffect(() => {
    api.techFields().then(setFields).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedField) { setSuggestions([]); return; }
    api.techStacks(selectedField).then((data) => {
      setSuggestions(Array.isArray(data) ? data : []);
    }).catch(() => setSuggestions([]));
  }, [selectedField]);

  function toggle(stack: string) {
    onStacksChange(
      selectedStacks.includes(stack)
        ? selectedStacks.filter((s) => s !== stack)
        : [...selectedStacks, stack]
    );
  }

  function addCustom() {
    const trimmed = custom.trim();
    if (trimmed && !selectedStacks.includes(trimmed)) {
      onStacksChange([...selectedStacks, trimmed]);
    }
    setCustom("");
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="mb-1 block text-sm font-medium text-ink">Domain / Field</label>
        <select
          value={selectedField}
          onChange={(e) => onFieldChange(e.target.value)}
          className="w-full rounded-md border border-stone-200 bg-white px-3 py-2 text-sm outline-none focus:border-moss focus:ring-1 focus:ring-moss"
        >
          <option value="">Select your primary field…</option>
          {fields.map((f) => (
            <option key={f} value={f}>{f}</option>
          ))}
        </select>
      </div>

      {selectedStacks.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium uppercase text-stone-500">Selected</p>
          <div className="flex flex-wrap gap-2">
            {selectedStacks.map((s) => (
              <span key={s} className="flex items-center gap-1 rounded-full bg-moss/10 px-3 py-1 text-xs font-medium text-moss">
                {s}
                <button onClick={() => toggle(s)} className="ml-0.5 hover:text-moss/60">
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      {suggestions.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium uppercase text-stone-500">Suggested for {selectedField}</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => toggle(s)}
                className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                  selectedStacks.includes(s)
                    ? "border-moss bg-moss/10 text-moss"
                    : "border-stone-200 text-stone-600 hover:border-moss hover:text-moss"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <input
          value={custom}
          onChange={(e) => setCustom(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addCustom())}
          placeholder="Add a custom technology…"
          className="flex-1 rounded-md border border-stone-200 px-3 py-2 text-sm outline-none focus:border-moss"
        />
        <button
          type="button"
          onClick={addCustom}
          className="rounded-md bg-stone-100 px-3 py-2 text-sm text-stone-700 hover:bg-stone-200"
        >
          Add
        </button>
      </div>
    </div>
  );
}
