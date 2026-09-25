import { DndContext, type DragEndEvent } from "@dnd-kit/core";
import type { ApplicationStage } from "../types/application";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getApplications, updateApplicationStage } from "../api/applications";
import KanbanColumn from "./KanbanColumn";

const columns: {
  id: ApplicationStage;
  title: string;
}[] = [
  {
    id: "applied",
    title: "Applied"
  },
  {
    id: "interview",
    title: "Interview"
  },
  {
    id: "offer",
    title: "Offer"
  },
  {
    id: "rejected",
    title: "Rejected"
  },
  {
    id: "withdrawn",
    title: "Withdrawn"
  }
];



function KanbanBoard() {
  const queryClient = useQueryClient();

  const {
    data: applications = [],
    isPending,
    isError,
    error
  } = useQuery({
    queryKey: ["applications"],
    queryFn: getApplications
  });

  const updateStageMutation = useMutation({
    mutationFn: ({
      id, stage
    }: {
      id: number,
      stage: ApplicationStage;
    }) => updateApplicationStage(id, stage),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["applications"]
      });
    }
  });

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;

    if(!over) {
      return;
    }

    const applicationId = Number(active.id);
    const newStage = over.id as ApplicationStage;

    updateStageMutation.mutate({
      id: applicationId,
      stage: newStage
    });

  }

  if(isPending) {
    return <p>Loading applications...</p>;
  }

  if(isError) {
    return (
      <p>Failed to load applications: {error.message}</p>
    );
  }

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div className="kanban-board">
        {columns.map((column) => {
          const columnApplications = applications.filter(
            (application) => application.stage === column.id
          );

          return (
            <KanbanColumn
              key={column.id}
              id={column.id}
              title={column.title}
              applications={columnApplications}
            />
          );

        })}
      </div>
    </DndContext>
  );
}

export default KanbanBoard;
