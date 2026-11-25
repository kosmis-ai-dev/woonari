# 소셜 로그인 API

카카오·구글·네이버의 로그인 시작, 회원 생성, 토큰 발급·갱신, 내 정보 조회와 로그아웃을 제공합니다. 현재 API·DB·모의 테스트까지 준비했습니다. 사용자 요청에 따라 실제 앱 키 입력과 계정 로그인 확인은 나중에 진행합니다.

## 설정

```sh
./woonari auth init
./woonari auth status
```

앱 설정은 `/Users/kosmis/work/kosmis/un/.local/woonari/auth/providers.env`에만 입력합니다. 파일 권한은600이며 Git·채팅에 키 값을 넣지 마세요.

| 설정 | 값 |
|---|---|
| `AUTH_PUBLIC_BASE_URL` | API 주소, 기본 `http://127.0.0.1:9090` |
| `KAKAO_CLIENT_ID` | 카카오 REST API 키 |
| `KAKAO_CLIENT_SECRET` | 같은 REST API 키의 Client secret |
| `GOOGLE_CLIENT_ID` | Google 웹 애플리케이션 OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | 같은 Google 클라이언트의 secret |
| `NAVER_CLIENT_ID` | 네이버 로그인 애플리케이션 Client ID |
| `NAVER_CLIENT_SECRET` | 같은 네이버 애플리케이션의 secret |

각 콘솔에 다음 Redirect/Callback URI를 등록합니다.

| 제공자 | 로컬 콜백 URI |
|---|---|
| 카카오 | `http://127.0.0.1:9090/v1/auth/kakao/callback` |
| 구글 | `http://127.0.0.1:9090/v1/auth/google/callback` |
| 네이버 | `http://127.0.0.1:9090/v1/auth/naver/callback` |

카카오는 로그인 사용 설정과 프로필 동의 항목을, Google은 웹 애플리케이션 자격증명·동의 화면을, 네이버는 로그인 애플리케이션과 프로필 제공 항목을 준비합니다. 네이버는 최신 OIDC 경로를 사용합니다. 닉네임·이메일 동의를 받지 못해도 제공자 고유 ID로 로그인합니다. [공식 문서 근거](social-login-sources.md)

`localhost`를 사용할 경우 BASE URL·등록한 콜백·브라우저 주소를 모두 같은 호스트로 통일하세요. 운영은 HTTPS를 사용합니다. BASE URL에는 경로·query·fragment를 붙이지 않습니다.

설정 후 `./woonari stop`과 `./woonari start`로 적용합니다. 미설정 제공자는 `503 social_not_configured`입니다. `configured: true`는 설정값 존재를 뜻하며 실제 로그인 성공을 뜻하지 않습니다.

## 호출 방법

[Swagger](http://127.0.0.1:9090/docs)의 **소셜 로그인 · 카카오·구글·네이버** 그룹을 사용합니다. `{provider}`는 `kakao`, `google`, `naver`이며 Swagger에는 각각 표시됩니다.

| 메서드 | 경로 | 기능 |
|---|---|---|
| GET | `/v1/auth/providers` | 설정 여부·호출 경로·콜백 주소 |
| GET | `/v1/auth/{provider}/authorize` | 로그인 URL 반환·브라우저 요청 쿠키 생성 |
| GET | `/v1/auth/{provider}/login` | 제공자 로그인 화면으로302 이동 |
| GET | `/v1/auth/{provider}/callback` | 로그인 완료·회원 생성·서비스 토큰 발급 |
| GET | `/v1/auth/me` | Bearer 토큰으로 내 회원 정보 조회 |
| POST | `/v1/auth/refresh` | 갱신 토큰으로 새 토큰 발급 |
| POST | `/v1/auth/logout` | 현재 로그인 세션 폐기 |

1. 브라우저 주소창에서 `http://127.0.0.1:9090/v1/auth/kakao/login`처럼 시작 주소를 엽니다.
2. 제공자에서 로그인·동의를 완료합니다. 같은 브라우저의 쿠키가 필요합니다.
3. 콜백 JSON에서 `access_token`, `refresh_token`, `user`를 받습니다. 토큰을 URL이나 공개 로그에 넣지 마세요.
4. `/v1/auth/me` 등에 `Authorization: Bearer <access_token>`을 사용합니다. Swagger **Authorize**에도 같은 토큰을 입력합니다.

Swagger에서 URL만 받을 때는 `/authorize`를 실행하고 반환된 `authorization_url`을 같은 브라우저에서 여세요. `/callback`은 제공자가 호출하는 경로이며 임의 code·state는 거절합니다. 현재 콜백은 JSON을 반환하고 프론트엔드 임의 주소로 리다이렉트하지 않습니다.

## 토큰·회원

자체 토큰은 임의 문자열입니다. Access token은 최대15분, 로그인 세션은 최초 로그인부터30일입니다. `/refresh`에는 다음 본문을 보냅니다.

```json
{"refresh_token": "<refresh_token>"}
```

갱신 후 새 access/refresh token으로 교체합니다. 이전 갱신 토큰을 재사용하면 해당 세션을 폐기합니다. 로그아웃은 현재 Woonari 세션만 종료하고 다른 기기의 세션은 유지합니다.

`user`에는 회원 ID·닉네임·선택 이메일·이메일 확인 여부·제공자 목록·생성 시각을 제공합니다. 제공자 고유 ID·제공자 토큰은 반환하지 않습니다. 같은 제공자의 같은 ID는 기존 회원이며 이메일이 같아도 다른 제공자의 계정을 자동 병합하지 않습니다. 네이버 이메일은 인증 상태가 없어 `email_verified=false`입니다. 네이버 ID 토큰과 프로필 ID의 일치는 실제 앱 설정 후 최종 확인해야 합니다.

기존 운세 API의 `X-API-Key` 방식은 유지합니다. 소셜 로그인 시작·콜백에는 이 키를 요구하지 않고 내 정보·로그아웃에는 자체 Bearer 토큰을 사용합니다. 운세 API를 자동으로 회원 전용으로 바꾸지는 않습니다.

## DB·검증

공식 실행은 전용 Secrets Manager 연결의 MySQL `woonari`를 사용합니다. 신규 설치 시 `./woonari db init-auth`로 다음 인증 전용 표5개를 생성·검증합니다.

- `woonari_auth_users`
- `woonari_auth_identities`
- `woonari_auth_sessions`
- `woonari_auth_used_refresh`
- `woonari_auth_states`

런타임은 스키마를 검증하며 자동 변경하지 않습니다. 과거 회원을 가져오거나 기존 운세 자료를 바꾸지 않습니다. 독립 개발·테스트용 SQLite는 전용 `.local/woonari/auth/`에 저장합니다. MySQL 실패 시 SQLite로 대체하지 않습니다.

제공자 토큰은 저장하지 않고 자체 토큰은 해시만 저장합니다. State는10분 유효·브라우저/제공자 바인딩·일회성을 적용합니다. PKCE를 사용하며 Google·Naver ID 토큰의 서명·발급자·대상·만료·nonce를 검증합니다. 외부 오류 원문·키를 응답에 넣지 않습니다. 공식 실행기는 인증 코드가 포함될 수 있는 접근 로그를 출력하지 않습니다.
