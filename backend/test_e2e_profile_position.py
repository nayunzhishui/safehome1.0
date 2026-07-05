"""End-to-end test for T4-03 profile position write to DB."""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database import get_connection, init_db, json_dumps, now_iso, row_to_dict
from services.assessment_profile_service import build_assessment_profile_position

def main():
    init_db()

    # Step 0: 确保worksheet有profile_model_id
    with get_connection() as conn:
        # 更新worksheet
        conn.execute("""
            UPDATE assessment_worksheets
            SET profile_model_id = '2_李霞庆_父母反思功能对初中生情绪智力的影响_论文数据_2_李霞庆_父母反思功能对初中生情绪智力的影响_论文数据_研究一数据合集_父母调查数据_问卷星_sav_parent_reflective_functioning_prfq__3bfd36b18c'
            WHERE id = 'parent_reflective_functioning_prfq'
        """)
        conn.commit()

        # 读取worksheet（需要包含questions）
        ws_row = conn.execute("""
            SELECT id, display_title, profile_model_id, questions_json
            FROM assessment_worksheets
            WHERE id = 'parent_reflective_functioning_prfq'
        """).fetchone()

        if not ws_row or not ws_row[2]:
            print("[FAIL] Worksheet profile_model_id is None")
            return False

        from database import json_loads
        test_worksheet = {
            'id': ws_row[0],
            'display_title': ws_row[1],
            'profile_model_id': ws_row[2],
            'questions': json_loads(ws_row[3], [])
        }

    print("=== T4-03 End-to-End Test ===")
    print(f"Worksheet: {test_worksheet['id']}")
    print()

    # 构造完整的18题答案（注意：使用 'value' 而非 'answer'）
    test_answers = [
        {'question_id': f'PRFQ{i:02d}', 'value': 4 if i % 2 == 0 else 3}
        for i in range(1, 19)
    ]

    test_scores = {
        'dimensions': [
            {'key': 'PRFQ_PM', 'label': 'PM', 'score': 3.2},
            {'key': 'PRFQ_CM', 'label': 'CM', 'score': 4.8},
            {'key': 'PRFQ_IC', 'label': 'IC', 'score': 2.5}
        ],
        'total_score': 68,
        'risk': {'risk_level': 'low'}
    }

    result_id = 'test_' + str(uuid.uuid4())[:8]
    user_id = 'test_user_' + str(uuid.uuid4())[:8]

    with get_connection() as conn:
        # 插入测试记录
        conn.execute("""
            INSERT INTO assessment_results (
                id, user_id, worksheet_id, worksheet_title,
                answers_json, scores_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            result_id, user_id, test_worksheet['id'], test_worksheet['display_title'],
            json_dumps(test_answers),
            json_dumps(test_scores),
            now_iso()
        ))
        conn.commit()

        # 获取记录并计算落点
        row = conn.execute('SELECT * FROM assessment_results WHERE id = ?', (result_id,)).fetchone()
        result_dict = row_to_dict(row)

        try:
            position = build_assessment_profile_position(result_dict, test_worksheet)
            pos = position.get('position', {})

            print('[PASS] Step 1: Position Calculation')
            print(f'  Cluster ID: {pos.get("cluster_id", "N/A")}')
            print(f'  PC1: {pos.get("pc1", "N/A")}')
            print(f'  PC2: {pos.get("pc2", "N/A")}')
            print(f'  Confidence: {pos.get("confidence", "N/A")}')

            # 写入DB
            conn.execute("""
                UPDATE assessment_results SET
                    profile_model_id = ?,
                    profile_cluster_id = ?,
                    profile_pc1 = ?,
                    profile_pc2 = ?,
                    profile_confidence = ?
                WHERE id = ?
            """, (
                position.get('model_id'),
                pos.get('cluster_id'),
                pos.get('pc1'),
                pos.get('pc2'),
                pos.get('confidence'),
                result_id
            ))
            conn.commit()
            print('[PASS] Step 2: Write to DB')

            # 验证
            check = conn.execute("""
                SELECT profile_pc1, profile_pc2, profile_cluster_id, profile_confidence
                FROM assessment_results WHERE id = ?
            """, (result_id,)).fetchone()

            if check and check[0] is not None:
                print('[PASS] Step 3: Verification')
                print(f'  DB pc1: {check[0]:.4f}')
                print(f'  DB pc2: {check[1]:.4f}')
                print(f'  DB cluster: {check[2]}')
                print(f'  DB confidence: {check[3]:.2f}')
                print()
                print('=' * 50)
                print(' SUCCESS: T4-03 END-TO-END TEST PASSED')
                print('=' * 50)
                return True
            else:
                print('[FAIL] Verification: No data in DB')
                return False

        except Exception as e:
            print(f'[FAIL] {e}')
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
