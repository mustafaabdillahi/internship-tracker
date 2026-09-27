import SyncGmailButton from "../components/SyncGmailButton";
import LogoutButton from "../components/LogoutButton";
import KanbanBoard from "../components/KanbanBoard";
import { useState } from "react";
import type { Application } from "../types/application";
import ApplicationModal from "../components/ApplicationModal";

function Dashboard() {

  const [isApplicationModalOpen, setIsApplicationModalOpen] = useState(false);
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null);

  return (
    <>
      <div>
          <h1>Dashboard</h1>
          <p>This is the dashboard page.</p>

          <button
            onClick={() => {
              setSelectedApplication(null);
              setIsApplicationModalOpen(true);
            }}>
            + New Application
          </button>
          
          <br />
          <KanbanBoard
            onEditApplication={(application) => {
              setSelectedApplication(application);
              setIsApplicationModalOpen(true);
            }}
          />
          <SyncGmailButton />
          <LogoutButton />
      </div>

      <div>
        <ApplicationModal
          key={selectedApplication?.id ?? "new"}
          isOpen={isApplicationModalOpen}
          application={selectedApplication ?? undefined}
          onClose={() => {
            setIsApplicationModalOpen(false);
            setSelectedApplication(null);
          }}
        />
      </div>
    </>
  )
}

export default Dashboard;