# OAuth 설정

<p align="right">
  <strong>한국어</strong> ·
  <a href="../en/oauth.md">English</a>
</p>

Google·Kakao OIDC 로그인은 [Authlib](https://docs.authlib.org/)로 처리합니다. 기존 아이디/비밀번호 로그인은 그대로 동작합니다.

## Google

1. [Google Cloud Console](https://console.cloud.google.com/)에서 OAuth 2.0 클라이언트 ID(웹 애플리케이션) 생성
2. 스코프: `openid`, `profile`, `email`
3. 승인된 리디렉션 URI (정확히 일치):

   - 로컬: `http://127.0.0.1:5000/auth/oauth/google/callback`
   - 프로덕션: `https://YOUR_DOMAIN/auth/oauth/google/callback`

4. `.env`에 `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` 설정

## Kakao

1. [Kakao Developers](https://developers.kakao.com/)에서 앱 등록 후 **Kakao Login** 활성화
2. **OpenID Connect(OIDC)** 활성화
3. 동의 항목: **닉네임(profile_nickname)**, **계정 이메일(account_email)** 등
4. `KAKAO_CLIENT_ID` = REST API 키. 시크릿 사용 시 `KAKAO_CLIENT_SECRET` 설정
5. Redirect URI:

   - 로컬: `http://127.0.0.1:5000/auth/oauth/kakao/callback`
   - 프로덕션: `https://YOUR_DOMAIN/auth/oauth/kakao/callback`

### Kakao 서버 IP

Kakao **허용 IP**에 배포 서버의 **아웃바운드 공인 IP**를 등록해야 합니다. 로컬 `127.0.0.1`은 서버→Kakao API 호출에 적용되지 않습니다.

### 이메일 검증

공급자가 **검증된 이메일**(`email_verified`)을 반환할 때만 계정을 연결합니다. Kakao는 ID 토큰에 `email`만 있고 `email_verified`가 없을 수 있어, 앱이 OIDC userinfo 또는 `/v2/user/me`로 검증 여부를 추가 확인합니다.

## 동작 요약

- 설정되지 않은 공급자는 UI에 버튼이 표시되지 않습니다.
- 로그인 성공 시 세션은 교체되며, 사용자가 선택한 **언어(locale)는 유지**됩니다.

환경 변수는 [환경 변수](configuration.md)를 참고하세요.
