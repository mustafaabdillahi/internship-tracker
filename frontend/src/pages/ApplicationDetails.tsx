import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { getApplication } from "../api/applications";

function ApplicationDetails() {
  const { id } = useParams();
  
  const {
      data,
      isPending,
      isError,
      error
    } = useQuery({
      queryKey: ["applications", id],
      queryFn: () => getApplication(id!),
      enabled: Boolean(id)
    });
  
    if(isPending) {
      return <p>Loading application...</p>;
    }
  
    if(isError) {
      return (
        <div>
          <h1>Application Details</h1>
          <p>Failed to load application: {error.name} | {error.message}
          </p>
        </div>
      );
    }

  return (
    <div>
        <h1>Application Details</h1>
        <p>Application ID: {id}</p>
        <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  )
}

export default ApplicationDetails;