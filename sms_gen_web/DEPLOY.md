# 🚀 배포 가이드

## 📋 필요한 파일 목록

배포하기 전에 다음 파일들이 모두 준비되었는지 확인하세요:

```
project/
├── main_app.py              # 메인 Streamlit 애플리케이션
├── enhanced_processor.py    # 향상된 데이터 처리 모듈
├── requirements.txt         # 패키지 의존성
├── run.py                  # 로컬 실행 스크립트 (선택)
├── README.md               # 사용 설명서
├── DEPLOY.md              # 이 파일
└── .streamlit/
    └── config.toml         # Streamlit 설정 (선택)
```

## 🌐 Streamlit Cloud 무료 배포

### 1단계: GitHub 저장소 생성

1. **GitHub 계정 준비**
   - [GitHub](https://github.com)에서 계정 생성/로그인

2. **새 저장소 생성**
   ```
   Repository name: travel-message-generator
   Description: 여행 잔금 문자 생성기
   Public/Private: Public (무료 배포용)
   ```

3. **파일 업로드**
   - 위의 모든 파일들을 저장소에 업로드
   - 또는 로컬에서 git을 사용하여 push

### 2단계: Streamlit Cloud 배포

1. **Streamlit Cloud 접속**
   - [share.streamlit.io](https://share.streamlit.io) 방문

2. **GitHub 연동**
   - GitHub 계정으로 로그인
   - 저장소 접근 권한 승인

3. **앱 배포**
   - "New app" 클릭
   - Repository: `your-username/travel-message-generator`
   - Branch: `main`
   - Main file path: `main_app.py`
   - "Deploy!" 클릭

4. **배포 완료**
   - 몇 분 후 `https://your-app-name.streamlit.app` URL 생성
   - 이 URL을 사용자들과 공유

## 🖥️ 로컬 개발 환경 설정

### 방법 1: run.py 사용 (권장)
```bash
python run.py
```

### 방법 2: 직접 실행
```bash
# 패키지 설치
pip install -r requirements.txt

# 애플리케이션 실행
streamlit run main_app.py
```

## 🔧 배포 후 설정

### 커스텀 도메인 (선택사항)
- Streamlit Cloud에서 커스텀 도메인 설정 가능
- 유료 플랜에서만 지원

### 환경 변수 설정 (필요시)
```toml
# .streamlit/secrets.toml
[passwords]
admin_password = "your_password"
```

### 성능 최적화
```toml
# .streamlit/config.toml
[server]
maxUploadSize = 200
enableCORS = false

[browser]
gatherUsageStats = false
```

## 📊 리소스 제한 (무료 플랜)

Streamlit Cloud 무료 플랜 제한사항:
- **CPU**: 1 core
- **메모리**: 1GB RAM
- **스토리지**: 임시 (재시작 시 초기화)
- **동시 사용자**: 제한 없음
- **업타임**: 앱이 사용되지 않으면 자동 sleep

### 최적화 팁:
1. **파일 크기**: 엑셀 파일 50MB 이하 권장
2. **메모리 관리**: 대용량 데이터 처리 시 청크 단위로 처리
3. **캐싱**: `@st.cache_data` 활용

## 🛠️ 문제 해결

### 배포 오류
```
ModuleNotFoundError: No module named 'xxx'
```
**해결**: `requirements.txt`에 누락된 패키지 추가

### 메모리 오류
```
Resource limits exceeded
```
**해결**: 데이터를 작은 단위로 나누어 처리

### 파일 업로드 오류
```
File size exceeds limit
```
**해결**: `.streamlit/config.toml`에서 `maxUploadSize` 증가

## 🔄 업데이트 방법

1. **코드 수정**
   - GitHub 저장소에서 파일 수정
   - 또는 로컬에서 수정 후 git push

2. **자동 재배포**
   - Streamlit Cloud가 변경사항을 자동 감지
   - 몇 분 내에 업데이트 반영

## 🔒 보안 고려사항

### 민감한 정보 보호
- 데이터베이스 연결 정보 등은 secrets.toml 사용
- 개인정보가 포함된 엑셀 파일 주의

### 접근 제한 (필요시)
```python
# main_app.py에 추가
if "authenticated" not in st.session_state:
    password = st.text_input("비밀번호", type="password")
    if password == "your_password":
        st.session_state.authenticated = True
    else:
        st.stop()
```

## 📈 모니터링

### 사용 통계 확인
- Streamlit Cloud 대시보드에서 확인 가능
- 사용자 수, 세션 시간 등

### 로그 확인
- 배포 페이지에서 "Manage app" → "Logs"
- 오류 발생 시 로그 확인

## 💡 추가 기능 아이디어

1. **사용자 인증**: 로그인 시스템 추가
2. **데이터베이스 연동**: PostgreSQL, MySQL 등
3. **API 연동**: 문자 발송 API 연결
4. **파일 저장**: Google Drive, AWS S3 등
5. **템플릿 관리**: 여러 템플릿 저장/불러오기

## 📞 지원

- **GitHub Issues**: 버그 리포트 및 기능 요청
- **Streamlit Community**: [discuss.streamlit.io](https://discuss.streamlit.io)
- **문서**: [docs.streamlit.io](https://docs.streamlit.io)