from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AnalysisContractTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding='utf-8-sig')

    def test_path_hierarchy_is_shared_by_generation_and_composition(self):
        for path in ('modules/dynamics/MODULE.md', 'modules/forecast/MODULE.md', 'modules/compose/MODULE.md'):
            with self.subTest(path=path):
                text = self.read(path)
                for term in ('同一对象', '同一窗口', '互斥', '外溢', '触发条件', '早期信号', '反向信号', '下一份材料'):
                    self.assertIn(term, text)


if __name__ == '__main__':
    unittest.main()
