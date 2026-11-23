#!/usr/bin/env node
// .project 대시보드 · 검사 도구 (외부 의존성 없음, Node 18+)
//
//   node .project/_tools/project-dashboard.mjs serve [--port 4800]   실시간 대시보드 (파일 바뀌면 자동 갱신)
//   node .project/_tools/project-dashboard.mjs build [--out <file>]  정적 HTML 생성 (공유·GitHub Pages용)
//   node .project/_tools/project-dashboard.mjs check                 데이터 정합성 검사 (오류 시 exit 1)
//   node .project/_tools/project-dashboard.mjs status                현재 상태 요약 (AI가 작업 전 확인용)
//   node .project/_tools/project-dashboard.mjs next                  지금 진행 가능한 다음 작업
//   node <kit>/tools/project-dashboard.mjs init [프로젝트경로]        .project 폴더 생성 + 도구 복사
//
// 옵션: --dir <.project 경로>  (기본: 이 파일이 .project/_tools 안에 있으면 그 상위, 아니면 ./.project)

import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const cmd = args[0] || 'help';
const opt = (name, def) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] ? args[i + 1] : def;
};

const TASK_STATUS = ['todo', 'doing', 'review', 'done', 'rework', 'verify', 'blocked', 'dropped'];
const FEATURE_STATUS = ['planned', 'building', 'done', 'changing'];
const CHANGE_STATUS = ['received', 'planned', 'in-progress', 'done', 'rejected'];

function resolveDir() {
  const d = opt('dir');
  if (d) return path.resolve(d);
  if (path.basename(HERE) === '_tools') return path.resolve(HERE, '..');
  return path.resolve(process.cwd(), '.project');
}

// ---------- 로딩 ----------
function readJsonDir(dir, errors) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter((f) => f.endsWith('.json'))
    .sort()
    .map((f) => {
      const file = path.join(dir, f);
      try {
        const obj = JSON.parse(fs.readFileSync(file, 'utf8'));
        obj.__file = path.relative(path.dirname(dir), file);
        if (obj.id && obj.id !== f.replace(/\.json$/, '')) {
          errors.push(`${obj.__file}: 파일명과 id(${obj.id})가 다릅니다`);
        }
        return obj;
      } catch (e) {
        errors.push(`${path.relative(path.dirname(dir), file)}: JSON 파싱 오류 — ${e.message}`);
        return null;
      }
    })
    .filter(Boolean);
}

function load(dir) {
  const errors = [];
  const warnings = [];
  if (!fs.existsSync(dir)) {
    throw new Error(`.project 폴더를 찾을 수 없습니다: ${dir}\n  → init 으로 먼저 만드세요.`);
  }
  let project = {};
  const pj = path.join(dir, 'project.json');
  if (fs.existsSync(pj)) {
    try { project = JSON.parse(fs.readFileSync(pj, 'utf8')); }
    catch (e) { errors.push(`project.json: JSON 파싱 오류 — ${e.message}`); }
  } else errors.push('project.json 이 없습니다');
  const planFile = path.join(dir, 'plan.md');
  const plan = fs.existsSync(planFile) ? fs.readFileSync(planFile, 'utf8') : '';
  const tasks = readJsonDir(path.join(dir, 'tasks'), errors);
  const features = readJsonDir(path.join(dir, 'features'), errors);
  const changes = readJsonDir(path.join(dir, 'changes'), errors);
  return { project, plan, tasks, features, changes, errors, warnings };
}

// ---------- 검사 ----------
function check(d) {
  const { project, tasks, features, changes, errors, warnings } = d;
  const stages = new Set((project.stages || []).map((s) => s.id));
  const T = new Map(tasks.map((t) => [t.id, t]));
  const F = new Map(features.map((f) => [f.id, f]));
  const C = new Map(changes.map((c) => [c.id, c]));
  const arr = (v) => (Array.isArray(v) ? v : []);
  const ref = (where, kind, map, ids) => arr(ids).forEach((id) => {
    if (!map.has(id)) errors.push(`${where}: 존재하지 않는 ${kind} ${id}`);
  });

  if (!project.name) errors.push('project.json: name 이 없습니다');
  if (!Array.isArray(project.stages)) errors.push('project.json: stages 배열이 없습니다');

  for (const t of tasks) {
    const w = t.__file;
    for (const k of ['id', 'title', 'stage', 'status']) if (!t[k]) errors.push(`${w}: ${k} 누락`);
    if (t.status && !TASK_STATUS.includes(t.status)) errors.push(`${w}: 잘못된 status "${t.status}"`);
    if (t.stage && !stages.has(t.stage)) errors.push(`${w}: project.json에 없는 단계 ${t.stage}`);
    ref(w, '기능', F, t.features);
    ref(w, '작업', T, t.dependsOn);
    ref(w, '수정요청', C, t.changes);
    arr(t.features).forEach((fid) => {
      const f = F.get(fid);
      if (f && !arr(f.tasks).includes(t.id)) errors.push(`${w}: ${fid}.tasks 에 ${t.id} 가 없습니다 (양방향 기록 필요)`);
    });
    arr(t.changes).forEach((cid) => {
      const c = C.get(cid);
      if (c && ![...arr(c.impact?.tasksAdded), ...arr(c.impact?.tasksReworked), ...arr(c.impact?.tasksUpdated), ...arr(c.impact?.tasksVerify)].includes(t.id)) {
        errors.push(`${w}: ${cid}.impact 의 tasksAdded/tasksReworked/tasksUpdated/tasksVerify 에 ${t.id} 가 없습니다`);
      }
    });
    if (t.status === 'done') {
      arr(t.dependsOn).forEach((dep) => {
        const dt = T.get(dep);
        if (dt && !['done', 'verify', 'review', 'rework'].includes(dt.status)) warnings.push(`${t.id} 는 완료인데 선행 작업 ${dep} 가 ${dt.status} 상태입니다`);
      });
    }
    if (!arr(t.features).length) warnings.push(`${t.id}: 연결된 기능이 없습니다`);
  }

  for (const f of features) {
    const w = f.__file;
    for (const k of ['id', 'name', 'status']) if (!f[k]) errors.push(`${w}: ${k} 누락`);
    if (f.status && !FEATURE_STATUS.includes(f.status)) errors.push(`${w}: 잘못된 status "${f.status}"`);
    ref(w, '작업', T, f.tasks);
    ref(w, '기능', F, f.dependsOn);
    ref(w, '수정요청', C, f.changes);
    arr(f.tasks).forEach((tid) => {
      const t = T.get(tid);
      if (t && !arr(t.features).includes(f.id)) errors.push(`${w}: ${tid}.features 에 ${f.id} 가 없습니다 (양방향 기록 필요)`);
    });
    const live = arr(f.tasks).map((id) => T.get(id)).filter((t) => t && t.status !== 'dropped');
    if (f.status === 'done' && live.some((t) => t.status !== 'done')) warnings.push(`${f.id} 는 done 인데 완료되지 않은 작업이 있습니다`);
    if (!f.spec || f.spec.trim().length < 20) warnings.push(`${f.id}: 기능 명세(spec)가 비어 있거나 너무 짧습니다`);
  }

  for (const c of changes) {
    const w = c.__file;
    for (const k of ['id', 'title', 'status']) if (!c[k]) errors.push(`${w}: ${k} 누락`);
    if (c.status && !CHANGE_STATUS.includes(c.status)) errors.push(`${w}: 잘못된 status "${c.status}"`);
    const im = c.impact || {};
    ref(w, '기능', F, im.features);
    ref(w, '기능', F, im.verifyFeatures);
    ref(w, '작업', T, im.tasksAdded);
    ref(w, '작업', T, im.tasksReworked);
    ref(w, '작업', T, im.tasksUpdated);
    ref(w, '작업', T, im.tasksVerify);
    arr(im.features).forEach((fid) => {
      const f = F.get(fid);
      if (f && !arr(f.changes).includes(c.id)) errors.push(`${w}: ${fid}.changes 에 ${c.id} 가 없습니다 (양방향 기록 필요)`);
    });
    [...arr(im.tasksAdded), ...arr(im.tasksReworked), ...arr(im.tasksUpdated), ...arr(im.tasksVerify)].forEach((tid) => {
      const t = T.get(tid);
      if (t && !arr(t.changes).includes(c.id)) errors.push(`${w}: ${tid}.changes 에 ${c.id} 가 없습니다 (양방향 기록 필요)`);
    });
    if (c.status === 'done') {
      [...arr(im.tasksAdded), ...arr(im.tasksReworked), ...arr(im.tasksUpdated), ...arr(im.tasksVerify)].forEach((tid) => {
        const t = T.get(tid);
        const laterCr = arr(t?.changes).at(-1) !== c.id; // 이후 다른 수정 요청으로 다시 열린 작업은 제외
        if (t && !laterCr && !['done', 'dropped'].includes(t.status)) warnings.push(`${c.id} 는 done 인데 ${tid} 가 ${t.status} 상태입니다`);
      });
    }
  }

  // 작업 의존 순환 검사
  const seen = new Set(); const stack = new Set();
  const visit = (id, trail) => {
    if (stack.has(id)) { errors.push(`작업 의존 순환: ${[...trail, id].join(' → ')}`); return; }
    if (seen.has(id)) return;
    seen.add(id); stack.add(id);
    arr(T.get(id)?.dependsOn).forEach((n) => visit(n, [...trail, id]));
    stack.delete(id);
  };
  tasks.forEach((t) => visit(t.id, []));
  return { errors, warnings };
}

// ---------- 모델 (대시보드용 데이터) ----------
function nextTasks(d) {
  const T = new Map(d.tasks.map((t) => [t.id, t]));
  const order = new Map((d.project.stages || []).map((s, i) => [s.id, i]));
  const ready = (t) => (t.dependsOn || []).every((id) => ['done', 'review', 'verify'].includes(T.get(id)?.status));
  const pri = { doing: 0, rework: 1, verify: 2, todo: 3 };
  return d.tasks
    .filter((t) => t.status in pri && (t.status !== 'todo' || ready(t)))
    .sort((a, b) => pri[a.status] - pri[b.status] || (order.get(a.stage) ?? 99) - (order.get(b.stage) ?? 99) || a.id.localeCompare(b.id));
}

function model(d) {
  const { errors, warnings } = check(d);
  const strip = (o) => { const { __file, ...rest } = o; return rest; };
  const tasks = d.tasks.map(strip);
  const changes = d.changes.map(strip);
  const features = d.features.map((f) => ({
    ...strip(f),
    usedBy: d.features.filter((x) => (x.dependsOn || []).includes(f.id)).map((x) => x.id),
  }));
  const live = tasks.filter((t) => t.status !== 'dropped');
  const by = (s) => live.filter((t) => t.status === s).length;
  const stages = (d.project.stages || []).map((s) => {
    const st = live.filter((t) => t.stage === s.id);
    return { ...s, total: st.length, done: st.filter((t) => t.status === 'done').length };
  });
  const activity = [];
  const push = (type, o, name) => (o.history || []).forEach((h, i) => activity.push({ ...h, type, id: o.id || 'project', name, i }));
  push('project', d.project, d.project.name);
  tasks.forEach((t) => push('task', t, t.title));
  features.forEach((f) => push('feature', f, f.name));
  changes.forEach((c) => push('change', c, c.title));
  activity.sort((a, b) => (b.date || '').localeCompare(a.date || '') || b.i - a.i);
  return {
    project: strip(d.project), plan: d.plan, tasks, features, changes, stages,
    stats: {
      total: live.length, done: by('done'), doing: by('doing'), review: by('review'), todo: by('todo'),
      rework: by('rework'), verify: by('verify'), blocked: by('blocked'),
      features: features.length,
      openChanges: changes.filter((c) => !['done', 'rejected'].includes(c.status)).length,
    },
    next: nextTasks(d).slice(0, 5).map((t) => t.id),
    activity: activity.slice(0, 60).map(({ i, ...a }) => a),
    check: { errors, warnings },
    generatedAt: new Date().toISOString(),
  };
}

function versionOf(dir) {
  const h = crypto.createHash('md5');
  const walk = (p) => {
    for (const f of fs.readdirSync(p, { withFileTypes: true })) {
      if (f.name === '_tools' || f.name.startsWith('.')) continue;
      const fp = path.join(p, f.name);
      if (f.isDirectory()) walk(fp);
      else { const s = fs.statSync(fp); h.update(`${fp}:${s.mtimeMs}:${s.size};`); }
    }
  };
  walk(dir);
  return h.digest('hex');
}

function template() {
  const local = path.join(HERE, 'dashboard.html');
  return fs.readFileSync(local, 'utf8');
}

function renderHtml(data, mode) {
  const json = JSON.stringify(data).replace(/</g, '\\u003c');
  return template()
    .replace('/*__DATA__*/null', json)
    .replace('/*__MODE__*/"static"', JSON.stringify(mode));
}

// ---------- 명령 ----------
const dir = cmd === 'init' ? null : resolveDir();

if (cmd === 'check') {
  const d = load(dir);
  const { errors, warnings } = check(d);
  warnings.forEach((w) => console.log(`⚠️  ${w}`));
  errors.forEach((e) => console.log(`❌ ${e}`));
  console.log(errors.length ? `\n오류 ${errors.length}건 — 수정이 필요합니다.` : `\n✅ 검사 통과 (경고 ${warnings.length}건)`);
  process.exit(errors.length ? 1 : 0);
}

else if (cmd === 'status') {
  const d = load(dir); const m = model(d);
  const s = m.stats;
  console.log(`# ${m.project.name}`);
  console.log(`작업 ${s.done}/${s.total} 완료 · 진행 ${s.doing} · 리뷰 ${s.review} · 재작업 ${s.rework} · 재검증 ${s.verify} · 막힘 ${s.blocked}`);
  m.stages.forEach((st) => console.log(`  ${st.id} ${st.name}: ${st.done}/${st.total}`));
  console.log(`기능 ${s.features}개 · 진행 중 수정요청 ${s.openChanges}건`);
  console.log(`다음 작업: ${m.next.join(', ') || '없음'}`);
  if (m.check.errors.length) console.log(`❌ 검사 오류 ${m.check.errors.length}건 — check 로 확인`);
}

else if (cmd === 'next') {
  const d = load(dir);
  const n = nextTasks(d);
  if (!n.length) { console.log('진행 가능한 작업이 없습니다.'); process.exit(0); }
  n.slice(0, 5).forEach((t) => console.log(`${t.id}\t[${t.status}]\t${t.stage}\t${t.title}\t기능:${(t.features || []).join(',')}`));
}

else if (cmd === 'build') {
  const d = load(dir);
  const out = path.resolve(opt('out', path.join(dir, 'dashboard.html')));
  fs.writeFileSync(out, renderHtml(model(d), 'static'));
  console.log(`대시보드 생성: ${out}`);
}

else if (cmd === 'serve') {
  const port = Number(opt('port', 4800));
  const server = http.createServer((req, res) => {
    try {
      if (req.url.startsWith('/api/version')) {
        res.writeHead(200, { 'content-type': 'application/json' });
        return res.end(JSON.stringify({ v: versionOf(dir) }));
      }
      if (req.url.startsWith('/api/data')) {
        res.writeHead(200, { 'content-type': 'application/json; charset=utf-8' });
        return res.end(JSON.stringify(model(load(dir))));
      }
      res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      res.end(renderHtml(model(load(dir)), 'live'));
    } catch (e) {
      res.writeHead(500, { 'content-type': 'text/plain; charset=utf-8' });
      res.end(String(e.message || e));
    }
  });
  server.listen(port, () => console.log(`대시보드: http://localhost:${port}  (파일이 바뀌면 자동 갱신, 종료: Ctrl+C)`));
}

else if (cmd === 'init') {
  const root = path.resolve(args[1] && !args[1].startsWith('--') ? args[1] : process.cwd());
  const pdir = path.join(root, '.project');
  const name = opt('name', path.basename(root));
  for (const sub of ['tasks', 'features', 'changes', '_tools']) fs.mkdirSync(path.join(pdir, sub), { recursive: true });
  for (const f of ['project-dashboard.mjs', 'dashboard.html']) fs.copyFileSync(path.join(HERE, f), path.join(pdir, '_tools', f));
  const schema = path.join(HERE, '..', 'SCHEMA.md');
  if (fs.existsSync(schema)) fs.copyFileSync(schema, path.join(pdir, '_tools', 'SCHEMA.md'));
  const today = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Seoul' }).format(new Date());
  const pj = path.join(pdir, 'project.json');
  if (!fs.existsSync(pj)) {
    fs.writeFileSync(pj, JSON.stringify({
      name, summary: '', stack: '', commands: { test: '', testOne: '', build: '' },
      stages: [], updatedAt: today,
      history: [{ date: today, by: 'ai', text: '프로젝트 생성' }],
    }, null, 2) + '\n');
  }
  const plan = path.join(pdir, 'plan.md');
  if (!fs.existsSync(plan)) fs.writeFileSync(plan, `# ${name} 기획\n\n(대화로 작성 중)\n`);
  for (const sub of ['tasks', 'features', 'changes']) {
    const keep = path.join(pdir, sub, '.gitkeep');
    if (!fs.existsSync(keep)) fs.writeFileSync(keep, '');
  }
  console.log(`생성 완료: ${pdir}\n대시보드: node .project/_tools/project-dashboard.mjs serve`);
}

else {
  console.log(fs.readFileSync(fileURLToPath(import.meta.url), 'utf8').split('\n').slice(1, 11).map((l) => l.replace(/^\/\/ ?/, '')).join('\n'));
}
