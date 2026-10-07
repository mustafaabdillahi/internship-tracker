import type { ApplicationNote } from "../../types/applicationDetail";

function ApplicationNotes({ notes }: {
  notes: ApplicationNote[];
}) {
  if(notes.length === 0) {
    return (
      <p className="text-sm text-grey-500">
          No notes yet.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {notes.map(note => (
          <div
            key={note.id}
            className="rounded-lg border p-4"
          >
            <p>{note.content}</p>
            <time className="mt-2 block text-xs text-grey-400">
              {note.created_at}
            </time>
          </div>
      ))}
    </div>
  )
}

export default ApplicationNotes;