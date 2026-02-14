const form = document.getElementById("query-form");
const statusEl = document.getElementById("status");
const graphqlEl = document.getElementById("graphql");
const resultsEl = document.getElementById("results");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusEl.textContent = "Querying...";
  graphqlEl.textContent = "";
  resultsEl.textContent = "";

  const phrase = document.getElementById("phrase").value;
  const docId = document.getElementById("doc_id").value;
  const limit = Number(document.getElementById("limit").value || 25);
  const sortBy = document.getElementById("sort_by").value;
  const sortOrder = document.getElementById("sort_order").value;

  try {
    const response = await fetch("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        phrase,
        doc_id: docId,
        limit,
        sort_by: sortBy,
        sort_order: sortOrder,
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      statusEl.textContent = "Query failed";
      graphqlEl.textContent = payload.graphql_query || "";
      resultsEl.textContent = JSON.stringify(payload, null, 2);
      return;
    }

    statusEl.textContent = `Found ${payload.count} record(s)`;
    graphqlEl.textContent = payload.graphql_query || "";
    resultsEl.textContent = JSON.stringify(payload.records, null, 2);
  } catch (error) {
    statusEl.textContent = "Query failed";
    resultsEl.textContent = String(error);
  }
});
