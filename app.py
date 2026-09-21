
import streamlit as st
import json
import os
import sys
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from note_manager import NoteManager
from example_manager import ExampleManager

# ─────────────────────────────────────────────
# 页面配置
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="个人知识管理平台",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# 自定义 CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 1.5rem;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .card-example {
        border-left: 4px solid #ff7f0e;
    }
    .tag {
        display: inline-block;
        background-color: #e3f2fd;
        color: #1565c0;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.8rem;
        margin: 2px;
    }
    .difficulty-easy   { color: #2e7d32; font-weight: bold; }
    .difficulty-medium { color: #f57f17; font-weight: bold; }
    .difficulty-hard   { color: #c62828; font-weight: bold; }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
    }
    .stat-number { font-size: 2.5rem; font-weight: bold; }
    .stat-label  { font-size: 0.9rem; opacity: 0.9; }
    .reviewed-badge {
        background-color: #c8e6c9;
        color: #1b5e20;
        border-radius: 10px;
        padding: 2px 8px;
        font-size: 0.75rem;
    }
    .not-reviewed-badge {
        background-color: #ffccbc;
        color: #bf360c;
        border-radius: 10px;
        padding: 2px 8px;
        font-size: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 初始化管理器（缓存，避免重复加载）
# ─────────────────────────────────────────────
@st.cache_resource
def get_managers():
    base_dir = os.path.dirname(__file__)
    note_mgr    = NoteManager(os.path.join(base_dir, 'data', 'notes', 'notes.json'))
    example_mgr = ExampleManager(os.path.join(base_dir, 'data', 'examples', 'examples.json'))
    return note_mgr, example_mgr

note_manager, example_manager = get_managers()

# ─────────────────────────────────────────────
# Session State 初始化
# ─────────────────────────────────────────────
for key, default in {
    'edit_note_id':    None,
    'edit_example_id': None,
    'confirm_delete_note':    None,
    'confirm_delete_example': None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────
DIFFICULTY_MAP = {'简单': 'easy', '中等': 'medium', '困难': 'hard'}
DIFFICULTY_MAP_REVERSE = {v: k for k, v in DIFFICULTY_MAP.items()}
DIFFICULTY_COLOR = {'简单': '🟢', '中等': '🟡', '困难': '🔴'}

def format_datetime(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        return dt_str or '—'

def render_tags(tags: list) -> str:
    if not tags:
        return ''
    return ' '.join(f'<span class="tag">#{t}</span>' for t in tags)

def difficulty_label(level: str) -> str:
    zh = DIFFICULTY_MAP_REVERSE.get(level, level)
    icon = DIFFICULTY_COLOR.get(zh, '')
    return f"{icon} {zh}"

# ─────────────────────────────────────────────
# 顶部标题
# ─────────────────────────────────────────────
st.markdown('<div class="main-header">📚 个人知识管理平台</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 侧边栏导航
# ─────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/books.png", width=80)
    st.markdown("## 🗂️ 导航菜单")
    tab_choice = st.radio(
        "选择功能模块",
        ["📝 笔记管理", "📖 例题库", "📊 数据统计"],
        label_visibility="collapsed"
    )
    st.markdown("---")

    # ── 导入 / 导出 ──────────────────────────
    st.markdown("### 🔄 数据备份")

    # 导出
    if st.button("⬇️ 导出所有数据", use_container_width=True):
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'notes':    note_manager.get_all_notes(),
                'examples': example_manager.get_all_examples(),
            }
            st.download_button(
                label="📥 点击下载 JSON",
                data=json.dumps(export_data, ensure_ascii=False, indent=2),
                file_name=f"knowledge_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"导出失败：{e}")

    # 导入
    uploaded = st.file_uploader("⬆️ 导入备份文件", type=['json'], label_visibility="collapsed")
    if uploaded:
        try:
            import_data = json.load(uploaded)
            notes_count    = len(import_data.get('notes', []))
            examples_count = len(import_data.get('examples', []))
            st.info(f"检测到 {notes_count} 条笔记、{examples_count} 道例题")
            if st.button("✅ 确认导入", use_container_width=True):
                imported_n = imported_e = 0
                for note in import_data.get('notes', []):
                    try:
                        note_manager.add_note(
                            title=note['title'], content=note['content'],
                            category=note.get('category', '未分类'),
                            tags=note.get('tags', [])
                        )
                        imported_n += 1
                    except Exception:
                        pass
                for ex in import_data.get('examples', []):
                    try:
                        example_manager.add_example(
                            title=ex['title'], problem=ex['problem'],
                            solution=ex['solution'],
                            category=ex.get('category', '未分类'),
                            difficulty_level=ex.get('difficulty_level', 'medium')
                        )
                        imported_e += 1
                    except Exception:
                        pass
                st.success(f"成功导入 {imported_n} 条笔记、{imported_e} 道例题！")
                st.cache_resource.clear()
                st.rerun()
        except Exception as e:
            st.error(f"导入失败，请检查文件格式：{e}")

    st.markdown("---")
    st.caption("💡 数据保存在本地 JSON 文件中")

# ═══════════════════════════════════════════════════════════════
# TAB 1：笔记管理
# ═══════════════════════════════════════════════════════════════
if tab_choice == "📝 笔记管理":
    st.header("📝 笔记管理")

    # ── 获取所有笔记 & 分类列表 ──────────────────
    all_notes = note_manager.get_all_notes()
    all_categories_notes = sorted({n.get('category', '未分类') for n in all_notes}) or ['未分类']

    # ── 新增笔记 ─────────────────────────────────
    with st.expander("➕ 新增笔记", expanded=not bool(all_notes)):
        with st.form("add_note_form", clear_on_submit=True):
            st.markdown("#### 填写笔记信息")
            col1, col2 = st.columns([2, 1])
            with col1:
                new_title = st.text_input("📌 标题 *", placeholder="请输入笔记标题")
            with col2:
                new_category = st.text_input("🗂️ 分类", placeholder="例：高数、动物学")
            new_content = st.text_area("📄 内容 *", placeholder="在此输入笔记内容...", height=200)
            new_tags_raw = st.text_input("🏷️ 标签（用逗号分隔）", placeholder="例：极限, 导数, 重点")
            submitted = st.form_submit_button("💾 保存笔记", use_container_width=True)
            if submitted:
                if not new_title.strip():
                    st.error("❌ 标题不能为空！")
                elif not new_content.strip():
                    st.error("❌ 内容不能为空！")
                else:
                    tags = [t.strip() for t in new_tags_raw.split(',') if t.strip()]
                    try:
                        note_manager.add_note(
                            title=new_title.strip(),
                            content=new_content.strip(),
                            category=new_category.strip() or '未分类',
                            tags=tags
                        )
                        st.success(f"✅ 笔记《{new_title}》已保存！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"保存失败：{e}")

    st.markdown("---")

    # ── 搜索 & 筛选 ──────────────────────────────
    st.markdown("#### 🔍 搜索与筛选")
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        search_note = st.text_input("搜索关键词", placeholder="搜索标题或内容...", label_visibility="collapsed")
    with col2:
        filter_category_note = st.selectbox("按分类筛选", ["全部分类"] + all_categories_notes, label_visibility="collapsed")
    with col3:
        filter_tag_note = st.text_input("按标签筛选", placeholder="输入标签名...", label_visibility="collapsed")

    # 过滤逻辑
    filtered_notes = all_notes
    if search_note.strip():
        kw = search_note.strip().lower()
        filtered_notes = [n for n in filtered_notes
                          if kw in n.get('title', '').lower() or kw in n.get('content', '').lower()]
    if filter_category_note != "全部分类":
        filtered_notes = [n for n in filtered_notes if n.get('category') == filter_category_note]
    if filter_tag_note.strip():
        ft = filter_tag_note.strip().lower()
        filtered_notes = [n for n in filtered_notes
                          if any(ft in t.lower() for t in n.get('tags', []))]

    st.markdown(f"**共找到 {len(filtered_notes)} 条笔记**")

    # ── 笔记列表 ─────────────────────────────────
    if not filtered_notes:
        st.info("📭 暂无笔记，请点击上方「新增笔记」开始记录！")
    else:
        for note in sorted(filtered_notes, key=lambda x: x.get('updated_at', ''), reverse=True):
            nid = note['id']

            # 编辑模式
            if st.session_state.edit_note_id == nid:
                with st.container():
                    st.markdown(f"##### ✏️ 编辑笔记：{note['title']}")
                    with st.form(f"edit_note_{nid}"):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            e_title = st.text_input("标题", value=note['title'])
                        with col2:
                            e_category = st.text_input("分类", value=note.get('category', ''))
                        e_content = st.text_area("内容", value=note['content'], height=200)
                        e_tags = st.text_input("标签（逗号分隔）", value=', '.join(note.get('tags', [])))
                        c1, c2 = st.columns(2)
                        with c1:
                            save_edit = st.form_submit_button("💾 保存修改", use_container_width=True)
                        with c2:
                            cancel_edit = st.form_submit_button("❌ 取消", use_container_width=True)
                        if save_edit:
                            if not e_title.strip():
                                st.error("标题不能为空！")
                            else:
                                try:
                                    note_manager.update_note(
                                        note_id=nid,
                                        title=e_title.strip(),
                                        content=e_content.strip(),
                                        category=e_category.strip() or '未分类',
                                        tags=[t.strip() for t in e_tags.split(',') if t.strip()]
                                    )
                                    st.success("✅ 笔记已更新！")
                                    st.session_state.edit_note_id = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"更新失败：{e}")
                        if cancel_edit:
                            st.session_state.edit_note_id = None
                            st.rerun()
            else:
                # 展示模式
                with st.expander(f"📄 {note['title']}  |  🗂️ {note.get('category', '未分类')}"):
                    col_main, col_actions = st.columns([5, 1])
                    with col_main:
                        st.markdown(note['content'])
                        if note.get('tags'):
                            st.markdown(render_tags(note['tags']), unsafe_allow_html=True)
                        st.caption(
                            f"🕐 创建：{format_datetime(note.get('created_at', ''))}　"
                            f"🔄 更新：{format_datetime(note.get('updated_at', ''))}"
                        )
                    with col_actions:
                        if st.button("✏️ 编辑", key=f"edit_n_{nid}", use_container_width=True):
                            st.session_state.edit_note_id = nid
                            st.rerun()
                        # 删除确认
                        if st.session_state.confirm_delete_note == nid:
                            st.warning("确认删除？")
                            if st.button("✅ 确认", key=f"confirm_del_n_{nid}", use_container_width=True):
                                try:
                                    note_manager.delete_note(nid)
                                    st.success("已删除！")
                                    st.session_state.confirm_delete_note = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"删除失败：{e}")
                            if st.button("❌ 取消", key=f"cancel_del_n_{nid}", use_container_width=True):
                                st.session_state.confirm_delete_note = None
                                st.rerun()
                        else:
                            if st.button("🗑️ 删除", key=f"del_n_{nid}", use_container_width=True):
                                st.session_state.confirm_delete_note = nid
                                st.rerun()

# ═══════════════════════════════════════════════════════════════
# TAB 2：例题库
# ═══════════════════════════════════════════════════════════════
elif tab_choice == "📖 例题库":
    st.header("📖 例题库")

    all_examples = example_manager.get_all_examples()
    all_categories_ex = sorted({e.get('category', '未分类') for e in all_examples}) or ['未分类']

    # ── 新增例题 ─────────────────────────────────
    with st.expander("➕ 新增例题", expanded=not bool(all_examples)):
        with st.form("add_example_form", clear_on_submit=True):
            st.markdown("#### 填写例题信息")
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                ex_title = st.text_input("📌 标题 *", placeholder="例题标题")
            with col2:
                ex_category = st.text_input("🗂️ 分类", placeholder="例：高数、动物学")
            with col3:
                ex_difficulty_zh = st.selectbox("难度", ["简单", "中等", "困难"])
            ex_problem  = st.text_area("❓ 题目 *", placeholder="在此输入题目内容...", height=150)
            ex_solution = st.text_area("✅ 解答 *", placeholder="在此输入解题过程和答案...", height=200)
            submitted_ex = st.form_submit_button("💾 保存例题", use_container_width=True)
            if submitted_ex:
                if not ex_title.strip():
                    st.error("❌ 标题不能为空！")
                elif not ex_problem.strip():
                    st.error("❌ 题目不能为空！")
                elif not ex_solution.strip():
                    st.error("❌ 解答不能为空！")
                else:
                    try:
                        example_manager.add_example(
                            title=ex_title.strip(),
                            problem=ex_problem.strip(),
                            solution=ex_solution.strip(),
                            category=ex_category.strip() or '未分类',
                            difficulty_level=DIFFICULTY_MAP[ex_difficulty_zh]
                        )
                        st.success(f"✅ 例题《{ex_title}》已保存！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"保存失败：{e}")

    st.markdown("---")

    # ── 搜索 & 筛选 ──────────────────────────────
    st.markdown("#### 🔍 搜索与筛选")
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        search_ex = st.text_input("搜索关键词", placeholder="搜索标题或题目...", label_visibility="collapsed")
    with col2:
        filter_cat_ex = st.selectbox("按分类筛选", ["全部分类"] + all_categories_ex, label_visibility="collapsed")
    with col3:
        filter_diff = st.selectbox("按难度筛选", ["全部难度", "简单", "中等", "困难"], label_visibility="collapsed")

    # 过滤逻辑
    filtered_ex = all_examples
    if search_ex.strip():
        kw = search_ex.strip().lower()
        filtered_ex = [e for e in filtered_ex
                       if kw in e.get('title', '').lower() or kw in e.get('problem', '').lower()]
    if filter_cat_ex != "全部分类":
        filtered_ex = [e for e in filtered_ex if e.get('category') == filter_cat_ex]
    if filter_diff != "全部难度":
        filtered_ex = [e for e in filtered_ex
                       if e.get('difficulty_level') == DIFFICULTY_MAP[filter_diff]]

    st.markdown(f"**共找到 {len(filtered_ex)} 道例题**")

    # ── 例题列表 ─────────────────────────────────
    if not filtered_ex:
        st.info("📭 暂无例题，请点击上方「新增例题」开始添加！")
    else:
        for ex in sorted(filtered_ex, key=lambda x: x.get('updated_at', ''), reverse=True):
            eid = ex['id']
            diff_label = difficulty_label(ex.get('difficulty_level', 'medium'))
            reviewed   = ex.get('is_reviewed', False)
            badge_html = ('<span class="reviewed-badge">✅ 已复习</span>'
                          if reviewed else '<span class="not-reviewed-badge">⏳ 未复习</span>')

            # 编辑模式
            if st.session_state.edit_example_id == eid:
                with st.container():
                    st.markdown(f"##### ✏️ 编辑例题：{ex['title']}")
                    with st.form(f"edit_ex_{eid}"):
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            ee_title = st.text_input("标题", value=ex['title'])
                        with col2:
                            ee_category = st.text_input("分类", value=ex.get('category', ''))
                        with col3:
                            cur_diff_zh = DIFFICULTY_MAP_REVERSE.get(ex.get('difficulty_level', 'medium'), '中等')
                            ee_diff_zh  = st.selectbox("难度", ["简单", "中等", "困难"],
                                                        index=["简单", "中等", "困难"].index(cur_diff_zh))
                        ee_problem  = st.text_area("题目",  value=ex['problem'],  height=150)
                        ee_solution = st.text_area("解答",  value=ex['solution'], height=200)
                        c1, c2 = st.columns(2)
                        with c1:
                            save_ex_edit = st.form_submit_button("💾 保存修改", use_container_width=True)
                        with c2:
                            cancel_ex_edit = st.form_submit_button("❌ 取消", use_container_width=True)
                        if save_ex_edit:
                            if not ee_title.strip():
                                st.error("标题不能为空！")
                            else:
                                try:
                                    example_manager.update_example(
                                        example_id=eid,
                                        title=ee_title.strip(),
                                        problem=ee_problem.strip(),
                                        solution=ee_solution.strip(),
                                        category=ee_category.strip() or '未分类',
                                        difficulty_level=DIFFICULTY_MAP[ee_diff_zh]
                                    )
                                    st.success("✅ 例题已更新！")
                                    st.session_state.edit_example_id = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"更新失败：{e}")
                        if cancel_ex_edit:
                            st.session_state.edit_example_id = None
                            st.rerun()
            else:
                # 展示模式
                header = f"{diff_label}  |  📖 {ex['title']}  |  🗂️ {ex.get('category', '未分类')}"
                with st.expander(header):
                    col_content, col_actions = st.columns([5, 1])
                    with col_content:
                        st.markdown(badge_html, unsafe_allow_html=True)
                        st.markdown("**❓ 题目**")
                        st.markdown(ex['problem'])
                        st.markdown("**✅ 解答**")
                        st.markdown(ex['solution'])
                        st.caption(
                            f"🕐 创建：{format_datetime(ex.get('created_at', ''))}　"
                            f"🔄 更新：{format_datetime(ex.get('updated_at', ''))}"
                        )
                    with col_actions:
                        # 复习状态切换
                        if reviewed:
                            if st.button("📌 取消复习", key=f"rev_{eid}", use_container_width=True):
                                try:
                                    example_manager.mark_reviewed(eid, False)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"操作失败：{e}")
                        else:
                            if st.button("✅ 标记复习", key=f"rev_{eid}", use_container_width=True):
                                try:
                                    example_manager.mark_reviewed(eid, True)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"操作失败：{e}")
                        if st.button("✏️ 编辑", key=f"edit_e_{eid}", use_container_width=True):
                            st.session_state.edit_example_id = eid
                            st.rerun()
                        # 删除确认
                        if st.session_state.confirm_delete_example == eid:
                            st.warning("确认删除？")
                            if st.button("✅ 确认", key=f"confirm_del_e_{eid}", use_container_width=True):
                                try:
                                    example_manager.delete_example(eid)
                                    st.success("已删除！")
                                    st.session_state.confirm_delete_example = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"删除失败：{e}")
                            if st.button("❌ 取消", key=f"cancel_del_e_{eid}", use_container_width=True):
                                st.session_state.confirm_delete_example = None
                                st.rerun()
                        else:
                            if st.button("🗑️ 删除", key=f"del_e_{eid}", use_container_width=True):
                                st.session_state.confirm_delete_example = eid
                                st.rerun()

# ═══════════════════════════════════════════════════════════════
# TAB 3：数据统计
# ═══════════════════════════════════════════════════════════════
elif tab_choice == "📊 数据统计":
    st.header("📊 数据统计")

    all_notes    = note_manager.get_all_notes()
    all_examples = example_manager.get_all_examples()

    # ── 总览数字 ─────────────────────────────────
    st.markdown("### 📈 总览")
    c1, c2, c3, c4 = st.columns(4)
    reviewed_count = sum(1 for e in all_examples if e.get('is_reviewed', False))

    with c1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{len(all_notes)}</div>
            <div class="stat-label">📝 笔记总数</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-box" style="background: linear-gradient(135deg,#f093fb,#f5576c)">
            <div class="stat-number">{len(all_examples)}</div>
            <div class="stat-label">📖 例题总数</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-box" style="background: linear-gradient(135deg,#4facfe,#00f2fe)">
            <div class="stat-number">{reviewed_count}</div>
            <div class="stat-label">✅ 已复习例题</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        total_cats = len({n.get('category') for n in all_notes} |
                         {e.get('category') for e in all_examples})
        st.markdown(f"""
        <div class="stat-box" style="background: linear-gradient(135deg,#43e97b,#38f9d7)">
            <div class="stat-number">{total_cats}</div>
            <div class="stat-label">🗂️ 分类总数</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 图表行 1 ─────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 📝 笔记分类分布")
        if all_notes:
            cat_counts = Counter(n.get('category', '未分类') for n in all_notes)
            fig_pie = px.pie(
                names=list(cat_counts.keys()),
                values=list(cat_counts.values()),
                color_discrete_sequence=px.colors.qualitative.Pastel,
                hole=0.35
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=True)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("暂无笔记数据")

    with col_right:
        st.markdown("#### 📖 例题难度分布")
        if all_examples:
            diff_counts = Counter(e.get('difficulty_level', 'medium') for e in all_examples)
            diff_labels = [DIFFICULTY_MAP_REVERSE.get(k, k) for k in diff_counts.keys()]
            diff_colors = {'简单': '#66bb6a', '中等': '#ffa726', '困难': '#ef5350'}
            fig_bar = go.Figure(go.Bar(
                x=diff_labels,
                y=list(diff_counts.values()),
                marker_color=[diff_colors.get(l, '#90caf9') for l in diff_labels],
                text=list(diff_counts.values()),
                textposition='outside'
            ))
            fig_bar.update_layout(
                xaxis_title="难度", yaxis_title="数量",
                margin=dict(t=20, b=20, l=20, r=20),
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("暂无例题数据")

    # ── 图表行 2 ─────────────────────────────────
    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.markdown("#### 🕐 最近活动时间线")
        activities = []
        for n in all_notes:
            activities.append({
                'time': n.get('updated_at', n.get('created_at', '')),
                'type': '📝 笔记',
                'title': n['title']
            })
        for e in all_examples:
            activities.append({
                'time': e.get('updated_at', e.get('created_at', '')),
                'type': '📖 例题',
                'title': e['title']
            })
        activities.sort(key=lambda x: x['time'], reverse=True)
        recent = activities[:10]
        if recent:
            for act in recent:
                st.markdown(
                    f"- `{format_datetime(act['time'])}` &nbsp; {act['type']} &nbsp; **{act['title']}**"
                )
        else:
            st.info("暂无活动记录")

    with col_right2:
        st.markdown("#### 🏷️ 标签云")
        all_tags = []
        for n in all_notes:
            all_tags.extend(n.get('tags', []))
        if all_tags:
            tag_counts = Counter(all_tags).most_common(30)
            max_count  = tag_counts[0][1] if tag_counts else 1
            tag_html   = ""
            for tag, cnt in tag_counts:
                size = 0.8 + (cnt / max_count) * 1.2
                tag_html += (
                    f'<span style="font-size:{size:.1f}rem; margin:4px; display:inline-block; '
                    f'background:#e3f2fd; color:#1565c0; border-radius:12px; padding:3px 10px;">'
                    f'#{tag} <small>({cnt})</small></span>'
                )
            st.markdown(tag_html, unsafe_allow_html=True)
        else:
            st.info("暂无标签数据")

    # ── 例题复习进度 ─────────────────────────────
    st.markdown("---")
    st.markdown("#### 📊 例题复习进度")
    if all_examples:
        not_reviewed = len(all_examples) - reviewed_count
        fig_progress = go.Figure(go.Bar(
            x=['已复习', '未复习'],
            y=[reviewed_count, not_reviewed],
            marker_color=['#66bb6a', '#ef9a9a'],
            text=[reviewed_count, not_reviewed],
            textposition='outside'
        ))
        fig_progress.update_layout(
            yaxis_title="数量",
            margin=dict(t=20, b=20, l=20, r=20),
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_progress, use_container_width=True)

        pct = reviewed_count / len(all_examples) * 100 if all_examples else 0
        st.progress(int(pct), text=f"复习完成度：{pct:.1f}%（{reviewed_count}/{len(all_examples)}）")
    else:
        st.info("暂无例题数据")
