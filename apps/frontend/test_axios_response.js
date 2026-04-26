// Test file to understand Axios response structure
// This simulates what the frontend receives

// In Axios, when you do: apiClient.get("/api/data")
// The response object has this structure:
// response = {
//   data: <actual server response>,
//   status: 200,
//   statusText: "OK",
//   headers: {...},
//   config: {...}
// }

// So if server returns: { summary: {...}, connectionBreakdown: [...] }
// Then axios wraps it as: response.data = { summary: {...}, connectionBreakdown: [...] }

// In the then handler:
// .then((response) => {
//   console.log(response);  // Full axios response object
//   console.log(response.data);  // The actual server response
// })

// CORRECT way to extract:
const testResponse = {
  data: {
    summary: {
      totalRuns: 103,
      totalRecords: 60,
      avgExecutionTime: 1896,
      estimatedDataSize: "30,720 bytes"
    },
    connectionBreakdown: [
      {
        connectionId: "test",
        runCount: 10,
        totalRecords: 50,
        avgExecutionTime: 2000,
        lastRun: "2025-11-07T00:00:00+00:00",
        connectionName: "Test"
      }
    ],
    data: []
  },
  status: 200,
  statusText: "OK"
};

// This is what we get in the .then() handler
const response = testResponse;

// Option 1: Extract directly
const apiData = response.data;
console.log("Option 1 - apiData:", apiData);
console.log("Has summary?", apiData.summary ? "YES" : "NO");
console.log("Has connectionBreakdown?", apiData.connectionBreakdown ? "YES" : "NO");

// Option 2: Verify structure
const isValid = apiData && 
  typeof apiData === 'object' && 
  apiData.summary && 
  apiData.connectionBreakdown;
console.log("Is valid?", isValid ? "YES" : "NO");
