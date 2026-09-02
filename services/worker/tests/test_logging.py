import json
import logging
import unittest

from worker import JsonFormatter


class JsonFormatterTests(unittest.TestCase):
    def test_log_is_structured_and_includes_safe_job_metadata(self):
        record = logging.LogRecord("mbas.worker", logging.INFO, __file__, 1, "Job received", (), None)
        record.payload_size = 42

        event = json.loads(JsonFormatter().format(record))

        self.assertEqual(event["message"], "Job received")
        self.assertEqual(event["payload_size"], 42)
        self.assertTrue(event["timestamp"].endswith("Z"))
        self.assertNotIn("payload", event)


if __name__ == "__main__":
    unittest.main()
