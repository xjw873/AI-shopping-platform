# # export_history_to_excel.py
# import os
# import pandas as pd
# from sqlalchemy import create_engine
# from datetime import datetime

# # 数据库路径（根据你的实际路径调整）
# DB_PATH = "D:/rainbow/新建文件夹/文件夹/llm大创/模糊问题的澄清/平台1/chat_logs_new.db"
# OUTPUT_EXCEL = f"D:/rainbow/新建文件夹/文件夹/llm大创/模糊问题的澄清/平台1/chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

# def export_to_excel():
#     if not os.path.exists(DB_PATH):
#         print(f"❌ 数据库文件不存在: {os.path.abspath(DB_PATH)}")
#         return

#     # 创建数据库引擎
#     engine = create_engine(f"sqlite:///{DB_PATH}")

#     # 读取 users 表
#     try:
#         users_df = pd.read_sql_query(
#             "SELECT id as user_id, user_id as user_uuid, created_at FROM users ORDER BY created_at",
#             engine
#         )
#     except Exception as e:
#         print(f"❌ 读取用户表失败: {e}")
#         return

#     # 读取 conversations 表
#     try:
#         convs_df = pd.read_sql_query(
#             """
#             SELECT c.id, u.user_id as user_uuid, c.user_message, c.ai_response, 
#                    c.timestamp, c.model_used, c.message_rating, c.service_rating
#             FROM conversations c
#             JOIN users u ON c.user_id = u.id
#             ORDER BY c.timestamp
#             """,
#             engine
#         )
#     except Exception as e:
#         print(f"❌ 读取对话表失败: {e}")
#         return

#     if convs_df.empty:
#         print("⚠️ 数据库中没有对话记录。")
#         return

#     # 导出到 Excel，每个用户一个sheet
#     with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
#         # 导出用户信息
#         users_df.to_excel(writer, sheet_name='用户列表', index=False)
        
#         # 按用户分组导出对话
#         for user_uuid, group in convs_df.groupby('user_uuid'):
#             # 截断sheet名（Excel限制31字符）
#             sheet_name = str(user_uuid)[:31]
            
#             # 重命名列
#             group = group.rename(columns={
#                 'id': '对话ID',
#                 'user_uuid': '用户ID',
#                 'user_message': '用户消息',
#                 'ai_response': 'AI回复',
#                 'timestamp': '时间',
#                 'model_used': '使用模型',
#                 'message_rating': '单条评分',
#                 'service_rating': '服务评分'
#             })
            
#             group.to_excel(writer, sheet_name=sheet_name, index=False)

#     print(f"✅ 成功导出到: {os.path.abspath(OUTPUT_EXCEL)}")
#     print(f"📊 用户数量: {len(users_df)}")
#     print(f"💬 对话总数: {len(convs_df)}")

# if __name__ == "__main__":
#     export_to_excel()

# export_sessions.py
import os
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

DB_PATH = r"D:\rainbow\新建文件夹\文件夹\llm大创\模糊问题的澄清\平台1\chat_logs_new1.db"
OUTPUT_EXCEL = f"D:/rainbow/新建文件夹/文件夹/llm大创/模糊问题的澄清/平台1/会话记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

def export_sessions():
    """导出所有会话和对话记录"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {os.path.abspath(DB_PATH)}")
        return

    engine = create_engine(f"sqlite:///{DB_PATH}")

    try:
        # 读取会话数据
        sessions_df = pd.read_sql_query(
            """
            SELECT 
                s.session_id as 会话ID,
                u.user_id as 用户ID,
                s.model_used as 使用模型,
                s.start_time as 开始时间,
                s.end_time as 结束时间,
                s.is_active as 是否活跃,
                COUNT(c.id) as 对话轮数
            FROM chat_sessions s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN conversations c ON s.id = c.session_id
            GROUP BY s.id
            ORDER BY s.start_time DESC
            """,
            engine
        )
    except Exception as e:
        print(f"❌ 读取会话表失败: {e}")
        return

    try:
        # 读取详细的对话数据
        convs_df = pd.read_sql_query(
            """
            SELECT 
                s.session_id as 会话ID,
                c.turn_number as 轮次,
                c.user_message as 用户提问,
                c.ai_response as AI回复,
                c.timestamp as 时间,
                c.message_rating as 消息评分
            FROM conversations c
            JOIN chat_sessions s ON c.session_id = s.id
            ORDER BY s.session_id, c.turn_number
            """,
            engine
        )
    except Exception as e:
        print(f"❌ 读取对话表失败: {e}")
        return

    if sessions_df.empty:
        print("⚠️ 数据库中没有会话记录。")
        return

    # 导出到Excel
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        # 1. 会话概览表
        sessions_df.to_excel(writer, sheet_name='会话概览', index=False)
        
        # 2. 详细对话记录表
        convs_df.to_excel(writer, sheet_name='所有对话记录', index=False)
        
        # 3. 按会话分组，每个会话一个sheet
        for session_id, session_convs in convs_df.groupby('会话ID'):
            # 获取会话信息
            session_info = sessions_df[sessions_df['会话ID'] == session_id]
            
            # 创建sheet名称
            sheet_name = f"会话_{session_id[:20]}"
            if len(sheet_name) > 31:
                sheet_name = sheet_name[:31]
            
            # 准备数据
            session_data = session_convs.copy()
            
            # 写入Excel
            session_data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 自动调整列宽
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

    print(f"✅ 成功导出到: {os.path.abspath(OUTPUT_EXCEL)}")
    print(f"💼 会话数量: {len(sessions_df)}")
    print(f"💬 对话记录总数: {len(convs_df)}")

if __name__ == "__main__":
    print("=== 导出会话和对话记录 ===")
    export_sessions()