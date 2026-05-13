#!/usr/bin/env python3
"""
Test script for link parsers and conflict resolution
Tests parsing of 3+ link types, tree building, and all conflict policies
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.parsers import YandexLinkParser, GoogleLinkParser, LocalPathParser
from app.core.parsers.base import LinkInfo
from app.core.preview import TreeBuilder, PreviewTree, TreeNode
from app.core.conflicts import ConflictResolver, ConflictPolicy, FileInfo


def test_yandex_parser():
    """Test Yandex link parser"""
    print("\n=== Testing YandexLinkParser ===")
    
    test_text = """
    Check these Yandex links:
    https://yadi.sk/d/abc123xyz
    https://disk.yandex.ru/i/folder456
    https://disk.yandex.com/d/document789
    """
    
    parser = YandexLinkParser()
    links = parser.parse(test_text)
    
    assert len(links) >= 3, f"Expected at least 3 Yandex links, got {len(links)}"
    
    for link in links:
        assert link.provider == 'yandex', f"Expected provider 'yandex', got '{link.provider}'"
        assert link.type in ['file', 'folder'], f"Invalid type: {link.type}"
        print(f"  ✓ Found: {link.url} (type: {link.type})")
    
    print(f"  ✓ Yandex parser test passed: {len(links)} links found")
    return True


def test_google_parser():
    """Test Google Drive link parser"""
    print("\n=== Testing GoogleLinkParser ===")
    
    test_text = """
    Google Drive files:
    https://drive.google.com/file/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ
    https://drive.google.com/drive/folders/1FolderIdHere123
    https://drive.google.com/folderview?id=1OldStyleFolder
    """
    
    parser = GoogleLinkParser()
    links = parser.parse(test_text)
    
    assert len(links) >= 3, f"Expected at least 3 Google links, got {len(links)}"
    
    for link in links:
        assert link.provider == 'google', f"Expected provider 'google', got '{link.provider}'"
        assert link.type in ['file', 'folder'], f"Invalid type: {link.type}"
        print(f"  ✓ Found: {link.url} (type: {link.type})")
    
    print(f"  ✓ Google parser test passed: {len(links)} links found")
    return True


def test_local_parser():
    """Test local path parser"""
    print("\n=== Testing LocalPathParser ===")
    
    test_text = """
    Local paths:
    /home/user/documents/report.pdf
    /var/data/backup
    C:\\Users\\Documents\\file.txt
    """
    
    parser = LocalPathParser()
    links = parser.parse(test_text)
    
    # At least Unix paths should be detected
    assert len(links) >= 2, f"Expected at least 2 local paths, got {len(links)}"
    
    for link in links:
        assert link.provider == 'local', f"Expected provider 'local', got '{link.provider}'"
        print(f"  ✓ Found: {link.url} (type: {link.type})")
    
    print(f"  ✓ Local parser test passed: {len(links)} links found")
    return True


def test_combined_parsing():
    """Test parsing text with mixed link types"""
    print("\n=== Testing Combined Parsing ===")
    
    test_text = """
    Here are various links:
    
    Yandex:
    - https://yadi.sk/d/file123
    - https://disk.yandex.ru/i/photo456
    
    Google:
    - https://drive.google.com/file/d/1GoogleFileId
    - https://drive.google.com/drive/folders/1GoogleFolderId
    
    Local:
    - /tmp/download.zip
    """
    
    all_links = []
    
    yandex_parser = YandexLinkParser()
    all_links.extend(yandex_parser.parse(test_text))
    
    google_parser = GoogleLinkParser()
    all_links.extend(google_parser.parse(test_text))
    
    local_parser = LocalPathParser()
    all_links.extend(local_parser.parse(test_text))
    
    assert len(all_links) >= 5, f"Expected at least 5 total links, got {len(all_links)}"
    
    providers = set(link.provider for link in all_links)
    assert len(providers) >= 2, f"Expected links from multiple providers, got: {providers}"
    
    print(f"  ✓ Combined parsing test passed: {len(all_links)} links from {len(providers)} providers")
    for link in all_links:
        print(f"    - {link.provider}: {link.url}")
    
    return True


async def test_tree_builder():
    """Test preview tree building"""
    print("\n=== Testing TreeBuilder ===")
    
    link = LinkInfo(
        url="https://yadi.sk/d/test123",
        provider="yandex",
        type="folder",
        metadata={}
    )
    
    builder = TreeBuilder()
    tree = await builder.build_tree(link)
    
    assert isinstance(tree, PreviewTree), "Expected PreviewTree instance"
    assert isinstance(tree.root, TreeNode), "Expected TreeNode as root"
    
    stats = tree.get_stats()
    assert 'total_files' in stats, "Stats missing total_files"
    assert 'total_folders' in stats, "Stats missing total_folders"
    assert 'total_size' in stats, "Stats missing total_size"
    
    print(f"  ✓ Tree built successfully")
    print(f"  ✓ Stats: {stats}")
    
    # Test serialization
    tree_dict = tree.to_dict()
    assert 'id' in tree_dict, "Serialized tree missing id"
    assert 'name' in tree_dict, "Serialized tree missing name"
    assert 'children' in tree_dict, "Serialized tree missing children"
    
    print(f"  ✓ Tree serialization test passed")
    return True


def test_conflict_resolver():
    """Test conflict resolution with all policies"""
    print("\n=== Testing ConflictResolver ===")
    
    src_file = FileInfo(
        path="/source/document.pdf",
        name="document.pdf",
        size=1024000,
        checksum="abc123"
    )
    
    dst_file = FileInfo(
        path="/destination/document.pdf",
        name="document.pdf",
        size=512000,
        checksum="xyz789"
    )
    
    policies_tested = []
    
    # Test SKIP policy
    result = ConflictResolver.resolve(src_file, dst_file, ConflictPolicy.SKIP)
    assert result.action_taken == 'skipped', f"SKIP policy failed: {result.action_taken}"
    assert result.warning is not None, "SKIP should have warning"
    print(f"  ✓ SKIP: {result.action_taken} - {result.warning}")
    policies_tested.append('SKIP')
    
    # Test OVERWRITE policy
    result = ConflictResolver.resolve(src_file, dst_file, ConflictPolicy.OVERWRITE)
    assert result.action_taken == 'overwritten', f"OVERWRITE policy failed: {result.action_taken}"
    print(f"  ✓ OVERWRITE: {result.action_taken}")
    policies_tested.append('OVERWRITE')
    
    # Test KEEP_BOTH policy
    result = ConflictResolver.resolve(src_file, dst_file, ConflictPolicy.KEEP_BOTH)
    assert result.action_taken == 'renamed', f"KEEP_BOTH policy failed: {result.action_taken}"
    assert result.new_path is not None, "KEEP_BOTH should have new_path"
    print(f"  ✓ KEEP_BOTH: {result.action_taken} -> {result.new_path}")
    policies_tested.append('KEEP_BOTH')
    
    # Test RENAME policy
    result = ConflictResolver.resolve(src_file, dst_file, ConflictPolicy.RENAME)
    assert result.action_taken == 'renamed', f"RENAME policy failed: {result.action_taken}"
    assert result.new_path is not None, "RENAME should have new_path"
    print(f"  ✓ RENAME: {result.action_taken} -> {result.new_path}")
    policies_tested.append('RENAME')
    
    # Test identical files (checksum match)
    identical_dst = FileInfo(
        path="/destination/document.pdf",
        name="document.pdf",
        size=1024000,
        checksum="abc123"  # Same as source
    )
    result = ConflictResolver.resolve(src_file, identical_dst, ConflictPolicy.OVERWRITE)
    assert result.checksum_match == True, "Should detect identical files"
    assert result.action_taken == 'skipped', "Identical files should be skipped"
    print(f"  ✓ Checksum match detection: files are identical, skipped")
    
    print(f"  ✓ All {len(policies_tested)} conflict policies tested: {', '.join(policies_tested)}")
    return True


async def main():
    """Run all tests"""
    print("=" * 60)
    print("MySaver Parser & Conflict Resolution Tests")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        if test_yandex_parser():
            tests_passed += 1
    except Exception as e:
        print(f"  ✗ Yandex parser test FAILED: {e}")
        tests_failed += 1
    
    try:
        if test_google_parser():
            tests_passed += 1
    except Exception as e:
        print(f"  ✗ Google parser test FAILED: {e}")
        tests_failed += 1
    
    try:
        if test_local_parser():
            tests_passed += 1
    except Exception as e:
        print(f"  ✗ Local parser test FAILED: {e}")
        tests_failed += 1
    
    try:
        if test_combined_parsing():
            tests_passed += 1
    except Exception as e:
        print(f"  ✗ Combined parsing test FAILED: {e}")
        tests_failed += 1
    
    try:
        if await test_tree_builder():
            tests_passed += 1
    except Exception as e:
        print(f"  ✗ Tree builder test FAILED: {e}")
        tests_failed += 1
    
    try:
        if test_conflict_resolver():
            tests_passed += 1
    except Exception as e:
        print(f"  ✗ Conflict resolver test FAILED: {e}")
        tests_failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)
    
    if tests_failed > 0:
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
