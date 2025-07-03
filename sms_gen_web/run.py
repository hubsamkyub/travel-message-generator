#!/usr/bin/env python3
"""
여행 잔금 문자 생성기 실행 스크립트
"""

import subprocess
import sys
import os

def check_requirements():
    """필요한 패키지가 설치되었는지 확인"""
    try:
        import streamlit
        import pandas
        import openpyxl
        print("✅ 모든 필요한 패키지가 설치되어 있습니다.")
        return True
    except ImportError as e:
        print(f"❌ 필요한 패키지가 설치되지 않았습니다: {e}")
        print("📦 다음 명령어로 패키지를 설치해주세요:")
        print("   pip install -r requirements.txt")
        return False

def main():
    print("🚀 여행 잔금 문자 생성기를 시작합니다...")
    print("-" * 50)
    
    # 현재 디렉토리 확인
    current_dir = os.getcwd()
    print(f"📁 현재 디렉토리: {current_dir}")
    
    # 필요한 파일들 확인
    required_files = ['main_app.py', 'enhanced_processor.py', 'requirements.txt']
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (없음)")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️ 다음 파일들이 필요합니다: {', '.join(missing_files)}")
        return
    
    # 패키지 확인
    print("\n📦 패키지 확인 중...")
    if not check_requirements():
        return
    
    # Streamlit 실행
    print("\n🌐 웹 애플리케이션을 시작합니다...")
    print("🔗 브라우저에서 http://localhost:8501 로 접속하세요")
    print("⏹️ 종료하려면 터미널에서 Ctrl+C를 누르세요")
    print("-" * 50)
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "main_app.py"])
    except KeyboardInterrupt:
        print("\n\n👋 애플리케이션이 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()