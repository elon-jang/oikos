#!/usr/bin/env python3
"""
기부금 영수증 MCP 서버

Claude Desktop/Code에서 자연어로 영수증을 발행할 수 있도록 하는 MCP 서버입니다.
개인정보 보호를 위해 응답에는 최소한의 정보만 포함됩니다.
"""

import os
import sys

# 상위 디렉토리의 모듈을 import할 수 있도록 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP

from .tools.receipt import (
    list_recipients,
    generate_receipt,
    generate_all_receipts,
    preview_receipt,
)
from .tools.validate import validate_data, validate_template
from .tools.history import get_history, get_person_history

# 환경 변수에서 데이터 디렉토리 읽기
DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# MCP 서버 생성
mcp = FastMCP(
    name="oikos-receipt",
    instructions="""기부금 영수증 발행 시스템입니다.

사용 가능한 기능:
- 대상자 목록 조회: list_recipients()
- 영수증 생성: generate_receipt(name) 또는 generate_all_receipts()
- 데이터 검증: validate_data()
- 발행 이력 조회: get_history()

개인정보 보호를 위해 상세 정보(이름, 금액)는 로컬 파일에서 확인하세요."""
)


# 영수증 도구 등록
@mcp.tool()
def list_donation_recipients(data_file: str = None) -> dict:
    """
    영수증 발행 대상자 목록을 조회합니다.

    Args:
        data_file: 데이터 파일 경로 (선택사항, 미지정 시 자동 감지)

    Returns:
        대상자 수와 총 금액 (개인정보 보호를 위해 상세 목록은 미포함)
    """
    return list_recipients(DATA_DIR, data_file)


@mcp.tool()
def generate_donation_receipt(name: str, data_file: str = None, template_file: str = None) -> dict:
    """
    특정 사람의 기부금 영수증을 생성합니다.

    Args:
        name: 대상자 이름
        data_file: 데이터 파일 경로 (선택사항)
        template_file: 템플릿 파일 경로 (선택사항)

    Returns:
        생성 결과 (파일 경로 포함)
    """
    return generate_receipt(DATA_DIR, name, data_file, template_file)


@mcp.tool()
def generate_all_donation_receipts(
    data_file: str = None,
    template_file: str = None,
    confirm: bool = False
) -> dict:
    """
    전체 대상자의 기부금 영수증을 생성합니다.

    Args:
        data_file: 데이터 파일 경로 (선택사항)
        template_file: 템플릿 파일 경로 (선택사항)
        confirm: 생성 확인 (False면 미리보기만, True면 실제 생성)

    Returns:
        생성 결과 또는 미리보기 정보
    """
    return generate_all_receipts(DATA_DIR, data_file, template_file, confirm)


@mcp.tool()
def preview_donation_receipt(name: str, data_file: str = None) -> dict:
    """
    영수증 내용을 미리봅니다 (파일 생성 없이).

    Args:
        name: 대상자 이름
        data_file: 데이터 파일 경로 (선택사항)

    Returns:
        영수증 미리보기 정보
    """
    return preview_receipt(DATA_DIR, name, data_file)


# 검증 도구 등록
@mcp.tool()
def validate_donation_data(data_file: str = None) -> dict:
    """
    데이터 파일의 유효성을 검사합니다.

    Args:
        data_file: 검사할 데이터 파일 경로 (선택사항, 미지정 시 자동 감지)

    Returns:
        검증 결과 (오류 목록 포함)
    """
    return validate_data(DATA_DIR, data_file)


@mcp.tool()
def validate_receipt_template(template_file: str = None) -> dict:
    """
    템플릿 파일의 유효성을 검사합니다.

    Args:
        template_file: 검사할 템플릿 파일 경로 (선택사항)

    Returns:
        검증 결과 (누락된 placeholder 목록 포함)
    """
    return validate_template(DATA_DIR, template_file)


# 이력 도구 등록
@mcp.tool()
def get_receipt_history(year: int = None) -> dict:
    """
    영수증 발행 이력을 조회합니다.

    Args:
        year: 조회할 연도 (선택사항, 미지정 시 현재 연도)

    Returns:
        발행 건수와 최근 발행 정보 (상세 내역은 로컬 파일 참조)
    """
    return get_history(DATA_DIR, year)


@mcp.tool()
def get_person_receipt_history(name: str, year: int = None) -> dict:
    """
    특정 사람의 영수증 발행 이력을 조회합니다.

    Args:
        name: 조회할 사람 이름
        year: 조회할 연도 (선택사항)

    Returns:
        해당 사람의 발행 여부와 횟수
    """
    return get_person_history(DATA_DIR, name, year)


def main():
    """MCP 서버 실행"""
    mcp.run(transport="stdio", show_banner=False, log_level="ERROR")


if __name__ == "__main__":
    main()
