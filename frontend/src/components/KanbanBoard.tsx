import { DndContext, DragOverlay, type DragEndEvent, type DragStartEvent } from "@dnd-kit/core";
import { type Filters, type Application, type ApplicationStage, type ApplicationSort } from "../types/application";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getApplications, updateApplication } from "../api/applications";
import KanbanColumn from "./KanbanColumn";
import { useMemo, useState } from "react";
import ApplicationCard from "./ApplicationCard";
import ApplicationFilters from "./ApplicationFilters";

const columns: {
  id: ApplicationStage;
  title: string;
}[] = [
  {
    id: "applied",
    title: "Applied"
  },
  {
    id: "oa",
    title: "Online Assessment"
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

interface KanbanBoardProps {
  onEditApplication: (application: Application) => void;
}


function sortApplications(applications: Application[], sort: ApplicationSort) {
  return [...applications].sort(
    (a, b) => {
      let a_name = a.company_name ?? "";
      let b_name = b.company_name ?? "";
      switch(sort) {
        case "applied_desc":
          return (
            new Date(b.date_applied).getTime() - 
            new Date(a.date_applied).getTime()
          );
        case "applied_asc":
          return (
            new Date(a.date_applied).getTime() - 
            new Date(b.date_applied).getTime()
          );
        case "updated_desc":
          return (
            new Date(b.updated_at).getTime() - 
            new Date(a.updated_at).getTime()
          );
        case "updated_asc":
          return (
            new Date(a.updated_at).getTime() - 
            new Date(b.updated_at).getTime()
          );
        case "company_asc":
          return a_name.localeCompare(b_name);
        case "company_desc":
          return b_name.localeCompare(a_name);
        default:
          return 0;
      }
    }
  );
}

function KanbanBoard({ onEditApplication }: KanbanBoardProps) {
  const queryClient = useQueryClient();

  const [filters, setFilters] = useState<Filters>({
    company: "",
    location: "",
    role: "",
    dateFrom: "",
    dateTo: ""
  });

  const [sort, setSort] = useState<ApplicationSort>("applied_desc");

  const {
    data: applications = [],
    isPending,
    isError,
    error
  } = useQuery({
    queryKey: ["applications", filters],
    queryFn: () => getApplications(filters),
    placeholderData: (previousData) => previousData
  });


  const sortedApplications = useMemo(
    () => sortApplications(applications, sort),
    [applications, sort]
  );

  const updateStageMutation = useMutation({
    mutationFn: ({
      id, stage
    }: {
      id: number,
      stage: ApplicationStage;
    }) => updateApplication(id, {stage: stage}),

    onMutate: async({ id, stage }) => {
      await queryClient.cancelQueries({
        queryKey: ["applications"]
      });

      const previousApplications = queryClient.getQueryData<Application[]>(
        ["applications"]
      );

      queryClient.setQueryData<Application[]>(
        ["applications"],
        (currentApplications = []) =>
            currentApplications.map((application) =>
            application.id === id
            ? {
              ...application,
              stage
            }
            : application
          )
      );

      return { previousApplications };
    },

    onError: (_error, _variables, context) => {
      if(context?.previousApplications) {
        queryClient.setQueryData(
          ["applications"],
          context.previousApplications
        );
      }
    },

    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["applications"]
      });
    }
  });

  const [activeApplicationId, setActiveApplicationId] =
    useState<number | null>(null);
  
  function handleDragStart(event: DragStartEvent) {
    setActiveApplicationId(Number(event.active.id));
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;

    setActiveApplicationId(null);

    if(!over) {
      return;
    }

    const applicationId = Number(active.id);

    const application = applications.find(
      (application) => application.id === applicationId
    );

    if(!application) {
      return;
    }

    const newStage = over.id as ApplicationStage;

    // Don't update anything if the application wasn't moved to another column
    if(application.stage === newStage) {
      return;
    }

    updateStageMutation.mutate({
      id: applicationId,
      stage: newStage
    });

  }

  const activeApplication = applications.find(
    (application) => application.id === activeApplicationId
  );

  if(isPending) {
    return <p>Loading applications...</p>;
  }

  if(isError) {
    return (
      <p>Failed to load applications: {error.message}</p>
    );
  }

  
  return (
    <>
      <select
        value={sort}
        onChange={(event) => {
          setSort(event.target.value as ApplicationSort)
        }}
      >
        <option value="applied_desc">Date applied — Newest</option>
        <option value="applied_asc">Date applied — Oldest</option>
        <option value="updated_desc">Last updated — Newest</option>
        <option value="updated_asc">Last updated — Oldest</option>
        <option value="company_asc">Company — A-Z</option>
        <option value="company_desc">Company — Z-A</option>
      </select>
      
      <br />
      <ApplicationFilters
        filters={filters}
        onChange={setFilters}
      />
      
      <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
        <div className="kanban-board">
          {columns.map((column) => {
            const columnApplications = sortedApplications.filter(
              (application) => application.stage === column.id
            );

            return (
              <KanbanColumn
                key={column.id}
                id={column.id}
                title={column.title}
                applications={columnApplications}
                activeApplicationId={activeApplicationId}
                onEdit={onEditApplication}
              />
            );

          })}
        </div>
        <DragOverlay dropAnimation={null}>
          {activeApplication ? (
            <ApplicationCard
              application={activeApplication}
              isOverlay
              onEdit={onEditApplication}
            />
          ): null}
        </DragOverlay>
      </DndContext>
    </>
  );
}

export default KanbanBoard;
