# 소셜 로그인 제공자 연결 근거 · CR-022 / T-042

`python_api/app/auth_providers.py`는 서버가 직접 발급받은 인증 코드만 교환합니다. 외부 SDK의 임의 토큰을 받아 회원을 생성하는 기능은 포함하지 않습니다. 제공자의 토큰과 오류 원문을 서비스 응답이나 로그에 반환하지 않습니다.

| 제공자 | 인가 | 토큰 교환 | 프로필 |
|---|---|---|---|
| 카카오 | `https://kauth.kakao.com/oauth/authorize` | `https://kauth.kakao.com/oauth/token` | `https://kapi.kakao.com/v2/user/me` |
| 구글 | `https://accounts.google.com/o/oauth2/v2/auth` | `https://oauth2.googleapis.com/token` | `https://openidconnect.googleapis.com/v1/userinfo` |
| 네이버 OIDC | `https://nid.naver.com/oauth2/authorize` | `https://nid.naver.com/oauth2/token` | `https://openapi.naver.com/v1/nid/me` |

## 카카오

REST API 키를 Client ID로 사용합니다. 최신 앱 키는 Client secret이 기본 활성화이므로 관리 화면의 설정에 맞춰 시크릿을 준비해야 합니다. 로그인 활성화와 callback URI 등록이 필요합니다. [카카오 설정 문서](https://developers.kakao.com/docs/en/kakaologin/prerequisite)

인가 코드에 S256 PKCE를 적용합니다. REST 파라미터 표에는 해당 항목이 생략돼 있지만 discovery와 카카오 담당자 답변에서 지원을 확인했습니다. [공식 discovery](https://kauth.kakao.com/.well-known/openid-configuration), [카카오 담당자 답변](https://devtalk.kakao.com/t/code-challenge-code-verifier/136785)

이 구현은 OIDC 활성화를 요구하지 않고 액세스 토큰으로 REST 프로필을 조회합니다. 선택적으로 발급된 ID 토큰을 인증에 사용하지 않습니다. `scope`는 인가 URL에 강제로 추가하지 않고 앱의 동의항목 설정을 따릅니다. 프로필의 양의 정수 `id`가 회원 식별자이며 이메일·닉네임은 없어도 됩니다. 이메일 인증은 `is_email_valid`와 `is_email_verified`가 모두 실제 boolean `true`일 때만 인정합니다. [카카오 REST API](https://developers.kakao.com/docs/ko/kakaologin/rest-api)

## 구글

웹 애플리케이션 OAuth Client ID/secret과 등록한 callback URI를 사용합니다. `openid profile email`, S256 PKCE와 nonce를 요청합니다. ID 토큰은 고정된 Google JWKS의 RSA 공개키로 RS256 서명을 검사하고 발급자·대상 클라이언트·만료·발급 시각·subject·nonce를 확인합니다. 공식 문서가 허용하는 두 발급자 `https://accounts.google.com`, `accounts.google.com`만 허용합니다. 프로필 `sub`와 검증된 토큰 `sub`도 일치해야 합니다. [구글 OIDC](https://developers.google.com/identity/openid-connect/openid-connect), [공식 discovery](https://accounts.google.com/.well-known/openid-configuration)

프로필의 `email_verified`는 boolean `true`만 인정합니다. 이메일은 바뀔 수 있으며 일부 외부 이메일은 Google이 현재 소유권을 보증하지 않으므로 계정 키나 자동 계정 병합 기준으로 사용하지 않습니다. [구글 백엔드 인증 안내](https://developers.google.com/identity/sign-in/web/backend-auth)

## 네이버

최신 OIDC의 `/oauth2/...` 경로를 선택했습니다. 기존 `/oauth2.0/...` OAuth API와 URL 및 필수 입력이 다르므로 혼용하지 않습니다. `openid profile`, S256 PKCE와 nonce를 사용하고 Client secret은 서버의 POST form으로 전달합니다. ID 토큰은 고정된 네이버 JWKS로 RS256 서명·발급자·대상·만료·발급 시각·subject·nonce를 확인합니다. ID 토큰에는 이름·이메일이 없으므로 별도로 프로필을 조회합니다. [네이버 개발가이드 §3.5](https://developers.naver.com/docs/login/devguide/devguide.md), [공식 discovery](https://nid.naver.com/.well-known/openid-configuration)

프로필 `resultcode=00`과 `response.id`를 확인합니다. 제공자는 두 식별자를 앱별 동일인 식별 정보로 설명하므로 이 구현에서는 프로필 ID와 검증된 토큰 subject의 일치를 요구합니다. 이 동일성은 실제 Woonari 앱 계정으로 최종 확인해야 합니다. 이메일 인증 여부는 프로필에 제공되지 않으므로 인증 완료로 표시하지 않습니다. [네이버 프로필 명세](https://developers.naver.com/docs/login/profile/profile.md)

## 검증 경계

세 제공자 모두 토큰 교환은 POST form, 프로필 조회는 Bearer 헤더를 사용합니다. 고정 HTTPS 주소만 호출하고 환경 프록시·HTTP 리다이렉트·자동 재시도를 사용하지 않습니다. ID 토큰의 `jku` 등 임의 주소를 따라가지 않습니다. provider와 subject를 회원 연결 키로 쓰고 이메일이 같다는 이유로 다른 계정을 합치지 않습니다.

`tests/test_auth_providers.py`는 모의 HTTP와 테스트 전용 RSA 키로 정상 교환, 잘못된 서명·알고리즘·발급자·대상·nonce·만료·subject, 프로필 누락·불일치, 오류·timeout·리다이렉트 차단을 검증합니다. 실제 앱 키와 사용자 동의가 필요한 브라우저 로그인 검증은 별도입니다.
