import Button from "./components/Button"

function App() {
	function onStatusClick() {
		console.log("Status button clicked.");
	}

	return (
		<div>
			<h1>Internship Tracker</h1>
			<Button onClick={onStatusClick}>Check status</Button>
		</div>
	);
}

export default App;