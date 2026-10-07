import type { StageEvent } from "../../types/applicationDetail";

interface Props {
  events: StageEvent[];
}

function StageTimeline({ events }: Props) {
  if(events.length === 0) {
    return (
      <p className="text-sm text-grey-500">
        No stage history available.
      </p>
    );
  }

  return (
    <div>
      {events.map((event, index) => (
        <div
          key={event.id}
          className="relative flex gap-4"
        >
          <div>
            <div className="h-3 w-3 rounded-full bg-blue-500" />
            {index < events.length - 1 && (
              <div className="ml-[5px] h-12 w-px bg-grey-300" />
            )}
          </div>

          <div className="pb-6">
            <p className="font-medium">
              {event.stage}
            </p>

            <time className="text-xs text-grey-400">
              {event.created_at}
            </time>
          </div>
        </div>
      ))}
    </div>
  )
}

export default StageTimeline;