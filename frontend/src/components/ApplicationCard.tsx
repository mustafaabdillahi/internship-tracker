import { useDraggable } from "@dnd-kit/core";
import type { Application } from "../types/application";

interface ApplicationCardProps {
  application: Application;
}

function ApplicationCard(
  { application }: ApplicationCardProps
) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform
  } = useDraggable({
    id: application.id
  });

  const style = transform
    ? {
      transform:
        `translate3d(${transform.x}px), ${transform.y}px, 0`
    }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className="application-card"
    >
      <strong>
        {application.company_name ?? "Unknown company"}
        
      </strong>
      <p>
        Role: {application.role ?? "Unknown"}
      </p>

      {application.loc && (
        <p>{application.loc}</p>
      )}
    </div>
  );
}

export default ApplicationCard;