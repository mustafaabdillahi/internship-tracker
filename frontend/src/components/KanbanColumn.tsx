import { useDroppable } from "@dnd-kit/core";
import type { Application, ApplicationStage } from "../types/application";
import ApplicationCard from "./ApplicationCard";

interface KanbanColumnProps {
  id: ApplicationStage;
  title: string;
  applications: Application[];
}

function KanbanColumn(
  {id, title, applications}: KanbanColumnProps
) {
  const {
    setNodeRef,
    isOver
  } = useDroppable({
    id
  });

  return (
    <div
      ref={setNodeRef}
      className={`kanban-column ${
        isOver ? "kanban-column-over": ""
      }`}
    >
      <h2>
        {title} ({applications.length})
      </h2>

      <div className="kanban-column-cards">
        {applications.map((application) => (
          <ApplicationCard
            key={application.id}
            application={application}
          />
        ))}
      </div>

    </div>
  )
}

export default KanbanColumn;