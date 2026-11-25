# Woonari 독립 환경

CR-006 / T-013 · 공식 실행·계정 진입점은 저장소 루트의 `./woonari`입니다. 동일한 Mac에서 프로세스와 설정·인증 경로를 분리하며 다른 프로젝트의 설정과 계정을 변경하지 않습니다. 별도 OS나 운영 AWS 리소스를 생성하는 작업은 포함하지 않습니다.

## 로컬 실행

```sh
./woonari init
./woonari start
./woonari status
./woonari stop
```

- Swagger: http://127.0.0.1:9090/docs
- 이 프로젝트 전용 보드: http://127.0.0.1:18101/
- Python 가상환경: `python_api/.venv/`
- 전용 설정/계정/로그: `.local/woonari/` (디렉터리 700, 설정 파일 600)
- 계정 지정 상태: `./woonari config show` (토큰·키는 표시하지 않음)

서버는 127.0.0.1에만 바인딩합니다. 다른 프로세스가 포트를 점유하면 실패하며 자동 종료하지 않습니다. 종료 시 전용 상태 기록과 실제 프로세스 식별을 비교합니다. 보드는 이 프로젝트의 `.project`만 표시합니다.

Node·Git·GitHub CLI·AWS CLI 실행 파일은 설치된 도구를 사용하며 계정 설정은 프로젝트 전용 경로로 고정합니다. 초기화에서 설치된 Node를 전용 `bin/node`에 등록합니다. Git LFS가 필요한 환경은 공식 Git LFS 실행 파일을 `.local/woonari/bin/git-lfs`에 설치합니다. 전용 상태 전체는 Git과 배포 사본에서 제외합니다.

새 환경에서 Python 의존성을 먼저 설치합니다.

```sh
python3 -m venv python_api/.venv
python_api/.venv/bin/python -m pip install -r python_api/requirements.lock
./woonari init
./woonari start
```

## AI 설정

`.local/woonari/api.env`의 빈 값을 직접 입력합니다. 비밀값은 채팅·명령 인자·Git에 저장하지 않습니다.

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=
AI_TIMEOUT_SECONDS=45
AI_MAX_CONCURRENCY=4
API_KEY=
```

실행기는 허용한 운영체제 변수로 자식 환경을 새로 만듭니다. 상속된 AI/GitHub/AWS/SSH 인증, 외부 Python 경로·프록시 설정을 가져오지 않습니다. API는 전용 파일의 5개 설정만 사용하며 기존 `python_api/.env`도 읽지 않습니다. 변경 후 서버를 재시작합니다. 사주 계산 규칙과 AI 출력 계약은 유지합니다.

## GitHub 전용 계정

대상은 `https://github.com/kosmis-ai-dev/woonari.git`입니다. 이메일과 별개인 GitHub 로그인명, 이 프로젝트의 커밋 작성자를 직접 지정합니다.

```sh
./woonari config set git.login GITHUB_USERNAME
./woonari config set git.name COMMIT_NAME
./woonari config set git.email COMMIT_EMAIL
# 대상 저장소에 접근할 전용 토큰을 .local/woonari/github/token에 저장한 후:
./woonari gh auth login
./woonari gh auth status
./woonari git status
```

전용 `GH_CONFIG_DIR`와 Git 설정을 사용합니다. 공용 토큰·글로벌 Git 사용자·osxkeychain credential helper·SSH agent를 대체 인증으로 사용하지 않습니다. GitHub에서 이 저장소만 선택한 전용 토큰을 만들고, 토큰 한 줄을 `.local/woonari/github/token`에 저장합니다. 파일은 소유자만 읽고 쓸 수 있는 `600` 권한이어야 하며 채팅·명령 인자·소스에 토큰 값을 넣지 않습니다. 기존 전용 `hosts.yml` 형식도 지원합니다.

`./woonari gh auth login`은 이 전용 파일을 사용해 실제 로그인 계정을 검증하는 명령입니다. GitHub CLI의 웹 로그인은 `--insecure-storage`를 사용해도 OS Keychain에 접근할 수 있어 실행하지 않습니다. 다른 프로젝트의 Keychain 항목이나 글로벌 Git 설정을 변경하지 않으며, 전용 폴더·파일의 소유자 권한과 심볼릭 링크 여부를 검사합니다. 저장소 쓰기 권한은 push 전에 별도로 확인합니다.

작업 사본은 `.publish/woonari`입니다. 네트워크 명령은 로그인 사용자와 HTTPS origin을 확인하고, push는 저장소 쓰기 권한도 확인합니다. CR-017 사용자 지시에 따라 현재 main 브랜치에 검증된 변경을 계속 push합니다. force push·임의 ref 전송·merge는 허용하지 않습니다. 원격 업로드 완료 여부는 T-012에서 별도 기록합니다.

Python 전용 최초 게시 브랜치는 `./woonari git prepare-python-branch publish/python-api-YYYYMMDD`로 준비합니다. 이전 ASP·대용량 자산 커밋은 로컬에 보존하고 새 게시 커밋의 조상에 포함하지 않습니다. 이 준비는 계정·작성자가 미설정이어도 가능하지만 커밋과 push는 전용 작성자·인증을 지정한 후에만 가능합니다. 자세한 검증·보존 범위는 [Python 전용 작업 안내](python-only.md)를 따릅니다.

GitHub에서 출판본을 clone한 경우에는 `PUBLICATION.json`과 `.git`이 함께 있는 clone 루트 자체가 작업 사본입니다. 일반 원본 폴더에 임의로 만든 Git 저장소는 자동 선택하지 않습니다.

## 신규 AWS 계정

기존 계정이나 `default` 프로필은 사용하지 않습니다. 사용자가 신규 계정의 12자리 ID와 로그인 방식을 먼저 확인해야 합니다. 아래 대문자 값은 실제 새 계정 ID로 바꿉니다.

```sh
./woonari config set aws.account_id NEW_12_DIGIT_ACCOUNT_ID
./woonari config set aws.region ap-northeast-2
./woonari aws configure sso
./woonari aws sso login
./woonari aws sts get-caller-identity
```

프로필명은 `woonari`, 설정·자격증명·SSO 및 세션 캐시는 `.local/woonari/aws/`에 둡니다. `~/.aws`, 상속된 키·프로필·EC2 metadata를 사용하지 않습니다. 서비스 실행 전 STS 계정 ID를 신규 계정 ID와 비교하며 불일치하면 중단합니다. CLI 옵션으로 프로필·endpoint를 바꿔 검사를 우회할 수 없습니다.

공유 도구 설정을 쓰는 `codeartifact login`, `eks update-kubeconfig` 및 역할 전환 옵션은 차단합니다. 프로젝트별 패키지 레지스트리나 Kubernetes 연결은 전용 설정 경로를 구현한 후 추가합니다.

설치된 AWS CLI의 Python 진입점에 프로젝트 캐시 경로를 지정하는 bootstrap을 사용합니다. 지원하지 않는 설치 형태나 캐시 경로 검증 실패 시 공용 캐시로 대체하지 않고 중단합니다. `HOME`은 변경하지 않습니다. 신규 계정 ID가 없으면 인증/서비스 명령도 중단합니다. AWS 리소스·배포·결제를 생성하지 않습니다.

## MySQL 연결 확인

CR-007 / T-015. 프로젝트 루트에서 `./woonari db check`를 실행합니다. 이 명령은 `woonari` AWS 프로필로 `inter`의 `AWSCURRENT` 버전을 읽고, TLS 인증서와 호스트명을 확인한 뒤 MySQL에서 `SELECT 1`을 실행합니다. 접속 정보는 메모리에서만 처리하고, 명령의 출력에는 점검 결과만 표시합니다.

시크릿 JSON에 `host`, `username`, `password`가 필요합니다. `dbname`이 있으면 해당 데이터베이스를 선택하고, 없으면 데이터베이스를 선택하지 않은 상태에서 접속을 확인합니다. `port`가 없으면 `3306`을 사용합니다. `engine`이 있으면 MySQL이어야 합니다. `.local/woonari/db/config.json`에 지정한 `secret_arn`의 리전과 계정을 검증하여 조회합니다. DB 이름을 `database`에 지정하면 시크릿의 `dbname/database`보다 우선합니다. 이번 프로젝트 대상은 `woonari`입니다. [AWS 데이터베이스 시크릿 JSON 형식](https://docs.aws.amazon.com/secretsmanager/latest/userguide/reference_secret_json_structure.html)

PyMySQL은 `python_api/requirements.lock`에 고정되어 있습니다. 다른 환경에서 RDS에 직접 연결할 경우 AWS의 PEM 번들을 `.local/woonari/db/rds-global-bundle.pem`에 둡니다. 자체 CA를 쓰는 MySQL 서버의 PEM 파일은 `.local/woonari/db/mysql-ca.pem`에 둡니다. [AWS RDS 인증서 번들](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html#UsingWithRDS.SSL.CertificatesDownload)

`inter`를 읽으려면 `secretsmanager:GetSecretValue`가 필요합니다. 고객 관리형 KMS 키로 암호화한 경우 해당 키의 `kms:Decrypt` 권한도 필요합니다. 2026-11-13의 기본 리전 조회는 SCP에 거부됐지만, 2026-11-18 사용자가 지정한 `ap-southeast-2`의 시크릿 ARN으로 재검증하여 TLS 로그인·SELECT 1 및 `woonari.tb_manse` 73,414행 적재를 완료했습니다. [Secrets Manager 조회 권한](https://docs.aws.amazon.com/cli/latest/reference/secretsmanager/get-secret-value.html) · [AWS Organizations SCP](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)

## 현재 연결 상태

2026-11-05 신규 IAM 액세스 키 설정 후 `./woonari aws sts get-caller-identity`가 성공했고, 설정한 신규 계정 ID와 실제 STS 계정이 일치함을 확인했습니다. 전용 프로필은 `woonari`, 리전은 `ap-northeast-2`입니다. 키 값과 계정 개인 식별자는 이 문서에 기록하지 않습니다. AWS 리소스 생성·권한 변경은 수행하지 않았습니다.

T-014의 남은 항목은 전용 GitHub 로그인명·커밋 작성자 및 저장소 쓰기 권한 확인입니다. 원격 Git 쓰기는 아직 대기 중이며 과거 공용 Git 인증을 재사용하지 않습니다.


## 만세력 DB 연결

CR-009 / T-017·T-018. [만세력 데이터베이스 안내](../python_api/docs/manse_database.md)의 가져오기 명령을 사용합니다. 공식 API 실행기는 전용 DB 설정의 `manse_backend=mysql`일 때 같은 시크릿으로 지정 DB에 접속합니다. 암호는 메모리에서만 유지하며 연결 정보와 TLS 컨텍스트는 최대 300초간 캐시한 뒤 갱신합니다. DB 오류가 나면 사주 계산은 503으로 중단하며 SQLite나 달력 패키지로 자동 전환하지 않습니다.

CR-010 / T-019·T-020: 원본 MySQL 만세력은 유지하고 사주 조회에 `lunar-leap-flags-v1` 교정표를 적용합니다. 일반 달·윤달 말일의 윤달 여부 10건만 바꾸며, 원본 출처 해시와 예상 행 값이 맞지 않으면 계산을 중단합니다. API 정책은 `asp-manse-db-v4`와 `lunar_correction_version`으로 적용 버전을 표시합니다. 원본 내보내기·재적재·출처 해시는 교정 전 값을 유지합니다.

CR-013 / T-027: `AI_PROVIDER=bedrock`은 명시한 `BEDROCK_AUTH_MODE`만 사용합니다. `iam`은 전용 `./woonari aws` 프로필·계정 검증과 CLI 이력 차단을 사용합니다. `api_key`는 사용자가 승인한 별도 AI 계정의 장기 키로 고정 Bedrock HTTPS 엔드포인트를 호출합니다. 프록시·리다이렉트·자동 재시도는 사용하지 않습니다. DB·Secrets Manager의 AWS 프로필과 계정은 바꾸지 않습니다.

장기 키는 `.local/woonari/ai/bedrock.env`에 `AWS_BEARER_TOKEN_BEDROCK` 한 항목으로 저장하고 권한600을 유지합니다. `api.env`에 `BEDROCK_AUTH_MODE=api_key`, 확인된 AI 계정의 `BEDROCK_ACCOUNT_ID`, 모델·리전을 설정합니다. 발급 계정은 해당 키로 조회한 추론 프로필의 ARN·리전·ID·활성 상태로 검증하며 키 해시와 계정에 묶인 검증 결과를 최대300초 캐시합니다. 키가 바뀌면 다시 검증합니다. 불일치 시503이며 IAM이나 다른 계정으로 대체하지 않습니다. 키·프롬프트·오류 원문은 argv·로그·사용량 DB에 넣지 않습니다.

`AI_DAILY_CALL_LIMIT=100`은 1~100 범위입니다. 공식 실행기와 모든 API 별칭·제공자는 `.local/woonari/ai/usage.sqlite3`를 공유합니다. 한국시간 매일00:00을 기준으로 실제 모델 전송 직전 영속 예약합니다. 전송 후 실패·시간 초과·출력계약 오류도 환불하지 않습니다. 계산·미완성 판정·입력 오류·전송 전 키 검증 실패는 차감하지 않습니다. 101번째 시도는429, 기록 삭제·손상·권한 이상·시계 역행은503으로 차단합니다. 기록을 삭제하거나 자동 초기화하지 않습니다. GET `/v1/ai-usage`에서 `limit`, `used`, `remaining`, `date`, `timezone`, `reset_at`을 확인합니다. 이 한도는 Woonari의 모델 호출에 적용되며 AWS 콘솔이나 다른 앱의 호출까지 제한하지 않습니다.

기존 CLI 계정에서 확인한 Anthropic 사용 목적 양식·SCP 거부 이력은 CR-011에 보존합니다. 현재 선택한 AI 전용 계정의 실제 모델 권한은 개별 생성 테스트로 확인합니다.

## main 전환 · CR-017
`./woonari git promote-main`으로 기존 게시 커밋을 유지하며 main으로 이름을 바꾸고 `./woonari git push`로 게시합니다. `./woonari gh set-default-main`은 로컬과 원격 main 커밋 일치를 확인한 뒤 기본 브랜치를 main으로 설정합니다. 이 명령은 토큰의 저장소 Administration 쓰기 권한이 필요할 수 있습니다. `./woonari git delete-published-branch`는 원격 main 일치·기본 브랜치 main·기존 게시 커밋의 조상 보존을 확인한 경우에만 승인된 이전 게시 브랜치를 삭제합니다. 이후 변경은 관련 검증·보드 갱신·배포 사본 검증 후 main에 커밋/push합니다.

## 소셜 로그인 전용 설정 · CR-022

`./woonari auth init|status`로 `.local/woonari/auth/providers.env`를 준비·확인합니다. 외부 환경변수나 다른 프로젝트의 OAuth 키를 읽지 않습니다. 공식 MySQL `woonari`의 신규 `woonari_auth_*` 5개 표만 사용하며 초기 생성은 `./woonari db init-auth`, 런타임은 읽기 전용 스키마 검증입니다. 과거 회원 데이터를 이관하지 않습니다. [소셜 로그인 가이드](social-login.md)를 참고하세요.
