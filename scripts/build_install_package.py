"""Build a clean, self-contained Skill folder from its verified source archive."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, io, json, stat, zipfile, zlib

ROOT_FILES={'SKILL.md','AGENTS.md','README.md','LICENSE','requirements.txt'}
ROOT_DIRS={'agents','protocols','references','schemas','scripts','source','templates'}
EXCLUDED={'scripts/serve_project_page.py','scripts/build_install_package.py',
          'scripts/evaluate_xi_kari_v4.py','scripts/xi_kari_runtime/evaluation_v4.py',
          'scripts/verify_source_preservation.py',
          'schemas/source-manifest.schema.json','schemas/source-candidate.schema.json',
          'schemas/concept-registry.schema.json','schemas/concept-inventory.schema.json',
          'schemas/concept-candidate-semantic-scopes.schema.json',
          'schemas/source-to-concept-map.schema.json','schemas/concept-relations.schema.json'}
STAMP=(1980,1,1,0,0,0)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def selected(name):
    p=PurePosixPath(name)
    if name in EXCLUDED or '__pycache__' in p.parts or p.suffix in {'.pyc','.pyo'}:
        return False
    if name.startswith('source/'):
        return name=='source/跨尺度多圈层结构推演框架v9.0.docx'
    if name.startswith('references/source/'):
        return name.startswith('references/source/v9.0/')
    if name.startswith('references/ontology/'):
        return name.startswith('references/ontology/v9.0/')
    if name.startswith('references/learning-packs/'):
        return name.startswith(('references/learning-packs/v9.0/','references/learning-packs/domains/'))
    return name not in EXCLUDED and (name in ROOT_FILES or (len(p.parts)>1 and p.parts[0] in ROOT_DIRS))
def assemble(source_zip,source_manifest):
    source=json.loads(source_manifest.read_text('utf-8'))
    assert sha(source_zip.read_bytes())==source['archive']['sha256']
    members=[];excluded=[]
    buffer=io.BytesIO()
    with zipfile.ZipFile(source_zip) as original,zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as result:
        assert original.testzip() is None
        assert original.namelist()==[row['path'] for row in source['members']]
        for row in source['members']:
            name=row['path'];data=original.read(name)
            assert sha(data)==row['sha256']
            if not selected(name):
                excluded.append(name);continue
            p=PurePosixPath(name)
            assert not p.is_absolute() and '..' not in p.parts and '\\' not in name
            archive_name='xi-kari-skill/'+name
            info=zipfile.ZipInfo(archive_name,STAMP)
            info.create_system=3
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(stat.S_IFREG | (0o755 if row['git_mode']=='100755' else 0o644)) << 16
            result.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
            members.append({'path':archive_name,'source_path':name,'git_blob_oid':row['git_blob_oid'],
                'git_mode':row['git_mode'],'bytes':len(data),'sha256':sha(data)})
    raw=buffer.getvalue()
    manifest={'schema':'xikari-install-package/1','source':source['source'],
        'source_archive_sha256':source['archive']['sha256'],
        'archive':{'root_directory':'xi-kari-skill','sha256':sha(raw),'bytes':len(raw),'members':len(members),
                   'compression':'deflate','compression_level':9,'zlib_version':zlib.ZLIB_VERSION,'timestamp':'1980-01-01T00:00:00'},
        'selection':{'root_files':sorted(ROOT_FILES),'root_directories':sorted(ROOT_DIRS),'excluded_paths':excluded},
        'members':members,'all_member_bytes_unchanged_from_source_commit':True,
        'python_or_dependencies_bundled':False,'default_instruction_mode_requires_python':False}
    return raw,(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-zip',type=Path,required=True)
    p.add_argument('--source-manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--check',action='store_true')
    a=p.parse_args();raw,manifest=assemble(a.source_zip,a.source_manifest)
    if a.check:
        assert a.output.read_bytes()==raw
        assert a.manifest.read_bytes()==manifest
    else:
        assert not a.output.exists() and not a.manifest.exists()
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.manifest.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_bytes(raw);a.manifest.write_bytes(manifest)
    print(json.dumps({'operation':'check' if a.check else 'build','passed':True,'writes':0 if a.check else 2,
        'sha256':sha(raw),'bytes':len(raw),'members':json.loads(manifest)['archive']['members']}))
if __name__=='__main__':main()
