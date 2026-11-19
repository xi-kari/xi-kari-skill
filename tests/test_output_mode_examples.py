"""Every output mode ships with its guide, one self-contained synthetic example, and working links."""

import importlib.util
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('read_source_for_mode_examples', ROOT / 'scripts/read_source.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
LINK = re.compile(r'\]\(([^)#\s]+)(?:#[^)\s]*)?\)')
INDEX = ROOT / 'references/output-modes.md'


def header(path: Path) -> dict:
    lines = path.read_text(encoding='utf-8').split('\n')
    assert lines[0] == '---' and lines[2] == '---', path
    return json.loads(lines[1])


def links(path: Path) -> list[Path]:
    found = []
    for target in LINK.findall(path.read_text(encoding='utf-8')):
        if '://' not in target and not target.startswith('mailto:'):
            found.append((path.parent / target).resolve())
    return found


class OutputModeExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = set(json.loads((ROOT / 'skill-package.json').read_text(encoding='utf-8'))['files'])
        cls.manifest = json.loads((ROOT / 'source/source-manifest.json').read_text(encoding='utf-8-sig'))
        source = (ROOT / 'source' / cls.manifest['source_file']).read_text(encoding='utf-8-sig')
        cls.sections, _ = reader.build_index(source.splitlines())
        cls.guides = sorted((ROOT / 'references/output-modes').glob('*.md'))

    def relative(self, path: Path) -> str:
        return path.relative_to(ROOT).as_posix()

    def test_index_names_every_guide_and_nothing_else(self):
        named = {path for path in links(INDEX) if path.parent == ROOT / 'references/output-modes'}
        self.assertEqual(named, set(self.guides))
        self.assertEqual(len(self.guides), 8)
        self.assertIn(ROOT / 'references/output-modes/domain-study.md', named)

    def test_each_guide_links_one_shipped_synthetic_example_bound_to_the_text(self):
        for guide in self.guides:
            examples = [path for path in links(guide) if path.parent == ROOT / 'assets/examples/output-modes']
            self.assertEqual(len(examples), 1, guide.name)
            example = examples[0]
            self.assertEqual(example.name, guide.name)
            self.assertTrue(example.is_file(), example)
            self.assertIn(self.relative(guide), self.package)
            self.assertIn(self.relative(example), self.package)
            meta = header(example)
            self.assertIs(meta.get('synthetic'), True, example.name)
            self.assertEqual(meta['theory_sha256'], self.manifest['sha256'], example.name)
            self.assertIn('`synthetic`', example.read_text(encoding='utf-8'), example.name)
            self.assertIn(guide.resolve(), links(example), f'{example.name} does not link back to its guide')

    def test_guides_and_examples_cite_existing_sections_and_resolve_their_links(self):
        for path in self.guides + sorted((ROOT / 'assets/examples/output-modes').glob('*.md')):
            for anchor in header(path)['anchors']:
                self.assertIn(anchor, self.sections, f'{path.name}: {anchor}')
            for target in links(path):
                self.assertTrue(target.exists(), f'{path.name}: {target}')
                if target.is_relative_to(ROOT) and target.is_file():
                    self.assertIn(self.relative(target), self.package, f'{path.name} links a file that is not shipped')

    def test_domain_study_is_reachable_from_the_entry_and_keeps_its_working_parts(self):
        guide = ROOT / 'references/output-modes/domain-study.md'
        text = guide.read_text(encoding='utf-8')
        entry = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue('领域专论' in entry and 'references/output-modes.md' in entry
                        and 'references/domain-index.md' in entry, 'SKILL.md does not lead to the domain study')
        for name in ('modules/research/MODULE.md', 'modules/domain-mapping/MODULE.md',
                     'references/domain-index.md', 'references/capability-quickstart.md'):
            self.assertTrue('domain-study.md' in (ROOT / name).read_text(encoding='utf-8'), name)
        targets = set(links(guide))
        for name in ('references/domain-index.md', 'modules/research/MODULE.md', 'modules/domain-mapping/MODULE.md',
                     'references/domains/README.md', 'agents/reviewer.md', 'references/study-design.md',
                     'references/research-work.md'):
            self.assertIn((ROOT / name).resolve(), targets, name)
        for phrase in ('先立领域自己的问题和已有答案', '读到的范围', '领域方法更强', '解释边界与问题',
                       '属于体系迁移', '复读所引的小节', '核对与审读', '每篇都做', '不写入任何领域库',
                       '单列一节', '所查范围内未见', 'M0 立题', '方法附注在最后', '只做到了多少'):
            self.assertIn(phrase, text)
        self.assertIn((ROOT / 'references/generation.md').resolve(), targets)

    def test_supporting_guides_carry_what_the_domain_study_relies_on(self):
        sourcing = (ROOT / 'references/research-work.md').read_text(encoding='utf-8')
        for phrase in ('追到原作', '经工具转述', '没打开', '文字层', '代读', '引号只用于', '承重的是'):
            self.assertIn(phrase, sourcing)
        reading = (ROOT / 'references/full-source-study.md').read_text(encoding='utf-8')
        for phrase in ('不要求全书同时留在上下文里', '不是放弃通读的理由', '不称完整覆盖'):
            self.assertIn(phrase, reading)
        self.assertIn('复读所引的小节', (ROOT / 'modules/domain-mapping/MODULE.md').read_text(encoding='utf-8'))
        self.assertIn('领域专论', (ROOT / 'agents/reviewer.md').read_text(encoding='utf-8'))
        identities = '定义对应、角色或对象实例化、部分对应、观察接口、类比候选、不对应、不适用'
        for name in ('references/output-modes/domain-study.md', 'references/domains/README.md',
                     'modules/domain-mapping/MODULE.md'):
            self.assertIn(identities, (ROOT / name).read_text(encoding='utf-8'), name)

    def test_domain_study_example_shows_each_part_the_guide_asks_for(self):
        text = (ROOT / 'assets/examples/output-modes/domain-study.md').read_text(encoding='utf-8')
        order = ['### 中心判断', '### 这个领域在问什么，已经知道什么', '### 理论怎样定位这个领域', '### 逐条对应',
                 '### 用两个公认的案例检验', '### 贡献与限度', '### 推出的候选（未经检验）', '### 解释边界与问题',
                 '### 参考来源与读到的范围', '### 可以留给下一次的领域卡（草稿，未写入）', '方法附注：']
        positions = [text.find(title) for title in order]
        self.assertNotIn(-1, positions)
        self.assertEqual(positions, sorted(positions))
        table = [line for line in text.splitlines() if line.startswith('| ') and '---' not in line]
        self.assertEqual(table[0].count('|'), 6)
        self.assertGreaterEqual(len(table), 5)
        closing = text[text.find('### 解释边界与问题'):text.find('### 参考来源与读到的范围')]
        for label in ('影响的结论：', '不影响：', '已经做的：', '为什么仍未解决：', '它把判断改成了什么：', '下一步：'):
            self.assertEqual(closing.count(label), 3, label)
        self.assertNotIn('§', text[:text.find('方法附注')])


if __name__ == '__main__':
    unittest.main()
