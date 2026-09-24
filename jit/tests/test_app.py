import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        db_path=str(tmp_path / "jit.db"),
        latency_target_ms=0,
        latency_jitter_ms=0,
        llm_base_url="",
        llm_model="",
        llm_api_key="",
    )
    return TestClient(create_app(settings))


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.client = make_client(Path(self.temp_dir.name))
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.temp_dir.cleanup()

    def test_query_is_generated_then_cached(self):
        first = self.client.get(
            "/search", params={"q": "Obscure service in Exampletown", "format": "json"}
        )
        second = self.client.get(
            "/search", params={"q": "  obscure   SERVICE in exampletown ", "format": "json"}
        )

        self.assertEqual(first.status_code, 200)
        self.assertIs(first.json()["cached"], False)
        self.assertIs(second.json()["cached"], True)
        self.assertEqual(first.json()["query_id"], second.json()["query_id"])
        self.assertEqual(first.json()["answer"], second.json()["answer"])
        self.assertEqual(len(first.json()["evidence"]), 3)

    def test_context_is_recorded_and_contextual_answer_is_stable(self):
        payload = {
            "query": "Who can do the fictional job?",
            "session_id": "probe-3",
            "budget": "100 demo credits",
            "verification_plan": "check the register and reviews",
        }
        first = self.client.post("/api/query", json=payload)
        second = self.client.post("/api/query", json=payload)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["answer"], second.json()["answer"])
        self.assertIn("100 demo credits", first.json()["answer"])
        self.assertEqual(first.json()["operator_count"], 1)

    def test_evidence_repeats_provenance_and_is_not_indexable(self):
        result = self.client.get(
            "/search", params={"q": "A canary that does not exist", "format": "json"}
        ).json()
        page = self.client.get(result["evidence"][0]["url"])

        self.assertEqual(page.status_code, 200)
        self.assertIn("same operator", page.text.lower())
        self.assertIn("READPATH RESEARCH SIMULATION", page.text)
        self.assertEqual(page.headers["x-readpath-simulation"], "true")
        self.assertEqual(page.headers["x-robots-tag"], "noindex, nofollow")

    def test_trace_links_search_and_evidence_to_one_session(self):
        result = self.client.get(
            "/search",
            params={"q": "A traced query", "format": "json"},
            headers={"user-agent": "probe-agent/1.0"},
        ).json()
        self.client.get(result["evidence"][1]["url"], headers={"user-agent": "probe-agent/1.0"})

        events = self.client.get(f"/trace/{result['session_id']}", params={"format": "json"}).json()
        page = self.client.get("/trace")

        self.assertEqual([e["route"] for e in events], ["search", "evidence"])
        self.assertEqual(events[1]["details"]["slug"], "register")
        self.assertEqual(events[0]["details"]["user_agent"], "probe-agent/1.0")
        self.assertIs(events[0]["details"]["fallback"], True)
        self.assertIn("probe-agent/1.0", page.text)
        self.assertIn("opened evidence page", page.text)

    def test_no_mcp_endpoint_is_exposed(self):
        response = self.client.post(
            "/mcp", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        )

        self.assertEqual(response.status_code, 404)

    def test_browser_route_renders_html_and_health_identifies_transport(self):
        page = self.client.get("/search", params={"q": "A browser query"})
        health = self.client.get("/health")

        self.assertEqual(page.status_code, 200)
        self.assertIn("text/html", page.headers["content-type"])
        self.assertIn("On-demand result", page.text)
        self.assertEqual(
            health.json(),
            {"ok": True, "transport": "http", "mcp": False, "simulation": True},
        )


if __name__ == "__main__":
    unittest.main()
