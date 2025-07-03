#!/usr/bin/env python3
"""
여행 잔금 문자 생성기 - 원클릭 실행 스크립트
모든 의존성 설치부터 애플리케이션 실행까지 자동으로 처리합니다.
"""

import os
import sys
import subprocess
import time
import platform
from pathlib import Path

class TravelMessageGeneratorStarter:
    """원클릭 실행을 위한 시작 클래스"""
    
    def __init__(self):
        self.project_name = "여행 잔금 문자 생성기"
        self.version = "1.0.0"
        self.python_min_version = (3, 9)
        self.required_files = [
            'main_app.py',
            'enhanced_processor.py', 
            'ui_helpers.py',
            'requirements.txt'
        ]
        self.optional_files = [
            'error_handler.py',
            'config_manager.py',
            'template_manager.py',
            'performance_optimizer.py'
        ]
    
    def print_banner(self):
        """시작 배너 출력"""
        banner = f"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║  ✈️  {self.project_name}  ✈️                  ║
║                                                          ║
║  버전: {self.version}                                     ║
║  Python 웹 애플리케이션                                    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def check_python_version(self):
        """Python 버전 확인"""
        current_version = sys.version_info
        
        print(f"🐍 Python 버전 확인: {current_version.major}.{current_version.minor}.{current_version.micro}")
        
        if current_version < self.python_min_version:
            print(f"❌ Python {self.python_min_version[0]}.{self.python_min_version[1]} 이상이 필요합니다.")
            print(f"   현재 버전: {current_version.major}.{current_version.minor}")
            print(f"   🔗 Python 다운로드: https://python.org/downloads/")
            return False
        
        print(f"✅ Python 버전 요구사항 충족")
        return True
    
    def check_required_files(self):
        """필수 파일 존재 확인"""
        print("📁 필수 파일 확인 중...")
        
        missing_files = []
        for file in self.required_files:
            if not os.path.exists(file):
                missing_files.append(file)
                print(f"❌ {file}")
            else:
                print(f"✅ {file}")
        
        if missing_files:
            print(f"\n❌ 다음 파일들이 누락되었습니다:")
            for file in missing_files:
                print(f"   - {file}")
            print(f"\n💡 해결방법:")
            print(f"   1. 모든 프로젝트 파일이 같은 디렉토리에 있는지 확인")
            print(f"   2. GitHub에서 전체 프로젝트를 다시 다운로드")
            return False
        
        # 선택적 파일 확인
        print("\n📋 선택적 파일 확인:")
        for file in self.optional_files:
            if os.path.exists(file):
                print(f"✅ {file}")
            else:
                print(f"⚠️ {file} (선택사항)")
        
        return True
    
    def install_requirements(self):
        """패키지 설치"""
        print("\n📦 패키지 설치 중...")
        
        try:
            # pip 업그레이드
            print("🔄 pip 업그레이드 중...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                         check=True, capture_output=True)
            
            # requirements.txt 설치
            if os.path.exists('requirements.txt'):
                print("📋 requirements.txt에서 패키지 설치 중...")
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ 모든 패키지 설치 완료")
                else:
                    print("⚠️ 일부 패키지 설치 실패:")
                    print(result.stderr)
                    print("\n💡 해결 시도 중...")
                    
                    # 개별 패키지 설치 시도
                    essential_packages = [
                        'streamlit>=1.28.0',
                        'pandas>=1.5.0', 
                        'openpyxl>=3.1.0'
                    ]
                    
                    for package in essential_packages:
                        try:
                            subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                         check=True, capture_output=True)
                            print(f"✅ {package}")
                        except subprocess.CalledProcessError:
                            print(f"❌ {package}")
            else:
                print("⚠️ requirements.txt 파일이 없습니다. 기본 패키지 설치 중...")
                essential_packages = [
                    'streamlit',
                    'pandas', 
                    'openpyxl',
                    'xlrd'
                ]
                
                for package in essential_packages:
                    try:
                        subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                     check=True, capture_output=True)
                        print(f"✅ {package}")
                    except subprocess.CalledProcessError:
                        print(f"❌ {package} 설치 실패")
        
        except Exception as e:
            print(f"❌ 패키지 설치 중 오류: {e}")
            return False
        
        return True
    
    def check_streamlit_installation(self):
        """Streamlit 설치 확인"""
        print("\n🔍 Streamlit 설치 확인 중...")
        
        try:
            import streamlit as st
            print(f"✅ Streamlit 설치됨 (버전: {st.__version__})")
            return True
        except ImportError:
            print("❌ Streamlit이 설치되지 않았습니다.")
            
            print("📦 Streamlit 설치 시도 중...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'streamlit'], 
                             check=True, capture_output=True)
                print("✅ Streamlit 설치 완료")
                return True
            except subprocess.CalledProcessError:
                print("❌ Streamlit 설치 실패")
                return False
    
    def create_sample_data(self):
        """샘플 데이터 생성 제안"""
        print("\n📊 샘플 데이터 생성")
        
        if os.path.exists('sample_data.py'):
            response = input("🤔 테스트용 샘플 엑셀 파일을 생성하시겠습니까? (y/n): ")
            
            if response.lower() in ['y', 'yes', '예', 'ㅇ']:
                try:
                    print("📄 샘플 엑셀 파일 생성 중...")
                    
                    # sample_data.py 실행
                    result = subprocess.run([sys.executable, '-c', '''
import sys
sys.path.append(".")
from sample_data import SampleDataGenerator
generator = SampleDataGenerator()
result = generator.generate_realistic_excel(num_teams=2)
print(f"샘플 파일 생성 완료: {result['filename']}")
                    '''], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print("✅ 샘플 파일 생성 완료")
                        print(result.stdout.strip())
                    else:
                        print("⚠️ 샘플 파일 생성 실패 (선택사항이므로 계속 진행)")
                        
                except Exception as e:
                    print(f"⚠️ 샘플 파일 생성 중 오류: {e} (선택사항이므로 계속 진행)")
        else:
            print("⚠️ sample_data.py 파일이 없습니다. (선택사항)")
    
    def start_application(self):
        """애플리케이션 시작"""
        print(f"\n🚀 {self.project_name} 시작 중...")
        print("⏳ 잠시만 기다려주세요...")
        
        try:
            # Streamlit 실행
            print("🌐 웹 브라우저가 자동으로 열립니다...")
            print("🔗 URL: http://localhost:8501")
            print("\n⏹️ 종료하려면 터미널에서 Ctrl+C를 누르세요\n")
            
            # 운영체제별 브라우저 열기 안내
            os_name = platform.system()
            if os_name == "Windows":
                print("💡 Windows: 브라우저가 자동으로 열리지 않으면 http://localhost:8501 로 접속하세요")
            elif os_name == "Darwin":  # macOS
                print("💡 macOS: 브라우저가 자동으로 열리지 않으면 http://localhost:8501 로 접속하세요")
            else:  # Linux
                print("💡 Linux: 브라우저에서 http://localhost:8501 로 접속하세요")
            
            print("=" * 60)
            
            # Streamlit 실행
            subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'main_app.py'])
            
        except KeyboardInterrupt:
            print("\n\n👋 애플리케이션이 종료되었습니다.")
            print("🙏 사용해주셔서 감사합니다!")
        except Exception as e:
            print(f"\n❌ 애플리케이션 실행 중 오류: {e}")
            
            print(f"\n💡 수동 실행 방법:")
            print(f"   streamlit run main_app.py")
    
    def run(self):
        """전체 실행 프로세스"""
        self.print_banner()
        
        # 단계별 검증
        if not self.check_python_version():
            input("\n❌ Python 버전을 업그레이드한 후 다시 실행해주세요. (엔터키로 종료)")
            return False
        
        if not self.check_required_files():
            input("\n❌ 누락된 파일을 추가한 후 다시 실행해주세요. (엔터키로 종료)")
            return False
        
        if not self.install_requirements():
            print("\n⚠️ 패키지 설치에 실패했지만 계속 진행합니다...")
        
        if not self.check_streamlit_installation():
            input("\n❌ Streamlit 설치에 실패했습니다. 수동으로 설치해주세요: pip install streamlit (엔터키로 종료)")
            return False
        
        self.create_sample_data()
        
        # 모든 준비 완료
        print(f"\n🎉 모든 준비가 완료되었습니다!")
        print(f"📋 설치된 구성 요소:")
        print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}")
        print(f"   ✅ Streamlit 웹 프레임워크")
        print(f"   ✅ 필수 파이썬 패키지들")
        print(f"   ✅ {self.project_name} 애플리케이션")
        
        input(f"\n🚀 {self.project_name}을(를) 시작하려면 엔터키를 누르세요...")
        
        self.start_application()
        return True


def main():
    """메인 함수"""
    try:
        starter = TravelMessageGeneratorStarter()
        starter.run()
    except KeyboardInterrupt:
        print("\n\n👋 설치가 취소되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        print(f"\n💡 수동 실행 방법:")
        print(f"   1. pip install streamlit pandas openpyxl")
        print(f"   2. streamlit run main_app.py")

if __name__ == "__main__":
    main()