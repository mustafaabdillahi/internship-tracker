import { useParams } from "react-router-dom";

function ApplicationDetails() {
  const { id } = useParams();

  return (
    <div>
        <h1>Application Details</h1>
        <p>Application ID: {id}</p>
    </div>
  )
}

export default ApplicationDetails;