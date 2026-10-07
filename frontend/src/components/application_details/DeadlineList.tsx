import type { ApplicationDeadline } from "../../types/applicationDetail";

interface Props {
  deadlines: ApplicationDeadline[];
}

function DeadlineList({ deadlines }: Props) {
  if(deadlines.length === 0) {
    return (
      <p className="text-sm text-grey-500">
        No deadlines recorded.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {deadlines.map(deadline => (
        <div
          key={deadline.id}
          className="rounded-lg border p-4"
        >
          <div className="font-medium">
            {deadline.type}
          </div>

          <div className="text-sm">
            {deadline.description}
          </div>

          <div className="text-sm text-grey-500">
            Due {deadline.due_at}
          </div>
        </div>
      ))}
    </div>
  );
}

export default DeadlineList;