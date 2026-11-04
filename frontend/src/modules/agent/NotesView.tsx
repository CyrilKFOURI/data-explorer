import { Bot, Trash2, User } from "lucide-react";
import { useState, type FormEvent } from "react";

import { t } from "../../lib/i18n";
import { Button } from "../../ui/Button";
import { ErrorNote, TextInput } from "../../ui/fields";
import { useAddNote, useDeleteNote, useNotes } from "./useAgent";

const MAX_CHARS = 300;

/** Facts about the dataset that every conversation starts with (spec 026, R-AG-M1). */
export function NotesView({ datasetId, onDone }: { datasetId: string; onDone: () => void }) {
  const notes = useNotes(datasetId);
  const add = useAddNote(datasetId);
  const remove = useDeleteNote(datasetId);
  const [text, setText] = useState("");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (text.trim()) add.mutate(text.trim(), { onSuccess: () => setText("") });
  };

  return (
    <div className="space-y-4 p-4 text-[13px]">
      <p className="text-xs text-ink-3">{t("agent.notesIntro")}</p>
      {notes.data && notes.data.length === 0 && <p className="text-ink-2">{t("agent.notesEmpty")}</p>}
      {notes.data && notes.data.length > 0 && (
        <ul className="divide-y divide-line rounded-xl border border-line" aria-label={t("agent.notes")}>
          {notes.data.map((note) => (
            <li key={note.id} className="flex items-start gap-2 px-3 py-2">
              {note.source === "agent" ? (
                <Bot size={14} className="mt-0.5 shrink-0 text-ink-3" aria-label={t("agent.noteByAgent")} />
              ) : (
                <User size={14} className="mt-0.5 shrink-0 text-ink-3" aria-label={t("agent.noteByUser")} />
              )}
              <span className="min-w-0 flex-1 break-words text-ink-1">{note.text}</span>
              <Button
                variant="ghost"
                iconOnly
                icon={Trash2}
                aria-label={t("agent.noteDelete")}
                title={t("agent.noteDelete")}
                onClick={() => remove.mutate(note.id)}
              />
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={submit} className="flex gap-2">
        <TextInput
          aria-label={t("agent.noteNew")}
          placeholder={t("agent.notePlaceholder")}
          maxLength={MAX_CHARS}
          value={text}
          onChange={(event) => setText(event.target.value)}
          className="min-w-0 flex-1"
        />
        <Button type="submit" disabled={!text.trim() || add.isPending}>
          {t("agent.noteAdd")}
        </Button>
      </form>
      {(add.isError || remove.isError) && <ErrorNote>{(add.error ?? remove.error)?.message}</ErrorNote>}
      <Button variant="primary" onClick={onDone}>
        {t("agent.backToChat")}
      </Button>
    </div>
  );
}
