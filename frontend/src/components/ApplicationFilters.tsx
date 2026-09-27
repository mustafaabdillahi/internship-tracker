import {type Filters } from "../types/application";

interface ApplicationFiltersProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

const emptyFilters: Filters = {
  company: "",
  location: "",
  role: "",
  dateFrom: "",
  dateTo: ""
}


export default function ApplicationFilters({ filters, onChange }: ApplicationFiltersProps) {
  return (
    <>
      <input
        type="text"
        placeholder="Company"
        value={filters.company}
        onChange={(event) => {
          onChange({
            ...filters,
            company: event.target.value
          });
        }}
      />

      <input
        type="text"
        placeholder="Location"
        value={filters.location}
        onChange={(event) => {
          onChange({
            ...filters,
            location: event.target.value,
          });
        }}
      />

      <input
        type="text"
        placeholder="Role"
        value={filters.role}
        onChange={(event) => {
          onChange({
            ...filters,
            role: event.target.value,
          });
        }}
      />
      
      <button
        type="button"
        onClick={() => onChange(emptyFilters)}  
      >
        Clear filters
      </button>

    </>
  );
}