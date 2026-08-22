import { useQuery } from "@tanstack/react-query";
import { getApplications } from "../api/applications";
import SyncGmailButton from "../components/SyncGmailButton";
import LogoutButton from "../components/LogoutButton";

function Dashboard() {
  const {
    data,
    isPending,
    isError,
    error
  } = useQuery({
    queryKey: ["applications"],
    queryFn: getApplications
  });

  if(isPending) {
    return <p>Loading applications...</p>;
  }

  if(isError) {
    return (
      <div>
        <h1>Dashboard</h1>
        <p>Failed to load applications: {error.name} | {error.message}
        </p>
      </div>
    );
  }

  return (
    <div>
        <h1>Dashboard</h1>
        <p>This is the dashboard page.</p>
        <pre>{JSON.stringify(data, null, 2)}</pre>
        <SyncGmailButton />
        <LogoutButton />
    </div>
  )
}

export default Dashboard;