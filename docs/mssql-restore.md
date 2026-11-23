# MSSQL 백업 복원과 판정 자료 상태

CR-014 / T-029~T-031, 조사일 2026-11-19.

후속 CR-015에서는 연간·월별 2개 표를 넘어 비회원 un 자료 78개 표·100,929행을 별도로 복원했다. 현재 전체 범위와 연결 상태는 [비회원 un 자료 전체 복원](un-data-restore.md)을 따른다. 아래는 최초 연간 자료 조사 결과이며 2027년의 미작성 상태는 유지된다.

제공된 DB 압축파일의 `dbkosmis_20251106.bak`를 전용 SQL Server에 복원했다. 원본 파일은 변경하지 않았으며 복원 DB는 읽기 전용이다. `RESTORE VERIFYONLY`와 `DBCC CHECKDB(PHYSICAL_ONLY)` 검사를 통과했다. 이는 물리 무결성 검사이며 운세 판정의 정확성을 보증하지 않는다.

복원 컨테이너 `woonari-restore-sql-20251106`은 외부 네트워크와 공개 포트가 없다. 복원 파일·암호·원문·조사 보고서는 `.local/woonari/restore/`에만 보관한다. 로컬 Apple Silicon에서 x86 에뮬레이션으로 조사했으며 운영용 SQL Server 환경으로 사용하지 않는다.

## 확보한 자료

| 원본 표 | 행 수 | 확인된 상태 |
|---|---:|---|
| `TB_yearLuck` | 7,000 | 2001~2050년, 기준 간 10 × 성별 bit 2 × chapter 7 |
| `TB_yearLuck_mon` | 1,200 | 기준 간 10 × 성별 bit 2 × 간지 60쌍, 본문 빈 행 없음 |
| `yearfortune del` | 0 | 기존 ASP가 사용하는 구 구조에는 데이터가 없음 |
| `tb_manse` | 47,846 | 기존 서비스 만세력 73,414행과 다른 자료이므로 대체하지 않음 |

**2027년 자료 140행은 미작성 초기 행이다.** 본문이 모두 빈 문자열이고, 별점은 1, 점수 11개와 부적 ID 5개는 모두 0이다. 같은 상태가 2021~2050년에 반복된다. 실제 본문이 있는 연도는 2001~2020년이다. 빈 행의 별점·0점을 개인의 길흉으로 해석하지 않는다.

웹 백업과 기존 ASP는 2014년까지의 구 연간 로직이 같다. 새 `TB_yearLuck` 호출부는 찾지 못했다. 관련 SQL 정의와 매개변수는 읽었으나 저장 프로시저를 실행하지 않았다. 회원·상담·결제·로그 행은 읽거나 이관하지 않았다.

## MySQL 보관과 조회

전용 Secrets Manager 연결로 **`woonari`** DB의 다음 표만 만든다.

- `woonari_legacy_year_luck`
- `woonari_legacy_year_luck_month`
- `woonari_legacy_fortune_metadata`

원본의 선택 키·본문·별점·점수·부적 ID를 그대로 보존하고 작성/수정 일시는 제외한다. 성별 SQL `bit`만 정수 0/1로 저장하며 남녀 의미를 임의 부여하지 않는다. 메타데이터에 원본/정규화 데이터 해시, 행 수, 열, 자연 키, 빈 초기 행의 품질 상태와 `mapping_status=unverified`를 기록한다. 본문은 비공개 DB에 보존하며 Python 패키지나 Git에 포함하지 않는다.

```sh
./woonari db sync-restored .local/woonari/restore/exports
```

적재 도구는 고정된 두 원본 파일의 SHA-256, 열·형식·중복·전체 키 범위를 먼저 검사한다. InnoDB·스키마·인덱스·트리거를 확인하고 별도 잠금과 트랜잭션으로 두 표를 함께 적재한다. 행과 출처를 재조회해 전체 해시를 비교한다. 같은 원본의 재실행은 `already_present`, 기존 자료가 다르면 보존 후 중단한다. 기존 만세력을 덮어쓰거나 삭제하지 않는다.

공식 `./woonari` 서버는 기존 MySQL 연결을 읽기 전용 진단 어댑터에도 연결한다. Swagger의 **시작 안내 → 복원 DB · 연간 un 자료와 남은 문제 확인**에서 연도를 바꿔 조회한다.

```text
GET /v1/restored-data?year=2027
```

이 경로는 적재 출처·행 수·빈 초기 행·필요 매핑을 반환한다. AI 호출과 사용량 차감은 없으며 원문·사용자 데이터·접속정보를 반환하지 않는다. 연결/출처/행 수 이상은 `503 restored_data_unavailable`이다. 어댑터가 없는 실행은 `status=not_connected`이다.

## 개인별 연간 해석을 활성화하기 위한 자료

기존 ASP의 선택은 `yearfortune WHERE memno + sex + year_pillar ORDER BY num`이다. 복원된 새 표는 다른 구조다.

- `sp_yearLuck_getContents`: `gan_ref + gend_ref + year_act`
- `sp_yearLuck_getContents_mon`: `gan_ref + gend_ref + gan_act + ji_act`

SQL의 연간 BU 조회 순서는 `chapter ASC, idx DESC`, BU 최종 결과는 `a_chapter ASC`다. 바깥 getter에는 `ORDER BY`가 없다. 이 사실을 구 `num` 순서와 동일하다고 간주하지 않는다.

다음 원본 코드·명세 또는 검증된 대조 결과가 필요하다.

1. `gan_ref`가 어떤 주의 천간인지와 0~9의 순서. 일반 천간은 `甲乙丙丁戊己庚辛壬癸`, 기존 도깨비 memno는 `己壬丁甲辛戊癸丙乙庚`로 서로 다르다.
2. `gend_ref` 0/1의 남녀 대응.
3. chapter 1~7의 실제 제목, score1~11의 항목·기간 의미.
4. 월별 `gan_act/ji_act`의 선택 및 절기 경계·표시기간 규칙.
5. **실제 값이 작성된 2027년 판정 자료 또는 승인된 신규 판정 로직.** 현재의 빈 기본 행은 충분한 자료가 아니다.

현재 연간 API는 기존 2001~2014년 조회키 진단을 유지하고, 그 밖의 연도는 `422 legacy_year_unsupported`다. 구 판정표나 새 표 매핑이 미완성인 상태에서 AI에게 점수·분기·2027년 내용을 채우도록 하지 않는다. 궁합 `tbAisyo`, 직업 COM, 별도 interlife·택일·행성 판정 자료의 누락도 이번 복원으로 자동 해결되지 않았다.

## 출처 검증값

| 항목 | SHA-256 |
|---|---|
| DB 7z 원본 | `92df12b4fc31d7a3ff26b5c130cdb04dc9a4bb73c6f1e376b331120b45de8c47` |
| 연간 선별 JSON | `869a1074b7c8e55c4fdd5ff45401317297ce2d10330e5fbeab7ee0a0d3c9e4b7` |
| 월별 선별 JSON | `f427c8bb5d34da799f9b1c51f55863e9851e7f5db78b08a3b3edc8e8976e49d5` |

전체 원본 목록·복원 결과·SQL 정의·연도별 품질 증거는 비공개 복원 폴더에 있으며 배포 대상이 아니다.
