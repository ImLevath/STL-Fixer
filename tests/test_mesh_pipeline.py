import unittest

import trimesh

from mesh_pipeline import process_mesh


class MeshPipelineTests(unittest.TestCase):
    def test_filters_tiny_components_and_returns_watertight_output(self):
        cube = trimesh.creation.box(extents=(10.0, 10.0, 10.0))

        tiny = trimesh.Trimesh(
            vertices=[(25.0, 0.0, 0.0), (25.2, 0.0, 0.0), (25.0, 0.2, 0.0)],
            faces=[(0, 1, 2)],
            process=False,
        )

        combined = trimesh.util.concatenate([cube, tiny])

        progress_messages = []
        processed = process_mesh(combined, progress=lambda _, message: progress_messages.append(message))

        self.assertGreaterEqual(len(processed.faces), 4)
        self.assertTrue(processed.is_watertight)
        self.assertIn("Disconnecting mesh islands...", progress_messages)
        self.assertIn("Filtering tiny artifacts...", progress_messages)
        self.assertIn("Applying UV unwrapping...", progress_messages)
        self.assertIn("Merging processed components...", progress_messages)
        self.assertIn("Generating solid watertight mesh...", progress_messages)


if __name__ == "__main__":
    unittest.main()
