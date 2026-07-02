def test_x_trace_id_is_returned_as_wright_correlation_id(sync_client):
    response = sync_client.get("/api/health", headers={"X-Trace-Id": "corr-test-123"})

    assert response.status_code == 200
    assert response.headers["X-Trace-Id"] == "corr-test-123"
