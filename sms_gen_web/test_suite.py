#!/usr/bin/env python3
"""
여행 잔금 문자 생성기 통합 테스트 스위트
"""

import unittest
import pandas as pd
import tempfile
import os
import json
from datetime import datetime
import sys
import io

# 테스트할 모듈들 import
try:
    from enhanced_processor import EnhancedDataProcessor, EnhancedMessageGenerator
    from ui_helpers import *
    from error_handler import ErrorHandler
    from config_manager import ConfigManager
    from template_manager import TemplateManager
    from sample_data import SampleDataGenerator
except ImportError as e:
    print(f"Warning: Could not import module: {e}")

class TestEnhancedDataProcessor(unittest.TestCase):
    """EnhancedDataProcessor 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        self.processor = EnhancedDataProcessor()
        
        # 테스트용 DataFrame 생성
        self.test_data = pd.DataFrame({
            '팀': ['1팀', '1팀', '2팀', '2팀'],
            '문자 발송 그룹': ['A그룹', 'A그룹', 'B그룹', 'B그룹'],
            '이름': ['김철수', '이영희', '박민수', '정수진'],
            '연락처': ['010-1234-5678', '', '010-5678-1234', ''],
            '상품가': [2800000, 2800000, 2800000, 2800000],
            '잔금': [1500000, 1500000, 1500000, 1500000]
        })
        
        # 매핑 정보
        self.required_columns = {
            '팀': 'team_name',
            '문자 발송 그룹': 'sender_group',
            '이름': 'name'
        }
        
        self.optional_columns = {
            '연락처': 'contact',
            '상품가': 'product_price',
            '잔금': 'total_balance'
        }
    
    def test_natural_sort_key(self):
        """자연 정렬 키 테스트"""
        result = self.processor.natural_sort_key("10팀")
        self.assertIsInstance(result, list)
        self.assertEqual(result, [10, '팀'])
    
    def test_parse_cell_address(self):
        """셀 주소 파싱 테스트"""
        row, col = self.processor.parse_cell_address("A1")
        self.assertEqual((row, col), (0, 0))
        
        row, col = self.processor.parse_cell_address("D2")
        self.assertEqual((row, col), (1, 3))
        
        row, col = self.processor.parse_cell_address("AA10")
        self.assertEqual((row, col), (9, 26))
        
        # 잘못된 주소
        row, col = self.processor.parse_cell_address("Invalid")
        self.assertEqual((row, col), (None, None))
    
    def test_extract_fixed_data(self):
        """고정 데이터 추출 테스트"""
        # 테스트용 DataFrame
        df_raw = pd.DataFrame([
            ['', '', '', '상품명', '하와이 7일'],
            ['', '', '', '완납일', '2024-12-20'],
            ['', '', '', '', '', '', '기준환율', 1300]
        ])
        
        fixed_mapping = {
            'product_name': 'D1',
            'payment_due_date': 'D2',
            'base_exchange_rate': 'G3'
        }
        
        result = self.processor.extract_fixed_data(df_raw, fixed_mapping)
        
        self.assertEqual(result['product_name'], '하와이 7일')
        self.assertEqual(result['payment_due_date'], '2024-12-20')
        self.assertEqual(result['base_exchange_rate'], 1300)
    
    def test_process_group_data(self):
        """그룹 데이터 처리 테스트"""
        result = self.processor.process_group_data(
            self.test_data, 
            self.required_columns, 
            self.optional_columns
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)  # 2개 그룹 예상
        
        # 첫 번째 그룹 검증
        first_group = list(result.values())[0]
        self.assertEqual(first_group['team_name'], '1팀')
        self.assertEqual(first_group['sender_group'], 'A그룹')
        self.assertEqual(first_group['group_size'], 2)
        self.assertIn('김철수', first_group['members'])
        self.assertIn('이영희', first_group['members'])


class TestEnhancedMessageGenerator(unittest.TestCase):
    """EnhancedMessageGenerator 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        self.generator = EnhancedMessageGenerator()
        
        # 테스트용 템플릿
        self.test_template = """안녕하세요, {product_name} 관련 안내입니다.
{group_members_text}
총 잔금: {total_balance:,}원
완납일: {payment_due_date}"""
        
        # 테스트용 그룹 데이터
        self.group_data = {
            'G001': {
                'group_id': 'G001',
                'team_name': '1팀',
                'sender_group': 'A그룹',
                'sender': '김철수',
                'members': ['김철수', '이영희'],
                'group_size': 2,
                'group_members_text': '김철수님, 이영희님',
                'total_balance': 3000000
            }
        }
        
        # 테스트용 고정 데이터
        self.fixed_data = {
            'product_name': '하와이 7일',
            'payment_due_date': '2024-12-20',
            'base_exchange_rate': 1300,
            'current_exchange_rate': 1350
        }
    
    def test_generate_messages_success(self):
        """메시지 생성 성공 테스트"""
        result = self.generator.generate_messages(
            self.test_template,
            self.group_data,
            self.fixed_data
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('messages', result)
        self.assertIn('total_count', result)
        self.assertEqual(result['total_count'], 1)
        
        # 생성된 메시지 검증
        message = result['messages']['G001']['message']
        self.assertIn('하와이 7일', message)
        self.assertIn('김철수님, 이영희님', message)
        self.assertIn('3,000,000원', message)
        self.assertIn('2024-12-20', message)
    
    def test_generate_messages_missing_variable(self):
        """누락된 변수 처리 테스트"""
        template_with_missing = "{product_name} - {missing_variable}"
        
        with self.assertRaises(Exception):
            self.generator.generate_messages(
                template_with_missing,
                self.group_data,
                self.fixed_data
            )
    
    def test_generate_messages_format_error(self):
        """포맷 오류 처리 테스트"""
        template_with_format_error = "{product_name:,}"  # 문자에 숫자 포맷 적용
        
        # 에러가 발생하지 않고 기본값으로 처리되는지 확인
        result = self.generator.generate_messages(
            template_with_format_error,
            self.group_data,
            self.fixed_data
        )
        
        self.assertIsInstance(result, dict)


class TestErrorHandler(unittest.TestCase):
    """ErrorHandler 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        self.error_handler = ErrorHandler()
    
    def test_classify_error(self):
        """에러 분류 테스트"""
        # FileNotFoundError
        error = FileNotFoundError("File not found")
        result = self.error_handler.classify_error(error)
        self.assertEqual(result, 'file_upload_error')
        
        # KeyError (변수 오류)
        error = KeyError("'missing_variable'")
        result = self.error_handler.classify_error(error)
        self.assertEqual(result, 'variable_error')
        
        # ValueError (검증 오류)
        error = ValueError("Invalid data")
        result = self.error_handler.classify_error(error)
        self.assertEqual(result, 'validation_error')
    
    def test_get_error_message(self):
        """에러 메시지 가져오기 테스트"""
        # 한국어 메시지
        message = self.error_handler.get_error_message('file_upload_error', 'ko')
        self.assertIn('파일 업로드', message)
        
        # 영어 메시지
        message = self.error_handler.get_error_message('file_upload_error', 'en')
        self.assertIn('uploading', message)
    
    def test_handle_error(self):
        """에러 처리 테스트"""
        error = ValueError("Test error")
        result = self.error_handler.handle_error(error, "test context")
        
        self.assertIsInstance(result, dict)
        self.assertIn('error_type', result)
        self.assertIn('original_error', result)
        self.assertIn('context', result)
        self.assertIn('message', result)
        self.assertIn('solutions', result)


class TestConfigManager(unittest.TestCase):
    """ConfigManager 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        # 임시 디렉토리 사용
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
    
    def tearDown(self):
        """테스트 정리"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_default_configs(self):
        """기본 설정 로드 테스트"""
        configs = self.config_manager.get_config_list()
        self.assertGreater(len(configs), 0)
        
        # 기본 설정들이 있는지 확인
        config_ids = [config['id'] for config in configs]
        self.assertIn('app_settings', config_ids)
    
    def test_save_and_load_config(self):
        """설정 저장 및 로드 테스트"""
        test_config = {
            'name': '테스트 설정',
            'settings': {'test_key': 'test_value'}
        }
        
        # 저장
        result = self.config_manager.save_config('test_config', test_config)
        self.assertTrue(result)
        
        # 로드
        loaded_config = self.config_manager.load_config('test_config')
        self.assertEqual(loaded_config['name'], '테스트 설정')
        self.assertEqual(loaded_config['settings']['test_key'], 'test_value')
    
    def test_get_setting(self):
        """설정값 가져오기 테스트"""
        value = self.config_manager.get_setting('app_settings', 'max_file_size_mb', 100)
        self.assertIsInstance(value, int)
        
        # 존재하지 않는 설정
        value = self.config_manager.get_setting('nonexistent', 'key', 'default')
        self.assertEqual(value, 'default')


class TestTemplateManager(unittest.TestCase):
    """TemplateManager 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        # 임시 디렉토리 사용
        self.temp_dir = tempfile.mkdtemp()
        self.template_manager = TemplateManager(self.temp_dir)
    
    def tearDown(self):
        """테스트 정리"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_default_templates(self):
        """기본 템플릿 로드 테스트"""
        templates = self.template_manager.get_template_list()
        self.assertGreater(len(templates), 0)
        
        # 표준 템플릿이 있는지 확인
        template_ids = [template['id'] for template in templates]
        self.assertIn('standard', template_ids)
    
    def test_create_template_from_content(self):
        """내용으로부터 템플릿 생성 테스트"""
        content = "안녕하세요, {product_name} 안내입니다. 잔금: {total_balance:,}원"
        
        template_id = self.template_manager.create_template_from_content(
            "테스트 템플릿", content, "테스트용 템플릿입니다."
        )
        
        self.assertIsInstance(template_id, str)
        
        # 로드해서 확인
        template = self.template_manager.load_template(template_id)
        self.assertEqual(template['content'], content)
        self.assertIn('product_name', template['variables'])
        self.assertIn('total_balance', template['variables'])
    
    def test_validate_template(self):
        """템플릿 검증 테스트"""
        # 올바른 템플릿
        valid_template = "안녕하세요, {product_name}입니다."
        result = self.template_manager.validate_template(valid_template)
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
        
        # 잘못된 템플릿 (괄호 불일치)
        invalid_template = "안녕하세요, {product_name입니다."
        result = self.template_manager.validate_template(invalid_template)
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['errors']), 0)


class TestSampleDataGenerator(unittest.TestCase):
    """SampleDataGenerator 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        self.generator = SampleDataGenerator()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """테스트 정리"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_generate_realistic_excel(self):
        """현실적인 엑셀 파일 생성 테스트"""
        result = self.generator.generate_realistic_excel(num_teams=2)
        
        self.assertIsInstance(result, dict)
        self.assertIn('filename', result)
        self.assertIn('destination', result)
        self.assertIn('teams', result)
        self.assertIn('groups', result)
        self.assertIn('members', result)
        
        # 파일이 실제로 생성되었는지 확인
        self.assertTrue(os.path.exists(result['filename']))
        
        # 엑셀 파일을 읽어서 검증
        df = pd.read_excel(result['filename'], sheet_name=0, header=8)
        self.assertGreater(len(df), 0)
        self.assertIn('팀', df.columns)
        self.assertIn('이름', df.columns)


class TestIntegration(unittest.TestCase):
    """통합 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
        
        # 샘플 데이터 생성
        self.generator = SampleDataGenerator()
        self.sample_file_info = self.generator.generate_realistic_excel(num_teams=2)
        self.sample_file = self.sample_file_info['filename']
    
    def tearDown(self):
        """테스트 정리"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_full_workflow(self):
        """전체 워크플로우 테스트"""
        # 1. 파일 읽기
        df_raw = pd.read_excel(self.sample_file, header=None)
        df_table = pd.read_excel(self.sample_file, header=8)
        
        # 2. 데이터 처리
        processor = EnhancedDataProcessor()
        
        # 고정 데이터 추출
        fixed_mapping = {
            'product_name': 'D1',
            'payment_due_date': 'D2',
            'base_exchange_rate': 'G1',
            'current_exchange_rate': 'G2'
        }
        fixed_data = processor.extract_fixed_data(df_raw, fixed_mapping)
        
        # 그룹 데이터 생성
        required_columns = {
            '팀': 'team_name',
            '문자 발송 그룹': 'sender_group',
            '이름': 'name'
        }
        optional_columns = {
            '연락처': 'contact',
            '잔금 안내 금액': 'total_balance'
        }
        
        group_data = processor.process_group_data(df_table, required_columns, optional_columns)
        
        # 3. 메시지 생성
        generator = EnhancedMessageGenerator()
        template = """안녕하세요, {product_name} 안내입니다.
{group_members_text}
총 잔금: {total_balance:,}원"""
        
        result = generator.generate_messages(template, group_data, fixed_data)
        
        # 4. 결과 검증
        self.assertIsInstance(result, dict)
        self.assertGreater(result['total_count'], 0)
        
        # 생성된 메시지가 올바른지 확인
        for message_data in result['messages'].values():
            message = message_data['message']
            self.assertIn(fixed_data['product_name'], message)
            self.assertIn('원', message)


def run_all_tests():
    """모든 테스트 실행"""
    print("🧪 여행 잔금 문자 생성기 테스트 시작")
    print("=" * 60)
    
    # 테스트 스위트 구성
    test_classes = [
        TestEnhancedDataProcessor,
        TestEnhancedMessageGenerator,
        TestErrorHandler,
        TestConfigManager,
        TestTemplateManager,
        TestSampleDataGenerator,
        TestIntegration
    ]
    
    # 각 테스트 클래스별로 실행
    total_tests = 0
    failed_tests = 0
    
    for test_class in test_classes:
        print(f"\n📋 {test_class.__name__} 테스트 중...")
        
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        
        # StringIO를 사용해서 출력 캡처
        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result = runner.run(suite)
        
        # 결과 출력
        tests_run = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        
        total_tests += tests_run
        failed_tests += failures + errors
        
        if failures == 0 and errors == 0:
            print(f"  ✅ 모든 테스트 통과 ({tests_run}개)")
        else:
            print(f"  ❌ 실패: {failures}개, 오류: {errors}개 / 총 {tests_run}개")
            
            # 실패한 테스트 상세 정보
            for failure in result.failures:
                print(f"    🔍 실패: {failure[0]}")
                print(f"       {failure[1].split('AssertionError:')[-1].strip()}")
            
            for error in result.errors:
                print(f"    💥 오류: {error[0]}")
                print(f"       {str(error[1]).split(':', 1)[-1].strip()}")
    
    # 최종 결과
    print("\n" + "=" * 60)
    print(f"🏁 테스트 완료")
    print(f"📊 총 테스트: {total_tests}개")
    print(f"✅ 통과: {total_tests - failed_tests}개")
    print(f"❌ 실패: {failed_tests}개")
    
    if failed_tests == 0:
        print("🎉 모든 테스트가 성공적으로 통과했습니다!")
        return True
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 위의 오류를 확인해주세요.")
        return False


def run_specific_test(test_name):
    """특정 테스트만 실행"""
    test_classes = {
        'processor': TestEnhancedDataProcessor,
        'generator': TestEnhancedMessageGenerator,
        'error': TestErrorHandler,
        'config': TestConfigManager,
        'template': TestTemplateManager,
        'sample': TestSampleDataGenerator,
        'integration': TestIntegration
    }
    
    if test_name in test_classes:
        test_class = test_classes[test_name]
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()
    else:
        print(f"❌ 알 수 없는 테스트: {test_name}")
        print(f"사용 가능한 테스트: {', '.join(test_classes.keys())}")
        return False


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='여행 잔금 문자 생성기 테스트')
    parser.add_argument('--test', '-t', help='실행할 특정 테스트 (processor, generator, error, config, template, sample, integration)')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 출력')
    
    args = parser.parse_args()
    
    if args.test:
        success = run_specific_test(args.test)
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()