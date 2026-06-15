# OAuth setup

<p align="right">
  <a href="../ko/oauth.md">한국어</a> ·
  <strong>English</strong>
</p>

Google and Kakao OIDC sign-in is handled by [Authlib](https://docs.authlib.org/). Username/password login remains unchanged.

## Google

1. Create an OAuth 2.0 Client ID (Web application) in the [Google Cloud Console](https://console.cloud.google.com/)
2. Scopes: `openid`, `profile`, `email`
3. Authorized redirect URIs (must match exactly):

   - Local: `http://127.0.0.1:5000/auth/oauth/google/callback`
   - Production: `https://YOUR_DOMAIN/auth/oauth/google/callback`

4. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`

## Kakao

1. Register an app in [Kakao Developers](https://developers.kakao.com/) and enable **Kakao Login**
2. Enable **OpenID Connect (OIDC)**
3. Consent items: **nickname (`profile_nickname`)**, **account email (`account_email`)**, etc.
4. `KAKAO_CLIENT_ID` = REST API key. Set `KAKAO_CLIENT_SECRET` if the app uses a client secret
5. Redirect URIs:

   - Local: `http://127.0.0.1:5000/auth/oauth/kakao/callback`
   - Production: `https://YOUR_DOMAIN/auth/oauth/kakao/callback`

### Kakao server IP

Add your deployment server's **outbound public IP** to Kakao **Allowed IP**. `127.0.0.1` does not apply to server-side Kakao API calls.

### Email verification

Accounts link only when the provider reports a **verified email** (`email_verified`). Kakao ID tokens may include `email` without `email_verified`; the app confirms verification via OIDC userinfo or `/v2/user/me`.

## Behavior summary

- Unconfigured providers do not render sign-in buttons.
- On success the session is rotated while the visitor's **locale** is preserved.

See [Configuration](configuration.md) for environment variables.
