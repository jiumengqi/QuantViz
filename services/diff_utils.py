# -*- coding: utf-8 -*-
"""
代码差异比较工具
用于生成代码版本之间的差异 HTML
"""
import difflib
import html


def generate_diff_html(old_code, new_code, old_label='旧版本', new_label='新版本'):
    """
    生成两个代码版本的差异 HTML
    
    Args:
        old_code: 旧版本代码
        new_code: 新版本代码
        old_label: 旧版本标签
        new_label: 新版本标签
    
    Returns:
        HTML 格式的差异对比字符串
    """
    if old_code is None:
        old_code = ''
    if new_code is None:
        new_code = ''
    
    old_lines = old_code.splitlines()
    new_lines = new_code.splitlines()
    
    # 计算行号宽度
    max_old_lines = len(old_lines)
    max_new_lines = len(new_lines)
    line_num_width = max(len(str(max(max_old_lines, max_new_lines))), 3)
    
    # 生成差异
    differ = difflib.HtmlDiff(tabsize=4, wrapcolumn=80)
    diff_html = differ.make_table(
        old_lines, 
        new_lines,
        fromdesc=old_label,
        todesc=new_label,
        context=True,
        numlines=3
    )
    
    # 生成并排对比视图的 HTML
    side_by_side_html = _generate_side_by_side(old_lines, new_lines, line_num_width)
    
    return {
        'diff_table': diff_html,
        'side_by_side': side_by_side_html,
        'stats': _calculate_diff_stats(old_lines, new_lines)
    }


def _generate_side_by_side(old_lines, new_lines, line_num_width):
    """
    生成并排显示的代码对比 HTML
    
    Args:
        old_lines: 旧版本代码行列表
        new_lines: 新版本代码行列表
        line_num_width: 行号宽度
    
    Returns:
        HTML 格式的并排对比字符串
    """
    differ = difflib.Differ()
    diff_result = list(differ.compare(old_lines, new_lines))
    
    old_html_lines = []
    new_html_lines = []
    
    old_line_num = 1
    new_line_num = 1
    
    for line in diff_result:
        code = html.escape(line[2:])
        prefix = line[0]
        
        if prefix == ' ':
            # 未修改的行
            old_html_lines.append(_format_code_line(old_line_num, code, 'unchanged', line_num_width))
            new_html_lines.append(_format_code_line(new_line_num, code, 'unchanged', line_num_width))
            old_line_num += 1
            new_line_num += 1
        elif prefix == '-':
            # 删除的行
            old_html_lines.append(_format_code_line(old_line_num, code, 'deleted', line_num_width))
            new_html_lines.append(_format_code_line('', '', 'empty', line_num_width))
            old_line_num += 1
        elif prefix == '+':
            # 新增的行
            old_html_lines.append(_format_code_line('', '', 'empty', line_num_width))
            new_html_lines.append(_format_code_line(new_line_num, code, 'added', line_num_width))
            new_line_num += 1
        elif prefix == '?':
            # 差异标记行，跳过
            continue
        else:
            # 处理不明确的行
            old_html_lines.append(_format_code_line(old_line_num, code, 'unchanged', line_num_width))
            new_html_lines.append(_format_code_line(new_line_num, code, 'unchanged', line_num_width))
            old_line_num += 1
            new_line_num += 1
    
    html_template = f'''
    <div class="diff-container">
        <style>
            .diff-container {{
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.5;
                border: 1px solid #ddd;
                border-radius: 4px;
                overflow: hidden;
            }}
            .diff-header {{
                display: flex;
                background: #f5f5f5;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }}
            .diff-header-cell {{
                flex: 1;
                padding: 8px 12px;
                border-right: 1px solid #ddd;
            }}
            .diff-header-cell:last-child {{
                border-right: none;
            }}
            .diff-body {{
                display: flex;
                max-height: 600px;
                overflow-y: auto;
            }}
            .diff-old, .diff-new {{
                flex: 1;
                overflow-x: auto;
            }}
            .diff-old {{ border-right: 1px solid #ddd; }}
            .code-line {{
                display: flex;
                white-space: pre;
            }}
            .line-number {{
                min-width: {line_num_width * 10}px;
                padding: 2px 8px;
                text-align: right;
                color: #999;
                background: #fafafa;
                user-select: none;
                border-right: 1px solid #ddd;
            }}
            .line-content {{
                flex: 1;
                padding: 2px 8px;
            }}
            .line-content.unchanged {{
                background: #fff;
            }}
            .line-content.added {{
                background: #e6ffed;
            }}
            .line-content.deleted {{
                background: #ffeef0;
            }}
            .line-content.empty {{
                background: #f5f5f5;
            }}
            .line-content.modified {{
                background: #fffbe6;
            }}
        </style>
        <div class="diff-header">
            <div class="diff-header-cell">旧版本</div>
            <div class="diff-header-cell">新版本</div>
        </div>
        <div class="diff-body">
            <div class="diff-old">
                {''.join(old_html_lines)}
            </div>
            <div class="diff-new">
                {''.join(new_html_lines)}
            </div>
        </div>
    </div>
    '''
    return html_template


def _format_code_line(line_num, code, status, line_num_width):
    """
    格式化单行代码 HTML
    
    Args:
        line_num: 行号
        code: 代码内容
        status: 状态 (unchanged, added, deleted, empty, modified)
        line_num_width: 行号宽度
    
    Returns:
        HTML 格式的行字符串
    """
    return f'''
    <div class="code-line">
        <span class="line-number">{line_num}</span>
        <span class="line-content {status}">{code}</span>
    </div>
    '''


def _calculate_diff_stats(old_lines, new_lines):
    """
    计算差异统计信息
    
    Args:
        old_lines: 旧版本代码行列表
        new_lines: 新版本代码行列表
    
    Returns:
        统计信息字典
    """
    differ = difflib.Differ()
    diff_result = list(differ.compare(old_lines, new_lines))
    
    added = 0
    deleted = 0
    unchanged = 0
    
    for line in diff_result:
        prefix = line[0]
        if prefix == ' ':
            unchanged += 1
        elif prefix == '-':
            deleted += 1
        elif prefix == '+':
            added += 1
    
    return {
        'added_lines': added,
        'deleted_lines': deleted,
        'unchanged_lines': unchanged,
        'total_changes': added + deleted
    }


def generate_unified_diff(old_code, new_code, old_label='version1', new_label='version2'):
    """
    生成统一格式的差异文本
    
    Args:
        old_code: 旧版本代码
        new_code: 新版本代码
        old_label: 旧版本标签
        new_label: 新版本标签
    
    Returns:
        差异文本字符串
    """
    old_lines = old_code.splitlines() if old_code else []
    new_lines = new_code.splitlines() if new_code else []
    
    diff = difflib.unified_diff(
        old_lines, 
        new_lines,
        fromfile=old_label,
        tofile=new_label,
        lineterm=''
    )
    
    return '\n'.join(diff)
