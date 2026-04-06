
## OpenAI API Key 설정 방법

### 🐧 Linux / 🍎 macOS

**임시 설정** (현재 터미널 세션에서만 유효)

```bash
export OPENAI_API_KEY='sk-...'
```

**영구 설정** (터미널을 새로 열어도 유지)

```bash
# bash 사용자
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
source ~/.bashrc

# zsh 사용자 (macOS 기본 셸)
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.zshrc
source ~/.zshrc
```

---

### 🪟 Windows

**명령 프롬프트 (CMD) — 임시 설정**

```cmd
set OPENAI_API_KEY=sk-...
```

**PowerShell — 임시 설정**

```powershell
$env:OPENAI_API_KEY="sk-..."
```

**영구 설정 (시스템 환경변수 등록)**

```powershell
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-...", "User")
```

---

### ✅ 설정 확인

```bash
# Linux / macOS
echo $OPENAI_API_KEY

# Windows CMD
echo %OPENAI_API_KEY%

# PowerShell
echo $env:OPENAI_API_KEY
```

정상적으로 설정되었다면 `sk-`로 시작하는 키가 출력된다.

---

### ⚠️ 주의사항

- API 키는 `sk-`로 시작하는 문자열이다.
- 키를 코드에 직접 하드코딩하지 않는다. `.env` 파일이나 환경변수로만 관리한다.
- `.env` 파일을 사용할 경우 반드시 `.gitignore`에 추가하여 키가 외부에 노출되지 않도록 한다.