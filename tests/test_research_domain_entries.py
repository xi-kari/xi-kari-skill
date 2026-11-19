"""Exercise the research and domain entries from the actual isolated install payload."""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('entries_package_builder', ROOT / 'scripts/build_install_package.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

DRAFTS = {
    'zh': ('# 结业比例提高说明了什么\n\n'
           '## 中心判断\n\n结业比例提高 20 个百分点由登记直接算出；原因尚未区分，见[末章](#解释边界与问题)。\n\n'
           '| 字段 | 含义 |\n| --- | --- |\n| completion\\_rate | 结业人数 ÷ 登记人数 |\n\n'
           '## 解释边界与问题\n\n**一、答疑与招募的作用分不开。** 影响“课程有效”，不影响结业比例本身。\n',
           '解释边界与问题'),
    'en': ('# What the higher completion rate shows\n\n'
           '## Central judgment\n\nThe rise of 20 points follows from the register; its cause is open, '
           'see [the closing chapter](#limits-of-explanation-and-issues).\n\n'
           '| Field | Meaning |\n| --- | --- |\n| completion\\_rate | completed ÷ registered |\n\n'
           '## Limits of explanation and issues\n\n**1. Tutoring and recruitment cannot be separated.** '
           'It affects “the course works”, not the completion rate itself.\n',
           'Limits of explanation and issues'),
}


class ResearchDomainEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.work = Path(cls.temp.name)
        result = builder.build(ROOT, cls.work / 'archives')
        with zipfile.ZipFile(cls.work / 'archives' / result['archive']) as archive:
            archive.extractall(cls.work / 'installed')
        cls.install = cls.work / 'installed' / result['archive_root']
        cls.initial = cls.snapshot()
        cls.guides = sorted(path for path in cls.install.rglob('*.md')
                            if path.relative_to(cls.install).parts[0] in {'SKILL.md', 'modules', 'references', 'assets'})

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def snapshot(cls):
        return {p.relative_to(cls.install).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in cls.install.rglob('*') if p.is_file()}

    def tearDown(self):
        self.assertEqual(self.initial, self.snapshot(), 'Running a shipped tool changed its install payload')

    def command(self, script, *args, success=True):
        process = subprocess.run([sys.executable, str(self.install / 'scripts' / script), *map(str, args)],
                                 cwd=self.work, capture_output=True, text=True, encoding='utf-8', timeout=30)
        if success:
            self.assertEqual(process.returncode, 0, process.stderr)
        else:
            self.assertNotEqual(process.returncode, 0, process.stdout)
            self.assertNotIn('Traceback', process.stderr)
        return process

    def read(self, name):
        return (self.install / name).read_text(encoding='utf-8')

    def test_hand_written_complete_draft_reads_cleanly_on_the_page_and_in_word(self):
        for lang, (text, chapter) in DRAFTS.items():
            with self.subTest(lang=lang):
                answer = self.work / f'xi-kari-answer-{lang}.md'
                answer.write_text(text, encoding='utf-8', newline='\n')
                page = self.work / f'xi-kari-answer-{lang}.html'
                self.command('render_answer.py', answer, '--output', page, '--lang', lang)
                body = page.read_text(encoding='utf-8')
                body = body[body.index('<article'):body.rindex('</article>')]
                self.assertIn(chapter, body)
                self.assertNotIn('href="file:', body)
                self.assertNotIn('completion\\_rate', body)
                word = self.work / f'xi-kari-answer-{lang}.docx'
                summary = json.loads(self.command('render_docx.py', answer, '--output', word, '--lang', lang).stdout)
                self.assertEqual(summary['unsupported'], [])
                with zipfile.ZipFile(word) as archive:
                    document = archive.read('word/document.xml').decode('utf-8')
                words = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', document))
                self.assertIn('completion_rate', words)
                self.assertIn(chapter, words)
                self.assertNotIn('\\', words)
                self.assertNotIn('](', words)

    def test_research_guides_ask_for_one_hand_written_draft_with_located_issues(self):
        module = self.read('modules/research/MODULE.md')
        for phrase in ('手写的完整稿', '解释边界与问题', '不影响哪些结论', '为什么仍未解决', '它把判断改成了什么',
                       '末章不能是唯一写着重大限制的地方', '只说“研究一下”也按这里交付'):
            self.assertIn(phrase, module)
        self.assertIn('来源或数据更正', self.read('references/continuation.md'))
        self.assertIn('来源或数据更正', module)
        example = self.read('assets/examples/research-answer.md')
        self.assertLess(example.index('### 中心判断'), example.index('### 解释边界与问题'))
        for label in ('影响的结论：', '不影响：', '已经做的：', '为什么仍未解决：', '它把判断改成了什么：', '下一步：'):
            self.assertEqual(example.count(label), 2, label)
        chapters = example[example.index('### 中心判断'):example.index('方法附注：')]
        self.assertNotIn('§', chapters)

    def test_domain_guides_keep_cards_outside_the_install_and_under_user_consent(self):
        module = self.read('modules/domain-mapping/MODULE.md')
        for phrase in ('领域库', '不是本题证据', '用户同意并指明领域库位置后才写入', '概念重构'):
            self.assertIn(phrase, module)
        guide = self.read('references/domains/README.md')
        for phrase in ('安装目录之外', '用户同意并给出领域库位置后才写入', '都只读', '修订记录', '卡片不代读原文'):
            self.assertIn(phrase, guide)

    def test_installed_card_tool_reads_samples_and_a_user_library_without_writing(self):
        listing = json.loads(self.command('domain_cards.py', 'list').stdout)
        self.assertEqual(len(listing['cards']), 3)
        self.assertTrue(all(row['theory'] == 'current' and row['problems'] == 0 for row in listing['cards']))
        self.assertTrue(json.loads(self.command('domain_cards.py', 'check').stdout)['ok'])
        example = self.install / 'assets/examples/domain-card-example.md'
        report = json.loads(self.command('domain_cards.py', '--library', example, 'check').stdout)
        self.assertEqual((report['error_count'], report['warning_count']), (0, 0))
        library = self.work / '我的 领域卡'
        library.mkdir(exist_ok=True)
        (library / 'delivery.md').write_bytes(example.read_bytes())
        (library / 'broken.md').write_text('# 没有卡头\n', encoding='utf-8')
        before = {path.name: path.read_bytes() for path in library.iterdir()}
        failed = self.command('domain_cards.py', '--library', library, 'check', success=False)
        self.assertEqual(json.loads(failed.stdout)['error_count'], 1)
        self.assertEqual(json.loads(self.command('domain_cards.py', '--library', library, 'list').stdout)['cards'][1]['id'],
                         'EXAMPLE-DOMAIN-CARD')
        self.assertEqual(before, {path.name: path.read_bytes() for path in library.iterdir()})

    def test_shipped_examples_are_bound_to_the_bundled_theory(self):
        manifest = json.loads(self.read('source/source-manifest.json'))
        for name in ('assets/examples/research-answer.md', 'assets/examples/domain-card-example.md'):
            with self.subTest(example=name):
                text = self.read(name)
                header = json.loads(text.split('\n')[1])
                self.assertEqual(header['theory_sha256'], manifest['sha256'])
                self.assertTrue(header['synthetic'])
                self.assertIn('synthetic', text.split('---', 2)[2][:400])
                for section in set(re.findall(r'§\s*((?:\d+|[A-D])(?:\.\d+)+)', text)):
                    self.assertIn(section, header['anchors'])
                    self.command('read_source.py', '--section', section)

    def test_finite_tools_keep_joint_conflicts_visible_in_the_install(self):
        source = self.install / 'assets/examples/finite-tools.json'
        collection = json.loads(source.read_text(encoding='utf-8'))
        results = {}
        for case in collection['models']:
            result = json.loads(self.command('finite_tools.py', '--model', source, '--case', case, 'compute').stdout)
            self.assertTrue(result['computed'])
            self.assertTrue(result['model']['fictional'])
            results[case] = result['result']
        self.assertEqual(results['schedule-shared-capacity']['status'], 'infeasible_in_model')
        self.assertIsNone(results['schedule-shared-capacity']['schedule'])
        self.assertTrue(results['relation-local-without-chain']['all_local_relations_nonempty'])
        self.assertEqual(results['relation-local-without-chain']['status'], 'no_joint_witness')
        self.command('finite_tools.py', '--model', source, '--case', 'schedule-shared-capacity',
                     'compute', '--output', self.install / 'forbidden-finite.json', success=False)

    def test_shipped_guides_link_to_shipped_resources(self):
        self.assertGreater(len(self.guides), 60)
        for path in self.guides:
            name = path.relative_to(self.install).as_posix()
            for target in re.findall(r'\]\(([^)\s]+)\)', path.read_text(encoding='utf-8')):
                if '://' in target or target.startswith('#'):
                    continue
                relative = target.split('#')[0]
                if relative:
                    destination = (path.parent / relative).resolve()
                    self.assertTrue(destination.is_relative_to(self.install.resolve()), (name, target))
                    self.assertTrue(destination.exists(), (name, target))

    def test_shipped_guides_name_only_scripts_that_are_shipped(self):
        shipped = {path.name for path in (self.install / 'scripts').glob('*.py')}
        for path in self.guides:
            name = path.relative_to(self.install).as_posix()
            for script in set(re.findall(r'(?<![\w/.-])([a-z][a-z_]*\.py)\b', path.read_text(encoding='utf-8'))):
                self.assertIn(script, shipped, f'{name} names {script}, which the package does not ship')


if __name__ == '__main__':
    unittest.main()
